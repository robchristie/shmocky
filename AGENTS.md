# AGENTS.md

This repository builds the Shmocky autonomous supervisor and control plane around Codex. It is not a workload repository. Its job is to prepare environments, run or resume or fork or steer Codex threads, capture structured events, reduce those events into durable state, enforce policy and approval gates, and expose observability through an API and dashboard.

Keep the framework minimal. Avoid agent societies, fragile orchestration graphs, and framework-defined cognitive workflows. Prefer a thin deterministic kernel, strong prompts, explicit policy, and rich observability.

## Mission

The system should let a codex coding agent keep going on a task with minimal human intervention while remaining easy to inspect and steer. The kernel should stay small:

- preflight the environment
- start, resume, fork, and steer Codex runs
- capture raw events
- reduce events into notebook and published-book projections
- evaluate progress and health
- enforce policy, budget, and approval rules

Everything else should remain outside the critical path.

## ExecPlans

When the work is more than a trivial edit, create or update an ExecPlan under `plans/` and follow `PLANS.md` from design through implementation.

Use an ExecPlan whenever the task:

- spans multiple packages or apps
- changes architecture, schemas, or event flow
- changes agent roles, prompts, policies, or approval rules
- introduces or removes a dependency, service, or storage layer
- is expected to take more than about thirty minutes
- has unknowns that should be de-risked with prototypes or spikes

Do not ask the user for "next steps" once the ExecPlan exists unless you hit an explicit approval gate or a truly blocking external dependency.

## Engineering rules

1. Prefer additive, testable changes over broad rewrites.
2. Keep interfaces explicit and typed at every process boundary.
3. Validate environment variables and external inputs at startup.
4. Avoid hidden global state.
5. Make event payloads and persisted records versionable.
6. Include timestamps, stable ids, and provenance in stored records whenever possible.
7. Do not log secrets, tokens, raw credentials, or unnecessary sensitive payloads. Redact when in doubt.
8. Treat raw agent event logs as sensitive operational data.
9. Keep failure modes observable. A blocked run should explain why it is blocked and what action would unblock it.
10. Do not introduce a database, queue, or memory system until file-backed or simple embedded storage is clearly insufficient.
11. Prefer local files and simple projections for the first implementation.
12. Use clear names. Avoid clever abstractions that save a few lines at the cost of readability.

## CI Workflow

Current CI steps:

- `uv sync --extra dev`
- `npm --prefix apps/web install`
- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run biome:check`

## Lint And Type Checking

- `ruff` is the fast lint/import-hygiene pass.
- `ty` is enabled as a pragmatic static check against the active `uv` environment.
- `Biome` is the frontend formatter/import-order gate for `apps/web`, including Svelte files.

## Review guidelines

When reviewing or self-reviewing changes, check the following first:

- Does the change preserve the thin-kernel architecture?
- Does it keep `codex app-server` integration structured and avoid brittle shell parsing of UI text?
- Are raw events persisted before projections are derived?
- Are approval and budget gates explicit and testable?
- Are secrets and sensitive payloads protected in logs and UI?
- Is the API boundary typed and validated?
- Are docs, commands, and tests updated to match the change?

## Completion criteria

A change is not complete until all of the following are true:

- the relevant ExecPlan is updated if one was required
- code, tests, and docs agree
- the root quality gates pass
- the change is observable in the dashboard or logs when relevant
- any new assumptions, surprises, or tradeoffs are captured in the ExecPlan or durable docs

Keep this file short, practical, and current. If the repo evolves, update this guidance rather than working around stale instructions.

