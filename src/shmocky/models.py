from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

type EventDirection = Literal["outbound", "inbound", "internal"]
type EventChannel = Literal["rpc", "stderr", "lifecycle"]
type EventMessageType = Literal[
    "request",
    "response",
    "notification",
    "server_request",
    "stderr",
    "lifecycle",
    "unknown",
]
type ApprovalPolicy = Literal["untrusted", "on-failure", "on-request", "never"]
type SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]
type ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
type WebAccessMode = Literal["disabled", "cached", "live"]
type AgentProvider = Literal["codex", "oracle"]
type WorkflowKind = Literal["linear_loop"]
type WorkflowDecisionType = Literal["continue", "complete", "fail"]
type WorkflowRunStatus = Literal[
    "idle",
    "starting",
    "running",
    "paused",
    "completed",
    "failed",
    "stopped",
]
type WorkflowPhase = Literal[
    "idle",
    "planning",
    "executing",
    "advising",
    "judging",
    "paused",
    "completed",
    "failed",
    "stopped",
]


class ConnectionState(BaseModel):
    backend_online: bool = True
    codex_connected: bool = False
    initialized: bool = False
    app_server_pid: int | None = None
    app_server_user_agent: str | None = None
    codex_home: str | None = None
    platform_family: str | None = None
    platform_os: str | None = None
    last_error: str | None = None


class ThreadState(BaseModel):
    id: str
    status: str = "idle"
    cwd: str | None = None
    model: str | None = None
    model_provider: str | None = None
    approval_policy: str | None = None
    sandbox_mode: str | None = None
    reasoning_effort: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class TurnState(BaseModel):
    id: str
    status: str = "pending"
    last_event_at: datetime | None = None
    error: str | None = None


class TranscriptItem(BaseModel):
    item_id: str
    role: Literal["user", "assistant"]
    text: str = ""
    phase: str | None = None
    status: Literal["streaming", "completed"] = "completed"
    turn_id: str | None = None


class PendingServerRequest(BaseModel):
    request_id: str
    method: str
    noted_at: datetime


class DashboardState(BaseModel):
    workspace_root: str
    event_log_path: str
    connection: ConnectionState
    thread: ThreadState | None = None
    turn: TurnState | None = None
    transcript: list[TranscriptItem] = Field(default_factory=list)
    mcp_servers: dict[str, str] = Field(default_factory=dict)
    rate_limits: dict[str, Any] | None = None
    pending_server_request: PendingServerRequest | None = None
    workflow_run: "WorkflowRunState | None" = None


class RawEventRecord(BaseModel):
    sequence: int
    event_id: str
    recorded_at: datetime
    direction: EventDirection
    channel: EventChannel
    message_type: EventMessageType
    method: str | None = None
    payload: Any


class DashboardSnapshot(BaseModel):
    state: DashboardState
    recent_events: list[RawEventRecord] = Field(default_factory=list)
    recent_workflow_events: list["WorkflowEventRecord"] = Field(default_factory=list)


class StreamEnvelope(BaseModel):
    type: Literal["event", "workflow_event", "state"]
    state: DashboardState
    event: RawEventRecord | None = None
    workflow_event: "WorkflowEventRecord | None" = None


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class OracleQueryRequest(BaseModel):
    prompt: str = Field(min_length=1)
    agent_id: str | None = Field(default=None, min_length=1, max_length=200)
    files: list[str] = Field(default_factory=list, max_length=64)


class OracleQueryResponse(BaseModel):
    answer: str
    remote_host: str
    duration_seconds: float
    attached_files: list[str] = Field(default_factory=list)
    stderr: str | None = None


class CodexAgentConfig(BaseModel):
    role: str
    startup_prompt: str | None = None
    description: str | None = None
    model: str | None = None
    model_provider: str | None = None
    reasoning_effort: ReasoningEffort | None = None
    approval_policy: ApprovalPolicy = "never"
    sandbox_mode: SandboxMode = "workspace-write"
    web_access: WebAccessMode = "disabled"
    service_tier: Literal["fast", "flex"] | None = None


class OracleAgentConfig(BaseModel):
    role: str
    startup_prompt: str | None = None
    description: str | None = None
    remote_host: str | None = None
    model_strategy: Literal["current", "ignore"] = "current"
    timeout_seconds: float | None = None
    prompt_char_limit: int | None = Field(default=None, ge=1_000, le=200_000)


class AgentDefinition(BaseModel):
    id: str
    provider: AgentProvider
    role: str
    startup_prompt: str | None = None
    description: str | None = None
    model: str | None = None
    model_provider: str | None = None
    reasoning_effort: ReasoningEffort | None = None
    approval_policy: ApprovalPolicy | None = None
    sandbox_mode: SandboxMode | None = None
    web_access: WebAccessMode | None = None
    service_tier: Literal["fast", "flex"] | None = None
    remote_host: str | None = None
    model_strategy: Literal["current", "ignore"] | None = None
    timeout_seconds: float | None = None
    prompt_char_limit: int | None = Field(default=None, ge=1_000, le=200_000)


class WorkflowDefinition(BaseModel):
    id: str
    kind: WorkflowKind = "linear_loop"
    planner_agent: str
    executor_agent: str
    expert_agent: str | None = None
    judge_agent: str
    plan_prompt_template: str
    execute_prompt_template: str
    expert_prompt_template: str | None = None
    judge_prompt_template: str
    max_loops: int = Field(default=4, ge=1, le=100)
    max_runtime_minutes: int = Field(default=30, ge=1, le=24 * 60)
    max_judge_calls: int = Field(default=4, ge=1, le=100)


class WorkflowCatalogResponse(BaseModel):
    config_path: str
    loaded: bool
    error: str | None = None
    agents: list[AgentDefinition] = Field(default_factory=list)
    workflows: list[WorkflowDefinition] = Field(default_factory=list)


class RunHistoryEntry(BaseModel):
    id: str
    workflow_id: str
    target_dir: str
    status: WorkflowRunStatus
    phase: WorkflowPhase
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    last_judge_decision: WorkflowDecisionType | None = None
    last_judge_summary: str | None = None
    last_error: str | None = None


class RunHistoryResponse(BaseModel):
    runs: list[RunHistoryEntry] = Field(default_factory=list)


class WorkflowRunRequest(BaseModel):
    workflow_id: str = Field(min_length=1, max_length=200)
    target_dir: str = Field(min_length=1, max_length=4_000)
    prompt: str = Field(min_length=1, max_length=20_000)


class WorkflowSteerRequest(BaseModel):
    note: str = Field(min_length=1, max_length=8_000)


class JudgeDecision(BaseModel):
    decision: WorkflowDecisionType
    summary: str = Field(min_length=1, max_length=8_000)
    next_prompt: str | None = Field(default=None, max_length=20_000)
    completion_note: str | None = Field(default=None, max_length=8_000)
    failure_reason: str | None = Field(default=None, max_length=8_000)


class WorkflowRunState(BaseModel):
    id: str
    workflow_id: str
    target_dir: str
    goal: str
    status: WorkflowRunStatus = "starting"
    phase: WorkflowPhase = "idle"
    codex_agent_id: str
    judge_agent_id: str
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    current_loop: int = 0
    max_loops: int
    judge_calls: int = 0
    max_judge_calls: int
    max_runtime_minutes: int
    expert_agent_id: str | None = None
    last_plan: str | None = None
    last_codex_output: str | None = None
    last_expert_assessment: str | None = None
    last_judge_decision: WorkflowDecisionType | None = None
    last_judge_summary: str | None = None
    last_continuation_prompt: str | None = Field(default=None, max_length=20_000)
    last_error: str | None = None
    pause_requested: bool = False
    stop_requested: bool = False
    pending_steering_notes: list[str] = Field(default_factory=list)
    recent_steering_notes: list[str] = Field(default_factory=list)


class WorkflowEventRecord(BaseModel):
    sequence: int
    event_id: str
    recorded_at: datetime
    kind: str
    message: str
    payload: Any = None
