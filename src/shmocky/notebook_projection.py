from __future__ import annotations

from pathlib import Path

from .models import DashboardSnapshot
from .notebook_models import (
    NotebookPageKind,
    NotebookPageListResponse,
    NotebookPageRecord,
    NotebookPageView,
    NotebookSourceRef,
)
from .notebook_renderer import markdown_filename, render_notebook_page
from .notebook_store import NotebookPageStore


class NotebookProjection:
    def __init__(
        self,
        *,
        store: NotebookPageStore,
        notebook_dir: Path,
        snapshot_path: Path,
    ) -> None:
        self._store = store
        self._notebook_dir = notebook_dir
        self._snapshot_path = snapshot_path
        self._notebook_dir.mkdir(parents=True, exist_ok=True)
        last_record = self._store.last_record()
        self._last_raw_event_seq_end = (
            last_record.source_ref.raw_event_seq_end if last_record is not None else None
        )
        self._last_workflow_event_seq_end = (
            last_record.source_ref.workflow_event_seq_end if last_record is not None else None
        )

    async def append_page(
        self,
        *,
        run_id: str,
        kind: NotebookPageKind,
        title: str,
        summary: str,
        snapshot: DashboardSnapshot,
        why: str | None = None,
        changes: list[str] | None = None,
        issues: list[str] | None = None,
        outcomes: list[str] | None = None,
        next_steps: list[str] | None = None,
        tags: list[str] | None = None,
        transcript_item_ids: list[str] | None = None,
        artifact_paths: dict[str, str] | None = None,
        amends_page_id: str | None = None,
    ) -> NotebookPageRecord:
        source_ref = self._build_source_ref(
            snapshot=snapshot,
            transcript_item_ids=transcript_item_ids or [],
            artifact_paths=artifact_paths or {},
        )
        record = await self._store.append(
            run_id=run_id,
            kind=kind,
            title=title,
            summary=summary,
            why=why,
            changes=changes,
            issues=issues,
            outcomes=outcomes,
            next_steps=next_steps,
            tags=tags,
            source_ref=source_ref,
            amends_page_id=amends_page_id,
        )
        self._write_markdown(record)
        self._last_raw_event_seq_end = record.source_ref.raw_event_seq_end
        self._last_workflow_event_seq_end = record.source_ref.workflow_event_seq_end
        return record

    def list_pages(self) -> NotebookPageListResponse:
        return NotebookPageListResponse(pages=self._store.load_all())

    def load_page(self, page_id: str) -> NotebookPageView | None:
        record = self._store.load_page(page_id)
        if record is None:
            return None
        markdown_path = self._markdown_path(record)
        if markdown_path.exists():
            markdown = markdown_path.read_text(encoding="utf-8")
        else:
            markdown = self._write_markdown(record)
        return NotebookPageView(
            record=record,
            markdown=markdown,
            markdown_path=str(markdown_path),
        )

    def _build_source_ref(
        self,
        *,
        snapshot: DashboardSnapshot,
        transcript_item_ids: list[str],
        artifact_paths: dict[str, str],
    ) -> NotebookSourceRef:
        raw_end = snapshot.recent_events[-1].sequence if snapshot.recent_events else None
        workflow_end = (
            snapshot.recent_workflow_events[-1].sequence
            if snapshot.recent_workflow_events
            else None
        )
        raw_start = self._range_start(
            previous_end=self._last_raw_event_seq_end,
            current_end=raw_end,
            fallback_start=(
                snapshot.recent_events[0].sequence if snapshot.recent_events else None
            ),
        )
        workflow_start = self._range_start(
            previous_end=self._last_workflow_event_seq_end,
            current_end=workflow_end,
            fallback_start=(
                snapshot.recent_workflow_events[0].sequence
                if snapshot.recent_workflow_events
                else None
            ),
        )
        return NotebookSourceRef(
            raw_event_seq_start=raw_start,
            raw_event_seq_end=raw_end,
            workflow_event_seq_start=workflow_start,
            workflow_event_seq_end=workflow_end,
            transcript_item_ids=transcript_item_ids,
            artifact_paths=artifact_paths,
            snapshot_path=str(self._snapshot_path),
        )

    @staticmethod
    def _range_start(
        *,
        previous_end: int | None,
        current_end: int | None,
        fallback_start: int | None,
    ) -> int | None:
        if current_end is None:
            return None
        if previous_end is None:
            return fallback_start or current_end
        next_expected = previous_end + 1
        if next_expected <= current_end:
            return next_expected
        return current_end

    def _write_markdown(self, record: NotebookPageRecord) -> str:
        markdown = render_notebook_page(record)
        markdown_path = self._markdown_path(record)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        return markdown

    def _markdown_path(self, record: NotebookPageRecord) -> Path:
        return self._notebook_dir / markdown_filename(record)
