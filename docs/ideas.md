* run history and resume support
* richer judge bundles and workflow templates
* managed worktree/copy for even stronger isolation without relying on operator discipline


test task

/nvme/development/testing/btc
Implement a CPU based Bitcoin hash solver. Create a benchmark framework to test your implementation against. Try to make it run as fast as possible.

Findings:

  1. High: approval and other server-request flows can still block a run with no browser-side action path. The backend tracks pending requests in src/shmocky/models.py:89 and src/ shmocky/projection.py:95, but the UI only treats them as observable protocol state rather than something you can resolve. On a more complex run, the first approval or user-input request can leave the workflow effectively stuck until you intervene outside the intended control surface.

  2. Medium: the new “pause on Oracle failure” behavior is only resumable while this backend process stays alive. On shutdown, the supervisor cancels the active run task in src/ shmocky/supervisor.py:214, and the current history system is view-only rather than execution-resumable. For long Oracle waits on Pro, a backend restart or deploy in the middle of a paused Oracle step will lose the live retry position even though the run snapshot remains inspectable.

  3. Medium: Codex expert/judge handoff is still hard to debug because those auxiliary Codex turns run in isolated sidecar bridges that do not stream into the main UI. The separate one-off bridges are created in src/shmocky/supervisor.py:932, and only the final answer is surfaced back into state. If a complex run starts making poor judge decisions, you currently cannot inspect the full judge transcript the way you can inspect the main engineer transcript.

  Recommendation

  I would not call any of these blockers for trying a more complex run, but I would raise the bar on two things first:

  - Add browser-side handling for pending server requests and approvals. That is the biggest real operational gap.
  - Add durable resume semantics for Oracle-blocked pauses, or at minimum make it explicit in the UI that “paused on Oracle failure” only survives while the current backend process remains up.

  After that, the next most useful observability feature would be a compact transcript or artifact viewer for Codex judge/expert turns, because once runs get more complex, you will want to see why the judge decided to continue or stop.

