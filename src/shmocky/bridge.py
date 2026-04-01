from __future__ import annotations

import asyncio
import contextlib
import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .event_store import RawEventStore
from .models import (
    CodexAgentConfig,
    DashboardSnapshot,
    EventChannel,
    EventDirection,
    EventMessageType,
    RawEventRecord,
    TranscriptItem,
    StreamEnvelope,
)
from .projection import SessionProjection
from .settings import AppSettings


class BridgeError(RuntimeError):
    """Raised when the app-server bridge cannot complete a request."""


class CodexAppServerBridge:
    def __init__(
        self,
        settings: AppSettings,
        *,
        workspace_root: Path | None = None,
        event_log_dir: Path | None = None,
        agent_config: CodexAgentConfig | None = None,
    ) -> None:
        self._settings = settings
        self._workspace_root = (workspace_root or settings.workspace_root).expanduser().resolve()
        self._agent_config = agent_config or CodexAgentConfig(role="engineer")
        event_log_root = event_log_dir or settings.event_log_dir
        event_log_path = self._make_event_log_path(event_log_root)
        self._event_store = RawEventStore(event_log_path)
        self._projection = SessionProjection(
            workspace_root=str(self._workspace_root),
            event_log_path=str(event_log_path),
        )
        self._recent_events: deque[RawEventRecord] = deque(maxlen=300)
        self._process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()
        self._thread_lock = asyncio.Lock()
        self._subscribers: set[asyncio.Queue[StreamEnvelope]] = set()
        self._request_counter = 0
        self._pending: dict[str, tuple[str, asyncio.Future[dict[str, Any]]]] = {}

    async def start(self) -> None:
        self._settings.event_log_dir.mkdir(parents=True, exist_ok=True)
        self._process = await asyncio.create_subprocess_exec(
            self._settings.codex_command,
            "app-server",
            cwd=str(self._workspace_root),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._projection.mark_process_started(self._process.pid)
        await self._append_internal_event(
            message="codex app-server started",
            payload={"pid": self._process.pid},
        )
        self._reader_task = asyncio.create_task(self._read_stdout())
        self._stderr_task = asyncio.create_task(self._read_stderr())
        await self._call(
            "initialize",
            {
                "clientInfo": {
                    "name": "shmocky",
                    "title": "Shmocky Browser Mirror",
                    "version": "0.1.0",
                },
                "capabilities": {
                    "experimentalApi": self._settings.experimental_api,
                },
            },
        )

    async def stop(self) -> None:
        if self._process is None:
            return
        if self._process.returncode is None:
            self._process.terminate()
            with contextlib.suppress(ProcessLookupError):
                await asyncio.wait_for(self._process.wait(), timeout=5)
        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._projection.mark_process_stopped()
        await self._append_internal_event(message="codex app-server stopped")
        self._process = None

    def snapshot(self) -> DashboardSnapshot:
        return DashboardSnapshot(
            state=self._projection.snapshot(),
            recent_events=[event.model_copy(deep=True) for event in self._recent_events],
        )

    async def resume_thread(self, thread_id: str) -> DashboardSnapshot:
        async with self._thread_lock:
            state = self._projection.snapshot()
            if state.thread is None or state.thread.id != thread_id:
                config: dict[str, Any] = {}
                if self._agent_config.reasoning_effort is not None:
                    config["model_reasoning_effort"] = self._agent_config.reasoning_effort
                if self._agent_config.web_access is not None:
                    config["web_search"] = self._agent_config.web_access
                await self._call(
                    "thread/resume",
                    {
                        "threadId": thread_id,
                        "cwd": str(self._workspace_root),
                        "approvalPolicy": self._agent_config.approval_policy,
                        "sandbox": self._agent_config.sandbox_mode,
                        "developerInstructions": self._agent_config.startup_prompt,
                        "model": self._agent_config.model,
                        "modelProvider": self._agent_config.model_provider,
                        "serviceTier": self._agent_config.service_tier,
                        "config": config or None,
                    },
                )
        return self.snapshot()

    def seed_transcript(self, items: list[TranscriptItem]) -> DashboardSnapshot:
        self._projection.seed_transcript(items)
        return self.snapshot()

    async def ensure_thread(self) -> DashboardSnapshot:
        async with self._thread_lock:
            state = self._projection.snapshot()
            if state.thread is None:
                config: dict[str, Any] = {}
                if self._agent_config.reasoning_effort is not None:
                    config["model_reasoning_effort"] = self._agent_config.reasoning_effort
                if self._agent_config.web_access is not None:
                    config["web_search"] = self._agent_config.web_access
                await self._call(
                    "thread/start",
                    {
                        "cwd": str(self._workspace_root),
                        "approvalPolicy": self._agent_config.approval_policy,
                        "sandbox": self._agent_config.sandbox_mode,
                        "developerInstructions": self._agent_config.startup_prompt,
                        "model": self._agent_config.model,
                        "modelProvider": self._agent_config.model_provider,
                        "serviceTier": self._agent_config.service_tier,
                        "config": config or None,
                        "experimentalRawEvents": False,
                        "persistExtendedHistory": True,
                    },
                )
        return self.snapshot()

    async def start_turn(self, prompt: str) -> DashboardSnapshot:
        state = await self.ensure_thread()
        thread = state.state.thread
        if thread is None:
            raise BridgeError("Thread could not be created")
        await self._call(
            "turn/start",
            {
                "threadId": thread.id,
                "input": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
            },
        )
        return self.snapshot()

    async def interrupt_turn(self) -> DashboardSnapshot:
        state = self._projection.snapshot()
        if state.thread is None or state.turn is None:
            return self.snapshot()
        await self._call(
            "turn/interrupt",
            {
                "threadId": state.thread.id,
                "turnId": state.turn.id,
            },
        )
        return self.snapshot()

    async def resolve_server_request(self, request_id: str, *, result: Any) -> DashboardSnapshot:
        state = self._projection.snapshot()
        pending = state.pending_server_request
        if pending is None:
            raise BridgeError("There is no pending server request to resolve.")
        if pending.request_id != request_id:
            raise BridgeError(
                f"Pending server request is '{pending.request_id}', not '{request_id}'."
            )
        await self._send_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            },
            direction="outbound",
            channel="rpc",
            message_type="response",
        )
        return self.snapshot()

    async def wait_for_turn_completion(self, turn_id: str) -> DashboardSnapshot:
        queue = await self.subscribe()
        try:
            while True:
                snapshot = self.snapshot()
                if self._is_terminal_turn(snapshot, turn_id):
                    return snapshot
                envelope = await queue.get()
                if self._is_terminal_turn(
                    DashboardSnapshot(
                        state=envelope.state,
                        recent_events=[],
                    ),
                    turn_id,
                ):
                    return self.snapshot()
        finally:
            self.unsubscribe(queue)

    async def subscribe(self) -> asyncio.Queue[StreamEnvelope]:
        queue: asyncio.Queue[StreamEnvelope] = asyncio.Queue(maxsize=512)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        self._subscribers.discard(queue)

    async def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._process is None or self._process.stdin is None:
            raise BridgeError("codex app-server is not running")
        self._request_counter += 1
        request_id = str(self._request_counter)
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[request_id] = (method, future)
        await self._send_message(
            message,
            direction="outbound",
            channel="rpc",
            message_type="request",
            method=method,
        )
        try:
            response = await asyncio.wait_for(
                future,
                timeout=self._settings.request_timeout_seconds,
            )
        except TimeoutError as exc:
            self._pending.pop(request_id, None)
            raise BridgeError(f"Timed out waiting for {method}") from exc
        if "error" in response:
            raise BridgeError(f"{method} failed: {response['error']}")
        return response.get("result", {})

    async def _read_stdout(self) -> None:
        assert self._process is not None
        assert self._process.stdout is not None
        while True:
            line = await self._process.stdout.readline()
            if not line:
                return_code = await self._process.wait()
                self._projection.mark_process_stopped(
                    error=f"codex app-server exited with code {return_code}"
                )
                await self._append_internal_event(
                    message="codex app-server exited",
                    payload={"returncode": return_code},
                )
                return
            raw = line.decode("utf-8").strip()
            if not raw:
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await self._append_internal_event(
                    message="received invalid JSON from app-server",
                    payload={"raw": raw},
                )
                continue
            await self._handle_inbound_message(message)

    async def _read_stderr(self) -> None:
        assert self._process is not None
        assert self._process.stderr is not None
        while True:
            line = await self._process.stderr.readline()
            if not line:
                return
            text = line.decode("utf-8").rstrip()
            if not text:
                continue
            await self._record_event(
                {"text": text},
                direction="inbound",
                channel="stderr",
                message_type="stderr",
            )

    async def _handle_inbound_message(self, message: dict[str, Any]) -> None:
        message_type = self._classify_inbound_message(message)
        record = await self._record_event(
            message,
            direction="inbound",
            channel="rpc",
            message_type=message_type,
            method=message.get("method"),
        )
        if message_type == "response":
            request_id = str(message.get("id"))
            pending = self._pending.pop(request_id, None)
            if pending is not None:
                method, future = pending
                if "result" in message and isinstance(message["result"], dict):
                    self._projection.apply_response(method, message["result"])
                if not future.done():
                    future.set_result(message)
        elif message_type == "notification":
            method = message.get("method")
            params = message.get("params")
            if isinstance(method, str) and isinstance(params, dict):
                self._projection.apply_notification(method, params)
        elif message_type == "server_request":
            request_id = str(message.get("id"))
            method = str(message.get("method"))
            params = message.get("params")
            self._projection.apply_server_request(
                request_id=request_id,
                method=method,
                params=params if isinstance(params, dict) else None,
            )
        await self._broadcast_event(record)

    async def _send_message(
        self,
        message: dict[str, Any],
        *,
        direction: EventDirection,
        channel: EventChannel,
        message_type: EventMessageType,
        method: str | None = None,
    ) -> None:
        if self._process is None or self._process.stdin is None:
            raise BridgeError("codex app-server is not running")
        await self._record_event(
            message,
            direction=direction,
            channel=channel,
            message_type=message_type,
            method=method,
        )
        encoded = json.dumps(message, separators=(",", ":")) + "\n"
        async with self._send_lock:
            self._process.stdin.write(encoded.encode("utf-8"))
            await self._process.stdin.drain()

    async def _record_event(
        self,
        payload: object,
        *,
        direction: EventDirection,
        channel: EventChannel,
        message_type: EventMessageType,
        method: str | None = None,
    ) -> RawEventRecord:
        record = await self._event_store.append(
            direction=direction,
            channel=channel,
            message_type=message_type,
            payload=payload,
            method=method,
        )
        self._recent_events.append(record)
        return record

    async def _append_internal_event(
        self,
        *,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        record = await self._record_event(
            {
                "message": message,
                "payload": payload or {},
                "recordedAt": datetime.now(UTC).isoformat(),
            },
            direction="internal",
            channel="lifecycle",
            message_type="lifecycle",
        )
        await self._broadcast_event(record)

    async def _broadcast_event(self, record: RawEventRecord) -> None:
        if not self._subscribers:
            return
        envelope = StreamEnvelope(type="event", event=record, state=self._projection.snapshot())
        stale: list[asyncio.Queue[StreamEnvelope]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self._subscribers.discard(queue)

    @staticmethod
    def _classify_inbound_message(message: dict[str, Any]) -> EventMessageType:
        if "id" in message and "method" in message:
            return "server_request"
        if "id" in message:
            return "response"
        if "method" in message:
            return "notification"
        return "unknown"

    @staticmethod
    def _make_event_log_path(directory: Path) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return directory / f"codex-app-server-{timestamp}.jsonl"

    @staticmethod
    def _is_terminal_turn(snapshot: DashboardSnapshot, turn_id: str) -> bool:
        turn = snapshot.state.turn
        if turn is None or turn.id != turn_id:
            return False
        return turn.status in {"completed", "failed", "cancelled", "interrupted"}
