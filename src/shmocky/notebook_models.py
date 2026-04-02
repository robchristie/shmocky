from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

type NotebookPageKind = Literal[
    "run_started",
    "worktree_prepared",
    "plan_adopted",
    "execution_slice",
    "steering_applied",
    "experiment_result",
    "judge_decision",
    "oracle_blocked",
    "run_resumed",
    "run_finished",
    "amendment",
]


class NotebookSourceRef(BaseModel):
    raw_event_seq_start: int | None = None
    raw_event_seq_end: int | None = None
    workflow_event_seq_start: int | None = None
    workflow_event_seq_end: int | None = None
    transcript_item_ids: list[str] = Field(default_factory=list)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    snapshot_path: str | None = None


class NotebookPageRecord(BaseModel):
    sequence: int
    page_id: str
    run_id: str
    recorded_at: datetime
    kind: NotebookPageKind
    title: str
    summary: str = Field(min_length=1, max_length=8_000)
    why: str | None = Field(default=None, max_length=8_000)
    changes: list[str] = Field(default_factory=list, max_length=32)
    issues: list[str] = Field(default_factory=list, max_length=32)
    outcomes: list[str] = Field(default_factory=list, max_length=32)
    next_steps: list[str] = Field(default_factory=list, max_length=32)
    tags: list[str] = Field(default_factory=list, max_length=32)
    source_ref: NotebookSourceRef = Field(default_factory=NotebookSourceRef)
    amends_page_id: str | None = None


class NotebookPageListResponse(BaseModel):
    pages: list[NotebookPageRecord] = Field(default_factory=list)


class NotebookPageView(BaseModel):
    record: NotebookPageRecord
    markdown: str
    markdown_path: str | None = None
