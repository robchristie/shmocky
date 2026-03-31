from __future__ import annotations

from pathlib import Path

import pytest

from shmocky.settings import AppSettings
from shmocky.workflow_config import WorkflowConfigError, WorkflowConfigLoader


def test_workflow_config_loader_reads_repo_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"
model = "gpt-5.4"
reasoning_effort = "high"
approval_policy = "never"
sandbox_mode = "workspace-write"
web_access = "live"

[agents.judge]
provider = "oracle"
role = "judge"
model_strategy = "current"
prompt_char_limit = 64000

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
judge_agent = "judge"
max_loops = 3
max_runtime_minutes = 20
max_judge_calls = 3
""".strip(),
        encoding="utf-8",
    )
    settings = AppSettings(
        workspace_root=tmp_path,
        workflow_config_path=config_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    catalog = WorkflowConfigLoader(settings).load()

    assert catalog.loaded is True
    assert [agent.id for agent in catalog.agents] == ["engineer", "judge"]
    assert [workflow.id for workflow in catalog.workflows] == ["plan_execute_judge"]
    assert catalog.agents[1].prompt_char_limit == 64_000
    assert catalog.workflows[0].plan_prompt_template
    assert catalog.workflows[0].judge_prompt_template


def test_workflow_config_loader_rejects_split_codex_agents(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.planner]
provider = "codex"
role = "planner"

[agents.executor]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "planner"
executor_agent = "executor"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    settings = AppSettings(
        workspace_root=tmp_path,
        workflow_config_path=config_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    with pytest.raises(WorkflowConfigError):
        WorkflowConfigLoader(settings).load()
