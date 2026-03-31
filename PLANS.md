# PLANS

An ExecPlan is the working design record for any non-trivial change in this repository.
It should stay short, concrete, and current enough that someone can read the plan and
understand both the intended architecture and the current execution status.

## When to create one

Create or update an ExecPlan when the work:

- spans multiple packages or apps
- changes architecture, schemas, or event flow
- changes agent roles, prompts, policies, or approval rules
- introduces or removes a dependency, service, or storage layer
- is expected to take more than about thirty minutes
- has material unknowns that should be de-risked with spikes

## File naming

Store plans in `plans/` using a sortable prefix and a short slug, for example:

- `plans/001-browser-mirror.md`
- `plans/002-approval-gates.md`

## Required sections

Each ExecPlan should include these sections:

1. `Summary`
2. `Scope`
3. `Architecture`
4. `Milestones`
5. `Validation`
6. `Open Questions`
7. `Progress Notes`

## Execution rules

- Update the plan before major implementation shifts.
- Record the smallest shippable slice first.
- Prefer additive milestones with explicit validation steps.
- Capture surprises, constraints, and deferred work in `Open Questions` or `Progress Notes`.
- When the change is complete, leave the plan in a state that explains what shipped and what remains.
