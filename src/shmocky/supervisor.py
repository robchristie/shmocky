from __future__ import annotations

import asyncio
import contextlib
import json
import re
import shutil
import subprocess
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from .bridge import BridgeError, CodexAppServerBridge
from .event_store import WorkflowEventStore
from .notebook_models import NotebookPageKind, NotebookPageListResponse, NotebookPageView
from .notebook_projection import NotebookProjection
from .notebook_store import NotebookPageStore
from .models import (
    AgentDefinition,
    CodexAgentConfig,
    ConnectionState,
    DashboardSnapshot,
    DashboardState,
    ExpertAssessment,
    JudgeDecision,
    OracleQueryRequest,
    OracleResumeCheckpoint,
    RunRoutingDecision,
    RunHistoryEntry,
    RunHistoryResponse,
    ServerRequestResolutionRequest,
    StreamEnvelope,
    TranscriptItem,
    WorkflowCatalogResponse,
    WorkflowDefinition,
    WorkflowEventRecord,
    WorkflowPhase,
    WorkflowRunRequest,
    WorkflowRunState,
    WorkflowRunStatus,
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
    notebook_projection: NotebookProjection


@dataclass(slots=True)
class LoadedRunContext:
    workflow: WorkflowDefinition
    codex_agent: AgentDefinition
    router_agent: AgentDefinition | None
    expert_agent: AgentDefinition | None
    judge_agent: AgentDefinition


@dataclass(slots=True)
class PreparedExecutionWorkspace:
    source_repo_root: Path
    execution_dir: Path
    workspace_strategy: Literal["git_worktree"]
    worktree_branch: str
    worktree_base_commit: str


@dataclass(slots=True)
class ExpertAssessmentResult:
    raw_text: str
    report: ExpertAssessment


@dataclass(slots=True)
class CodexTurnResult:
    text: str
    turn_id: str
    transcript_item_ids: list[str]


class WorkflowSupervisor:
    RUN_MANIFEST_FILENAME = "run.json"
    RUN_SNAPSHOT_FILENAME = "dashboard-snapshot.json"
    RUN_NOTEBOOK_FILENAME = "notebook-pages.jsonl"
    RUN_NOTEBOOK_DIRNAME = "notebook"
    SNAPSHOT_FLUSH_DEBOUNCE_SECONDS = 0.25

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
        self._snapshot_flush_task: asyncio.Task[None] | None = None
        self._snapshot_flush_lock = asyncio.Lock()
        self._staged_snapshot: DashboardSnapshot | None = None
        self._staged_snapshot_path: Path | None = None
        self._staged_snapshot_revision = 0
        self._snapshot_revision = 0
        self._snapshot_flushed_revision = 0
        self._pause_gate = asyncio.Event()
        self._pause_gate.set()
        self._last_catalog_error: str | None = None
        self._restore_resumable_run()

    def _restore_resumable_run(self) -> None:
        run_dir = self._find_resumable_run_dir()
        if run_dir is None:
            return
        snapshot_path = run_dir / self.RUN_SNAPSHOT_FILENAME
        try:
            snapshot = DashboardSnapshot.model_validate_json(
                snapshot_path.read_text(encoding="utf-8")
            )
        except Exception:
            return
        workflow_run = snapshot.state.workflow_run
        if (
            workflow_run is None
            or workflow_run.status != "paused"
            or workflow_run.oracle_resume_checkpoint is None
        ):
            return
        self._run_state = workflow_run
        self._resources = self._create_run_resources(run_dir)
        self._recent_workflow_events.clear()
        self._recent_workflow_events.extend(
            self._load_workflow_events(run_dir / "workflow-events.jsonl")
        )
        self._archived_snapshot = snapshot
        self._pause_gate.clear()

    def _create_run_resources(self, run_dir: Path) -> RunResources:
        return RunResources(
            run_dir=run_dir,
            workflow_event_store=WorkflowEventStore(run_dir / "workflow-events.jsonl"),
            notebook_projection=NotebookProjection(
                store=NotebookPageStore(run_dir / self.RUN_NOTEBOOK_FILENAME),
                notebook_dir=run_dir / self.RUN_NOTEBOOK_DIRNAME,
                snapshot_path=run_dir / self.RUN_SNAPSHOT_FILENAME,
            ),
        )

    def _find_resumable_run_dir(self) -> Path | None:
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
            if (
                workflow_run is not None
                and workflow_run.status == "paused"
                and workflow_run.oracle_resume_checkpoint is not None
            ):
                return run_dir
        return None

    @staticmethod
    def _load_workflow_events(path: Path) -> list[WorkflowEventRecord]:
        if not path.exists():
            return []
        records: list[WorkflowEventRecord] = []
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        records.append(WorkflowEventRecord.model_validate_json(line))
                    except Exception:
                        continue
        except OSError:
            return []
        return records[-200:]

    def _load_run_context_from_manifest(self) -> LoadedRunContext:
        if self._resources is None:
            raise WorkflowSupervisorError("No workflow resources are available.")
        manifest_path = self._resources.run_dir / self.RUN_MANIFEST_FILENAME
        if not manifest_path.exists():
            raise WorkflowSupervisorError(
                f"Run manifest is missing for '{self._resources.run_dir.name}'."
            )
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            workflow = WorkflowDefinition.model_validate(payload["workflow"])
            agents_payload = payload["agents"]
            codex_payload = agents_payload.get("builder") or agents_payload["codex"]
            codex_agent = AgentDefinition.model_validate(codex_payload)
            router_payload = agents_payload.get("router")
            router_agent = (
                AgentDefinition.model_validate(router_payload)
                if isinstance(router_payload, dict)
                else None
            )
            expert_payload = agents_payload.get("expert")
            expert_agent = (
                AgentDefinition.model_validate(expert_payload)
                if isinstance(expert_payload, dict)
                else None
            )
            judge_agent = AgentDefinition.model_validate(agents_payload["judge"])
        except Exception as exc:
            raise WorkflowSupervisorError(
                f"Run manifest for '{self._resources.run_dir.name}' is unreadable."
            ) from exc
        return LoadedRunContext(
            workflow=workflow,
            codex_agent=codex_agent,
            router_agent=router_agent,
            expert_agent=expert_agent,
            judge_agent=judge_agent,
        )

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
                    execution_dir=workflow_run.execution_dir,
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

    def notebook_pages(self, run_id: str) -> NotebookPageListResponse:
        run_dir = self._settings.run_log_dir / run_id
        if not run_dir.exists() or not run_dir.is_dir():
            raise WorkflowNotFoundError(f"Unknown run '{run_id}'.")
        notebook_path = run_dir / self.RUN_NOTEBOOK_FILENAME
        if not notebook_path.exists():
            return NotebookPageListResponse()
        projection = NotebookProjection(
            store=NotebookPageStore(notebook_path),
            notebook_dir=run_dir / self.RUN_NOTEBOOK_DIRNAME,
            snapshot_path=run_dir / self.RUN_SNAPSHOT_FILENAME,
        )
        return projection.list_pages()

    def notebook_page(self, run_id: str, page_id: str) -> NotebookPageView:
        run_dir = self._settings.run_log_dir / run_id
        if not run_dir.exists() or not run_dir.is_dir():
            raise WorkflowNotFoundError(f"Unknown run '{run_id}'.")
        notebook_path = run_dir / self.RUN_NOTEBOOK_FILENAME
        if not notebook_path.exists():
            raise WorkflowNotFoundError(f"Unknown notebook page '{page_id}' for run '{run_id}'.")
        projection = NotebookProjection(
            store=NotebookPageStore(notebook_path),
            notebook_dir=run_dir / self.RUN_NOTEBOOK_DIRNAME,
            snapshot_path=run_dir / self.RUN_SNAPSHOT_FILENAME,
        )
        page = projection.load_page(page_id)
        if page is None:
            raise WorkflowNotFoundError(f"Unknown notebook page '{page_id}' for run '{run_id}'.")
        return page

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
            if (
                self._run_state is not None
                and self._run_state.status == "paused"
                and self._run_state.oracle_resume_checkpoint is not None
            ):
                self._stage_run_snapshot()
            await self._flush_staged_snapshot_now()

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

    async def resolve_server_request(
        self,
        request_id: str,
        payload: ServerRequestResolutionRequest,
    ) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        pending = self._bridge.snapshot().state.pending_server_request
        if pending is None:
            raise WorkflowSupervisorError("There is no pending server request to resolve.")
        if pending.request_id != request_id:
            raise WorkflowSupervisorError(
                f"Pending server request is '{pending.request_id}', not '{request_id}'."
            )
        await self._bridge.resolve_server_request(request_id, result=payload.result)
        await self._record_workflow_event(
            "server_request_responded",
            f"Operator responded to {pending.method}.",
            payload={"requestId": request_id, "method": pending.method},
        )
        return self.snapshot()

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

            source_repo_root = self._validate_target_dir(Path(payload.target_dir))

            agent_by_id = {agent.id: agent for agent in catalog.agents}
            codex_agent = agent_by_id[workflow.executor_agent]
            router_agent = (
                agent_by_id[workflow.router_agent]
                if workflow.router_agent is not None
                else None
            )
            expert_agent = (
                agent_by_id[workflow.expert_agent]
                if workflow.expert_agent is not None
                else None
            )
            judge_agent = agent_by_id[workflow.judge_agent]

            run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
            workspace = self._prepare_execution_workspace(source_repo_root, run_id)
            run_dir = self._settings.run_log_dir / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            resources = self._create_run_resources(run_dir)
            self._resources = resources
            self._archived_snapshot = None
            self._recent_workflow_events.clear()
            self._pause_gate.set()
            self._run_state = WorkflowRunState(
                id=run_id,
                run_name=payload.run_name.strip() if payload.run_name else None,
                workflow_id=workflow.id,
                target_dir=str(workspace.source_repo_root),
                execution_dir=str(workspace.execution_dir),
                workspace_strategy=workspace.workspace_strategy,
                worktree_branch=workspace.worktree_branch,
                worktree_base_commit=workspace.worktree_base_commit,
                goal=payload.prompt,
                status="starting",
                phase="idle",
                codex_agent_id=codex_agent.id,
                router_agent_id=router_agent.id if router_agent is not None else None,
                expert_agent_id=expert_agent.id if expert_agent is not None else None,
                judge_agent_id=judge_agent.id,
                started_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                max_loops=workflow.max_loops,
                max_judge_calls=workflow.max_judge_calls,
                max_runtime_minutes=workflow.max_runtime_minutes,
            )
            if router_agent is not None:
                (
                    codex_agent,
                    expert_agent,
                    judge_agent,
                    routing_decision,
                ) = await self._route_agents(
                    workflow=workflow,
                    router_agent=router_agent,
                    agent_by_id=agent_by_id,
                )
                if self._run_state is None:
                    raise WorkflowSupervisorError("Workflow run disappeared during routing.")
                self._run_state.codex_agent_id = codex_agent.id
                self._run_state.expert_agent_id = (
                    expert_agent.id if expert_agent is not None else None
                )
                self._run_state.judge_agent_id = judge_agent.id
                self._run_state.last_routing_decision = routing_decision
            self._write_json(
                run_dir / self.RUN_MANIFEST_FILENAME,
                {
                    "runId": run_id,
                    "request": payload.model_dump(mode="json"),
                    "workflow": workflow.model_dump(mode="json"),
                    "agents": {
                        "builder": codex_agent.model_dump(mode="json"),
                        "router": (
                            router_agent.model_dump(mode="json")
                            if router_agent is not None
                            else None
                        ),
                        "expert": (
                            expert_agent.model_dump(mode="json")
                            if expert_agent is not None
                            else None
                        ),
                        "judge": judge_agent.model_dump(mode="json"),
                    },
                    "workspace": {
                        "sourceRepoRoot": str(workspace.source_repo_root),
                        "executionDir": str(workspace.execution_dir),
                        "workspaceStrategy": workspace.workspace_strategy,
                        "worktreeBranch": workspace.worktree_branch,
                        "worktreeBaseCommit": workspace.worktree_base_commit,
                    },
                    "routingDecision": (
                        self._run_state.last_routing_decision.model_dump(mode="json")
                        if self._run_state.last_routing_decision is not None
                        else None
                    ),
                },
            )
            self._stage_run_snapshot()
            await self._flush_staged_snapshot_now()
            try:
                await self._record_workflow_event(
                    "worktree_prepared",
                    "Prepared the managed execution worktree.",
                    payload={
                        "sourceRepoRoot": str(workspace.source_repo_root),
                        "executionDir": str(workspace.execution_dir),
                        "workspaceStrategy": workspace.workspace_strategy,
                        "worktreeBranch": workspace.worktree_branch,
                        "worktreeBaseCommit": workspace.worktree_base_commit,
                    },
                )
                await self._append_notebook_page(
                    kind="worktree_prepared",
                    title="Managed worktree prepared",
                    summary=(
                        f"Prepared a managed {workspace.workspace_strategy} workspace at "
                        f"{workspace.execution_dir} from {workspace.source_repo_root}."
                    ),
                    why=(
                        "Runs execute in an isolated managed worktree so Shmocky can supervise "
                        "changes without mutating the source repository directly."
                    ),
                    outcomes=[
                        f"Source repo root: {workspace.source_repo_root}",
                        f"Execution directory: {workspace.execution_dir}",
                        f"Branch: {workspace.worktree_branch}",
                        f"Base commit: {workspace.worktree_base_commit}",
                    ],
                    tags=["workspace", "git-worktree"],
                )
                await self._record_workflow_event(
                    "run_started",
                    (
                        "Started run "
                        f"'{self._run_state.run_name}' using workflow '{workflow.id}' "
                        f"for {workspace.source_repo_root}"
                        if self._run_state.run_name
                        else f"Started workflow '{workflow.id}' for {workspace.source_repo_root}"
                    ),
                    payload={
                        "runId": run_id,
                        "runName": self._run_state.run_name,
                        "workflowId": workflow.id,
                        "targetDir": str(workspace.source_repo_root),
                        "executionDir": str(workspace.execution_dir),
                        "workspaceStrategy": workspace.workspace_strategy,
                        "worktreeBranch": workspace.worktree_branch,
                        "worktreeBaseCommit": workspace.worktree_base_commit,
                        "routerAgentId": router_agent.id if router_agent is not None else None,
                        "builderAgentId": codex_agent.id,
                        "expertAgentId": expert_agent.id if expert_agent is not None else None,
                        "judgeAgentId": judge_agent.id,
                        "routingSummary": (
                            self._run_state.last_routing_decision.summary
                            if self._run_state.last_routing_decision is not None
                            else None
                        ),
                    },
                )
                await self._append_notebook_page(
                    kind="run_started",
                    title=(
                        f"Run started: {self._run_state.run_name}"
                        if self._run_state.run_name
                        else f"Run started: {workflow.id}"
                    ),
                    summary=(
                        f"Started workflow '{workflow.id}' against {workspace.source_repo_root}."
                    ),
                    why=self._run_state.goal,
                    outcomes=[
                        f"Workflow: {workflow.id}",
                        f"Builder: {codex_agent.id}",
                        f"Judge: {judge_agent.id}",
                        (
                            f"Expert: {expert_agent.id}"
                            if expert_agent is not None
                            else "Expert: none"
                        ),
                    ],
                    next_steps=["Start the managed Codex builder session and execute the first slice."],
                    tags=["run", workflow.id],
                )
                if self._run_state.last_routing_decision is not None:
                    await self._append_notebook_page(
                        kind="plan_adopted",
                        title="Routed execution plan adopted",
                        summary=self._run_state.last_routing_decision.summary,
                        why="The router selected the allowed agent composition for this run.",
                        outcomes=[
                            f"Builder: {self._run_state.last_routing_decision.executor_agent_id}",
                            f"Judge: {self._run_state.last_routing_decision.judge_agent_id}",
                            (
                                "Expert: "
                                f"{self._run_state.last_routing_decision.expert_agent_id or 'none'}"
                            ),
                        ],
                        tags=["routing", "agent-selection"],
                    )
                await self._start_bridge(workspace.execution_dir, codex_agent)
            except Exception:
                await self._rollback_failed_run_start()
                raise
            self._run_task = asyncio.create_task(
                self._execute_run(workflow, codex_agent, expert_agent, judge_agent)
            )
            await self._broadcast_state()
            return self.snapshot()

    async def _rollback_failed_run_start(self) -> None:
        await self._stop_bridge()
        if self._run_task is not None:
            self._run_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._run_task
            self._run_task = None
        self._cleanup_managed_workspace()
        await self._cancel_snapshot_flush_task()
        self._run_state = None
        self._resources = None
        self._archived_snapshot = None
        self._staged_snapshot = None
        self._staged_snapshot_path = None
        self._staged_snapshot_revision = 0
        self._snapshot_revision = 0
        self._snapshot_flushed_revision = 0
        self._recent_workflow_events.clear()
        self._pause_gate.set()

    def _validate_target_dir(self, target_dir: Path) -> Path:
        resolved = target_dir.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise WorkflowSupervisorError(
                f"Target directory does not exist or is not a directory: {resolved}"
            )
        if resolved.is_relative_to(self._settings.workspace_root):
            raise WorkflowSupervisorError(
                "Target directory is inside the Shmocky workspace. "
                "Use an external git repository root for isolation."
            )

        containing_git_root = self._git_root_for(resolved)
        if containing_git_root is None:
            raise WorkflowSupervisorError(
                "Target directory is not a git repository root. "
                "Managed workflow runs require a git repository root."
            )
        if containing_git_root != resolved:
            raise WorkflowSupervisorError(
                "Target directory must be the git repository root itself: "
                f"{containing_git_root}. Nested paths are not supported for managed worktree runs."
            )
        return resolved

    def _prepare_execution_workspace(
        self,
        source_repo_root: Path,
        run_id: str,
    ) -> PreparedExecutionWorkspace:
        worktree_root = self._managed_worktree_root()
        execution_dir = worktree_root / run_id
        branch_name = f"shmocky/{run_id}"
        base_commit = self._git_head_commit_for(source_repo_root)
        if execution_dir.exists():
            raise WorkflowSupervisorError(
                f"Managed worktree path already exists: {execution_dir}"
            )
        worktree_root.mkdir(parents=True, exist_ok=True)
        try:
            self._run_git(
                source_repo_root,
                "worktree",
                "add",
                "-b",
                branch_name,
                str(execution_dir),
                base_commit,
            )
        except Exception:
            self._cleanup_prepared_worktree(source_repo_root, execution_dir, branch_name)
            raise
        return PreparedExecutionWorkspace(
            source_repo_root=source_repo_root,
            execution_dir=execution_dir,
            workspace_strategy="git_worktree",
            worktree_branch=branch_name,
            worktree_base_commit=base_commit,
        )

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
                if self._run_task is None:
                    checkpoint = self._run_state.oracle_resume_checkpoint
                    if checkpoint is None:
                        raise WorkflowSupervisorError(
                            "This paused run cannot be resumed after backend restart."
                        )
                    context = self._load_run_context_from_manifest()
                    transcript_seed = (
                        self._archived_snapshot.state.transcript
                        if self._archived_snapshot is not None
                        else []
                    )
                    await self._start_bridge(
                        self._execution_dir_for_run(),
                        context.codex_agent,
                        resume_thread_id=checkpoint.thread_id,
                        transcript_seed=transcript_seed,
                    )
                    self._run_task = asyncio.create_task(
                        self._resume_from_oracle_checkpoint(context)
                    )
                self._run_state.status = "running"
                self._run_state.updated_at = datetime.now(UTC)
                self._pause_gate.set()
                await self._record_workflow_event("resumed", "Workflow run resumed.")
                await self._append_notebook_page(
                    kind="run_resumed",
                    title="Run resumed",
                    summary="Resumed a previously paused workflow run.",
                    why="Operator resume cleared the pause gate and allowed workflow execution to continue.",
                    outcomes=[
                        f"Status: {self._run_state.status}",
                        f"Phase: {self._run_state.phase}",
                    ],
                    tags=["resume"],
                )
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

    async def _start_bridge(
        self,
        target_dir: Path,
        codex_agent: Any,
        *,
        resume_thread_id: str | None = None,
        transcript_seed: list[TranscriptItem] | None = None,
    ) -> None:
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
        if resume_thread_id is not None:
            await bridge.resume_thread(resume_thread_id)
        if transcript_seed:
            bridge.seed_transcript(transcript_seed)
        queue = await bridge.subscribe()
        self._bridge = bridge
        self._bridge_queue = queue
        self._bridge_task = asyncio.create_task(self._relay_bridge_events(queue))
        await self._record_workflow_event(
            "codex_session_resumed" if resume_thread_id is not None else "codex_session_started",
            (
                "Resumed Codex app-server session for the workflow run."
                if resume_thread_id is not None
                else "Started Codex app-server session for the workflow run."
            ),
            payload={
                "workspaceRoot": str(target_dir),
                "threadId": resume_thread_id,
            },
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
                self._stage_run_snapshot()
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

    async def _route_agents(
        self,
        *,
        workflow: WorkflowDefinition,
        router_agent: AgentDefinition,
        agent_by_id: dict[str, AgentDefinition],
    ) -> tuple[AgentDefinition, AgentDefinition | None, AgentDefinition, RunRoutingDecision]:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        self._run_state.phase = "routing"
        self._run_state.updated_at = datetime.now(UTC)
        await self._record_workflow_event(
            "routing_started",
            f"Started router selection with agent '{router_agent.id}'.",
            payload={"agentId": router_agent.id},
        )
        routing_bundle = self._build_routing_bundle(workflow, agent_by_id)
        router_prompt = self._render_agent_prompt(
            workflow.router_prompt_template or "",
            agent=router_agent,
            goal=self._run_state.goal,
            routing_bundle=routing_bundle,
            judge_bundle="",
            last_output="",
            expert_assessment="",
        )
        decision = await self._run_router(router_agent, workflow, router_prompt)
        executor = agent_by_id[decision.executor_agent_id]
        judge = agent_by_id[decision.judge_agent_id]
        expert = (
            agent_by_id[decision.expert_agent_id]
            if decision.expert_agent_id is not None
            else None
        )
        await self._record_workflow_event(
            "routing_completed",
            "Router selected the workflow agent composition.",
            payload=decision.model_dump(mode="json"),
        )
        return executor, expert, judge, decision

    async def _execute_run(
        self,
        workflow: Any,
        codex_agent: Any,
        expert_agent: Any,
        judge_agent: Any,
    ) -> None:
        try:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            initial_execute_prompt = self._render_agent_prompt(
                workflow.execute_prompt_template,
                agent=codex_agent,
                goal=self._run_state.goal,
                last_output="",
                judge_bundle="",
                expert_assessment="",
            )
            await self._execute_remaining_loops(
                workflow,
                initial_execute_prompt,
                start_loop=1,
                builder_agent=codex_agent,
                expert_agent=expert_agent,
                judge_agent=judge_agent,
            )
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

    async def _resume_from_oracle_checkpoint(self, context: LoadedRunContext) -> None:
        try:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            checkpoint = self._run_state.oracle_resume_checkpoint
            if checkpoint is None:
                raise WorkflowSupervisorError("No Oracle resume checkpoint is available.")
            if self._run_state.last_codex_output is None:
                raise WorkflowSupervisorError(
                    "Cannot resume Oracle-blocked run without preserved Codex output."
                )
            loop_index = checkpoint.loop_index
            codex_output = self._run_state.last_codex_output
            expert_assessment = self._run_state.last_expert_assessment
            expert_report = self._run_state.last_expert_report

            if checkpoint.agent_label == "expert":
                expert_agent = context.expert_agent
                if expert_agent is None or context.workflow.expert_prompt_template is None:
                    raise WorkflowSupervisorError(
                        "Cannot resume expert step because the expert agent is missing."
                    )
                await self._ensure_checkpoint(
                    "advising",
                    f"Resuming expert assessment loop {loop_index}.",
                )
                while True:
                    try:
                        expert_result = await self._run_expert(expert_agent, checkpoint.prompt)
                        expert_assessment = self._format_expert_assessment(expert_result.report)
                        expert_report = expert_result.report
                        break
                    except (OracleAgentError, OracleNotConfiguredError) as exc:
                        if expert_agent.provider != "oracle":
                            raise
                        await self._pause_for_oracle_failure(
                            agent_label="expert",
                            agent_id=expert_agent.id,
                            prompt=checkpoint.prompt,
                            detail=str(exc),
                        )
                if self._run_state is None:
                    raise WorkflowSupervisorError(
                        "Workflow run disappeared during expert assessment."
                    )
                self._clear_oracle_pause("expert")
                self._run_state.last_expert_assessment = self._clip(
                    expert_assessment,
                    limit=8_000,
                )
                self._run_state.last_expert_report = expert_report
                await self._ensure_checkpoint("judging", f"Judge evaluation loop {loop_index}.")
                await self._check_budgets(loop_index, before_judge=True)
                judge_bundle = await self._build_judge_bundle(
                    codex_output,
                    expert_assessment=expert_assessment,
                    expert_report=expert_report,
                )
                judge_prompt = self._render_agent_prompt(
                    context.workflow.judge_prompt_template,
                    agent=context.judge_agent,
                    goal=self._run_state.goal or "",
                    last_output=codex_output,
                    judge_bundle=judge_bundle,
                    expert_assessment=expert_assessment or "",
                )
            else:
                await self._ensure_checkpoint(
                    "judging",
                    f"Resuming judge evaluation loop {loop_index}.",
                )
            await self._check_budgets(loop_index, before_judge=True)
            judge_prompt = checkpoint.prompt

            while True:
                try:
                    decision = await self._run_judge(context.judge_agent, judge_prompt)
                    break
                except (OracleAgentError, OracleNotConfiguredError) as exc:
                    if context.judge_agent.provider != "oracle":
                        raise
                    await self._pause_for_oracle_failure(
                        agent_label="judge",
                        agent_id=context.judge_agent.id,
                        prompt=judge_prompt,
                        detail=str(exc),
                    )
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared after judging.")
            self._clear_oracle_pause("judge")
            next_prompt = await self._apply_judge_decision(decision)
            if next_prompt is None:
                return
            await self._execute_remaining_loops(
                context.workflow,
                next_prompt,
                start_loop=loop_index + 1,
                builder_agent=context.codex_agent,
                expert_agent=context.expert_agent,
                judge_agent=context.judge_agent,
            )
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

    async def _execute_remaining_loops(
        self,
        workflow: Any,
        execute_prompt: str,
        *,
        start_loop: int,
        builder_agent: Any,
        expert_agent: Any,
        judge_agent: Any,
    ) -> None:
        loop_index = start_loop - 1
        while True:
            loop_index += 1
            await self._check_budgets(loop_index)
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared during execution.")
            self._run_state.current_loop = loop_index
            self._run_state.updated_at = datetime.now(UTC)

            await self._ensure_checkpoint("executing", f"Codex execution loop {loop_index}.")
            execute_prompt, applied_steering_notes = self._consume_steering(execute_prompt)
            if applied_steering_notes:
                await self._record_workflow_event(
                    "steering_applied",
                    "Applied queued operator steering to the next builder turn.",
                    payload={"notes": applied_steering_notes},
                )
                await self._append_notebook_page(
                    kind="steering_applied",
                    title=f"Steering applied for loop {loop_index}",
                    summary="Applied operator steering before the next builder execution slice.",
                    why="Scoped steering overrides were queued for the next execution turn.",
                    changes=applied_steering_notes,
                    next_steps=["Execute the next builder slice with the scoped task update."],
                    tags=["steering", f"loop-{loop_index}"],
                )
            codex_result = await self._run_codex_turn(execute_prompt, kind="executing")
            codex_output = codex_result.text
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared during judging.")
            self._run_state.last_codex_output = self._clip(codex_output)
            await self._append_notebook_page(
                kind="execution_slice",
                title=f"Execution slice {loop_index} completed",
                summary=self._first_sentence(codex_output, fallback="Completed a builder execution slice."),
                why=f"Builder loop {loop_index} executed against the current managed workspace state.",
                changes=await self._git_stat_lines(limit=6),
                outcomes=[f"Builder turn completed as `{codex_result.turn_id}`."],
                next_steps=["Review expert and judge results for the next decision."],
                tags=["builder", f"loop-{loop_index}"],
                transcript_item_ids=codex_result.transcript_item_ids,
            )

            expert_assessment: str | None = None
            expert_report: ExpertAssessment | None = None
            if expert_agent is not None and workflow.expert_prompt_template is not None:
                await self._ensure_checkpoint(
                    "advising",
                    f"Expert assessment loop {loop_index}.",
                )
                expert_bundle = await self._build_judge_bundle(
                    codex_output,
                    expert_assessment=None,
                    expert_report=None,
                )
                expert_prompt = self._render_agent_prompt(
                    workflow.expert_prompt_template,
                    agent=expert_agent,
                    goal=self._run_state.goal or "",
                    last_output=codex_output,
                    judge_bundle=expert_bundle,
                    expert_assessment="",
                )
                while True:
                    try:
                        expert_result = await self._run_expert(expert_agent, expert_prompt)
                        expert_assessment = self._format_expert_assessment(expert_result.report)
                        expert_report = expert_result.report
                        break
                    except (OracleAgentError, OracleNotConfiguredError) as exc:
                        if expert_agent.provider != "oracle":
                            raise
                        await self._pause_for_oracle_failure(
                            agent_label="expert",
                            agent_id=expert_agent.id,
                            prompt=expert_prompt,
                            detail=str(exc),
                        )
                if self._run_state is None:
                    raise WorkflowSupervisorError(
                        "Workflow run disappeared during expert assessment."
                    )
                self._clear_oracle_pause("expert")
                self._run_state.last_expert_assessment = self._clip(
                    expert_assessment,
                    limit=8_000,
                )
                self._run_state.last_expert_report = expert_report

            await self._ensure_checkpoint("judging", f"Judge evaluation loop {loop_index}.")
            await self._check_budgets(loop_index, before_judge=True)
            judge_bundle = await self._build_judge_bundle(
                codex_output,
                expert_assessment=expert_assessment,
                expert_report=expert_report,
            )
            judge_prompt = self._render_agent_prompt(
                workflow.judge_prompt_template,
                agent=judge_agent,
                goal=self._run_state.goal or "",
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
                        agent_id=judge_agent.id,
                        prompt=judge_prompt,
                        detail=str(exc),
                    )
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared after judging.")
            self._clear_oracle_pause("judge")
            next_prompt = await self._apply_judge_decision(decision)
            if next_prompt is None:
                return
            execute_prompt = next_prompt

    async def _apply_judge_decision(self, decision: JudgeDecision) -> str | None:
        if self._run_state is None:
            raise WorkflowSupervisorError("Workflow run disappeared after judging.")
        self._run_state.judge_calls += 1
        self._run_state.last_judge_decision = decision.decision
        self._run_state.last_judge_summary = decision.summary
        self._run_state.last_continuation_prompt = (
            decision.next_prompt if decision.decision == "continue" else None
        )
        self._run_state.updated_at = datetime.now(UTC)
        next_steps: list[str] = []
        issues: list[str] = []
        outcomes = [f"Decision: {decision.decision}", decision.summary]
        if decision.decision == "continue" and decision.next_prompt:
            next_steps.append(decision.next_prompt)
        if decision.decision == "complete" and decision.completion_note:
            outcomes.append(decision.completion_note)
        if decision.decision == "fail" and decision.failure_reason:
            issues.append(decision.failure_reason)
        await self._append_notebook_page(
            kind="judge_decision",
            title=f"Judge decision: {decision.decision}",
            summary=decision.summary,
            why="The judge evaluated the current run state, repo evidence, and optional expert input.",
            issues=issues,
            outcomes=outcomes,
            next_steps=next_steps,
            tags=["judge", decision.decision],
            artifact_paths=self._artifact_paths(
                "judge_request",
                "last-judge-request.json",
                "judge_response",
                "last-judge-response.json",
            ),
        )

        if decision.decision == "complete":
            await self._finish_run(
                status="completed",
                phase="completed",
                note=decision.completion_note or decision.summary,
            )
            return None
        if decision.decision == "fail":
            await self._finish_run(
                status="failed",
                phase="failed",
                note=decision.failure_reason or decision.summary,
            )
            return None
        if not decision.next_prompt:
            raise WorkflowSupervisorError(
                "Judge returned continue without a next_prompt."
            )
        return decision.next_prompt

    async def _run_codex_turn(
        self,
        prompt: str,
        *,
        kind: str,
        output_schema: dict[str, Any] | None = None,
    ) -> CodexTurnResult:
        if self._bridge is None:
            raise WorkflowSupervisorError("Codex session is not available.")
        await self._record_workflow_event(
            "codex_turn_started",
            f"Started Codex {kind} turn.",
            payload={"prompt": self._clip(prompt, limit=2_000)},
        )
        snapshot = await self._bridge.start_turn(prompt, output_schema=output_schema)
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
        return CodexTurnResult(
            text=assistant_text,
            turn_id=turn.id,
            transcript_item_ids=self._assistant_item_ids_for_turn(completed, turn.id),
        )

    async def _run_router(
        self,
        router_agent: AgentDefinition,
        workflow: WorkflowDefinition,
        prompt: str,
    ) -> RunRoutingDecision:
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-router-request.json", {"prompt": prompt})
        raw_answer = await self._run_aux_codex_turn(
            router_agent,
            prompt,
            event_log_subdir="router-codex-events",
            label="router",
            output_schema=self._router_output_schema(workflow),
        )
        decision = RunRoutingDecision.model_validate_json(self._extract_json(raw_answer))
        if self._resources is not None:
            self._write_json(
                self._resources.run_dir / "last-router-response.json",
                {
                    "answer": raw_answer,
                    "provider": "codex",
                    "decision": decision.model_dump(mode="json"),
                },
            )
        return decision

    async def _run_expert(self, expert_agent: Any, prompt: str) -> ExpertAssessmentResult:
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-expert-request.json", {"prompt": prompt})
        await self._record_workflow_event(
            "expert_started",
            f"Started {expert_agent.provider} expert assessment.",
            payload={"agentId": expert_agent.id, "provider": expert_agent.provider},
        )
        remote_host: str | None = None
        duration_seconds: float | None = None
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
            remote_host = response.remote_host
            duration_seconds = response.duration_seconds
        else:
            answer = await self._run_aux_codex_turn(
                expert_agent,
                prompt,
                event_log_subdir="expert-codex-events",
                label="expert",
                output_schema=self._expert_output_schema(),
            )
        report = self._parse_expert_assessment(answer)
        if self._resources is not None:
            response_payload: dict[str, object] = {
                "answer": answer,
                "provider": expert_agent.provider,
                "report": report.model_dump(mode="json"),
            }
            if remote_host is not None:
                response_payload["remoteHost"] = remote_host
            if duration_seconds is not None:
                response_payload["durationSeconds"] = duration_seconds
            self._write_json(
                self._resources.run_dir / "last-expert-response.json",
                response_payload,
            )
        await self._record_workflow_event(
            "expert_completed",
            f"Completed {expert_agent.provider} expert assessment.",
            payload={
                "agentId": expert_agent.id,
                "provider": expert_agent.provider,
                "summary": self._clip(report.summary, limit=1_000),
                "recommendedNextPrompt": self._clip(report.recommended_next_prompt, limit=2_000),
            },
        )
        return ExpertAssessmentResult(raw_text=answer, report=report)

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
                output_schema=self._judge_output_schema(),
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
        *,
        before_judge: bool = False,
    ) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow state is available.")
        elapsed_minutes = (datetime.now(UTC) - self._run_state.started_at).total_seconds() / 60
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

    def _clear_oracle_pause(self, agent_label: Literal["expert", "judge"]) -> None:
        if self._run_state is None:
            return
        checkpoint = self._run_state.oracle_resume_checkpoint
        if checkpoint is not None and checkpoint.agent_label == agent_label:
            self._run_state.oracle_resume_checkpoint = None
        prefix = f"Oracle {agent_label} failed and the run is paused:"
        if self._run_state.last_error and self._run_state.last_error.startswith(prefix):
            self._run_state.last_error = None
        self._run_state.updated_at = datetime.now(UTC)

    async def _pause_for_oracle_failure(
        self,
        *,
        agent_label: Literal["expert", "judge"],
        agent_id: str,
        prompt: str,
        detail: str,
    ) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        thread_id: str | None = None
        if self._bridge is not None:
            bridge_thread = self._bridge.snapshot().state.thread
            if bridge_thread is not None:
                thread_id = bridge_thread.id
        elif self._archived_snapshot is not None and self._archived_snapshot.state.thread is not None:
            thread_id = self._archived_snapshot.state.thread.id
        if thread_id is None:
            raise WorkflowSupervisorError("Cannot pause for Oracle failure without a Codex thread.")
        self._pause_gate.clear()
        self._run_state.status = "paused"
        self._run_state.phase = "paused"
        self._run_state.oracle_resume_checkpoint = OracleResumeCheckpoint(
            agent_label=agent_label,
            agent_id=agent_id,
            thread_id=thread_id,
            loop_index=max(1, self._run_state.current_loop),
            prompt=prompt,
            detail=detail,
            noted_at=datetime.now(UTC),
        )
        self._run_state.last_error = (
            f"Oracle {agent_label} failed and the run is paused: {detail}"
        )
        self._run_state.updated_at = datetime.now(UTC)
        await self._record_workflow_event(
            "oracle_blocked",
            f"Oracle {agent_label} failed; run paused until operator resume.",
            payload={
                "agent": agent_label,
                "agentId": agent_id,
                "detail": detail,
                "threadId": thread_id,
                "loop": self._run_state.current_loop,
            },
        )
        await self._append_notebook_page(
            kind="oracle_blocked",
            title=f"Oracle {agent_label} blocked the run",
            summary=f"Oracle {agent_label} failed and the run paused for operator intervention.",
            why=detail,
            issues=[detail],
            next_steps=["Fix the Oracle path or remote session, then resume the run."],
            tags=["oracle", "blocked", agent_label],
        )
        await self._broadcast_state()
        await self._flush_staged_snapshot_now()
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
            await self._flush_staged_snapshot_now()
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
            self._run_state.oracle_resume_checkpoint = None
            self._run_state.last_error = note if status == "failed" else None
            self._run_state.completed_at = datetime.now(UTC)
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                f"run_{status}",
                note,
            )
            await self._append_notebook_page(
                kind="run_finished",
                title=f"Run {status}",
                summary=note,
                why="The workflow reached a terminal state.",
                issues=[note] if status == "failed" else None,
                outcomes=[
                    f"Status: {status}",
                    f"Phase: {phase}",
                    f"Loops: {self._run_state.current_loop}/{self._run_state.max_loops}",
                    (
                        f"Judge calls: {self._run_state.judge_calls}/{self._run_state.max_judge_calls}"
                    ),
                ],
                tags=["run-finished", status],
            )
        await self._stop_bridge()
        await self._broadcast_state()
        await self._flush_staged_snapshot_now()

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
        self._stage_run_snapshot()
        await self._broadcast(
            StreamEnvelope(
                type="workflow_event",
                state=self.snapshot().state,
                event=None,
                workflow_event=record,
            )
        )

    async def _append_notebook_page(
        self,
        *,
        kind: NotebookPageKind,
        title: str,
        summary: str,
        why: str | None = None,
        changes: list[str] | None = None,
        issues: list[str] | None = None,
        outcomes: list[str] | None = None,
        next_steps: list[str] | None = None,
        tags: list[str] | None = None,
        transcript_item_ids: list[str] | None = None,
        artifact_paths: dict[str, str] | None = None,
        amends_page_id: str | None = None,
    ) -> None:
        if self._resources is None or self._run_state is None:
            return
        await self._resources.notebook_projection.append_page(
            run_id=self._run_state.id,
            kind=kind,
            title=title,
            summary=summary,
            snapshot=self.snapshot(),
            why=why,
            changes=changes,
            issues=issues,
            outcomes=outcomes,
            next_steps=next_steps,
            tags=tags,
            transcript_item_ids=transcript_item_ids,
            artifact_paths=artifact_paths,
            amends_page_id=amends_page_id,
        )

    async def _broadcast_state(self) -> None:
        self._stage_run_snapshot()
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
        expert_report: ExpertAssessment | None,
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
            "executionDir": self._run_state.execution_dir,
            "routingDecision": (
                self._run_state.last_routing_decision.model_dump(mode="json")
                if self._run_state.last_routing_decision is not None
                else None
            ),
            "loop": self._run_state.current_loop,
            "judgeCalls": self._run_state.judge_calls,
            "recentSteeringNotes": self._run_state.recent_steering_notes[-5:],
            "lastCodexOutput": self._clip(codex_output, limit=8_000),
            "expertAssessment": self._clip(expert_assessment, limit=8_000),
            "expertReport": (
                expert_report.model_dump(mode="json") if expert_report is not None else None
            ),
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
        output_schema: dict[str, Any] | None = None,
    ) -> str:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        if self._resources is None:
            raise WorkflowSupervisorError("No workflow resources are available.")
        bridge = CodexAppServerBridge(
            self._settings,
            workspace_root=self._execution_dir_for_run(),
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
            snapshot = await bridge.start_turn(prompt, output_schema=output_schema)
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
            str(self._execution_dir_for_run()),
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

    async def _git_stat_lines(self, *, limit: int = 6) -> list[str]:
        diff_stat = await self._git_output("diff", "--stat")
        if not diff_stat or diff_stat in {"(empty)", "git command failed", "git command timed out"}:
            return []
        lines = [line.strip() for line in diff_stat.splitlines() if line.strip()]
        summary_lines = [
            line for line in lines if not line.endswith("changed)") and "file changed" not in line
        ]
        return summary_lines[:limit]

    def _artifact_paths(self, *pairs: str) -> dict[str, str]:
        if self._resources is None:
            return {}
        iterator = iter(pairs)
        paths: dict[str, str] = {}
        for key, relative_path in zip(iterator, iterator, strict=False):
            artifact_path = self._resources.run_dir / relative_path
            if artifact_path.exists():
                paths[key] = str(artifact_path)
        return paths

    def _consume_steering(self, prompt: str) -> tuple[str, list[str]]:
        if self._run_state is None or not self._run_state.pending_steering_notes:
            return prompt, []
        notes = [note.strip() for note in self._run_state.pending_steering_notes if note.strip()]
        self._run_state.pending_steering_notes.clear()
        self._run_state.recent_steering_notes.extend(notes)
        self._run_state.recent_steering_notes = self._run_state.recent_steering_notes[-10:]
        if not notes:
            return prompt, []
        notes_block = "\n".join(f"- {note}" for note in notes)
        return (
            (
                f"{prompt}\n\n<task_update>\n"
                "Scope: next execution turn only\n"
                "Override:\n"
                f"{notes_block}\n"
                "Carry forward:\n"
                "- All earlier run instructions still apply unless they conflict with the override above.\n"
                "</task_update>"
            ),
            notes,
        )

    def _build_routing_bundle(
        self,
        workflow: WorkflowDefinition,
        agent_by_id: dict[str, AgentDefinition],
    ) -> str:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        payload = {
            "goal": self._run_state.goal,
            "workflowId": workflow.id,
            "targetDir": self._run_state.target_dir,
            "executionDir": self._run_state.execution_dir,
            "candidates": {
                "executorAgents": [
                    self._agent_summary(agent_by_id[agent_id])
                    for agent_id in workflow.router_executor_options
                ],
                "judgeAgents": [
                    self._agent_summary(agent_by_id[agent_id])
                    for agent_id in workflow.router_judge_options
                ],
                "expertAgents": [
                    self._agent_summary(agent_by_id[agent_id])
                    for agent_id in workflow.router_expert_options
                ],
                "allowNoExpert": True,
            },
        }
        return json.dumps(payload, ensure_ascii=True, indent=2)

    @staticmethod
    def _agent_summary(agent: AgentDefinition) -> dict[str, object]:
        return {
            "id": agent.id,
            "provider": agent.provider,
            "role": agent.role,
            "description": agent.description,
            "model": agent.model,
            "reasoningEffort": agent.reasoning_effort,
            "webAccess": agent.web_access,
        }

    @staticmethod
    def _judge_output_schema() -> dict[str, Any]:
        return JudgeDecision.model_json_schema()

    @staticmethod
    def _expert_output_schema() -> dict[str, Any]:
        return ExpertAssessment.model_json_schema()

    @staticmethod
    def _router_output_schema(workflow: WorkflowDefinition) -> dict[str, Any]:
        expert_options = [
            {"type": "string", "enum": workflow.router_expert_options},
            {"type": "null"},
        ]
        if not workflow.router_expert_options:
            expert_options = [{"type": "null"}]
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "workflow_id": {"type": "string", "enum": [workflow.id]},
                "executor_agent_id": {
                    "type": "string",
                    "enum": workflow.router_executor_options,
                },
                "judge_agent_id": {
                    "type": "string",
                    "enum": workflow.router_judge_options,
                },
                "expert_agent_id": {"anyOf": expert_options},
                "summary": {"type": "string"},
            },
            "required": [
                "workflow_id",
                "executor_agent_id",
                "judge_agent_id",
                "expert_agent_id",
                "summary",
            ],
        }

    @staticmethod
    def _assistant_text_for_turn(snapshot: DashboardSnapshot, turn_id: str) -> str:
        for item in reversed(snapshot.state.transcript):
            if item.role == "assistant" and item.turn_id == turn_id:
                return item.text.strip()
        return ""

    @staticmethod
    def _assistant_item_ids_for_turn(snapshot: DashboardSnapshot, turn_id: str) -> list[str]:
        return [
            item.item_id
            for item in snapshot.state.transcript
            if item.role == "assistant" and item.turn_id == turn_id
        ]

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
    def _git_head_commit_for(path: Path) -> str:
        try:
            completed = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "HEAD"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise WorkflowSupervisorError(
                f"Could not inspect git HEAD for {path}: {exc}"
            ) from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "git rev-parse HEAD failed"
            raise WorkflowSupervisorError(
                f"Could not determine the base commit for managed worktree creation: {detail}"
            )
        return completed.stdout.strip()

    @staticmethod
    def _run_git(repo_root: Path, *args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", "-C", str(repo_root), *args],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise WorkflowSupervisorError(f"Could not run git in {repo_root}: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
            raise WorkflowSupervisorError(detail)
        return completed.stdout.strip()

    def _managed_worktree_root(self) -> Path:
        return self._settings.workspace_root / ".shmocky" / "worktrees"

    def _execution_dir_for_run(self) -> Path:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        execution_dir = self._run_state.execution_dir or self._run_state.target_dir
        return Path(execution_dir)

    def _cleanup_managed_workspace(self) -> None:
        if self._run_state is None or self._run_state.workspace_strategy != "git_worktree":
            return
        execution_dir_value = self._run_state.execution_dir
        branch_name = self._run_state.worktree_branch
        if not execution_dir_value or not branch_name:
            return
        self._cleanup_prepared_worktree(
            Path(self._run_state.target_dir),
            Path(execution_dir_value),
            branch_name,
        )

    def _cleanup_prepared_worktree(
        self,
        source_repo_root: Path,
        execution_dir: Path,
        branch_name: str,
    ) -> None:
        if execution_dir.exists():
            try:
                self._run_git(source_repo_root, "worktree", "remove", "--force", str(execution_dir))
            except WorkflowSupervisorError:
                shutil.rmtree(execution_dir, ignore_errors=True)
        try:
            self._run_git(source_repo_root, "branch", "-D", branch_name)
        except WorkflowSupervisorError:
            pass

    @classmethod
    def _parse_expert_assessment(cls, raw_answer: str) -> ExpertAssessment:
        json_error: Exception | None = None
        try:
            payload = cls._extract_json(raw_answer)
            return ExpertAssessment.model_validate_json(payload)
        except (ValidationError, WorkflowSupervisorError) as exc:
            json_error = exc

        try:
            return cls._parse_expert_text_assessment(raw_answer)
        except ValidationError as exc:
            fallback = cls._fallback_expert_assessment(raw_answer)
            if fallback is not None:
                return fallback
            raise WorkflowSupervisorError(
                "Expert returned a malformed assessment payload that could not be parsed."
            ) from exc
        except WorkflowSupervisorError as exc:
            fallback = cls._fallback_expert_assessment(raw_answer)
            if fallback is not None:
                return fallback
            raise WorkflowSupervisorError(
                "Expert returned a malformed assessment payload that could not be parsed."
            ) from (json_error or exc)

    @classmethod
    def _parse_expert_text_assessment(cls, raw_answer: str) -> ExpertAssessment:
        text = cls._strip_code_fence(raw_answer)
        sections = cls._extract_labeled_sections(
            text,
            (
                "summary",
                "risks",
                "missed opportunities",
                "suggested checks",
                "recommended next prompt",
            ),
        )
        summary = sections.get("summary")
        if not summary:
            raise WorkflowSupervisorError("Expert response is missing a Summary section.")
        payload: dict[str, object] = {
            "summary": summary.strip(),
            "risks": cls._extract_bullets(sections.get("risks")),
            "missed_opportunities": cls._extract_bullets(sections.get("missed opportunities")),
            "suggested_checks": cls._extract_bullets(sections.get("suggested checks")),
        }
        recommended_next_prompt = sections.get("recommended next prompt")
        if recommended_next_prompt:
            payload["recommended_next_prompt"] = recommended_next_prompt.strip()
        return ExpertAssessment.model_validate(payload)

    @staticmethod
    def _format_expert_assessment(report: ExpertAssessment) -> str:
        sections = [f"Summary:\n{report.summary.strip()}"]
        for title, items in (
            ("Risks", report.risks),
            ("Missed opportunities", report.missed_opportunities),
            ("Suggested checks", report.suggested_checks),
        ):
            bullet_block = "\n".join(f"- {item}" for item in items) if items else "- none"
            sections.append(f"{title}:\n{bullet_block}")
        if report.recommended_next_prompt:
            sections.append(
                "Recommended next prompt:\n"
                + report.recommended_next_prompt.strip()
            )
        return "\n\n".join(sections)

    @classmethod
    def _fallback_expert_assessment(cls, raw_answer: str) -> ExpertAssessment | None:
        summary = cls._clip(cls._strip_code_fence(raw_answer), limit=8_000)
        if not summary:
            return None
        return ExpertAssessment(summary=summary)

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
    def _extract_labeled_sections(
        text: str,
        labels: tuple[str, ...],
    ) -> dict[str, str]:
        escaped_labels = "|".join(re.escape(label) for label in labels)
        pattern = re.compile(rf"(?im)^({escaped_labels})\s*:\s*")
        matches = list(pattern.finditer(text))
        if not matches:
            raise WorkflowSupervisorError("Response does not use the expected labels.")

        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            section_name = match.group(1).lower()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[section_name] = text[start:end].strip()
        return sections

    @classmethod
    def _extract_judge_text_sections(cls, text: str) -> dict[str, str]:
        return cls._extract_labeled_sections(
            text,
            ("Decision", "Summary", "Next prompt", "Completion note", "Failure reason"),
        )

    @staticmethod
    def _extract_bullets(text: str | None) -> list[str]:
        if not text:
            return []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        bullets: list[str] = []
        for line in lines:
            if line.startswith("- "):
                bullets.append(line[2:].strip())
            elif line.startswith("* "):
                bullets.append(line[2:].strip())
            elif line != "- none" and line != "none":
                bullets.append(line)
        return bullets

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

    @classmethod
    def _first_sentence(cls, text: str | None, *, fallback: str) -> str:
        clipped = cls._clip(text, limit=800)
        if not clipped:
            return fallback
        match = re.search(r"(.+?[.!?])(?:\s|$)", clipped, re.DOTALL)
        if match is not None:
            return match.group(1).strip()
        first_line = clipped.splitlines()[0].strip()
        return first_line or fallback

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _stage_run_snapshot(self) -> None:
        if self._resources is None:
            return
        snapshot = self.snapshot()
        snapshot_path = self._resources.run_dir / self.RUN_SNAPSHOT_FILENAME
        self._archived_snapshot = snapshot.model_copy(deep=True)
        self._staged_snapshot = snapshot
        self._staged_snapshot_path = snapshot_path
        self._snapshot_revision += 1
        self._staged_snapshot_revision = self._snapshot_revision
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            self._write_snapshot_file(snapshot_path, snapshot.model_dump_json(indent=2))
            self._snapshot_flushed_revision = self._staged_snapshot_revision
            return
        if self._snapshot_flush_task is None or self._snapshot_flush_task.done():
            self._snapshot_flush_task = asyncio.create_task(self._flush_staged_snapshot_loop())

    async def _flush_staged_snapshot_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.SNAPSHOT_FLUSH_DEBOUNCE_SECONDS)
                await self._flush_staged_snapshot_to_disk()
                if self._snapshot_flushed_revision >= self._snapshot_revision:
                    return
        except asyncio.CancelledError:
            return
        finally:
            current = asyncio.current_task()
            if self._snapshot_flush_task is current:
                self._snapshot_flush_task = None

    async def _flush_staged_snapshot_now(self) -> None:
        await self._cancel_snapshot_flush_task()
        await self._flush_staged_snapshot_to_disk()

    async def _cancel_snapshot_flush_task(self) -> None:
        task = self._snapshot_flush_task
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        self._snapshot_flush_task = None

    async def _flush_staged_snapshot_to_disk(self) -> None:
        async with self._snapshot_flush_lock:
            snapshot = self._staged_snapshot
            snapshot_path = self._staged_snapshot_path
            revision = self._staged_snapshot_revision
            if snapshot is None or snapshot_path is None:
                return
            payload = snapshot.model_dump_json(indent=2)
            await asyncio.to_thread(self._write_snapshot_file, snapshot_path, payload)
            if revision > self._snapshot_flushed_revision:
                self._snapshot_flushed_revision = revision

    @staticmethod
    def _write_snapshot_file(path: Path, payload: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")


def as_http_error(error: Exception) -> HTTPException:
    if isinstance(error, WorkflowConflictError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, WorkflowNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))
