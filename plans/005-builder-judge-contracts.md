# ExecPlan 005: Builder And Typed Judge Contracts

## Summary

Realign Shmocky with the current GPT-5.4 and Codex guidance by removing the up-front planning turn,
moving the main Codex agent to a contract-driven `builder`, constraining the Codex judge with
schema-typed final output through the app-server `turn/start.outputSchema` field, and rendering
operator steering as scoped `<task_update>` blocks instead of loose appended prose.

This ships in two slices:

1. `builder` + typed `judge` + `<task_update>` steering
2. optional semistructured `expert` output + optional typed `router`

This change implements slice 1 and leaves slice 2 explicitly deferred.

## Scope

In scope:

- remove the always-on planning turn from workflow execution
- rename the main Codex agent/configuration from `engineer` to `builder`
- update default prompts to emphasize contracts, persistence, completeness, verification, and safe
  tool use rather than role prose
- add app-server `outputSchema` support to bridge turn starts
- run Codex judge turns with a strict `JudgeDecision` schema
- render steering as `<task_update>` with scope, override, and carry-forward semantics
- update workflow config, docs, UI labels, and tests to match the new `builder` terminology

Out of scope:

- typed router execution
- semistructured expert schema parsing
- new artifact models beyond the existing `JudgeDecision`
- replacing Oracle or adding paid API sidecars

## Architecture

Backend:

- `WorkflowDefinition` becomes builder-centric; the supervisor no longer executes a separate
  planning phase before coding.
- `CodexAppServerBridge.start_turn()` accepts an optional JSON Schema and forwards it to
  `turn/start.outputSchema`.
- Standard builder turns remain free text and unconstrained.
- Judge turns use a sidecar Codex bridge with `outputSchema` set to the `JudgeDecision` schema,
  keeping control-plane decisions typed without leaving the Codex quota path.
- Steering is injected as a structured `<task_update>` block so mid-run overrides are explicit and
  scoped.

Frontend:

- workflow summaries label the main coding agent as `Builder`
- operator text and transcript behavior remain otherwise unchanged in slice 1

## Milestones

1. Prompt and workflow model cleanup
   - remove planner-specific workflow fields from config loading
   - rename default agent config from `engineer` to `builder`
   - rewrite builder and judge prompts around contracts
2. Typed judge transport
   - add optional `output_schema` to bridge turns
   - run Codex judge turns with schema-constrained output
3. Steering contract
   - replace free-text steering append with `<task_update>`
4. Validation
   - update config, supervisor, and bridge tests
   - run backend and frontend quality gates

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run check`
- `npm --prefix apps/web run biome:check`

## Open Questions

- whether the optional `expert` slice should use labeled text sections or a looser Pydantic-backed
  parser for semistructured advisory output
- whether the `router` should be enabled by default only once there are enough workflow choices to
  justify the extra decision step

## Progress Notes

- 2026-04-01: Confirmed locally that `codex exec --output-schema` is backed by the app-server
  protocol. `turn/start` exposes `outputSchema`, so typed router/judge turns can stay inside the
  Codex app path without paid API sidecars.
- 2026-04-01: Shipped slice 1. The always-on planning turn was removed, the main Codex agent was
  renamed to `builder`, builder prompts were rewritten around persistence and verification
  contracts, and workflow steering now renders as a scoped `<task_update>` block.
- 2026-04-01: Codex judge turns now use app-server `turn/start.outputSchema` with the
  `JudgeDecision` schema, keeping control-plane output typed while staying on the Codex app path.
- 2026-04-01: Slice 2 remains deferred. Expert semistructured output and an optional typed router
  are not implemented in this change.
