# ExecPlan 001: Browser Mirror For Codex App Server

## Summary

Ship the first vertical slice of Shmocky as a thin browser wrapper around `codex app-server`.
The backend owns a single app-server subprocess, persists raw protocol traffic to local files,
derives a small in-memory session projection, and fans updates out to the browser. The web UI
shows backend and Codex connectivity, thread and turn state, a streaming transcript, and a raw
event log that mirrors the TUI's observable flow closely enough to inspect what Codex is doing.

## Scope

In scope:

- start `codex app-server` from the backend on startup
- initialize the app-server connection and expose backend and Codex health
- support starting one workspace thread and sending turns into it
- support interrupting an active turn
- persist raw inbound and outbound JSON-RPC messages before applying projections
- expose a websocket stream for UI observability
- build an operator-style Svelte 5 SPA with a status header and browser-side transcript/event log

Out of scope for this slice:

- multi-thread management beyond a single active workspace thread
- approval workflows and user-input request handling in the browser
- resume, fork, archival, and notebook/published-book projections
- auth, budgets, policy gates, or multi-user tenancy

## Architecture

Backend:

- `FastAPI` app with a lifespan-managed `CodexAppServerBridge`
- child-process bridge talks to `codex app-server` over stdio using line-delimited JSON-RPC
- `RawEventStore` appends every outbound request and inbound response/notification to a JSONL file
- `SessionProjection` keeps current connection, thread, turn, transcript, and recent errors in memory
- websocket endpoint broadcasts raw events plus the latest projection snapshot

Frontend:

- `Svelte 5` SPA in `apps/web`
- restrained operator layout: header, transcript pane, event pane, composer
- websocket client hydrates from `/api/state`, then consumes streaming updates
- initial UI uses the project's shadcn-svelte foundation without turning the surface into a card grid

## Milestones

1. Planning and protocol capture
   - create `PLANS.md`
   - create this ExecPlan
   - validate `initialize`, `thread/start`, and `turn/start` against a live `codex app-server`
2. Backend bridge
   - add Python dependencies and backend package scaffold
   - implement event store, projection, and bridge
   - add FastAPI routes and websocket stream
3. Browser mirror
   - scaffold Svelte 5 app
   - add operator layout and live event/transcript rendering
   - wire frontend dev proxy to the backend
4. Validation and docs
   - add focused tests for projection and event persistence
   - update README with run instructions and current limits

## Validation

- `uv sync --extra dev`
- `npm --prefix apps/web install`
- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run biome:check`
- manual smoke test: start backend, open browser UI, start a thread, send a prompt, observe streamed output

## Open Questions

- Whether the first production transport should remain stdio-only or move to an internal websocket app-server listener.
- How much of the server-request surface should be supported before the next slice: approvals only, or approvals plus tool/user-input requests.
- Whether the backend should auto-create a workspace thread on startup or wait until the browser asks for one.

## Progress Notes

- 2026-03-31: Confirmed locally that `codex app-server` accepts newline-delimited JSON-RPC over stdio.
- 2026-03-31: Confirmed the minimum request flow for this slice is `initialize`, `thread/start`, `turn/start`, with streaming notifications such as `item/agentMessage/delta`, `thread/status/changed`, and `turn/completed`.
- 2026-03-31: Implemented the FastAPI bridge, file-backed raw event log, in-memory session projection, websocket fanout, and the first browser mirror UI in `apps/web`.
- 2026-03-31: Added a thread-creation lock after smoke testing exposed a race where concurrent API calls could create two workspace threads.
- 2026-03-31: Validated the shipped slice with `uv sync --extra dev`, `uv run ruff check .`, `uv run ty check`, `uv run --extra dev pytest -q`, `npm --prefix apps/web run check`, `npm --prefix apps/web run biome:check`, and a manual smoke test against a live backend on port `8011`.
