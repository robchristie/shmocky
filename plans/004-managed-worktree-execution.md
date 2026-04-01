# ExecPlan 004: Managed Worktree Execution

## Summary

Move workflow execution from direct in-repo runs to kernel-managed git worktrees. A workflow
`target_dir` now means the source repository root selected by the operator. Before Codex starts, the
supervisor validates that the target is a git repository root, creates a managed worktree under
Shmocky's own `.shmocky/worktrees/` area, records the source-vs-execution mapping in run state, and
then runs Codex inside the managed worktree.

## Scope

In scope:

- require workflow `target_dir` to be a git repository root
- create a managed worktree and dedicated branch per run
- record source repo, execution dir, branch, and base commit in run state and persisted artifacts
- run the main Codex session and auxiliary Codex steps inside the managed worktree
- fail fast when worktree creation is not possible
- clean up the managed worktree when run startup fails after workspace creation
- update the browser UI copy so the source repo root and execution workspace are distinct

Out of scope:

- automatic cleanup for completed or stopped runs
- non-git execution modes
- arbitrary operator-selected workspace directories
- cloning repositories from remotes

## Architecture

Backend:

- `WorkflowSupervisor` owns workspace preparation as orchestration, not as agent logic.
- A new worktree-preflight path validates that `target_dir` exists, is outside the Shmocky repo, is
  a git repository, and is the repository root itself.
- A managed workspace is created under `.shmocky/worktrees/<run-id>/` with branch
  `shmocky/<run-id>` from the target repo's current `HEAD`.
- `WorkflowRunState` stores both the source repo root and execution metadata so resume, history, and
  the UI can distinguish them.
- Startup rollback removes the provisional worktree if Codex startup fails after workspace creation.

Frontend:

- The run launcher labels `target_dir` as the source repo root.
- The operator surface shows source repo and execution workspace separately for active and archived
  runs.

## Milestones

1. Planning and models
   - add run-state fields for managed workspace metadata
   - add the ExecPlan and update docs language from "target directory" to source repo root
2. Worktree orchestration
   - validate source repo roots
   - create managed worktrees and persist their metadata
   - switch Codex execution paths to the worktree
3. Observability and rollback
   - expose execution metadata in API/state/UI
   - remove managed worktrees on failed startup rollback
4. Validation
   - add focused supervisor tests for repo validation, managed worktree creation, and rollback
   - run backend and frontend quality gates

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run check`
- `npm --prefix apps/web run biome:check`
- focused manual smoke: start a workflow run against an external git repo and confirm Codex runs in
  `.shmocky/worktrees/<run-id>` rather than the source repo root

## Open Questions

- whether completed or stopped runs should later gain explicit worktree cleanup controls in the UI
- whether v2 should reintroduce a non-git execution strategy alongside `git_worktree`

## Progress Notes

- 2026-04-01: Locked v1 worktree behavior to kernel-managed execution only: workflow `target_dir`
  is now the source git repo root, while Codex runs in `.shmocky/worktrees/<run-id>`.
- 2026-04-01: Added managed-worktree preparation, persisted source-vs-execution workspace
  metadata in run state and manifests, switched Codex and git operations onto the execution
  worktree, and updated startup rollback to remove provisional worktrees when a run fails before it
  fully starts.
- 2026-04-01: Updated the browser operator surface to label `target_dir` as the source repo root and
  show the managed execution workspace, branch, and base commit for active and archived runs.
