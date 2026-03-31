# Shmocky

Shmocky is a thin browser wrapper around `codex app-server`.

This repository is intentionally starting small. The current slice gives you a
single-user control surface with:

- a FastAPI backend that starts and manages one `codex app-server` subprocess
- append-only raw JSON-RPC event logs under `.shmocky/events/`
- a small in-memory projection for connection, thread, turn, transcript, and MCP status
- a Svelte 5 SPA that mirrors the live stream in a browser with a transcript pane and a raw event pane

## Current Scope

Implemented:

- backend startup and `initialize` handshake with `codex app-server`
- one active workflow run at a time, driven by repo-local TOML config
- one long-lived Codex thread per workflow run
- Oracle judging through a structured sidecar loop
- pause, resume, stop, and steer controls from the browser
- one-at-a-time Oracle consults through `POST /api/oracle/query`
- websocket fanout for browser observability
- file-backed raw event persistence before projection updates

Not implemented yet:

- approvals and tool/user-input request handling in the browser
- general graph execution, multi-run scheduling, repo cloning, or browser-side workflow editing
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
and the main workspace should let you select a workflow, point it at a local target directory,
launch a run, inspect Codex transcript plus workflow activity, and pause, resume, stop, or steer.

## Workflow Config

Shmocky reads workflow and agent definitions from `shmocky.toml` in the repo root.

The current built-in config ships one default workflow:

- `plan_execute_judge`

The current workflow shape is intentionally narrow:

- repo-local TOML config
- one active run at a time
- one Codex planner or executor thread per run
- one Oracle judge that returns strict JSON decisions

The backend exposes:

- `GET /api/workflows`
- `POST /api/runs`
- `GET /api/runs/active`
- `POST /api/runs/active/pause`
- `POST /api/runs/active/resume`
- `POST /api/runs/active/stop`
- `POST /api/runs/active/steer`

The browser is the primary way to use these, but the endpoints are available for smoke tests and automation.

## Oracle Sidecar

Shmocky can also invoke a slow Oracle sidecar for high-value consultation work without folding it
into the Codex control loop. The backend reads:

- `ORACLE_REMOTE_TOKEN` from `.env`
- `ORACLE_REMOTE_HOST` optionally, defaulting to `https://oracle.yutani.tech:9473`

The backend normalizes URL-style remote hosts into the `host:port` format Oracle expects, so both
`https://oracle.yutani.tech:9473` and `oracle.yutani.tech:9473` work.

Query it directly through the API:

```bash
curl -X POST http://127.0.0.1:8000/api/oracle/query \
  -H 'content-type: application/json' \
  -d '{
    "prompt": "Review this architecture for hidden operational risks.",
    "files": ["README.md", "src/shmocky/**/*.py"]
  }'
```

Notes:

- Oracle calls are serialized intentionally to avoid spamming the remote signed-in browser.
- The current slice returns the final answer only. It does not stream partial Oracle output into the UI.
- Attached `files` are resolved relative to the workspace root and expanded from glob patterns before invocation.

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
