from __future__ import annotations

from pathlib import Path

from shmocky.models import ConnectionState, DashboardSnapshot, DashboardState
from shmocky.notebook_projection import NotebookProjection
from shmocky.notebook_store import NotebookPageStore


def test_notebook_projection_appends_page_and_renders_markdown(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "run-1"
    run_dir.mkdir(parents=True)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=False),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    projection = NotebookProjection(
        store=NotebookPageStore(run_dir / "notebook-pages.jsonl"),
        notebook_dir=run_dir / "notebook",
        snapshot_path=run_dir / "dashboard-snapshot.json",
    )

    async def exercise() -> None:
        await projection.append_page(
            run_id="run-1",
            kind="run_started",
            title="Run started: benchmark loop",
            summary="Started the benchmark optimization loop.",
            snapshot=snapshot,
            why="The operator requested a supervised optimization run.",
            outcomes=["Workflow: plan_execute_judge"],
            tags=["run", "benchmark"],
        )

    import asyncio

    asyncio.run(exercise())

    pages = projection.list_pages().pages
    assert len(pages) == 1
    assert pages[0].kind == "run_started"
    assert pages[0].source_ref.snapshot_path == str(run_dir / "dashboard-snapshot.json")

    view = projection.load_page(pages[0].page_id)
    assert view is not None
    assert "# Run started: benchmark loop" in view.markdown
    assert "## Summary" in view.markdown
    assert Path(view.markdown_path or "").exists()
