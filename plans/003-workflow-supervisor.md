# ExecPlan 003: Declarative Workflow Supervisor

## Summary

Add a thin workflow supervisor on top of the existing Codex bridge and Oracle sidecar so Shmocky
can run a named workflow against a local repo path with minimal human steering. V1 stays narrow:

- one active workflow run at a time
- repo-local TOML config as the source of truth
- one long-lived Codex thread per run
- a linear loop workflow, not a general graph runtime
- Oracle as a structured evaluator that decides `continue`, `complete`, or `fail`

## Scope

In scope:

- typed workflow and agent configuration in repo-local TOML
- a single-run supervisor owning Codex, Oracle, budgets, pause or resume or stop, and steering
- persisted workflow supervisor events under `.shmocky/runs/`
- API endpoints to launch, observe, and control workflow runs
- SPA workflow launcher and control surfaces

Out of scope:

- general DAG execution or agent society orchestration
- repo cloning or git URL intake
- multiple concurrent workflow runs
- browser-based TOML editing

## Architecture

Backend:

- `shmocky.toml` defines `agents` and `workflows`.
- `WorkflowSupervisor` owns the active run, creates a per-run `CodexAppServerBridge`, invokes the
  Oracle sidecar for judge steps, persists workflow events, and exposes combined dashboard state.
- `CodexAppServerBridge` remains the raw app-server transport and transcript projection layer, but
  is now created per target directory rather than once at app startup.
- `OracleAgent` remains a serialized sidecar and is used directly by the supervisor for judge steps.

Frontend:

- the existing transcript and raw protocol panes stay visible
- a new workflow surface launches named workflows, shows loop state and budgets, and offers pause,
  resume, stop, and steer controls

## Milestones

1. Config and runtime
   - add workflow config models and loader
   - add per-run supervisor and persisted workflow events
2. API and state
   - expose workflow catalog and run-control endpoints
   - combine workflow state with existing dashboard state
3. UI
   - add workflow launcher and control surfaces
   - show workflow-level events separately from raw protocol events
4. Validation
   - add focused config and supervisor tests
   - run backend and frontend quality gates

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run check`
- `npm --prefix apps/web run biome:check`
- focused manual smoke: start a workflow run from the browser and confirm Codex plus Oracle participate

## Open Questions

- whether v2 should allow planner and executor to be separate Codex sessions rather than one shared thread
- whether Oracle should later move to a more typed MCP integration instead of CLI wrapping

## Progress Notes

- 2026-03-31: Locked v1 product shape to repo-local TOML, linear loop workflows, local target directories, and one active run at a time.
- 2026-03-31: Added backend workflow models, config loader, workflow supervisor skeleton, per-run Codex session startup, and combined workflow plus transcript dashboard state.
- 2026-03-31: Added `shmocky.toml`, workflow APIs, SPA run launcher and controls, workflow event projection, and focused config plus supervisor tests.
- 2026-03-31: Focused end-to-end smoke passed with a temporary one-loop workflow against a throwaway git repo, confirming Codex planning and execution plus Oracle structured completion judging.
- 2026-03-31: Smoke testing surfaced a real template-rendering bug with literal JSON braces in judge prompts; prompt rendering now replaces only known placeholders and leaves other braces intact.
- 2026-03-31: Added target-directory isolation guards so runs reject directories inside the Shmocky repo or nested inside another git repository unless explicitly overridden.
- 2026-03-31: Moved Oracle prompt-size policy to Oracle agent config with `prompt_char_limit` in `shmocky.toml`, while keeping the global env setting as a fallback for ad hoc Oracle queries.
- 2026-03-31: Rebalanced the operator UI so workflow activity remains in the primary right-rail view, with the protocol stream moved behind a dedicated debug tab instead of always consuming vertical space.
- 2026-03-31: Added durable per-run dashboard snapshots plus history APIs and a browser run selector, so completed runs can be reopened with transcript, workflow activity, and recent protocol context intact.
- 2026-03-31: Relaxed the Oracle judge contract from strict JSON to a labeled plain-text decision format, while keeping JSON parsing as a backward-compatible fallback.
- 2026-03-31: Split advisory and control roles so Oracle can act as a free-text expert while a Codex judge owns workflow decisions, making cross-agent handoff observable without relying on Oracle for structured control output.
- 2026-04-01: Added per-Oracle-agent `chatgpt_url` support so advisory runs can be directed into dedicated ChatGPT project folders instead of cluttering the main browser history.
- 2026-04-01: Oracle-side failures now pause workflow runs in a resumable state instead of failing outright, and the default Oracle wait budget was raised to one hour for slower browser-model calls.
