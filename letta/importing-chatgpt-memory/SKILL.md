---
name: importing-chatgpt-memory
description: Clone ChatGPT saved memory into Letta, then optionally enrich it with broader conversation history. Designed for a slick onboarding flow that extracts hidden saved-memory/context blocks, builds Letta-ready previews, and only asks questions at meaningful checkpoints.
license: MIT
---

# Cloning ChatGPT Memory into Letta

Use this skill when a user wants Letta to inherit ChatGPT memory as faithfully as possible without blindly importing an entire export.

## Good fits

- clone my ChatGPT memory into Letta
- inspect hidden saved profile / custom-instruction context
- migrate ChatGPT memory into active Letta memory
- enrich the clone with work context or collaboration preferences from old chats
- preserve selected transcripts for high-fidelity audit/reference

The skill should work well even when the user says something minimal like:
- "I want to import my ChatGPT memory"
- "Can you clone my ChatGPT memory into Letta?"
- "Import my ChatGPT export"

Do **not** depend on the user writing an optimized prompt.

## Scope

This skill is for **memory onboarding**, not just transcript rendering.

It should:
- extract ChatGPT saved memory and editable-context blocks first
- build a Letta-oriented preview of what should become active vs progressive memory
- write obvious, high-confidence items while narrating progress
- optionally enrich from the broader archive afterward
- optionally export transcripts for high-fidelity archival

It should **not**:
- blindly import the whole archive
- treat runtime context as durable memory
- flatten historical context into always-visible memory by default
- auto-store sensitive personal material without confirmation
- write memory into a malformed MemFS structure

## Default posture

Use a **clone first, enrich second** workflow.

1. ask a short structured intake
2. inspect the export
3. extract explicit ChatGPT memory first
4. build a Letta-ready preview
5. write obvious high-confidence items while learning
6. stop for review by default after the explicit clone pass
7. optionally enrich from the broader archive afterward
8. ask only at meaningful checkpoints

Users should feel like they are being guided through an onboarding flow, not dropped into a bag of scripts.

The onboarding should be robust to sparse user input. The agent should supply the structure, not ask the user to craft a better request.

## Interaction style

### Start with a short dialog

When available, prefer the structured **AskUserQuestion** flow so the import feels like a dialog.

Good question types:
- export location (if not obvious)
- import scope (saved memory only, memory + work context, full history mining)
- review cadence: "Stop for review after the explicit memory clone, or keep going autonomously?"
- topic focus: "Any specific projects or topics you want me to look for?"
- sensitivity: "Anything I should avoid storing?"

Avoid questions that don't actually change the workflow. For example, "how do you want historical context handled?" sounds meaningful but the answer rarely changes what scripts you run. Focus on questions whose answers fork the process.

This intake exists so the user does **not** need to front-load all of this context in their first message.

Use:
- **single-choice** for policy decisions
- **multi-select** for scope selection

### After intake, drive the process

Once scope is clear, be more authoritative than permissive.

Do **not** keep returning with vague prompts like:
- "what do you want me to do next?"
- "should I keep going?"

Instead:
1. say what you wrote
2. say what you are reviewing next
3. continue automatically

Only stop for:
- contradictory facts
- sensitive/intimate material
- major scope changes
- real uncertainty about what counts as durable memory

Do **not** stop for low-risk routing decisions once the user's scope is already broad and clear.

Also do **not** respond by teaching the user how they should have phrased the request. Just run the onboarding properly.

## Workflow

### 0. Locate the export

ChatGPT exports are typically named with a long hash and timestamp, e.g.:
`8a8f3ee0...-2026-03-31-18-41-51-e0dc362a....zip`

Common locations:
- `~/Downloads/` (most common — this is where the browser saves it)
- Desktop or a custom export folder

If the user doesn't know the exact path, glob for zip files in Downloads and look for the distinctive long-hash naming pattern or check for files containing `conversations-*.json` entries.

### 1. Inventory the export

Start by listing conversations and surfacing hidden-context-heavy candidates.

```bash
python3 scripts/list-conversations.py <export.zip>
python3 scripts/list-conversations.py <export.zip> --sort hidden --min-hidden 1
python3 scripts/list-conversations.py <export.zip> --json --limit 50
```

Use this to understand scale, find likely memory-heavy conversations, and decide whether broader archive review is even necessary.

**Warning:** For large archives (300+ conversations), `--json` output can easily exceed 100K characters and flood your context window. Mitigations:
- Use `--limit 50` to start — you can always paginate with `--start-index`
- Pipe to a file and read selectively: `... --json > /tmp/conversations.json`
- Use `--title-contains` to filter before dumping JSON
- The non-JSON (table) output is much more compact for initial inventory

### 2. Extract ChatGPT saved memory first

This is the default onboarding path.

Run the saved-memory extractor before doing any large transcript review:

```bash
python3 scripts/extract-saved-memory.py <export.zip>
python3 scripts/extract-saved-memory.py <export.zip> --json --output /tmp/chatgpt-saved-memory.json
```

If you want to both view and save the JSON, run the command once with `--output` and then read the saved file.

This script pulls the highest-signal onboarding inputs from the entire export:
- `about_user_message`
- `about_model_message`
- `user_profile`
- `user_instructions`

It also deduplicates repeated values and shows when they were first/last seen.

### 3. Build a Letta-ready preview

Turn the extraction into a clean preview of:
- likely active-memory candidates
- historical/progressive-memory candidates
- runtime-only context
- contradictions or review items

```bash
python3 scripts/build-memory-preview.py /tmp/chatgpt-saved-memory.json
python3 scripts/build-memory-preview.py /tmp/chatgpt-saved-memory.json --output /tmp/chatgpt-memory-preview.md
```

This is the core "what ChatGPT appears to remember about you" step.

**Note:** For users with simple ChatGPT profiles (e.g. just a name and one-liner), the preview mostly reformats what `extract-saved-memory.py` already showed. In those cases, skip the preview and go straight to writing memory. The preview is most valuable when the profile has contradictions, multiple historical versions, or a mix of durable and runtime context.

### Merging with existing memory

If the agent already has populated memory blocks (e.g. from `/init` or a previous session), **do not overwrite them**. Read the existing blocks first and merge ChatGPT findings into the existing structure:

- Use `str_replace` to add new sections to existing blocks rather than rewriting them
- If the existing memory already covers a topic (e.g. working style, project list), augment it — don't replace it
- ChatGPT memory may be stale relative to what the agent already knows. Prefer existing memory for current facts; use ChatGPT data to fill gaps (background, preferences, historical context)

### Safe write targets and memory structure

Before writing memory, inspect `system/` and the relevant reference directories.

Important MemFS rule:
- **Never create overlapping file/folder paths** such as `system/human.md` and `system/human/...` or `system/persona.md` and `system/persona/...`.

Preferred destinations:
- `system/human.md` — condensed durable user facts and collaboration preferences that should be in-context every turn
- `reference/chatgpt/import-YYYY-MM-DD.md` — import audit trail, exclusions, uncertainty notes, source path
- `reference/chatgpt/work-and-technical-background.md` — historical or progressive work context
- `reference/chatgpt/collaboration-preferences.md` — mined interaction/style patterns that do not all need to live in `system/`
- `reference/chatgpt/transcripts/` — curated transcript exports for fidelity/auditability

If `system/human.md` already exists, update that file instead of inventing a sibling folder.
If `system/persona.md` already exists, update that file instead of inventing a sibling folder.

Use progressive disclosure aggressively: keep active memory small, and link outward with `[[reference/chatgpt/...]]` paths so future agents can discover the archive.

### 4. Write obvious high-confidence memory while learning

Good candidates to write immediately:
- name and stable identity basics
- current role or project context that is explicit and recent
- explicit response preferences from hidden saved memory
- repeated formatting preferences
- collaboration preferences like directness, question volume, anti-sycophancy

When you write while learning:
1. keep the write small and specific
2. tell the user what you wrote
3. tell the user what you are reviewing next
4. continue

### 5. Optional archive enrichment

Only after the saved-memory clone is handled, and by default **after a review checkpoint**, optionally mine broader conversation history for:
- work/project context
- collaboration patterns
- historical background
- other durable facts the user wants preserved

Use the transcript renderers for this:

```bash
python3 scripts/render-conversation.py <export.zip> --index 12 --output /tmp/chatgpt-12.md

python3 scripts/render-range.py <export.zip> \
  --start-index 220 \
  --end-index 274 \
  --output-dir /tmp/chatgpt-range \
  --skip-empty-hidden \
  --compact-nontext
```

**Default to doing enrichment directly** — render a few high-signal conversations yourself using `--title-contains` to filter. Only use subagents when the archive is large enough to justify parallelism (200+ conversations), and always have a fallback plan for when they fail (see "Working at scale with subagents" below).

#### Topic-based mining pattern

There is no single script for topic-based discovery + rendering. Use this two-step pattern:

```bash
# Step 1: Find conversations by topic
python3 scripts/list-conversations.py <export.zip> --title-contains "Julia" --json

# Step 2: Render the most promising ones individually
python3 scripts/render-conversation.py <export.zip> --index 95
python3 scripts/render-conversation.py <export.zip> --index 144
```

For broader topic sweeps, try multiple `--title-contains` queries (e.g. "Julia", "Bayesian", "economics") and deduplicate by index before rendering.

#### Stale-context / retraction sweep

Before promoting historical findings to active memory, do a lightweight sweep for explicit corrections in later conversations.

Use content search, not just title search:

```bash
python3 scripts/search-conversations.py <export.zip> --query "not doing" --query "no longer" --query "forget that" --query "remove from memory"
python3 scripts/search-conversations.py <export.zip> --query "used to" --query "don't assume" --json --limit 20
```

Typical signals:
- the user says a project is no longer active
- the user says to forget or remove old context
- the user says a role, employer, affiliation, or plan is outdated

When old context conflicts with a newer explicit correction, prefer the newer correction.

### 6. Optional high-fidelity transcript export

If the user wants maximum fidelity or future auditability, export selected transcripts.

```bash
python3 scripts/export-transcripts.py <export.zip> \
  --indexes 229,288 \
  --output-dir /tmp/chatgpt-transcripts \
  --skip-empty-hidden \
  --compact-nontext
```

For transcript export into a memory repository or memory-like layout:

```bash
python3 scripts/export-transcripts.py <export.zip> \
  --start-index 220 \
  --end-index 230 \
  --output-dir /tmp/chatgpt-transcripts \
  --skip-empty-hidden \
  --compact-nontext \
  --memory-frontmatter
```

Transcript export should be treated as an **optional archival feature**, not the default onboarding path.

### Storing transcripts in the memory repo

Some transcripts are genuinely useful as reference memory — deep technical discussions, project planning sessions, or conversations where the user stated specific preferences in detail. The key is selectivity.

**Do:**
- Store only transcripts that contain durable context not already captured in memory blocks
- Put them in `reference/chatgpt/transcripts/` (not `system/`) so they don't pin to the context window
- Prefer summarized versions over verbatim when the key facts can be distilled into a few paragraphs
- Use verbatim only when fidelity matters (exact decisions, nuanced preferences, detailed technical context)
- Scale with the archive: a user with 500 conversations might have 30-50 worth preserving. Don't impose an artificial cap — use judgment about signal density
- Pair transcript exports with a small audit/import file explaining why they were preserved

**Don't:**
- Dump all rendered transcripts into the memory repo
- Store transcripts in `system/` where they'd consume context window space
- Store transcripts that are redundant with what's already in active memory blocks

## Hidden context to watch for

Recent ChatGPT exports often contain the clearest explicit memory in hidden system/context messages.

High-signal fields:
- `metadata.user_context_message_data.about_user_message`
- `metadata.user_context_message_data.about_model_message`
- `content.user_profile` from `user_editable_context`
- `content.user_instructions` from `user_editable_context`

Important distinctions:
- the same saved-memory block may repeat across many conversations
- some hidden messages are runtime execution context, not durable memory
- account metadata from `user.json` / `user_settings.json` is usually audit material, not active memory (note: no script currently extracts from these files — inspect manually if needed)

Examples of runtime-only context:
- current date
- current timezone
- current location
- temporary recency instructions tied to a specific export moment

Examples of durable collaboration context:
- directness / brevity preferences
- formatting preferences
- search-first instructions for current events
- anti-sycophancy or anti-pedantry preferences

## What belongs where

### Active memory

Good candidates:
- stable identity facts
- current role / recurring project context
- durable response preferences
- durable collaboration preferences
- long-lived tool/workflow preferences

### Progressive memory

Good candidates:
- historical roles or project arcs
- previous versions of ChatGPT saved memory
- older but still useful background context
- selected transcript exports for fidelity / auditability

### Ask before storing

Stop and confirm before storing:
- intimate relationship details
- health or mental-health details
- sensitive personal material that is not clearly necessary for future collaboration
- contradictions where the current truth is unclear

## Working at scale with subagents

For larger exports (200+ conversations), use separate subagents for parallel mining. Each subagent should have a focused scope and explicit instructions on which scripts to use.

If the scope is broad and the parent agent is becoming the bottleneck, parallelize more aggressively. It is often better to run 3-6 tightly scoped mining subagents than to funnel everything back through one synthesizer.

### Subagent design rules

- **Give each subagent the full script paths** — they don't inherit your skill knowledge
- **Limit scope to 10-15 rendered conversations per subagent** — more than that risks context overflow or timeouts
- **Use `general-purpose` subagent type** — these subagents need to run scripts via Bash
- **Partition output paths up front** — each writing subagent should own a non-overlapping destination such as `reference/chatgpt/work-and-technical-background.md`, `reference/chatgpt/collaboration-preferences.md`, or a transcript subdirectory
- **Allow direct progressive-memory writes when safe** — subagents can write audit files, reference summaries, and curated transcript exports directly into the memory directory if the paths are clearly partitioned
- **Keep active-memory writes coordinated** — unless a subagent has an explicitly assigned, non-overlapping target, have the parent agent merge final high-confidence facts into `system/human.md` / `system/persona.md`
- **Always provide a fallback plan** — if a subagent fails, do the mining directly using `list-conversations.py --title-contains` followed by targeted `render-conversation.py` calls

### Recommended mining passes

Split into topic-focused subagents:

1. **Work/project context** — find conversations about the user's job, company, recurring projects
2. **Technical background** — languages, frameworks, tools, research topics
3. **Personal context** — hobbies, relationships, life events (handle sensitively)
4. **Collaboration preferences** — how they like to interact with AI, formatting preferences, pet peeves
5. **Retraction / stale-context pass** — explicit corrections, outdated affiliations, projects the user says to forget

### Subagent prompt template

```
You're mining a ChatGPT export for [TOPIC] context. The export is at:
[EXPORT_PATH]

Step 1: Find relevant conversations:
python3 scripts/list-conversations.py "[EXPORT_PATH]" --title-contains "[KEYWORD]" --json

# Optional: search message contents directly for corrections or buried context
python3 scripts/search-conversations.py "[EXPORT_PATH]" --query "[KEYWORD]" --json

Step 2: Render the top 5-10 most relevant conversations:
python3 scripts/render-conversation.py "[EXPORT_PATH]" --index [N] --skip-thoughts --skip-empty-tool-messages

Extract and return:
- [SPECIFIC QUESTION 1]
- [SPECIFIC QUESTION 2]
- [SPECIFIC QUESTION 3]

Output a concise summary of findings. Separate into: safe-to-write-now, proposal-only, historical/progressive, and sensitive findings.
```

### When subagents fail

Subagents can fail silently due to timeouts or context limits. If a mining subagent fails:
1. Don't retry with the same broad scope
2. Use `list-conversations.py --title-contains` directly to find relevant conversations
3. Render 3-5 of the highest-signal ones yourself
4. Extract what you can — partial coverage is fine

## Scripts

### `scripts/list-conversations.py`

Use for archive inventory.

Key features:
- list by global index
- sort by hidden-context count
- filter with `--min-hidden`
- emit JSON for agent workflows

### `scripts/extract-saved-memory.py`

Use for the first onboarding pass.

It extracts and deduplicates:
- `about_user_message`
- `about_model_message`
- `user_profile`
- `user_instructions`

It also reports first/last seen timestamps and source samples.

Supports:
- `--json`
- `--output`

### `scripts/build-memory-preview.py`

Use to build the Letta-oriented preview.

It separates:
- likely active-memory candidates
- historical/progressive-memory candidates
- runtime-only context
- contradictions / review items

### `scripts/render-conversation.py`

Use for deep review of one conversation.

Useful mining flags:
- `--skip-thoughts`
- `--skip-empty-tool-messages`
- `--user-only`
- `--assistant-only`

### `scripts/render-range.py`

Use for batch transcript rendering during archive enrichment.

Also supports the same noise-reduction flags as `render-conversation.py`.

### `scripts/search-conversations.py`

Use when title search is not enough.

Good fits:
- stale-context / retraction sweeps
- finding buried project mentions inside generic titles
- locating "forget this" / "not doing this anymore" corrections
- searching for specific phrases before choosing which conversations to render

### `scripts/export-transcripts.py`

Use for optional high-fidelity archival exports.

Supports:
- selected indexes or ranges
- transcript chunking
- optional memory-style frontmatter
- a generated transcript index file

## Final user-facing summary

At the end of a run, report back in this order:

1. **What ChatGPT explicitly remembered**
2. **What got cloned into active Letta memory**
3. **What was preserved as historical/progressive memory**
4. **What was excluded and why**
5. **What still needs confirmation**
6. **Whether the user wants a `/doctor` pass to validate the resulting memory structure and prompt hygiene**

## References

- `references/chatgpt-export-notes.md`
- `references/memory-import-workflow.md`
