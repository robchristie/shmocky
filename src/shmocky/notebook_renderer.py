from __future__ import annotations

import re

from .notebook_models import NotebookPageRecord


def markdown_filename(record: NotebookPageRecord) -> str:
    slug = _slugify(record.title) or record.kind.replace("_", "-")
    return f"{record.sequence:04d}-{slug}.md"


def render_notebook_page(record: NotebookPageRecord) -> str:
    lines: list[str] = [
        f"# {record.title}",
        "",
        f"- Page ID: `{record.page_id}`",
        f"- Run ID: `{record.run_id}`",
        f"- Kind: `{record.kind}`",
        f"- Recorded At: `{record.recorded_at.isoformat()}`",
        "",
        "## Summary",
        "",
        record.summary,
        "",
    ]
    if record.why:
        lines.extend(["## Why", "", record.why, ""])
    _append_list_section(lines, "Changes", record.changes)
    _append_list_section(lines, "Issues", record.issues)
    _append_list_section(lines, "Outcomes", record.outcomes)
    _append_list_section(lines, "Next Steps", record.next_steps)
    if record.tags:
        lines.extend(["## Tags", "", ", ".join(f"`{tag}`" for tag in record.tags), ""])
    if record.amends_page_id:
        lines.extend(["## Amendment", "", f"Amends page `{record.amends_page_id}`.", ""])
    lines.extend(_render_source_refs(record))
    return "\n".join(lines).rstrip() + "\n"


def _append_list_section(lines: list[str], heading: str, values: list[str]) -> None:
    if not values:
        return
    lines.extend([f"## {heading}", ""])
    lines.extend(f"- {value}" for value in values)
    lines.append("")


def _render_source_refs(record: NotebookPageRecord) -> list[str]:
    source = record.source_ref
    lines = ["## Source Refs", ""]
    if source.raw_event_seq_start is not None or source.raw_event_seq_end is not None:
        lines.append(
            f"- Raw events: `{source.raw_event_seq_start or '?'}..{source.raw_event_seq_end or '?'}`"
        )
    if source.workflow_event_seq_start is not None or source.workflow_event_seq_end is not None:
        lines.append(
            "- Workflow events: "
            f"`{source.workflow_event_seq_start or '?'}..{source.workflow_event_seq_end or '?'}`"
        )
    if source.transcript_item_ids:
        lines.append(
            "- Transcript items: "
            + ", ".join(f"`{item_id}`" for item_id in source.transcript_item_ids)
        )
    if source.snapshot_path:
        lines.append(f"- Snapshot: `{source.snapshot_path}`")
    if source.artifact_paths:
        lines.append("- Artifacts:")
        lines.extend(f"  - `{name}`: `{path}`" for name, path in source.artifact_paths.items())
    if len(lines) == 2:
        lines.append("- None recorded.")
    lines.append("")
    return lines


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60]
