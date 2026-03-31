from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any, cast

from .models import (
    ConnectionState,
    DashboardState,
    PendingServerRequest,
    ThreadState,
    TranscriptItem,
    TurnState,
)


class SessionProjection:
    """Small in-memory view over raw app-server events."""

    def __init__(self, *, workspace_root: str, event_log_path: str) -> None:
        self._state = DashboardState(
            workspace_root=workspace_root,
            event_log_path=event_log_path,
            connection=ConnectionState(),
        )
        self._transcript = OrderedDict[str, TranscriptItem]()

    def snapshot(self) -> DashboardState:
        state = self._state.model_copy(deep=True)
        state.transcript = [item.model_copy(deep=True) for item in self._transcript.values()]
        return state

    def mark_process_started(self, pid: int) -> None:
        self._state.connection.backend_online = True
        self._state.connection.app_server_pid = pid
        self._state.connection.last_error = None

    def mark_process_stopped(self, *, error: str | None = None) -> None:
        self._state.connection.codex_connected = False
        self._state.connection.initialized = False
        self._state.connection.app_server_pid = None
        if error is not None:
            self._state.connection.last_error = error

    def apply_response(self, method: str, result: dict[str, Any] | None) -> None:
        if method == "initialize" and result is not None:
            self._state.connection.codex_connected = True
            self._state.connection.initialized = True
            self._state.connection.app_server_user_agent = result.get("userAgent")
            self._state.connection.codex_home = result.get("codexHome")
            self._state.connection.platform_family = result.get("platformFamily")
            self._state.connection.platform_os = result.get("platformOs")
            return
        if method == "thread/start" and result is not None:
            self._update_thread(result.get("thread"), response=result)
            return
        if method == "turn/start" and result is not None:
            self._update_turn(result.get("turn"))
            return
        if method == "turn/interrupt" and self._state.turn is not None:
            self._state.turn.status = "interruptRequested"
            self._state.turn.last_event_at = datetime.now(UTC)

    def apply_notification(self, method: str, params: dict[str, Any]) -> None:
        match method:
            case "error":
                self._state.connection.last_error = params.get("message") or str(params)
            case "thread/started":
                self._update_thread(params.get("thread"))
            case "thread/status/changed":
                if self._state.thread is not None:
                    self._state.thread.status = params.get("status", {}).get("type", "unknown")
            case "turn/started":
                self._update_turn(params.get("turn"))
            case "turn/completed":
                self._update_turn(params.get("turn"))
            case "mcpServer/startupStatus/updated":
                name = params.get("name")
                status = params.get("status")
                if isinstance(name, str) and isinstance(status, str):
                    self._state.mcp_servers[name] = status
            case "account/rateLimits/updated":
                self._state.rate_limits = params.get("rateLimits")
            case "item/started":
                self._upsert_transcript_item(params.get("item"), streaming=True)
            case "item/completed":
                self._upsert_transcript_item(params.get("item"), streaming=False)
            case "item/agentMessage/delta":
                self._append_agent_delta(params)
            case "serverRequest/resolved":
                if self._state.pending_server_request is not None:
                    if self._state.pending_server_request.request_id == str(params.get("id")):
                        self._state.pending_server_request = None

    def apply_server_request(self, request_id: str, method: str) -> None:
        self._state.pending_server_request = PendingServerRequest(
            request_id=request_id,
            method=method,
            noted_at=datetime.now(UTC),
        )

    def _update_thread(
        self,
        thread_payload: dict[str, Any] | None,
        *,
        response: dict[str, Any] | None = None,
    ) -> None:
        if not thread_payload:
            return
        previous = self._state.thread if self._state.thread and self._state.thread.id == thread_payload["id"] else None
        sandbox = response.get("sandbox") if response else None
        sandbox_type = previous.sandbox_mode if previous is not None else None
        if isinstance(sandbox, dict):
            sandbox_type = sandbox.get("type")
        self._state.thread = ThreadState(
            id=thread_payload["id"],
            status=thread_payload.get("status", {}).get("type", previous.status if previous is not None else "idle"),
            cwd=thread_payload.get("cwd", previous.cwd if previous is not None else None),
            model=response.get("model") if response else (previous.model if previous is not None else None),
            model_provider=(
                response.get("modelProvider")
                if response
                else thread_payload.get("modelProvider", previous.model_provider if previous is not None else None)
            ),
            approval_policy=(
                response.get("approvalPolicy")
                if response
                else (previous.approval_policy if previous is not None else None)
            ),
            sandbox_mode=sandbox_type,
            reasoning_effort=(
                response.get("reasoningEffort")
                if response
                else (previous.reasoning_effort if previous is not None else None)
            ),
            created_at=thread_payload.get("createdAt", previous.created_at if previous is not None else None),
            updated_at=thread_payload.get("updatedAt", previous.updated_at if previous is not None else None),
        )

    def _update_turn(self, turn_payload: dict[str, Any] | None) -> None:
        if not turn_payload:
            return
        self._state.turn = TurnState(
            id=turn_payload["id"],
            status=turn_payload.get("status", "unknown"),
            last_event_at=datetime.now(UTC),
            error=self._extract_turn_error(turn_payload.get("error")),
        )

    def _upsert_transcript_item(self, item: dict[str, Any] | None, *, streaming: bool) -> None:
        if not item:
            return
        item_type = item.get("type")
        item_id = item.get("id")
        if item_type not in {"userMessage", "agentMessage"} or not isinstance(item_id, str):
            return
        role = "user" if item_type == "userMessage" else "assistant"
        text = self._extract_item_text(item)
        phase = item.get("phase")
        turn_id = self._state.turn.id if self._state.turn is not None else None
        current = self._transcript.get(item_id)
        if current is None:
            current = TranscriptItem(
                item_id=item_id,
                role=role,
                text=text,
                phase=phase,
                status="streaming" if streaming and role == "assistant" else "completed",
                turn_id=turn_id,
            )
            self._transcript[item_id] = current
        else:
            current.text = text or current.text
            current.phase = phase or current.phase
            current.status = "streaming" if streaming and role == "assistant" else "completed"
        self._trim_transcript()

    def _append_agent_delta(self, params: dict[str, Any]) -> None:
        item_id = params.get("itemId")
        delta = params.get("delta")
        if not isinstance(item_id, str) or not isinstance(delta, str):
            return
        current = self._transcript.get(item_id)
        if current is None:
            current = TranscriptItem(
                item_id=item_id,
                role="assistant",
                text="",
                status="streaming",
                turn_id=params.get("turnId"),
            )
            self._transcript[item_id] = current
        current.text += delta
        current.status = "streaming"
        self._trim_transcript()

    def _trim_transcript(self, *, limit: int = 200) -> None:
        while len(self._transcript) > limit:
            self._transcript.popitem(last=False)

    @staticmethod
    def _extract_turn_error(error: object) -> str | None:
        if error is None:
            return None
        if isinstance(error, str):
            return error
        if isinstance(error, dict):
            message = cast(dict[str, object], error).get("message")
            if isinstance(message, str):
                return message
        return str(error)

    @staticmethod
    def _extract_item_text(item: dict[str, Any]) -> str:
        if item.get("type") == "agentMessage":
            text = item.get("text")
            return text if isinstance(text, str) else ""
        content = item.get("content")
        if not isinstance(content, list):
            return ""
        parts: list[str] = []
        for entry in content:
            if isinstance(entry, dict) and entry.get("type") == "text":
                text = entry.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
