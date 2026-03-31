from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import AgentDefinition, WorkflowCatalogResponse, WorkflowDefinition
from .settings import AppSettings

DEFAULT_PLAN_PROMPT_TEMPLATE = """You are preparing the first execution plan for this workflow run.

Goal:
{goal}

Produce a concrete implementation plan for the repository in front of you. Keep it actionable and
focused on the next small slice that should actually be executed now."""

DEFAULT_EXECUTE_PROMPT_TEMPLATE = """Execute the next slice of work for this workflow run.

Goal:
{goal}

Plan:
{plan}

Carry the work forward in the repository. If you are blocked, say exactly what blocked you."""

DEFAULT_JUDGE_PROMPT_TEMPLATE = """You are the workflow judge. Review the run context below and
return strict JSON with this schema only:

{
  "decision": "continue" | "complete" | "fail",
  "summary": "short operator-facing summary",
  "next_prompt": "required when decision is continue",
  "completion_note": "optional when decision is complete",
  "failure_reason": "optional when decision is fail"
}

Rules:
- Return JSON only.
- Choose "continue" only when a single next Codex prompt would materially advance the goal.
- Choose "complete" only when the goal appears satisfied.
- Choose "fail" only when the run is blocked or the approach is no longer viable.

Context:
{judge_bundle}"""


class WorkflowConfigError(RuntimeError):
    pass


class WorkflowConfigLoader:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def path(self) -> Path:
        return self._settings.workflow_config_path

    def load(self) -> WorkflowCatalogResponse:
        path = self.path
        if not path.exists():
            raise WorkflowConfigError(f"Workflow config file not found: {path}")

        try:
            with path.open("rb") as handle:
                payload = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise WorkflowConfigError(f"Invalid TOML in {path}: {exc}") from exc

        agents = self._load_agents(payload.get("agents"))
        workflows = self._load_workflows(payload.get("workflows"), agents)
        return WorkflowCatalogResponse(
            config_path=str(path),
            loaded=True,
            agents=agents,
            workflows=workflows,
        )

    def _load_agents(self, payload: object) -> list[AgentDefinition]:
        if not isinstance(payload, dict):
            raise WorkflowConfigError("Workflow config must define an [agents] table.")
        agents: list[AgentDefinition] = []
        for agent_id, raw_agent in payload.items():
            if not isinstance(agent_id, str) or not isinstance(raw_agent, dict):
                raise WorkflowConfigError("Each agent entry must be a TOML table.")
            normalized_agent = dict(raw_agent)
            try:
                agent = AgentDefinition.model_validate({"id": agent_id, **normalized_agent})
            except ValidationError as exc:
                raise WorkflowConfigError(f"Invalid agent '{agent_id}': {exc}") from exc
            self._validate_agent(agent, normalized_agent)
            agents.append(agent)
        if not agents:
            raise WorkflowConfigError("Workflow config must define at least one agent.")
        return sorted(agents, key=lambda agent: agent.id)

    def _load_workflows(
        self,
        payload: object,
        agents: list[AgentDefinition],
    ) -> list[WorkflowDefinition]:
        if not isinstance(payload, dict):
            raise WorkflowConfigError("Workflow config must define a [workflows] table.")
        agent_by_id = {agent.id: agent for agent in agents}
        workflows: list[WorkflowDefinition] = []
        for workflow_id, raw_workflow in payload.items():
            if not isinstance(workflow_id, str) or not isinstance(raw_workflow, dict):
                raise WorkflowConfigError("Each workflow entry must be a TOML table.")
            workflow_payload = {
                "id": workflow_id,
                "plan_prompt_template": DEFAULT_PLAN_PROMPT_TEMPLATE,
                "execute_prompt_template": DEFAULT_EXECUTE_PROMPT_TEMPLATE,
                "judge_prompt_template": DEFAULT_JUDGE_PROMPT_TEMPLATE,
                **raw_workflow,
            }
            try:
                workflow = WorkflowDefinition.model_validate(workflow_payload)
            except ValidationError as exc:
                raise WorkflowConfigError(f"Invalid workflow '{workflow_id}': {exc}") from exc
            for ref_name in (
                workflow.planner_agent,
                workflow.executor_agent,
                workflow.judge_agent,
            ):
                if ref_name not in agent_by_id:
                    raise WorkflowConfigError(
                        f"Workflow '{workflow_id}' references unknown agent '{ref_name}'."
                    )
            planner = agent_by_id[workflow.planner_agent]
            executor = agent_by_id[workflow.executor_agent]
            judge = agent_by_id[workflow.judge_agent]
            if planner.provider != "codex" or executor.provider != "codex":
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use Codex agents for planner and executor."
                )
            if workflow.planner_agent != workflow.executor_agent:
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use the same Codex agent for planner and executor in v1."
                )
            if judge.provider != "oracle":
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use an Oracle agent for judging."
                )
            workflows.append(workflow)
        if not workflows:
            raise WorkflowConfigError("Workflow config must define at least one workflow.")
        return sorted(workflows, key=lambda workflow: workflow.id)

    @staticmethod
    def _validate_agent(agent: AgentDefinition, raw_agent: dict[str, Any]) -> None:
        codex_keys = {
            "provider",
            "role",
            "startup_prompt",
            "description",
            "model",
            "model_provider",
            "reasoning_effort",
            "approval_policy",
            "sandbox_mode",
            "web_access",
            "service_tier",
        }
        oracle_keys = {
            "provider",
            "role",
            "startup_prompt",
            "description",
            "remote_host",
            "model_strategy",
            "timeout_seconds",
        }
        allowed_keys = codex_keys if agent.provider == "codex" else oracle_keys
        unknown_keys = sorted(set(raw_agent) - allowed_keys)
        if unknown_keys:
            raise WorkflowConfigError(
                f"Agent '{agent.id}' uses unsupported options for provider '{agent.provider}': "
                + ", ".join(unknown_keys)
            )
