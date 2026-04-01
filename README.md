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
- durable per-run history snapshots with transcript and workflow activity replay
- websocket fanout for browser observability
- file-backed raw event persistence before projection updates

Not implemented yet:

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
and the main workspace should let you select a workflow, point it at a local git repository root,
launch a run, inspect Codex transcript plus workflow activity, pause, resume, stop, or steer,
respond to pending Codex approval or user-input requests from the workflow run tab, and durably
resume an Oracle-blocked paused run after a backend restart.

## Workflow Config

Shmocky reads workflow and agent definitions from `shmocky.toml` in the repo root.

The current built-in config ships one default workflow:

- `plan_execute_judge`

The current workflow shape is intentionally narrow:

- repo-local TOML config
- one active run at a time
- one Codex builder thread per run
- one optional expert advisory hop plus a Codex judge that decides whether to continue
- workflow `target_dir` means the source git repository root
- Shmocky creates a managed worktree under `.shmocky/worktrees/<run-id>` and runs Codex there
- source repos must be external git repository roots, not nested subdirectories inside another repo

Oracle agent definitions can also carry role-specific sidecar settings such as `remote_host`,
`chatgpt_url`, `timeout_seconds`, `model_strategy`, and `prompt_char_limit`, so different judge or
analyst roles can run with different budgets and dedicated ChatGPT project folders from the same
`shmocky.toml`.

If you switch Oracle’s browser model to slower modes such as ChatGPT Pro, raise or keep
`timeout_seconds` accordingly. The default backend fallback is now `3600` seconds, and Oracle-agent
failures inside workflow runs pause the run for operator intervention instead of failing it
immediately.

The backend exposes:

- `GET /api/workflows`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `POST /api/runs`
- `GET /api/runs/active`
- `POST /api/runs/active/pause`
- `POST /api/runs/active/resume`
- `POST /api/runs/active/stop`
- `POST /api/runs/active/steer`
- `POST /api/server-requests/{request_id}/resolve`

The browser is the primary way to use these, but the endpoints are available for smoke tests and automation. Each run now stores a durable `dashboard-snapshot.json` under `.shmocky/runs/<run-id>/`, which the UI can reopen to restore transcript, workflow activity, and recent protocol context after the live Codex session has ended.

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
    "agent_id": "judge",
    "prompt": "Review this architecture for hidden operational risks.",
    "files": ["README.md", "src/shmocky/**/*.py"]
  }'
```

Notes:

- Oracle calls are serialized intentionally to avoid spamming the remote signed-in browser.
- The current slice returns the final answer only. It does not stream partial Oracle output into the UI.
- Attached `files` are resolved relative to the workspace root and expanded from glob patterns before invocation.
- Oracle prompt size is bounded by the selected Oracle agent's `prompt_char_limit` when `agent_id` is
  provided, otherwise it falls back to `SHMOCKY_ORACLE_PROMPT_CHAR_LIMIT` and defaults to `20000`.

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
