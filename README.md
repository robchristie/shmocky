# Shmocky

Shmocky is a thin browser wrapper around `codex app-server`.

This repository is intentionally starting small. The first shipped slice gives you a
single-user control surface with:

- a FastAPI backend that starts and manages one `codex app-server` subprocess
- append-only raw JSON-RPC event logs under `.shmocky/events/`
- a small in-memory projection for connection, thread, turn, transcript, and MCP status
- a Svelte 5 SPA that mirrors the live stream in a browser with a transcript pane and a raw event pane

## Current Scope

Implemented:

- backend startup and `initialize` handshake with `codex app-server`
- one active workspace thread
- prompt submission through `turn/start`
- turn interruption through `turn/interrupt`
- websocket fanout for browser observability
- file-backed raw event persistence before projection updates

Not implemented yet:

- approvals and tool/user-input request handling in the browser
- multi-thread management, resume, fork, archive, or notebook projections
- auth, budgets, policy gates, or multi-user tenancy

## Run

Backend:

```bash
uv sync --extra dev
uv run shmocky-api
```

Frontend:

```bash
npm --prefix apps/web install
npm --prefix apps/web run dev
```

If port `8000` is already in use, choose another backend port and point the Vite proxy at it:

```bash
SHMOCKY_API_PORT=8011 uv run shmocky-api
SHMOCKY_API_URL=http://127.0.0.1:8011 npm --prefix apps/web run dev
```

For headless or remote use through a hostname, also allow that hostname in Vite:

```bash
SHMOCKY_ALLOWED_HOSTS=lv426.yutani.tech npm --prefix apps/web run dev -- --host 0.0.0.0 --port 4321
```

The helper scripts in `scripts/` default to:

- backend on `127.0.0.1:${SHMOCKY_API_PORT:-8011}`
- frontend on `${SHMOCKY_FRONTEND_HOST:-0.0.0.0}:${SHMOCKY_FRONTEND_PORT:-4321}`
- Vite allowed hosts set from `SHMOCKY_ALLOWED_HOSTS` or, by default in `scripts/run-frontend.sh`, `*` for remote dev access

Then open the Vite URL in a browser. The header should show backend and Codex connectivity,
and the main workspace should let you start a thread, send prompts, interrupt turns, and inspect
the raw event stream.

## Quality Gates

```bash
uv sync --extra dev
npm --prefix apps/web install
uv run ruff check .
uv run ty check
uv run --extra dev pytest -q
npm --prefix apps/web run check
npm --prefix apps/web run biome:check
```

## Notes

- Raw app-server traffic is treated as sensitive operational data. Do not commit `.shmocky/`.
- The browser surface is intentionally observability-first, not a general orchestration layer.
- The relevant design record for this slice is [plans/001-browser-mirror.md](/nvme/development/shmocky/plans/001-browser-mirror.md).
