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


class StreamEnvelope(BaseModel):
    type: Literal["event", "state"]
    state: DashboardState
    event: RawEventRecord | None = None


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
