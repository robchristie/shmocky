from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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
