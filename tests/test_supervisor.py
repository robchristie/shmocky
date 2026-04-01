from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from shmocky.bridge import BridgeError, CodexAppServerBridge
from shmocky.event_store import WorkflowEventStore
from shmocky.models import (
    ConnectionState,
    DashboardSnapshot,
    DashboardState,
    OracleResumeCheckpoint,
    PendingServerRequest,
    ServerRequestResolutionRequest,
    ThreadState,
    TranscriptItem,
    WorkflowEventRecord,
    WorkflowRunRequest,
    WorkflowRunState,
)
from shmocky.settings import AppSettings
from shmocky.supervisor import LoadedRunContext, RunResources, WorkflowSupervisor, WorkflowSupervisorError


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Shmocky Test"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "shmocky@example.com"],
        check=True,
    )
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "init"], check=True)


def test_supervisor_extract_json_from_fenced_answer() -> None:
    payload = WorkflowSupervisor._extract_json(
        """```json
{
  "decision": "continue",
  "summary": "Need one more step.",
  "next_prompt": "Run the tests and fix the failure."
}
```"""
    )

    assert '"decision": "continue"' in payload


def test_supervisor_repairs_judge_payload_with_unescaped_quotes_in_next_prompt() -> None:
    decision = WorkflowSupervisor._parse_judge_decision(
        '{"decision":"continue","summary":"Need one more step.",'
        '"next_prompt":"Preserve "lowest winning nonce" semantics while tuning chunk sizing."}'
    )

    assert decision.decision == "continue"
    assert decision.summary == "Need one more step."
    assert (
        decision.next_prompt
        == 'Preserve "lowest winning nonce" semantics while tuning chunk sizing.'
    )


def test_supervisor_parses_labeled_text_judge_response() -> None:
    decision = WorkflowSupervisor._parse_judge_decision(
        """Decision: continue
Summary: Need one more implementation slice.
Next prompt:
Continue from the current repository state.

Focus on benchmark realism and preserve correctness.
"""
    )

    assert decision.decision == "continue"
    assert decision.summary == "Need one more implementation slice."
    assert decision.next_prompt == (
        "Continue from the current repository state.\n\n"
        "Focus on benchmark realism and preserve correctness."
    )


def test_supervisor_render_template_preserves_literal_json_braces() -> None:
    rendered = WorkflowSupervisor._render_template(
        'Return {"decision":"complete"} and {judge_bundle}',
        judge_bundle="BUNDLE",
    )

    assert rendered == 'Return {"decision":"complete"} and BUNDLE'


def test_supervisor_render_judge_prompt_fits_oracle_limit() -> None:
    prompt_limit = 20_000
    prompt = WorkflowSupervisor._render_judge_prompt(
        "Context:\n{judge_bundle}",
        prompt_limit=prompt_limit,
        goal="goal",
        last_output="output",
        judge_bundle="X" * (prompt_limit + 5_000),
    )

    assert len(prompt) <= prompt_limit
    assert prompt.startswith("Context:\n")


def test_supervisor_formats_scoped_task_update_for_steering(tmp_path: Path) -> None:
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="steering test",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path / "repo"),
        goal="Finish the task.",
        status="running",
        phase="executing",
        codex_agent_id="builder",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
        pending_steering_notes=["Prioritize flaky tests.", "Do not touch UI files."],
    )

    updated_prompt = supervisor._consume_steering("Continue the task.")

    assert "<task_update>" in updated_prompt
    assert "Scope: next execution turn only" in updated_prompt
    assert "- Prioritize flaky tests." in updated_prompt
    assert "- Do not touch UI files." in updated_prompt
    assert "Carry forward:" in updated_prompt
    assert supervisor._run_state.pending_steering_notes == []


def test_supervisor_rejects_target_inside_workspace_root(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.builder]
provider = "codex"
role = "builder"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
executor_agent = "builder"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    target_dir = tmp_path / "var" / "test"
    target_dir.mkdir(parents=True)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(WorkflowSupervisorError, match="inside the Shmocky workspace"):
        supervisor._validate_target_dir(target_dir)


def test_supervisor_rejects_non_git_target_dir(tmp_path: Path) -> None:
    config_path = tmp_path / "config-home" / "shmocky.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
[agents.builder]
provider = "codex"
role = "builder"

[agents.judge]
provider = "codex"
role = "judge"

[workflows.plan_execute_judge]
executor_agent = "builder"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    target_dir = tmp_path / "external-dir"
    target_dir.mkdir()
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=config_path.parent,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(WorkflowSupervisorError, match="git repository root"):
        supervisor._validate_target_dir(target_dir)


def test_supervisor_rejects_target_nested_in_other_repo(tmp_path: Path) -> None:
    config_path = tmp_path / "config-home" / "shmocky.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
[agents.builder]
provider = "codex"
role = "builder"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
executor_agent = "builder"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    repo_root = tmp_path / "external-repo"
    target_dir = repo_root / "nested" / "workdir"
    target_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=config_path.parent,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(
        WorkflowSupervisorError,
        match="must be the git repository root itself",
    ):
        supervisor._validate_target_dir(target_dir)


def test_supervisor_lists_and_loads_persisted_run_snapshots(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "20260331T120000Z-abcdef12"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 3, 31, 12, 0, tzinfo=UTC)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=False),
            workflow_run=WorkflowRunState(
                id="20260331T120000Z-abcdef12",
                run_name="workflow testing xyz",
                workflow_id="plan_execute_judge",
                target_dir=str(tmp_path / "repo"),
                goal="Ship the feature.",
                status="completed",
                phase="completed",
                codex_agent_id="builder",
                judge_agent_id="judge",
                started_at=started_at,
                updated_at=started_at,
                completed_at=started_at,
                max_loops=4,
                max_judge_calls=4,
                max_runtime_minutes=45,
                last_judge_decision="complete",
                last_judge_summary="Done.",
            ),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    (run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME).write_text(
        snapshot.model_dump_json(indent=2),
        encoding="utf-8",
    )
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    history = supervisor.runs_history()
    loaded = supervisor.load_run_snapshot("20260331T120000Z-abcdef12")

    assert [entry.id for entry in history.runs] == ["20260331T120000Z-abcdef12"]
    assert history.runs[0].run_name == "workflow testing xyz"
    assert history.runs[0].last_judge_summary == "Done."
    assert loaded.state.workflow_run is not None
    assert loaded.state.workflow_run.status == "completed"


def test_supervisor_debounces_snapshot_flushes_for_bursty_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "run-1"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._resources = RunResources(
        run_dir=run_dir,
        workflow_event_store=WorkflowEventStore(run_dir / "workflow-events.jsonl"),
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="burst test",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path / "repo"),
        goal="Keep snapshot writes cheap.",
        status="running",
        phase="executing",
        codex_agent_id="builder",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
    )

    writes: list[Path] = []

    def fake_write_snapshot_file(path: Path, payload: str) -> None:
        writes.append(path)

    monkeypatch.setattr(
        WorkflowSupervisor,
        "_write_snapshot_file",
        staticmethod(fake_write_snapshot_file),
    )

    async def exercise() -> None:
        supervisor._stage_run_snapshot()
        supervisor._stage_run_snapshot()
        supervisor._stage_run_snapshot()
        await asyncio.sleep(supervisor.SNAPSHOT_FLUSH_DEBOUNCE_SECONDS * 3)

    asyncio.run(exercise())

    assert writes == [run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME]


def test_supervisor_snapshot_uses_archived_completed_run_when_bridge_is_gone(
    tmp_path: Path,
) -> None:
    started_at = datetime(2026, 3, 31, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="named run",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path / "repo"),
        goal="Explain the run.",
        status="failed",
        phase="failed",
        codex_agent_id="builder",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        completed_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
        last_continuation_prompt="Run the benchmark again with the new flag.",
        last_error="Loop budget exceeded.",
    )
    supervisor._archived_snapshot = DashboardSnapshot.model_validate(
        {
            "state": {
                "workspace_root": str(tmp_path / "repo"),
                "event_log_path": str(tmp_path / ".shmocky" / "events"),
                "connection": {
                    "backend_online": True,
                    "codex_connected": True,
                    "initialized": True,
                    "app_server_pid": 123,
                },
                "thread": {"id": "thread-1", "status": "idle"},
                "transcript": [
                    {
                        "item_id": "assistant-1",
                        "role": "assistant",
                        "text": "Investigated the repository.",
                        "status": "completed",
                        "turn_id": "turn-1",
                    }
                ],
                "workflow_run": supervisor._run_state.model_dump(mode="json"),
            },
            "recent_events": [],
            "recent_workflow_events": [],
        }
    )

    snapshot = supervisor.snapshot()

    assert snapshot.state.connection.codex_connected is False
    assert snapshot.state.connection.app_server_pid is None
    assert snapshot.state.workflow_run is not None
    assert snapshot.state.workflow_run.last_error == "Loop budget exceeded."
    assert (
        snapshot.state.workflow_run.last_continuation_prompt
        == "Run the benchmark again with the new flag."
    )
    assert [item.text for item in snapshot.state.transcript] == [
        "Investigated the repository."
    ]


def test_supervisor_resolves_pending_server_request(tmp_path: Path) -> None:
    noted_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    class DummyBridge:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []
            self._snapshot = DashboardSnapshot(
                state=DashboardState(
                    workspace_root=str(tmp_path),
                    event_log_path=str(tmp_path / ".shmocky" / "events"),
                    connection=ConnectionState(backend_online=True, codex_connected=True),
                    pending_server_request=PendingServerRequest(
                        request_id="req-1",
                        method="item/commandExecution/requestApproval",
                        params={"command": "git status"},
                        noted_at=noted_at,
                    ),
                ),
                recent_events=[],
                recent_workflow_events=[],
            )

        def snapshot(self) -> DashboardSnapshot:
            return self._snapshot

        async def resolve_server_request(self, request_id: str, *, result: object) -> DashboardSnapshot:
            self.calls.append((request_id, result))
            return self._snapshot

    bridge = DummyBridge()
    supervisor._bridge = cast(CodexAppServerBridge, bridge)

    snapshot = asyncio.run(
        supervisor.resolve_server_request(
            "req-1",
            ServerRequestResolutionRequest(result={"decision": "accept"}),
        )
    )

    assert bridge.calls == [("req-1", {"decision": "accept"})]
    assert snapshot.state.pending_server_request is not None
    assert snapshot.state.pending_server_request.request_id == "req-1"


def test_supervisor_pauses_and_resumes_after_oracle_failure(tmp_path: Path) -> None:
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="oracle wait test",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path),
        goal="Keep waiting for Oracle.",
        status="running",
        phase="advising",
        codex_agent_id="builder",
        expert_agent_id="expert",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
    )

    async def exercise() -> None:
        supervisor._archived_snapshot = DashboardSnapshot(
            state=DashboardState(
                workspace_root=str(tmp_path),
                event_log_path=str(tmp_path / ".shmocky" / "events"),
                connection=ConnectionState(backend_online=True, codex_connected=False),
                thread=ThreadState(id="thread-1", status="idle"),
                workflow_run=supervisor._run_state,
            ),
            recent_events=[],
            recent_workflow_events=[],
        )
        task = asyncio.create_task(
            supervisor._pause_for_oracle_failure(
                agent_label="expert",
                agent_id="expert",
                prompt="Assess the current run.",
                detail="Oracle query timed out after 3600s.",
            )
        )
        supervisor._run_task = task
        await asyncio.sleep(0)
        assert supervisor._run_state is not None
        assert supervisor._run_state.status == "paused"
        assert supervisor._run_state.phase == "paused"
        assert supervisor._run_state.last_error is not None
        assert "Oracle expert failed and the run is paused" in supervisor._run_state.last_error

        await supervisor.resume_run()
        await task
        supervisor._run_task = None

    asyncio.run(exercise())

    assert supervisor._run_state is not None
    assert supervisor._run_state.status == "running"


def test_supervisor_restores_resumable_oracle_pause_from_disk(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "20260401T120000Z-resume123"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    noted_at = datetime(2026, 4, 1, 12, 30, tzinfo=UTC)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=True),
            thread=ThreadState(id="thread-1", status="idle"),
            transcript=[
                TranscriptItem(
                    item_id="assistant-1",
                    role="assistant",
                    text="Investigated the repo.",
                    status="completed",
                    turn_id="turn-1",
                )
            ],
            workflow_run=WorkflowRunState(
                id="20260401T120000Z-resume123",
                run_name="oracle resume",
                workflow_id="plan_execute_judge",
                target_dir=str(tmp_path / "repo"),
                goal="Keep the run resumable.",
                status="paused",
                phase="paused",
                codex_agent_id="builder",
                expert_agent_id="expert",
                judge_agent_id="judge",
                started_at=started_at,
                updated_at=noted_at,
                current_loop=2,
                max_loops=4,
                judge_calls=1,
                max_judge_calls=4,
                max_runtime_minutes=45,
                last_codex_output="Codex output",
                oracle_resume_checkpoint=OracleResumeCheckpoint(
                    agent_label="expert",
                    agent_id="expert",
                    thread_id="thread-1",
                    loop_index=2,
                    prompt="Assess the current run.",
                    detail="Oracle timed out.",
                    noted_at=noted_at,
                ),
                last_error="Oracle expert failed and the run is paused: Oracle timed out.",
            ),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    (run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME).write_text(
        snapshot.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (run_dir / "workflow-events.jsonl").write_text(
        WorkflowEventRecord(
            sequence=1,
            event_id="event-1",
            recorded_at=noted_at,
            kind="oracle_blocked",
            message="Oracle expert failed; run paused until operator resume.",
            payload={"agent": "expert"},
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    restored = supervisor.snapshot()

    assert restored.state.workflow_run is not None
    assert restored.state.workflow_run.oracle_resume_checkpoint is not None
    assert restored.state.workflow_run.oracle_resume_checkpoint.thread_id == "thread-1"
    assert restored.state.thread is not None
    assert restored.state.thread.id == "thread-1"
    assert restored.state.transcript[0].text == "Investigated the repo."


def test_supervisor_resume_run_restarts_paused_oracle_run_from_manifest(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "20260401T120000Z-resume124"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    noted_at = datetime(2026, 4, 1, 12, 30, tzinfo=UTC)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=False),
            thread=ThreadState(id="thread-9", status="idle"),
            transcript=[
                TranscriptItem(
                    item_id="assistant-1",
                    role="assistant",
                    text="Investigated the repo.",
                    status="completed",
                    turn_id="turn-1",
                )
            ],
            workflow_run=WorkflowRunState(
                id="20260401T120000Z-resume124",
                run_name="oracle resume",
                workflow_id="plan_execute_judge",
                target_dir=str(tmp_path / "repo"),
                goal="Keep the run resumable.",
                status="paused",
                phase="paused",
                codex_agent_id="builder",
                expert_agent_id="expert",
                judge_agent_id="judge",
                started_at=started_at,
                updated_at=noted_at,
                current_loop=2,
                max_loops=4,
                judge_calls=1,
                max_judge_calls=4,
                max_runtime_minutes=45,
                last_codex_output="Codex output",
                oracle_resume_checkpoint=OracleResumeCheckpoint(
                    agent_label="expert",
                    agent_id="expert",
                    thread_id="thread-9",
                    loop_index=2,
                    prompt="Assess the current run.",
                    detail="Oracle timed out.",
                    noted_at=noted_at,
                ),
                last_error="Oracle expert failed and the run is paused: Oracle timed out.",
            ),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    (run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME).write_text(
        snapshot.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (run_dir / WorkflowSupervisor.RUN_MANIFEST_FILENAME).write_text(
        """{
  "runId": "20260401T120000Z-resume124",
  "workflow": {
    "id": "plan_execute_judge",
    "kind": "linear_loop",
    "executor_agent": "builder",
    "expert_agent": "expert",
    "judge_agent": "judge",
    "execute_prompt_template": "Execute {goal}",
    "expert_prompt_template": "Expert {judge_bundle}",
    "judge_prompt_template": "Judge {judge_bundle}",
    "max_loops": 4,
    "max_runtime_minutes": 45,
    "max_judge_calls": 4
  },
  "agents": {
    "codex": {
      "id": "builder",
      "provider": "codex",
      "role": "builder",
      "model": "gpt-5.3-codex-spark"
    },
    "expert": {
      "id": "expert",
      "provider": "oracle",
      "role": "expert",
      "timeout_seconds": 3600
    },
    "judge": {
      "id": "judge",
      "provider": "codex",
      "role": "judge",
      "model": "gpt-5.4"
    }
  }
}
""",
        encoding="utf-8",
    )

    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    recorded: dict[str, object] = {}

    async def fake_start_bridge(
        target_dir: Path,
        codex_agent: object,
        *,
        resume_thread_id: str | None = None,
        transcript_seed: list[TranscriptItem] | None = None,
    ) -> None:
        recorded["target_dir"] = str(target_dir)
        recorded["resume_thread_id"] = resume_thread_id
        recorded["transcript_seed_count"] = len(transcript_seed or [])
        recorded["codex_role"] = getattr(codex_agent, "role")

    async def fake_resume_from_oracle_checkpoint(context: LoadedRunContext) -> None:
        recorded["workflow_id"] = context.workflow.id
        recorded["expert_agent_id"] = context.expert_agent.id if context.expert_agent else None

    cast(Any, supervisor)._start_bridge = fake_start_bridge
    cast(Any, supervisor)._resume_from_oracle_checkpoint = fake_resume_from_oracle_checkpoint

    async def exercise() -> DashboardSnapshot:
        resumed = await supervisor.resume_run()
        if supervisor._run_task is not None:
            await supervisor._run_task
        return resumed

    resumed = asyncio.run(exercise())

    assert resumed.state.workflow_run is not None
    assert resumed.state.workflow_run.status == "running"
    assert recorded == {
        "target_dir": str(tmp_path / "repo"),
        "resume_thread_id": "thread-9",
        "transcript_seed_count": 1,
        "codex_role": "builder",
        "workflow_id": "plan_execute_judge",
        "expert_agent_id": "expert",
    }


def test_supervisor_start_run_uses_managed_worktree(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.builder]
provider = "codex"
role = "builder"

[agents.judge]
provider = "codex"
role = "judge"

[workflows.plan_execute_judge]
executor_agent = "builder"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    source_repo_root = tmp_path.parent / f"{tmp_path.name}-repo"
    _init_git_repo(source_repo_root)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    recorded: dict[str, str] = {}

    async def successful_start_bridge(target_dir: Path, codex_agent: object, **_: object) -> None:
        recorded["execution_dir"] = str(target_dir)

    async def fake_execute_run(*args: object, **kwargs: object) -> None:
        await supervisor._finish_run(
            status="stopped",
            phase="stopped",
            note="test cleanup",
        )

    async def exercise() -> DashboardSnapshot:
        cast(Any, supervisor)._start_bridge = successful_start_bridge
        cast(Any, supervisor)._execute_run = fake_execute_run
        snapshot = await supervisor.start_run(
            WorkflowRunRequest(
                workflow_id="plan_execute_judge",
                target_dir=str(source_repo_root),
                prompt="test managed worktree",
            )
        )
        await asyncio.sleep(0)
        return snapshot

    snapshot = asyncio.run(exercise())

    assert snapshot.state.workflow_run is not None
    run = snapshot.state.workflow_run
    assert run.target_dir == str(source_repo_root)
    assert run.execution_dir is not None
    assert run.execution_dir == recorded["execution_dir"]
    assert run.execution_dir.startswith(str(tmp_path / ".shmocky" / "worktrees"))
    assert run.workspace_strategy == "git_worktree"
    assert run.worktree_branch == f"shmocky/{run.id}"
    assert run.worktree_base_commit
    assert Path(run.execution_dir).exists()

    manifest_payload = json.loads(
        (tmp_path / ".shmocky" / "runs" / run.id / WorkflowSupervisor.RUN_MANIFEST_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert manifest_payload["workspace"]["sourceRepoRoot"] == str(source_repo_root)
    assert manifest_payload["workspace"]["executionDir"] == run.execution_dir
    assert manifest_payload["workspace"]["workspaceStrategy"] == "git_worktree"


def test_supervisor_rolls_back_failed_run_start(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.builder]
provider = "codex"
role = "builder"

[agents.judge]
provider = "codex"
role = "judge"

[workflows.plan_execute_judge]
executor_agent = "builder"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    target_dir = tmp_path.parent / f"{tmp_path.name}-target-repo"
    _init_git_repo(target_dir)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    async def failing_start_bridge(target_dir: Path, codex_agent: object, **_: object) -> None:
        raise BridgeError("initialize failed")

    async def successful_start_bridge(target_dir: Path, codex_agent: object, **_: object) -> None:
        return None

    async def fake_execute_run(*args: object, **kwargs: object) -> None:
        await supervisor._finish_run(
            status="stopped",
            phase="stopped",
            note="test cleanup",
        )

    async def exercise() -> DashboardSnapshot:
        cast(Any, supervisor)._start_bridge = failing_start_bridge

        with pytest.raises(BridgeError, match="initialize failed"):
            await supervisor.start_run(
                WorkflowRunRequest(
                    workflow_id="plan_execute_judge",
                    target_dir=str(target_dir),
                    prompt="test startup rollback",
                )
            )

        assert supervisor._run_state is None
        assert supervisor._resources is None
        assert supervisor._archived_snapshot is None
        assert list(supervisor._recent_workflow_events) == []
        assert not any((tmp_path / ".shmocky" / "worktrees").glob("*"))

        cast(Any, supervisor)._start_bridge = successful_start_bridge
        cast(Any, supervisor)._execute_run = fake_execute_run

        snapshot = await supervisor.start_run(
            WorkflowRunRequest(
                workflow_id="plan_execute_judge",
                target_dir=str(target_dir),
                prompt="test startup retry",
            )
        )
        await asyncio.sleep(0)
        return snapshot

    snapshot = asyncio.run(exercise())

    assert snapshot.state.workflow_run is not None
    assert snapshot.state.workflow_run.workflow_id == "plan_execute_judge"
    assert snapshot.state.workflow_run.execution_dir is not None
    assert supervisor._run_state is not None
    assert supervisor._run_state.status == "stopped"
