from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import subprocess
from pathlib import Path

import pytest

from shmocky.models import (
    ConnectionState,
    DashboardSnapshot,
    DashboardState,
    WorkflowRunState,
)
from shmocky.settings import AppSettings
from shmocky.supervisor import WorkflowSupervisor, WorkflowSupervisorError


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
        plan="plan",
        last_output="output",
        judge_bundle="X" * (prompt_limit + 5_000),
    )

    assert len(prompt) <= prompt_limit
    assert prompt.startswith("Context:\n")


def test_supervisor_rejects_target_inside_workspace_root(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
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


def test_supervisor_rejects_target_nested_in_other_repo(tmp_path: Path) -> None:
    config_path = tmp_path / "config-home" / "shmocky.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
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
        match="nested inside another git repository",
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
                codex_agent_id="engineer",
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
        codex_agent_id="engineer",
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
        codex_agent_id="engineer",
        expert_agent_id="expert",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
    )

    async def exercise() -> None:
        task = asyncio.create_task(
            supervisor._pause_for_oracle_failure(
                agent_label="expert",
                detail="Oracle query timed out after 3600s.",
            )
        )
        await asyncio.sleep(0)
        assert supervisor._run_state is not None
        assert supervisor._run_state.status == "paused"
        assert supervisor._run_state.phase == "paused"
        assert supervisor._run_state.last_error is not None
        assert "Oracle expert failed and the run is paused" in supervisor._run_state.last_error

        await supervisor.resume_run()
        await task

    asyncio.run(exercise())

    assert supervisor._run_state is not None
    assert supervisor._run_state.status == "running"
