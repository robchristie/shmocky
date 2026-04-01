from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import AgentDefinition, WorkflowCatalogResponse, WorkflowDefinition
from .settings import AppSettings

DEFAULT_EXECUTE_PROMPT_TEMPLATE = """<builder_task>
Goal:
{goal}

Carry the repository forward to completion from the current workspace state.

Constraints:
- Work directly in the repo instead of stopping at an up-front plan.
- Use tools as needed until the task is actually complete or a real blocker is proven.
- Verify meaningful changes before concluding.
</builder_task>"""

DEFAULT_EXPERT_PROMPT_TEMPLATE = """You are the workflow expert advisor. Review the run context below
and return plain text only.

Your job:
- assess the current run state and the latest Codex work
- identify the most important risks, missed opportunities, or next experiments
- suggest what the judge should consider before deciding whether to continue

Keep the response concise but specific. Free text is fine.

Context:
{judge_bundle}"""

DEFAULT_JUDGE_PROMPT_TEMPLATE = """<judge_task>
Review the run context below and produce a strict decision object.

Decision policy:
- `continue` only when one concrete next builder prompt would materially advance the goal
- `complete` only when the goal appears satisfied and the evidence supports stopping
- `fail` only when the run is blocked, unsafe, or no longer viable

Requirements:
- Ground the decision in the supplied repo and run evidence
- Keep `summary` short and operator-facing
- If you choose `continue`, provide a complete `next_prompt`
- Do not emit prose outside the constrained response
</judge_task>

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
                "execute_prompt_template": DEFAULT_EXECUTE_PROMPT_TEMPLATE,
                "expert_prompt_template": DEFAULT_EXPERT_PROMPT_TEMPLATE,
                "judge_prompt_template": DEFAULT_JUDGE_PROMPT_TEMPLATE,
                **raw_workflow,
            }
            try:
                workflow = WorkflowDefinition.model_validate(workflow_payload)
            except ValidationError as exc:
                raise WorkflowConfigError(f"Invalid workflow '{workflow_id}': {exc}") from exc
            for ref_name in (workflow.executor_agent, workflow.judge_agent):
                if ref_name not in agent_by_id:
                    raise WorkflowConfigError(
                        f"Workflow '{workflow_id}' references unknown agent '{ref_name}'."
                    )
            if workflow.expert_agent is not None and workflow.expert_agent not in agent_by_id:
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' references unknown agent '{workflow.expert_agent}'."
                )
            executor = agent_by_id[workflow.executor_agent]
            judge = agent_by_id[workflow.judge_agent]
            expert = (
                agent_by_id[workflow.expert_agent]
                if workflow.expert_agent is not None
                else None
            )
            if executor.provider != "codex":
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use a Codex agent for execution."
                )
            if judge.provider != "codex":
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use a Codex agent for judging."
                )
            if expert is not None and expert.provider not in {"oracle", "codex"}:
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' uses unsupported expert provider '{expert.provider}'."
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
            "chatgpt_url",
            "model_strategy",
            "timeout_seconds",
            "prompt_char_limit",
        }
        allowed_keys = codex_keys if agent.provider == "codex" else oracle_keys
        unknown_keys = sorted(set(raw_agent) - allowed_keys)
        if unknown_keys:
            raise WorkflowConfigError(
                f"Agent '{agent.id}' uses unsupported options for provider '{agent.provider}': "
                + ", ".join(unknown_keys)
            )
