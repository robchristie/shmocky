from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import json
from uuid import uuid4

from .models import (
    EventChannel,
    EventDirection,
    EventMessageType,
    RawEventRecord,
    WorkflowEventRecord,
)


class RawEventStore:
    """Append-only JSONL store for raw app-server traffic."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._sequence = _load_last_sequence(path)

    async def append(
        self,
        *,
        direction: EventDirection,
        channel: EventChannel,
        message_type: EventMessageType,
        payload: object,
        method: str | None = None,
    ) -> RawEventRecord:
        async with self._lock:
            self._sequence += 1
            record = RawEventRecord(
                sequence=self._sequence,
                event_id=str(uuid4()),
                recorded_at=datetime.now(UTC),
                direction=direction,
                channel=channel,
                message_type=message_type,
                method=method,
                payload=payload,
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")
            return record


class WorkflowEventStore:
    """Append-only JSONL store for workflow supervisor events."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._sequence = _load_last_sequence(path)

    async def append(
        self,
        *,
        kind: str,
        message: str,
        payload: object | None = None,
    ) -> WorkflowEventRecord:
        async with self._lock:
            self._sequence += 1
            record = WorkflowEventRecord(
                sequence=self._sequence,
                event_id=str(uuid4()),
                recorded_at=datetime.now(UTC),
                kind=kind,
                message=message,
                payload=payload,
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")
            return record


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
