from __future__ import annotations

import asyncio
import json
import re
import subprocess
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from .bridge import BridgeError, CodexAppServerBridge
from .event_store import WorkflowEventStore
from .models import (
    CodexAgentConfig,
    ConnectionState,
    DashboardSnapshot,
    DashboardState,
    JudgeDecision,
    OracleQueryRequest,
    RunHistoryEntry,
    RunHistoryResponse,
    WorkflowPhase,
    WorkflowRunStatus,
    StreamEnvelope,
    WorkflowCatalogResponse,
    WorkflowEventRecord,
    WorkflowRunRequest,
    WorkflowRunState,
    WorkflowSteerRequest,
)
from .oracle_agent import OracleAgent, OracleAgentError, OracleNotConfiguredError
from .settings import AppSettings
from .workflow_config import WorkflowConfigError, WorkflowConfigLoader


class WorkflowSupervisorError(RuntimeError):
    pass


class WorkflowConflictError(WorkflowSupervisorError):
    pass


class WorkflowNotFoundError(WorkflowSupervisorError):
    pass


class WorkflowStoppedError(WorkflowSupervisorError):
    pass


@dataclass(slots=True)
class RunResources:
    run_dir: Path
    workflow_event_store: WorkflowEventStore


class WorkflowSupervisor:
    RUN_MANIFEST_FILENAME = "run.json"
    RUN_SNAPSHOT_FILENAME = "dashboard-snapshot.json"

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._loader = WorkflowConfigLoader(settings)
        self._oracle = OracleAgent(settings)
        self._lock = asyncio.Lock()
        self._subscribers: set[asyncio.Queue[StreamEnvelope]] = set()
        self._recent_workflow_events: deque[WorkflowEventRecord] = deque(maxlen=200)
        self._run_state: WorkflowRunState | None = None
        self._run_task: asyncio.Task[None] | None = None
        self._bridge: CodexAppServerBridge | None = None
        self._bridge_task: asyncio.Task[None] | None = None
        self._bridge_queue: asyncio.Queue[StreamEnvelope] | None = None
        self._resources: RunResources | None = None
        self._archived_snapshot: DashboardSnapshot | None = None
        self._pause_gate = asyncio.Event()
        self._pause_gate.set()
        self._last_catalog_error: str | None = None

    def snapshot(self) -> DashboardSnapshot:
        if self._bridge is None and self._archived_snapshot is not None:
            snapshot = self._archived_snapshot.model_copy(deep=True)
            snapshot.state.connection.backend_online = True
            snapshot.state.connection.codex_connected = False
            snapshot.state.connection.initialized = False
            snapshot.state.connection.app_server_pid = None
            snapshot.state.pending_server_request = None
            if self._run_state is not None:
                snapshot.state.workflow_run = self._run_state.model_copy(deep=True)
            return snapshot

        bridge_snapshot = self._bridge.snapshot() if self._bridge is not None else None
        bridge_state = bridge_snapshot.state if bridge_snapshot is not None else None
        workspace_root = (
            bridge_state.workspace_root if bridge_state is not None else str(self._settings.workspace_root)
        )
        event_log_path = (
            bridge_state.event_log_path
            if bridge_state is not None
            else str(self._settings.event_log_dir)
        )
        state = DashboardState(
            workspace_root=workspace_root,
            event_log_path=event_log_path,
            connection=(
                bridge_state.connection.model_copy(deep=True)
                if bridge_state is not None
                else ConnectionState()
            ),
            thread=bridge_state.thread.model_copy(deep=True) if bridge_state and bridge_state.thread else None,
            turn=bridge_state.turn.model_copy(deep=True) if bridge_state and bridge_state.turn else None,
            transcript=(
                [item.model_copy(deep=True) for item in bridge_state.transcript]
                if bridge_state is not None
                else []
            ),
            mcp_servers=dict(bridge_state.mcp_servers) if bridge_state is not None else {},
            rate_limits=bridge_state.rate_limits if bridge_state is not None else None,
            pending_server_request=(
                bridge_state.pending_server_request.model_copy(deep=True)
                if bridge_state and bridge_state.pending_server_request
                else None
            ),
            workflow_run=self._run_state.model_copy(deep=True) if self._run_state is not None else None,
        )
        return DashboardSnapshot(
            state=state,
            recent_events=bridge_snapshot.recent_events if bridge_snapshot is not None else [],
            recent_workflow_events=[
                record.model_copy(deep=True) for record in self._recent_workflow_events
            ],
        )

    def runs_history(self) -> RunHistoryResponse:
        run_entries: list[RunHistoryEntry] = []
        for run_dir in sorted(
            self._settings.run_log_dir.glob("*"),
            key=lambda path: path.name,
            reverse=True,
        ):
            if not run_dir.is_dir():
                continue
            snapshot_path = run_dir / self.RUN_SNAPSHOT_FILENAME
            if not snapshot_path.exists():
                continue
            try:
                snapshot = DashboardSnapshot.model_validate_json(
                    snapshot_path.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            workflow_run = snapshot.state.workflow_run
            if workflow_run is None:
                continue
            run_entries.append(
                RunHistoryEntry(
                    id=workflow_run.id,
                    run_name=workflow_run.run_name,
                    workflow_id=workflow_run.workflow_id,
                    target_dir=workflow_run.target_dir,
                    status=workflow_run.status,
                    phase=workflow_run.phase,
                    started_at=workflow_run.started_at,
                    updated_at=workflow_run.updated_at,
                    completed_at=workflow_run.completed_at,
                    last_judge_decision=workflow_run.last_judge_decision,
                    last_judge_summary=workflow_run.last_judge_summary,
                    last_error=workflow_run.last_error,
                )
            )
        return RunHistoryResponse(runs=run_entries)

    def load_run_snapshot(self, run_id: str) -> DashboardSnapshot:
        snapshot_path = self._settings.run_log_dir / run_id / self.RUN_SNAPSHOT_FILENAME
        if not snapshot_path.exists():
            raise WorkflowNotFoundError(f"Unknown run '{run_id}'.")
        try:
            return DashboardSnapshot.model_validate_json(
                snapshot_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise WorkflowSupervisorError(
                f"Stored snapshot for run '{run_id}' is unreadable."
            ) from exc

    def workflows_catalog(self) -> WorkflowCatalogResponse:
        try:
            catalog = self._loader.load()
            self._last_catalog_error = None
            return catalog
        except WorkflowConfigError as exc:
            self._last_catalog_error = str(exc)
            return WorkflowCatalogResponse(
                config_path=str(self._loader.path),
                loaded=False,
                error=str(exc),
            )

    async def subscribe(self) -> asyncio.Queue[StreamEnvelope]:
        queue: asyncio.Queue[StreamEnvelope] = asyncio.Queue(maxsize=512)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        self._subscribers.discard(queue)

    async def shutdown(self) -> None:
        async with self._lock:
            if self._run_task is not None:
                self._run_task.cancel()
                try:
                    await self._run_task
                except asyncio.CancelledError:
                    pass
                self._run_task = None
            await self._stop_bridge()

    async def start_thread(self) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        return await self._bridge.ensure_thread()

    async def send_prompt(self, prompt: str) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        return await self._bridge.start_turn(prompt)

    async def interrupt_turn(self) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        return await self._bridge.interrupt_turn()

    async def start_run(self, payload: WorkflowRunRequest) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is not None and self._run_state.status in {
                "starting",
                "running",
                "paused",
            }:
                raise WorkflowConflictError("A workflow run is already active.")

            catalog = self._loader.load()
            workflow = next(
                (entry for entry in catalog.workflows if entry.id == payload.workflow_id),
                None,
            )
            if workflow is None:
                raise WorkflowNotFoundError(f"Unknown workflow '{payload.workflow_id}'.")

            target_dir = self._validate_target_dir(Path(payload.target_dir))

            agent_by_id = {agent.id: agent for agent in catalog.agents}
            codex_agent = agent_by_id[workflow.executor_agent]
            expert_agent = (
                agent_by_id[workflow.expert_agent]
                if workflow.expert_agent is not None
                else None
            )
            judge_agent = agent_by_id[workflow.judge_agent]

            run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
            run_dir = self._settings.run_log_dir / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            resources = RunResources(
                run_dir=run_dir,
                workflow_event_store=WorkflowEventStore(run_dir / "workflow-events.jsonl"),
            )
            self._resources = resources
            self._archived_snapshot = None
            self._recent_workflow_events.clear()
            self._pause_gate.set()
            self._run_state = WorkflowRunState(
                id=run_id,
                run_name=payload.run_name.strip() if payload.run_name else None,
                workflow_id=workflow.id,
                target_dir=str(target_dir),
                goal=payload.prompt,
                status="starting",
                phase="idle",
                codex_agent_id=codex_agent.id,
                expert_agent_id=expert_agent.id if expert_agent is not None else None,
                judge_agent_id=judge_agent.id,
                started_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                max_loops=workflow.max_loops,
                max_judge_calls=workflow.max_judge_calls,
                max_runtime_minutes=workflow.max_runtime_minutes,
            )
            self._write_json(
                run_dir / self.RUN_MANIFEST_FILENAME,
                {
                    "runId": run_id,
                    "request": payload.model_dump(mode="json"),
                    "workflow": workflow.model_dump(mode="json"),
                    "agents": {
                        "codex": codex_agent.model_dump(mode="json"),
                        "expert": (
                            expert_agent.model_dump(mode="json")
                            if expert_agent is not None
                            else None
                        ),
                        "judge": judge_agent.model_dump(mode="json"),
                    },
                },
            )
            self._persist_run_snapshot()
            await self._record_workflow_event(
                "run_started",
                (
                    f"Started run '{self._run_state.run_name}' using workflow '{workflow.id}' for {target_dir}"
                    if self._run_state.run_name
                    else f"Started workflow '{workflow.id}' for {target_dir}"
                ),
                payload={
                    "runId": run_id,
                    "runName": self._run_state.run_name,
                    "workflowId": workflow.id,
                    "targetDir": str(target_dir),
                },
            )
            await self._start_bridge(target_dir, codex_agent)
            self._run_task = asyncio.create_task(
                self._execute_run(workflow, codex_agent, expert_agent, judge_agent)
            )
            await self._broadcast_state()
            return self.snapshot()

    def _validate_target_dir(self, target_dir: Path) -> Path:
        resolved = target_dir.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise WorkflowSupervisorError(
                f"Target directory does not exist or is not a directory: {resolved}"
            )
        if not self._settings.allow_nested_target_dirs and resolved.is_relative_to(
            self._settings.workspace_root
        ):
            raise WorkflowSupervisorError(
                "Target directory is inside the Shmocky workspace. "
                "Use a repository root or an external directory for isolation."
            )

        containing_git_root = self._git_root_for(resolved)
        if (
            not self._settings.allow_nested_target_dirs
            and containing_git_root is not None
            and containing_git_root != resolved
        ):
            raise WorkflowSupervisorError(
                "Target directory is nested inside another git repository: "
                f"{containing_git_root}. Use the repository root itself so parent repo "
                "instructions and history do not leak into the run."
            )
        return resolved

    async def pause_run(self) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            if self._run_state.status in {"completed", "failed", "stopped"}:
                return self.snapshot()
            self._run_state.pause_requested = True
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                "pause_requested",
                "Pause requested; the run will pause after the current step.",
            )
            return self.snapshot()

    async def resume_run(self) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            self._run_state.pause_requested = False
            if self._run_state.status == "paused":
                self._run_state.status = "running"
                self._run_state.updated_at = datetime.now(UTC)
                self._pause_gate.set()
                await self._record_workflow_event("resumed", "Workflow run resumed.")
            return self.snapshot()

    async def stop_run(self) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            self._run_state.stop_requested = True
            self._run_state.updated_at = datetime.now(UTC)
            self._pause_gate.set()
            if self._bridge is not None:
                await self._bridge.interrupt_turn()
            await self._record_workflow_event(
                "stop_requested",
                "Stop requested; the run will stop after the current step.",
            )
            return self.snapshot()

    async def steer_run(self, payload: WorkflowSteerRequest) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            self._run_state.pending_steering_notes.append(payload.note.strip())
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                "steer_queued",
                "Queued an operator steering note for the next Codex execution turn.",
                payload={"note": payload.note.strip()},
            )
            return self.snapshot()

    async def _start_bridge(self, target_dir: Path, codex_agent: Any) -> None:
        await self._stop_bridge()
        bridge = CodexAppServerBridge(
            self._settings,
            workspace_root=target_dir,
            event_log_dir=(self._resources.run_dir / "codex-events") if self._resources else None,
            agent_config=CodexAgentConfig(
                role=codex_agent.role,
                startup_prompt=codex_agent.startup_prompt,
                description=codex_agent.description,
                model=codex_agent.model,
                model_provider=codex_agent.model_provider,
                reasoning_effort=codex_agent.reasoning_effort,
                approval_policy=codex_agent.approval_policy or "never",
                sandbox_mode=codex_agent.sandbox_mode or "workspace-write",
                web_access=codex_agent.web_access or "disabled",
                service_tier=codex_agent.service_tier,
            ),
        )
        await bridge.start()
        queue = await bridge.subscribe()
        self._bridge = bridge
        self._bridge_queue = queue
        self._bridge_task = asyncio.create_task(self._relay_bridge_events(queue))
        await self._record_workflow_event(
            "codex_session_started",
            "Started Codex app-server session for the workflow run.",
            payload={"workspaceRoot": str(target_dir)},
        )

    async def _stop_bridge(self) -> None:
        if self._bridge_task is not None:
            self._bridge_task.cancel()
            try:
                await self._bridge_task
            except asyncio.CancelledError:
                pass
            self._bridge_task = None
        if self._bridge is not None and self._bridge_queue is not None:
            self._bridge.unsubscribe(self._bridge_queue)
        if self._bridge is not None:
            await self._bridge.stop()
        self._bridge = None
        self._bridge_queue = None

    async def _relay_bridge_events(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        try:
            while True:
                envelope = await queue.get()
                if envelope.type != "event" or envelope.event is None:
                    continue
                self._persist_run_snapshot()
                await self._broadcast(
                    StreamEnvelope(
                        type="event",
                        state=self.snapshot().state,
                        event=envelope.event,
                        workflow_event=None,
                    )
                )
        except asyncio.CancelledError:
            return

    async def _execute_run(
        self,
        workflow: Any,
        codex_agent: Any,
        expert_agent: Any,
        judge_agent: Any,
    ) -> None:
        started_at = monotonic()
        try:
            await self._ensure_checkpoint("planning", "Planning with Codex.")
            plan_prompt = self._render_template(
                workflow.plan_prompt_template,
                goal=self._run_state.goal if self._run_state else "",
            )
            plan_output = await self._run_codex_turn(plan_prompt, kind="planning")
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared during planning.")
            self._run_state.last_plan = self._clip(plan_output)
            initial_execute_prompt = self._render_template(
                workflow.execute_prompt_template,
                goal=self._run_state.goal,
                plan=plan_output,
            )

            execute_prompt = initial_execute_prompt
            loop_index = 0
            while True:
                loop_index += 1
                await self._check_budgets(loop_index, started_at)
                if self._run_state is None:
                    raise WorkflowSupervisorError("Workflow run disappeared during execution.")
                self._run_state.current_loop = loop_index
                self._run_state.updated_at = datetime.now(UTC)

                await self._ensure_checkpoint("executing", f"Codex execution loop {loop_index}.")
                execute_prompt = self._consume_steering(execute_prompt)
                codex_output = await self._run_codex_turn(execute_prompt, kind="executing")
                if self._run_state is None:
                    raise WorkflowSupervisorError("Workflow run disappeared during judging.")
                self._run_state.last_codex_output = self._clip(codex_output)

                expert_assessment: str | None = None
                if expert_agent is not None and workflow.expert_prompt_template is not None:
                    await self._ensure_checkpoint(
                        "advising",
                        f"Expert assessment loop {loop_index}.",
                    )
                    expert_bundle = await self._build_judge_bundle(
                        codex_output,
                        expert_assessment=None,
                    )
                    expert_prompt = self._render_agent_prompt(
                        workflow.expert_prompt_template,
                        agent=expert_agent,
                        goal=self._run_state.goal or "",
                        plan=plan_output,
                        last_output=codex_output,
                        judge_bundle=expert_bundle,
                        expert_assessment="",
                    )
                    while True:
                        try:
                            expert_assessment = await self._run_expert(expert_agent, expert_prompt)
                            break
                        except (OracleAgentError, OracleNotConfiguredError) as exc:
                            if expert_agent.provider != "oracle":
                                raise
                            await self._pause_for_oracle_failure(
                                agent_label="expert",
                                detail=str(exc),
                            )
                    if self._run_state is None:
                        raise WorkflowSupervisorError(
                            "Workflow run disappeared during expert assessment."
                        )
                    if self._run_state.last_error and self._run_state.last_error.startswith(
                        "Oracle expert failed and the run is paused:"
                    ):
                        self._run_state.last_error = None
                    self._run_state.last_expert_assessment = self._clip(
                        expert_assessment,
                        limit=8_000,
                    )

                await self._ensure_checkpoint("judging", f"Judge evaluation loop {loop_index}.")
                await self._check_budgets(loop_index, started_at, before_judge=True)
                judge_bundle = await self._build_judge_bundle(
                    codex_output,
                    expert_assessment=expert_assessment,
                )
                judge_prompt = self._render_agent_prompt(
                    workflow.judge_prompt_template,
                    agent=judge_agent,
                    goal=self._run_state.goal or "",
                    plan=plan_output,
                    last_output=codex_output,
                    judge_bundle=judge_bundle,
                    expert_assessment=expert_assessment or "",
                )
                while True:
                    try:
                        decision = await self._run_judge(judge_agent, judge_prompt)
                        break
                    except (OracleAgentError, OracleNotConfiguredError) as exc:
                        if judge_agent.provider != "oracle":
                            raise
                        await self._pause_for_oracle_failure(
                            agent_label="judge",
                            detail=str(exc),
                        )
                if self._run_state is None:
                    raise WorkflowSupervisorError("Workflow run disappeared after judging.")
                if self._run_state.last_error and self._run_state.last_error.startswith(
                    "Oracle judge failed and the run is paused:"
                ):
                    self._run_state.last_error = None
                self._run_state.judge_calls += 1
                self._run_state.last_judge_decision = decision.decision
                self._run_state.last_judge_summary = decision.summary
                self._run_state.last_continuation_prompt = (
                    decision.next_prompt if decision.decision == "continue" else None
                )
                self._run_state.updated_at = datetime.now(UTC)

                if decision.decision == "complete":
                    await self._finish_run(
                        status="completed",
                        phase="completed",
                        note=decision.completion_note or decision.summary,
                    )
                    return
                if decision.decision == "fail":
                    await self._finish_run(
                        status="failed",
                        phase="failed",
                        note=decision.failure_reason or decision.summary,
                    )
                    return
                if not decision.next_prompt:
                    raise WorkflowSupervisorError(
                        "Judge returned continue without a next_prompt."
                    )
                execute_prompt = decision.next_prompt
        except WorkflowStoppedError:
            await self._finish_run(
                status="stopped",
                phase="stopped",
                note="Workflow run stopped by operator request.",
            )
        except (BridgeError, OracleAgentError, OracleNotConfiguredError, WorkflowSupervisorError) as exc:
            await self._finish_run(status="failed", phase="failed", note=str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            await self._finish_run(status="failed", phase="failed", note=str(exc))

    async def _run_codex_turn(self, prompt: str, *, kind: str) -> str:
        if self._bridge is None:
            raise WorkflowSupervisorError("Codex session is not available.")
        await self._record_workflow_event(
            "codex_turn_started",
            f"Started Codex {kind} turn.",
            payload={"prompt": self._clip(prompt, limit=2_000)},
        )
        snapshot = await self._bridge.start_turn(prompt)
        turn = snapshot.state.turn
        if turn is None:
            raise WorkflowSupervisorError("Codex did not create a turn.")
        completed = await self._bridge.wait_for_turn_completion(turn.id)
        assistant_text = self._assistant_text_for_turn(completed, turn.id)
        await self._record_workflow_event(
            "codex_turn_completed",
            f"Completed Codex {kind} turn.",
            payload={
                "turnId": turn.id,
                "status": completed.state.turn.status if completed.state.turn else None,
            },
        )
        if completed.state.turn and completed.state.turn.error:
            raise WorkflowSupervisorError(completed.state.turn.error)
        if not assistant_text:
            raise WorkflowSupervisorError("Codex completed the turn without an assistant message.")
        return assistant_text

    async def _run_expert(self, expert_agent: Any, prompt: str) -> str:
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-expert-request.json", {"prompt": prompt})
        await self._record_workflow_event(
            "expert_started",
            f"Started {expert_agent.provider} expert assessment.",
            payload={"agentId": expert_agent.id, "provider": expert_agent.provider},
        )
        if expert_agent.provider == "oracle":
            response = await self._oracle.query(
                OracleQueryRequest(prompt=prompt),
                remote_host=expert_agent.remote_host,
                chatgpt_url=expert_agent.chatgpt_url,
                model_strategy=expert_agent.model_strategy,
                timeout_seconds=expert_agent.timeout_seconds,
                prompt_char_limit=expert_agent.prompt_char_limit,
            )
            answer = response.answer.strip()
            if self._resources is not None:
                self._write_json(
                    self._resources.run_dir / "last-expert-response.json",
                    {
                        "answer": answer,
                        "provider": "oracle",
                        "remoteHost": response.remote_host,
                        "durationSeconds": response.duration_seconds,
                    },
                )
        else:
            answer = await self._run_aux_codex_turn(
                expert_agent,
                prompt,
                event_log_subdir="expert-codex-events",
                label="expert",
            )
            if self._resources is not None:
                self._write_json(
                    self._resources.run_dir / "last-expert-response.json",
                    {
                        "answer": answer,
                        "provider": "codex",
                    },
                )
        await self._record_workflow_event(
            "expert_completed",
            f"Completed {expert_agent.provider} expert assessment.",
            payload={
                "agentId": expert_agent.id,
                "provider": expert_agent.provider,
                "answer": self._clip(answer, limit=2_000),
            },
        )
        return answer

    async def _run_judge(self, judge_agent: Any, prompt: str) -> JudgeDecision:
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-judge-request.json", {"prompt": prompt})
        await self._record_workflow_event(
            "judge_started",
            f"Started {judge_agent.provider} judge evaluation.",
            payload={"agentId": judge_agent.id, "provider": judge_agent.provider},
        )
        if judge_agent.provider == "oracle":
            response = await self._oracle.query(
                OracleQueryRequest(prompt=prompt),
                remote_host=judge_agent.remote_host,
                chatgpt_url=judge_agent.chatgpt_url,
                model_strategy=judge_agent.model_strategy,
                timeout_seconds=judge_agent.timeout_seconds,
                prompt_char_limit=judge_agent.prompt_char_limit,
            )
            raw_answer = response.answer.strip()
            response_payload: dict[str, object] = {
                "answer": raw_answer,
                "provider": "oracle",
                "remoteHost": response.remote_host,
                "durationSeconds": response.duration_seconds,
            }
        else:
            raw_answer = await self._run_aux_codex_turn(
                judge_agent,
                prompt,
                event_log_subdir="judge-codex-events",
                label="judge",
            )
            response_payload = {
                "answer": raw_answer,
                "provider": "codex",
            }
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-judge-response.json", response_payload)
        decision = self._parse_judge_decision(raw_answer)
        await self._record_workflow_event(
            "judge_completed",
            f"{judge_agent.provider} returned '{decision.decision}'.",
            payload=decision.model_dump(mode="json"),
        )
        return decision

    async def _check_budgets(
        self,
        loop_index: int,
        started_at: float,
        *,
        before_judge: bool = False,
    ) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow state is available.")
        elapsed_minutes = (monotonic() - started_at) / 60
        if elapsed_minutes >= self._run_state.max_runtime_minutes:
            raise WorkflowSupervisorError(
                f"Workflow runtime budget exceeded ({self._run_state.max_runtime_minutes} minutes)."
            )
        if loop_index > self._run_state.max_loops:
            raise WorkflowSupervisorError(
                f"Workflow loop budget exceeded ({self._run_state.max_loops} loops)."
            )
        if before_judge and self._run_state.judge_calls >= self._run_state.max_judge_calls:
            raise WorkflowSupervisorError(
                f"Workflow judge-call budget exceeded ({self._run_state.max_judge_calls} calls)."
            )

    async def _pause_for_oracle_failure(self, *, agent_label: str, detail: str) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        self._pause_gate.clear()
        self._run_state.status = "paused"
        self._run_state.phase = "paused"
        self._run_state.last_error = (
            f"Oracle {agent_label} failed and the run is paused: {detail}"
        )
        self._run_state.updated_at = datetime.now(UTC)
        await self._record_workflow_event(
            "oracle_blocked",
            f"Oracle {agent_label} failed; run paused until operator resume.",
            payload={"agent": agent_label, "detail": detail},
        )
        await self._broadcast_state()
        await self._pause_gate.wait()
        if self._run_state.stop_requested:
            raise WorkflowStoppedError("Workflow stop requested.")

    async def _ensure_checkpoint(self, phase: WorkflowPhase, message: str) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        if self._run_state.stop_requested:
            raise WorkflowStoppedError("Workflow stop requested.")
        if self._run_state.pause_requested:
            self._pause_gate.clear()
            self._run_state.status = "paused"
            self._run_state.phase = "paused"
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                "paused",
                "Workflow run paused between steps.",
            )
            await self._broadcast_state()
            await self._pause_gate.wait()
        if self._run_state.stop_requested:
            raise WorkflowStoppedError("Workflow stop requested.")
        self._run_state.status = "running"
        self._run_state.phase = phase
        self._run_state.updated_at = datetime.now(UTC)
        await self._record_workflow_event("phase_changed", message)

    async def _finish_run(
        self,
        *,
        status: WorkflowRunStatus,
        phase: WorkflowPhase,
        note: str,
    ) -> None:
        if self._run_state is not None:
            self._run_state.status = status
            self._run_state.phase = phase
            self._run_state.last_error = note if status == "failed" else None
            self._run_state.completed_at = datetime.now(UTC)
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                f"run_{status}",
                note,
            )
        await self._stop_bridge()
        await self._broadcast_state()

    async def _record_workflow_event(
        self,
        kind: str,
        message: str,
        *,
        payload: object | None = None,
    ) -> None:
        if self._resources is None:
            return
        record = await self._resources.workflow_event_store.append(
            kind=kind,
            message=message,
            payload=payload,
        )
        self._recent_workflow_events.append(record)
        if self._run_state is not None:
            self._run_state.updated_at = datetime.now(UTC)
        self._persist_run_snapshot()
        await self._broadcast(
            StreamEnvelope(
                type="workflow_event",
                state=self.snapshot().state,
                event=None,
                workflow_event=record,
            )
        )

    async def _broadcast_state(self) -> None:
        self._persist_run_snapshot()
        await self._broadcast(
            StreamEnvelope(
                type="state",
                state=self.snapshot().state,
                event=None,
                workflow_event=None,
            )
        )

    async def _broadcast(self, envelope: StreamEnvelope) -> None:
        stale: list[asyncio.Queue[StreamEnvelope]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self._subscribers.discard(queue)

    async def _build_judge_bundle(
        self,
        codex_output: str,
        *,
        expert_assessment: str | None,
    ) -> str:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        git_status = await self._git_output("status", "--short")
        git_diff_stat = await self._git_output("diff", "--stat")
        git_diff_excerpt = await self._git_output("diff", "--", ".")
        bridge_snapshot = self._bridge.snapshot() if self._bridge is not None else None
        payload = {
            "goal": self._run_state.goal,
            "workflowId": self._run_state.workflow_id,
            "targetDir": self._run_state.target_dir,
            "loop": self._run_state.current_loop,
            "judgeCalls": self._run_state.judge_calls,
            "recentSteeringNotes": self._run_state.recent_steering_notes[-5:],
            "lastPlan": self._run_state.last_plan,
            "lastCodexOutput": self._clip(codex_output, limit=8_000),
            "expertAssessment": self._clip(expert_assessment, limit=8_000),
            "codexLastError": (
                bridge_snapshot.state.turn.error
                if bridge_snapshot is not None and bridge_snapshot.state.turn is not None
                else None
            ),
            "pendingServerRequest": (
                bridge_snapshot.state.pending_server_request.model_dump(mode="json")
                if bridge_snapshot is not None and bridge_snapshot.state.pending_server_request
                else None
            ),
            "gitStatusShort": git_status,
            "gitDiffStat": git_diff_stat,
            "gitDiffExcerpt": self._clip(git_diff_excerpt, limit=8_000),
        }
        return json.dumps(payload, ensure_ascii=True, indent=2)

    async def _run_aux_codex_turn(
        self,
        agent: Any,
        prompt: str,
        *,
        event_log_subdir: str,
        label: str,
    ) -> str:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        if self._resources is None:
            raise WorkflowSupervisorError("No workflow resources are available.")
        bridge = CodexAppServerBridge(
            self._settings,
            workspace_root=Path(self._run_state.target_dir),
            event_log_dir=self._resources.run_dir / event_log_subdir,
            agent_config=CodexAgentConfig(
                role=agent.role,
                startup_prompt=agent.startup_prompt,
                description=agent.description,
                model=agent.model,
                model_provider=agent.model_provider,
                reasoning_effort=agent.reasoning_effort,
                approval_policy=agent.approval_policy or "never",
                sandbox_mode=agent.sandbox_mode or "workspace-write",
                web_access=agent.web_access or "disabled",
                service_tier=agent.service_tier,
            ),
        )
        await bridge.start()
        try:
            snapshot = await bridge.start_turn(prompt)
            turn = snapshot.state.turn
            if turn is None:
                raise WorkflowSupervisorError(f"Codex {label} did not create a turn.")
            completed = await bridge.wait_for_turn_completion(turn.id)
            assistant_text = self._assistant_text_for_turn(completed, turn.id)
            if completed.state.turn and completed.state.turn.error:
                raise WorkflowSupervisorError(completed.state.turn.error)
            if not assistant_text:
                raise WorkflowSupervisorError(
                    f"Codex {label} completed the turn without an assistant message."
                )
            return assistant_text
        finally:
            await bridge.stop()

    async def _git_output(self, *args: str) -> str:
        if self._run_state is None:
            return "no workflow run"
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            self._run_state.target_dir,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=15)
        except TimeoutError:
            process.kill()
            await process.wait()
            return "git command timed out"
        stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
        if process.returncode != 0:
            return stderr_text or stdout_text or "git command failed"
        return stdout_text or "(empty)"

    def _consume_steering(self, prompt: str) -> str:
        if self._run_state is None or not self._run_state.pending_steering_notes:
            return prompt
        notes = [note.strip() for note in self._run_state.pending_steering_notes if note.strip()]
        self._run_state.pending_steering_notes.clear()
        self._run_state.recent_steering_notes.extend(notes)
        self._run_state.recent_steering_notes = self._run_state.recent_steering_notes[-10:]
        if not notes:
            return prompt
        notes_block = "\n".join(f"- {note}" for note in notes)
        return (
            f"{prompt}\n\nOperator steering to apply on this step:\n"
            f"{notes_block}\n\n"
            "Follow this steering unless it directly conflicts with higher-priority instructions."
        )

    @staticmethod
    def _assistant_text_for_turn(snapshot: DashboardSnapshot, turn_id: str) -> str:
        for item in reversed(snapshot.state.transcript):
            if item.role == "assistant" and item.turn_id == turn_id:
                return item.text.strip()
        return ""

    @staticmethod
    def _git_root_for(path: Path) -> Path | None:
        try:
            completed = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            return None
        if completed.returncode != 0:
            return None
        root = completed.stdout.strip()
        return Path(root).resolve() if root else None

    @staticmethod
    def _extract_json(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            stripped = stripped.removeprefix("json").strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise WorkflowSupervisorError("Judge did not return a JSON object.")
        return stripped[start : end + 1]

    @classmethod
    def _parse_judge_decision(cls, raw_answer: str) -> JudgeDecision:
        json_error: Exception | None = None
        try:
            payload = cls._extract_json(raw_answer)
            try:
                return JudgeDecision.model_validate_json(payload)
            except ValidationError:
                repaired = cls._repair_judge_payload(payload)
                return JudgeDecision.model_validate(repaired)
        except (ValidationError, WorkflowSupervisorError) as exc:
            json_error = exc

        try:
            return cls._parse_judge_text_decision(raw_answer)
        except ValidationError as exc:
            raise WorkflowSupervisorError(
                "Judge returned a malformed decision payload that could not be parsed."
            ) from exc
        except WorkflowSupervisorError as exc:
            raise WorkflowSupervisorError(
                "Judge returned a malformed decision payload that could not be parsed."
            ) from (json_error or exc)

    @classmethod
    def _repair_judge_payload(cls, payload: str) -> dict[str, object]:
        decision_match = re.search(
            r'"decision"\s*:\s*"(?P<decision>continue|complete|fail)"',
            payload,
        )
        if decision_match is None:
            raise WorkflowSupervisorError("Judge decision payload is missing a valid decision.")

        repaired: dict[str, object] = {"decision": decision_match.group("decision")}
        for field_name in (
            "summary",
            "next_prompt",
            "completion_note",
            "failure_reason",
        ):
            field_value = cls._extract_string_field(payload, field_name)
            if field_value is not None:
                repaired[field_name] = field_value
        return repaired

    @classmethod
    def _parse_judge_text_decision(cls, raw_answer: str) -> JudgeDecision:
        text = cls._strip_code_fence(raw_answer)
        sections = cls._extract_judge_text_sections(text)
        if "decision" not in sections:
            raise WorkflowSupervisorError("Judge text response is missing a Decision section.")
        if "summary" not in sections:
            raise WorkflowSupervisorError("Judge text response is missing a Summary section.")

        payload: dict[str, object] = {
            "decision": sections["decision"].strip().lower(),
            "summary": sections["summary"].strip(),
        }
        section_map = {
            "next prompt": "next_prompt",
            "completion note": "completion_note",
            "failure reason": "failure_reason",
        }
        for section_name, field_name in section_map.items():
            value = sections.get(section_name)
            if value:
                payload[field_name] = value.strip()
        return JudgeDecision.model_validate(payload)

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if not lines:
            return stripped
        body_lines = lines[1:]
        if body_lines and body_lines[-1].strip() == "```":
            body_lines = body_lines[:-1]
        return "\n".join(body_lines).strip()

    @staticmethod
    def _extract_judge_text_sections(text: str) -> dict[str, str]:
        pattern = re.compile(
            r"(?im)^(Decision|Summary|Next prompt|Completion note|Failure reason)\s*:\s*"
        )
        matches = list(pattern.finditer(text))
        if not matches:
            raise WorkflowSupervisorError("Judge text response does not use the expected labels.")

        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            section_name = match.group(1).lower()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[section_name] = text[start:end].strip()
        return sections

    @staticmethod
    def _extract_string_field(payload: str, field_name: str) -> str | None:
        key = f'"{field_name}"'
        key_index = payload.find(key)
        if key_index == -1:
            return None
        colon_index = payload.find(":", key_index + len(key))
        if colon_index == -1:
            return None
        value_index = colon_index + 1
        while value_index < len(payload) and payload[value_index].isspace():
            value_index += 1
        if value_index >= len(payload):
            return None
        if payload.startswith("null", value_index):
            return None
        if payload[value_index] != '"':
            return None

        value_chars: list[str] = []
        index = value_index + 1
        while index < len(payload):
            char = payload[index]
            if char == "\\" and index + 1 < len(payload):
                value_chars.append(char)
                value_chars.append(payload[index + 1])
                index += 2
                continue
            if char == '"':
                lookahead = index + 1
                while lookahead < len(payload) and payload[lookahead].isspace():
                    lookahead += 1
                if lookahead >= len(payload) or payload[lookahead] in {",", "}"}:
                    try:
                        return json.loads('"' + "".join(value_chars) + '"')
                    except json.JSONDecodeError:
                        return "".join(value_chars)
            value_chars.append(char)
            index += 1
        return None

    @staticmethod
    def _render_template(template: str, **values: str) -> str:
        rendered = template
        for key, value in values.items():
            rendered = rendered.replace("{" + key + "}", value)
        return rendered

    @classmethod
    def _render_agent_prompt(
        cls,
        template: str,
        *,
        agent: Any,
        **values: str,
    ) -> str:
        if agent.provider == "oracle":
            prompt_limit = agent.prompt_char_limit or 20_000
            return cls._render_judge_prompt(template, prompt_limit=prompt_limit, **values)
        return cls._render_template(template, **values)

    @classmethod
    def _render_judge_prompt(
        cls,
        template: str,
        *,
        prompt_limit: int,
        **values: str,
    ) -> str:
        current_values = {key: value for key, value in values.items()}
        prompt = cls._render_template(template, **current_values)
        if len(prompt) <= prompt_limit:
            return prompt

        for key in ("judge_bundle", "last_output", "plan", "goal"):
            current = current_values.get(key, "")
            if not current:
                continue
            overflow = len(prompt) - prompt_limit
            if overflow <= 0:
                break
            new_limit = max(256, len(current) - overflow - 256)
            current_values[key] = cls._clip(current, limit=new_limit) or ""
            prompt = cls._render_template(template, **current_values)
            if len(prompt) <= prompt_limit:
                return prompt

        if len(prompt) > prompt_limit:
            return prompt[: prompt_limit - 1] + "…"
        return prompt

    @staticmethod
    def _clip(text: str | None, *, limit: int = 4_000) -> str | None:
        if text is None:
            return None
        stripped = text.strip()
        if len(stripped) <= limit:
            return stripped
        return stripped[: limit - 1] + "…"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _persist_run_snapshot(self) -> None:
        if self._resources is None:
            return
        snapshot = self.snapshot()
        snapshot_path = self._resources.run_dir / self.RUN_SNAPSHOT_FILENAME
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            snapshot.model_dump_json(indent=2),
            encoding="utf-8",
        )
        self._archived_snapshot = snapshot.model_copy(deep=True)


def as_http_error(error: Exception) -> HTTPException:
    if isinstance(error, WorkflowConflictError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, WorkflowNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))
