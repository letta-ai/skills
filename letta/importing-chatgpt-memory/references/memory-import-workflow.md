# Memory import workflow

## Goal

Turn ChatGPT export material into good Letta memory, not maximal Letta memory.

Assume the user may enter with a very small request such as "import my ChatGPT memory." The agent should create the structure through intake and workflow, not require the user to provide an ideal prompt.

Use a **clone first, enrich second** model:

1. clone explicit ChatGPT saved memory
2. write obvious current memory
3. stop for review by default after the explicit clone pass
4. enrich from broader transcript history only if useful

## Default posture

Use a hybrid posture:

- write obvious, low-risk, high-confidence memory while reviewing
- keep ambiguous, historical, sensitive, or broad imports proposal-first

1. List the archive.
2. Extract hidden saved memory and editable-context blocks.
3. Build a Letta-oriented preview.
4. Write obvious durable items as they are confirmed.
5. Render and review broader transcripts only if deeper enrichment is needed.
6. Propose the uncertain or broad updates.
7. Apply the rest only after review.

## Intake questions

Before you inspect the export, ask a short intake set:

1. Where is the export zip?
2. What should be prioritized?
   - explicit saved memory / hidden context
   - work/project context
   - personality / collaboration preferences
   - broader archive mining
3. How aggressive should the review be?
   - saved-memory-first
   - targeted conversations only
   - broader archive sweep
4. Should the workflow stay fully proposal-first, or should obvious items be written while reviewing?

Default to **write obvious items while learning, propose the rest**.

When available, use structured single-choice and multi-select questions so the workflow feels like a dialog rather than a wall of freeform prompts.
But do not overuse questions: once scope is broad and clear, continue automatically.

Do not coach the user on how to phrase a better import request unless they explicitly ask for help testing prompts. The product goal is that a simple request should work.

## Be authoritative after intake

After the intake questions are answered, stop acting like every next step needs user approval.

Preferred posture:
- state what you wrote
- state what you are reviewing next
- continue automatically

Only interrupt the flow when you hit:
- contradictory facts
- sensitive/intimate material
- a large scope change
- genuine uncertainty about what should count as durable memory

Do not interrupt the flow for low-risk decisions that follow naturally from the user's stated scope.

## When to write immediately

Write immediately when the fact is:

- explicit rather than inferred
- current-looking rather than obviously historical
- low sensitivity
- clearly useful in future collaboration

Examples:
- name
- current employer / role when explicitly stated and recent
- stable response preferences
- formatting preferences
- collaboration preferences such as "fewer questions at once"
- canonical ChatGPT saved-memory text when it is explicit and current-looking

When you write while learning, tell the user what you wrote so the progress is visible.
Also tell the user what the next review pass is, so the process feels guided rather than tentative.

## When to hold for review

Hold for proposal/review when the fact is:

- historical or maybe stale
- contradictory with newer material
- sensitive or intimate
- based mostly on assistant interpretation rather than user statements
- too broad to safely pin without confirmation

## Good candidates for active Letta memory

Import into active memory when the fact is:

- stable over time
- useful in future collaboration
- clearly stated or repeatedly reinforced
- not sensitive beyond what is needed for the working relationship

Examples:
- name
- long-lived response preferences
- durable personality / collaboration preferences
- recurring project context
- stable tool or workflow preferences
- durable personal notes the user clearly wants remembered

## Better fits for audit/import files

Keep information in an audit/import file when it is:

- historical and possibly stale
- weakly supported
- sensitive and unnecessary for future work
- a one-off task or temporary emotional state
- too detailed for pinned system memory

Examples:
- old job titles that may no longer be true
- transient plans for the week
- full raw transcript excerpts
- account metadata that is not needed day to day

Selected transcript exports are fine here too when the user wants high fidelity, as long as they stay progressive and out of pinned system memory.

## Personality / collaboration rubric

When the user wants personality imported, translate transcripts into durable collaboration traits.

Good things to extract:
- tone preferences (direct, warm, dry, playful, formal)
- formatting preferences (bullets, terse paragraphs, code-first, no preamble)
- proactivity preferences (ask first vs. act first)
- question-volume preferences (single follow-up vs. many questions)
- correction patterns (how the user signals something is off)
- anti-patterns they dislike (sycophancy, hedging, pedantry, over-explaining)

Things to treat as weak evidence unless the user clearly confirms them:
- one-off frustration
- temporary sadness or stress
- intimate relationship details
- medical or mental-health information that is not necessary for future collaboration

## Confidence and contradiction handling

Use stronger confidence when a fact is:
- explicitly present in hidden saved memory
- repeated across multiple conversations
- restated later as current/canonical

If a fact is high-confidence by this rubric and low-sensitivity, it is usually safe to write while reviewing.

Use lower confidence when a fact is:
- old and time-sensitive
- contradicted by newer conversations
- sensitive and not clearly collaboration-relevant
- only weakly implied by assistant summaries

If you find contradictions, do not guess. Call them out and ask the user which version is current.

## Parallel review guidance

If the archive is large:

- ask how aggressive the mining should be
- split review by conversation or shard
- use cheap subagents for reading and synthesis
- use `render-range.py` for batch preparation when helpful
- merge only high-confidence candidates into the final proposal

Concrete roles that work well:
- **explicit memory reviewer** — hidden context, custom instructions, repeated saved-memory blocks
- **work context reviewer** — projects, tech stack, workflows, team/org context
- **personality reviewer** — tone, formatting, question-volume, proactivity, correction patterns
- **broad miner** — additional high-confidence durable facts from a wider slice of the archive

For a slick onboarding flow, the explicit-memory reviewer should usually run first and drive the first memory writes before broad miners start.

Have each reviewer separate:
- safe-to-write-now findings
- proposal-only findings

## Useful output pattern

When reporting back after reviewing rendered markdown, structure the result as:

1. **Explicit saved memory found**
2. **Durable preferences**
3. **Project/work context**
4. **Personality / collaboration patterns**
5. **Historical or uncertain facts**
6. **What was written during review**
7. **Proposed Letta memory updates**
