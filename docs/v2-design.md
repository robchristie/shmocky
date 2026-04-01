I've been going over the following references:
https://developers.openai.com/api/docs/guides/prompt-guidance/ "Prompt guidance for GPT-5.4 | OpenAI API"
https://developers.openai.com/api/docs/guides/structured-outputs/ "Structured model outputs | OpenAI API"
https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/ "Codex Prompting Guide"

I think the next major change is to be better aligned with the above guidance.

A better defined agent collection would be:

* `router` — cheap, fast, typed
* `builder` — main Codex engineer (the old engineer)
* `judge` — strict evaluator/reviewer
* `expert` — optional Oracle or strong model for design/postmortem work only
    
It seems GPT-5.4 works best with explicit output contracts, dependency checks, completeness rules, verification loops, and scoped mid-conversation updates. And the current Codex prompting guide specifically recommends removing prompting for upfront plans, preambles, and status updates during coding rollouts because that can make the model stop early.

Our current loop always does a planning turn before execution, but OpenAI’s current Codex guidance recommends starting from the standard Codex prompt and specifically removing prompting for upfront plans, preambles, and status updates during rollout because that can cause the model to stop before finishing the work. So, lets drop the planner agent.

This implies we should rewrite the prompts around contracts, not roles

We should upgrade the builder prompt with reusable blocks, not just role prose.
The GPT-5.4 prompt guidance is very clear that the highest-leverage gains come from explicit output contracts, tool-use expectations, completion criteria, and lightweight verification, rather than just cranking reasoning effort. It specifically recommends blocks like <tool_persistence_rules>, <dependency_checks>, <completeness_contract>, and <verification_loop>, and says reasoning effort should be treated as a last-mile knob.
The current engineer startup prompt is intentionally minimal. I’d keep that spirit, but expand it with modular blocks such as:

* autonomy and persistence
* tool boundaries
* dependency checks
* completeness contract
* verification loop
* default follow-through policy
* optional research/citation mode only when web access is enabled

I would put these blocks into the builder prompt:

* `<default_follow_through_policy>`
* `<instruction_priority>`
* `<tool_persistence_rules>`
* `<dependency_checks>`
* `<completeness_contract>`
* `<verification_loop>`
* `<action_safety>`

Those exact patterns are now called out in the GPT-5.4 prompt guidance as high-leverage ways to improve long-horizon execution and tool discipline.

And I would render operator steering as a scoped `<task_update>` block, not a loose appended paragraph. The current guidance explicitly recommends scope + override + carry-forward for mid-conversation instruction changes.

For the typed router agent, the idea is to make the first decision in a run a structured `RunRoutingDecision`. Use Structured Outputs for this so the supervisor gets a valid schema instead of trying to scrape prose. OpenAI’s Structured Outputs docs explicitly position JSON Schema/Pydantic-backed outputs as the reliable way to make control-plane calls type-safe.

I’d make the router choose only from a small whitelist e.g.:

* `workflow_id`
* `codex_agent_id`
* `judge_agent_id`
* `expert_agent_id | null`

This keeps the supervisor deterministic. The router selects from approved options; it does not invent new graphs or new agent types on the fly.

Make artifacts first-class and typed

Transcript text is not enough. Shmocky should judge from machine-readable artifacts

I would add these Pydantic models in Shmocky:

* `ExperimentSpec`
* `EvalReport`
* `MutationProposal`
* `CandidateComparison`
* `CandidateAcceptanceDecision`

This is also where I’d use Structured Outputs very aggressively:

* router output
* mutation proposal
* acceptance decision
* incident diagnosis
* promotion decision

Use free text for the coding agent. Use schemas for the control plane. That division is clean and reliable.

We decided to make Oracle a free-text expert and Codex as the decision owner. I think that's still correct. But, I wonder if we could make the expert output semi-structured?

e.g.
summary
risks[]
missed_opportunities[]
suggested_checks[]
recommended_next_prompt

Then the judge consumes that plus repo state and emits a strict decision object. That preserves the useful “different brain” effect without handing control to a fuzzy manager loop.

For steering, I'd turn operator steering into scoped updates instead of loose appended text. The current _consume_steering() appends free-text notes into the next execution prompt. That works, but the newer prompt guidance explicitly recommends scoped steering messages that state scope, override, and carry-forward. It also recommends making instruction priority explicit and using default follow-through rules.

So instead of:
Operator steering to apply on this step:
- fix flaky tests first

Render something like:
<task_update>
Scope: next execution turn only
Override:
- Prioritize fixing flaky tests before feature work.
- Do not change UI files in this turn.
Carry forward:
- All earlier run instructions still apply unless they conflict.
</task_update>

That will make steering much more predictable.

Does this change make sense? Anything else you'd suggest?


---

• Yes. This change makes sense, and it is aligned with the current OpenAI guidance.

  The strongest parts of your proposal are:

  - dropping the always-on planner turn for Codex rollout work
  - moving the control plane toward typed outputs and away from prose scraping
  - upgrading the builder prompt from role prose to explicit contracts
  - rendering operator steering as a scoped <task_update> block
  - keeping Oracle advisory, not in charge of control flow

  That lines up with the current docs:

  - GPT-5.4 prompt guidance emphasizes explicit contracts, dependency-aware tool rules, verif
    ication loops, and scoped mid-conversation updates rather than just increasing reasoning
    effort (Prompt guidance (https://developers.openai.com/api/docs/guides/prompt-guidance))
  - the Codex prompting guide explicitly says to start from the standard Codex prompt and rem
    ove prompting for upfront plans, preambles, and status updates during rollout because that
    can cause early stopping (Codex Prompting Guide
    (https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide))
  - Structured Outputs are the recommended way to keep control-plane decisions schema-safe (S
    tructured outputs (https://developers.openai.com/api/docs/guides/structured-outputs))

  A few concrete recommendations.

  1. I would make the new default agent set exactly:

  - builder: Codex, free-text, tool-using, sole mutator
  - judge: typed, read-only, strict decision owner
  - expert: optional, advisory only
  - router: optional at first, not required for every run

  I would not make router mandatory in the first cut unless you already have multiple
  workflows or multiple viable builder/judge pairings. If you only have one workflow and one
  normal builder, a router adds complexity before it adds real value. The clean phased path
  is:

  - first: remove planner, strengthen builder prompt, type the judge decision
  - second: add optional router when you have enough choices to justify routing

  2. Your prompt direction is correct.
     For the builder prompt, I would absolutely move to reusable blocks like:

  - <default_follow_through_policy>
  - <instruction_priority>
  - <tool_persistence_rules>
  - <dependency_checks>
  - <completeness_contract>
  - <verification_loop>
  - <action_safety>

  That is directly aligned with the GPT-5.4 guidance around follow-through policy, instruction
  priority, persistent tool use, and verification (Prompt guidance
  (https://developers.openai.com/api/docs/guides/prompt-guidance)). I would also keep the bui
  lder prompt narrowly operational:

  - what counts as done
  - when to use tools
  - when to verify
  - when to stop and ask
  - no explicit prompt to emit plans or status chatter during execution

  3. Your steering change is a strong improvement.
     The <task_update> shape you proposed is almost exactly what the prompt guidance recommen
     ds for mid-conversation changes: scope, override, carry-forward (Prompt guidance
     (https://developers.openai.com/api/docs/guides/prompt-guidance)). I would make that the
     only steering format Shmocky emits. It will be more predictable than the current appended
     prose.
  4. Typed control plane is the right split.
     I agree with:

  - free text for builder
  - typed schemas for router, judge, mutation proposals, promotion decisions, incident
    diagnosis

  One important caveat: the current Structured Outputs guide has some generic compatibility t
  ext that still mentions older 4o-family snapshots, but the current model pages for both GPT-
  5.4 (https://developers.openai.com/api/docs/models/gpt-5.4) and GPT-5-Codex
  (https://developers.openai.com/api/docs/models/gpt-5-codex) now say “Structured outputs: Su
  pported.” My read is that Structured Outputs are supported on those models via the API, but
  I have not verified that the codex app-server surface itself exposes schema-constrained out
  puts. That part is an inference from the model pages plus your current architecture, and it
  matters.

  Because of that, I would suggest:

  - builder stays on codex app-server
  - router and judge should probably be API-sidecars using Responses API models directly, at
    least initially
  - do not assume app-server gives you the schema controls you want until we verify it in a
    small spike

  That keeps the control plane deterministic without forcing the builder off the Codex
  harness.

  5. Oracle semi-structured expert output is a good idea, but only lightly structured.
     I would not ask browser Oracle for strict JSON. I would ask for labeled sections, for
     example:

  - Summary:
  - Risks:
  - Missed opportunities:
  - Suggested checks:
  - Recommended next prompt:

  Then Shmocky can parse that permissively into a typed internal object. That gives you more
  observability than raw prose, but avoids the brittleness you already saw with browser-
  managed ChatGPT output.

  6. Artifacts should become first-class, but I would stage them.
     I agree with the direction, but I would not introduce all five artifact types at once. I
     would start with:

  - EvalReport
  - CandidateAcceptanceDecision
  - maybe MutationProposal

  That is enough to reshape the loop around evidence instead of transcript prose. Then add
  ExperimentSpec and CandidateComparison once the first artifact pipeline is stable.

  7. One thing I would add: make the judge evidence-bound.
     The judge should not just say continue/complete/fail. It should also be required to point
     to evidence fields from the run bundle, for example:

  - checks executed
  - files changed
  - git diff summary
  - unresolved failures
  - acceptance criteria satisfied / unsatisfied

  So the decision object should probably look like:

  - decision
  - summary
  - evidence
  - missing_requirements
  - next_prompt when continuing

  That will make run history much more useful than a bare decision string.

  8. Another thing I’d add: do not call expert every loop by default.
     Oracle is slow and expensive in operator attention. I would make expert invocation
     policy-driven:

  - only when judge says “stuck”
  - only every N loops
  - only for design ambiguity
  - only on failure/postmortem
  - optionally operator-forced

  That preserves the “different brain” benefit without putting Oracle on the hot path of every
  iteration.

  So my overall recommendation is:

  - Yes, make this change.
  - Remove the planner agent.
  - Strengthen the builder prompt around contracts and verification.
  - Move steering to <task_update>.
  - Keep Oracle advisory and only semi-structured.
  - Make the judge typed and evidence-bound.
  - Delay mandatory router adoption until you actually have multiple workflow/agent choices.
  - Use direct API structured outputs for router/judge unless we verify app-server schema
    support.

  If you want, the next concrete step should be an ExecPlan that ships this in two slices:

  1. builder + typed judge + task_update steering
  2. optional expert schema + optional router

  That would give you most of the value without trying to redesign the whole control plane in
  one jump.


