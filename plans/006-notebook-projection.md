# ExecPlan 006: Notebook Projection

## Summary

Add a notebook as a deterministic projection over append-only run facts rather than a free-form
agent diary. The notebook will store canonical typed page records in JSONL, render human-readable
markdown pages beside them, expose read APIs, and surface the result in the browser as a
high-signal narrative view over the run.

## Scope

In scope:

- add typed notebook page and source-reference models
- add a file-backed append-only notebook page store under each run directory
- render markdown notebook pages from canonical records
- emit notebook pages at high-signal supervisor milestones
- expose notebook list and detail APIs
- add a browser notebook tab for the selected live or historical run

Out of scope:

- LLM-written notebook pages
- notebook search or retrieval APIs
- notebook editing or page mutation
- using notebook pages as authoritative workflow state
- database-backed notebook storage

## Architecture

Backend:

- notebook records live under `.shmocky/runs/<run-id>/notebook-pages.jsonl`
- rendered markdown lives under `.shmocky/runs/<run-id>/notebook/`
- the supervisor owns notebook emission through a small notebook projection helper
- notebook source refs point back to raw event ranges, workflow event ranges, transcript items,
  snapshot paths, and artifact paths when available
- canonical notebook records remain the source of truth; markdown is derived output

Frontend:

- add a `Notebook` operator-rail tab for the selected run
- show notebook pages newest first
- selecting a page shows the rendered markdown plus source refs

## Milestones

1. Notebook storage primitives
   - add notebook models, store, renderer, and projection helper
2. Supervisor integration
   - emit pages for run start, worktree preparation, adopted routing/plan, steering applied,
     execution slice, judge decision, Oracle block, run resume, and run finish
3. API surface
   - add run notebook list and page detail endpoints
4. UI
   - add a notebook browser tab and page detail pane
5. Validation
   - add focused backend tests and run full repo quality gates

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run check`
- `npm --prefix apps/web run biome:check`

## Open Questions

- whether a later slice should derive notebook pages asynchronously from workflow events instead of
  emitting them directly from supervisor milestone methods
- whether notebook pages should eventually include lightweight repo tags such as source repo root or
  workflow id to support cross-run retrieval

## Progress Notes

- 2026-04-02: Started notebook implementation as a projection over append-only facts, with
  canonical JSONL pages plus rendered markdown under each run directory.
- 2026-04-02: Shipped the first notebook slice. Canonical notebook page records now live in
  `notebook-pages.jsonl`, rendered markdown pages are written under `notebook/`, the supervisor
  emits milestone pages deterministically, and the browser exposes a Notebook tab backed by new
  run notebook APIs.
- 2026-04-02: The current notebook is intentionally deterministic and template-rendered. It does
  not depend on an LLM to create or edit pages, and old pages remain immutable; future corrections
  should arrive as amendment pages rather than in-place rewrites.
