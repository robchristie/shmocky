from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .notebook_models import NotebookPageKind, NotebookPageRecord, NotebookSourceRef


class NotebookPageStore:
    """Append-only JSONL store for canonical notebook page records."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._sequence = _load_last_sequence(path)

    async def append(
        self,
        *,
        run_id: str,
        kind: NotebookPageKind,
        title: str,
        summary: str,
        why: str | None = None,
        changes: list[str] | None = None,
        issues: list[str] | None = None,
        outcomes: list[str] | None = None,
        next_steps: list[str] | None = None,
        tags: list[str] | None = None,
        source_ref: NotebookSourceRef | None = None,
        amends_page_id: str | None = None,
    ) -> NotebookPageRecord:
        async with self._lock:
            self._sequence += 1
            record = NotebookPageRecord(
                sequence=self._sequence,
                page_id=str(uuid4()),
                run_id=run_id,
                recorded_at=datetime.now(UTC),
                kind=kind,
                title=title,
                summary=summary,
                why=why,
                changes=changes or [],
                issues=issues or [],
                outcomes=outcomes or [],
                next_steps=next_steps or [],
                tags=tags or [],
                source_ref=source_ref or NotebookSourceRef(),
                amends_page_id=amends_page_id,
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")
            return record

    def load_all(self) -> list[NotebookPageRecord]:
        if not self.path.exists():
            return []
        records: list[NotebookPageRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                records.append(NotebookPageRecord.model_validate_json(line))
        return records

    def load_page(self, page_id: str) -> NotebookPageRecord | None:
        for record in self.load_all():
            if record.page_id == page_id:
                return record
        return None

    def last_record(self) -> NotebookPageRecord | None:
        records = self.load_all()
        return records[-1] if records else None


def _load_last_sequence(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        last_line = ""
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last_line = line
        if not last_line:
            return 0
        payload = json.loads(last_line)
        sequence = payload.get("sequence")
        return sequence if isinstance(sequence, int) and sequence >= 0 else 0
    except Exception:
        return 0
