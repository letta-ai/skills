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
3. extract and preview in one step
4. write obvious high-confidence items while learning
5. continue into archive enrichment if scoped — narrate progress, let the user interrupt
6. ask only at meaningful checkpoints
7. run `/doctor` to validate the final memory structure

Users should feel like they are being guided through an onboarding flow, not dropped into a bag of scripts.

The onboarding should be robust to sparse user input. The agent should supply the structure, not ask the user to craft a better request.

**This skill is a workflow, not reference material.** Follow the numbered steps in order. Read the guidance for each step before executing it — especially the merge rules and write targets. Moving fast is good; skipping steps is not. "Autonomous" means you drive the process without stopping for permission, not that you skip the instructions.

## Interaction style

### Start with a short dialog

When available, prefer the structured **AskUserQuestion** flow so the import feels like a dialog.

Good question types:
- export location (if not obvious)
- import scope (saved memory only, memory + work context, full history mining)
- topic focus: "Any specific projects or topics you want me to look for?"
- sensitivity: "Anything I should avoid storing?"

Do **not** ask about review cadence. Most users don't have a strong preference, and the ones who do will say so. Default to keeping going — narrate what you're doing and let the user interrupt if they want to pause. This keeps the flow moving instead of creating a false checkpoint.

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

## Progress tracking

This import can take multiple minutes for large archives. **Never let the user sit in silence.** The import should feel like a guided, living process.

### Use TodoWrite for phases

Create a todo list at the start of the import and update it as you go:

1. Locate export and run inventory
2. Extract and preview saved memory
3. Write active memory (`system/human.md`)
4. Write import audit + progressive memory (`reference/chatgpt/`)
5. Archive enrichment (if scoped)
6. Validate with /doctor

Mark each phase `in_progress` before starting and `completed` when done.

### Narrate between script calls

After each script completes, tell the user what you found before running the next one:

- "Found 347 conversations spanning 2023–2026. Extracting saved memory now..."
- "ChatGPT remembered 12 facts about you across 4 fields. Building the preview..."
- "Writing 8 high-confidence items to active memory. Next: archive enrichment..."
- "Dispatching 4 mining agents across 200 conversations..."

### Report stats

Surface concrete numbers whenever you have them:
- total conversation count
- saved-memory field counts
- how many items written vs held for review
- mining progress (conversations scanned, findings per chunk)

### Use --progress on scripts

All long-running scripts support `--progress` which prints status to stderr. Use it for large archives so the user sees work happening even during script execution.

## Workflow

### 0. Locate the export

ChatGPT exports are typically named with a long hash and timestamp, e.g.:
`8a8f3ee0...-2026-03-31-18-41-51-e0dc362a....zip`

Common locations:
- `~/Downloads/` (most common — this is where the browser saves it)
- Desktop or a custom export folder

If the user doesn't know the exact path, glob for zip files in Downloads:

```bash
ls -t ~/Downloads/*.zip | head -20
```

Downloads folders are often crowded. ChatGPT exports follow a distinctive pattern — look for filenames matching `[8+ hex chars]-YYYY-MM-DD-*`. A quick filter:

```bash
ls ~/Downloads/*.zip | grep -E '[0-9a-f]{8}.*-[0-9]{4}-[0-9]{2}-[0-9]{2}-'
```

If still ambiguous, check whether the zip contains `conversations-*.json` entries:

```bash
unzip -l <candidate.zip> | grep conversations-
```

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

### 2. Extract and preview in one step

Use the preview builder directly on the zip — it runs the extraction internally:

```bash
python3 scripts/build-memory-preview.py <export.zip>
python3 scripts/build-memory-preview.py <export.zip> --output /tmp/chatgpt-memory-preview.md
python3 scripts/build-memory-preview.py <export.zip> --progress
```

This combines what was previously two steps (extract → preview) into one. It pulls the highest-signal onboarding inputs from the entire export:
- `about_user_message`
- `about_model_message`
- `user_profile`
- `user_instructions`

And categorises them into:
- **Active memory candidates** — what should be in-context every turn
- **Runtime context** — timezone, location, current date (skip these)
- **Historical/progressive candidates** — older versions, previous profiles
- **Contradictions** — fields with multiple versions that need review

If you need the raw extraction JSON separately (e.g. for subagent dispatch or audit), use `extract-saved-memory.py` directly:

```bash
python3 scripts/extract-saved-memory.py <export.zip> --json --output /tmp/chatgpt-saved-memory.json
```

**Note:** For users with simple ChatGPT profiles (e.g. just a name and one-liner), the preview mostly reformats what's already obvious. In those cases, read the preview output and go straight to writing memory. The preview is most valuable when the profile has contradictions, multiple historical versions, or a mix of durable and runtime context.

### Merging with existing memory

If `system/human.md` or `system/persona.md` already has content, **you are merging, not replacing**.

**Anti-pattern:** Reading the existing block, then doing a `str_replace` that swaps the entire content for a new version. This is overwriting, even if you read first. The existing content was written by the user or a previous session — it has context you don't have. Don't throw it away.

**Correct pattern:** Use targeted `str_replace` calls that add new lines or sections to the existing file. Concretely:

1. Read the existing block (it's already in your system prompt)
2. Identify what's **missing** — facts from ChatGPT that the existing block doesn't cover
3. Use `str_replace` to insert the missing facts into the appropriate section, or append a new section at the end
4. **Never replace a line that already exists** unless the ChatGPT data is explicitly newer and contradicts it

Example — if `system/human.md` already says "Works at Letta" and ChatGPT saved memory says "Works at Letta on agent infrastructure", the merge is:
```
str_replace "Works at Letta" → "Works at Letta on agent infrastructure"
```
Not: replace the entire file with a rewritten version.

If the existing block is empty or minimal (just the default template), a full write is fine. The merge discipline applies when there's existing content worth preserving.

### Serialise memory writes

**Do not create or update multiple memory files in parallel.** The memory tool can hit race conditions when called concurrently, producing spurious errors even when the writes succeed. This makes it hard to know what actually landed.

Write memory files one at a time. The speed difference is negligible — memory writes are fast. The reliability difference is not.

### Safe write targets and memory structure

Before writing memory, inspect `system/` and the relevant reference directories.

Important MemFS rule:
- **Never create overlapping file/folder paths** such as `system/human.md` and `system/human/...` or `system/persona.md` and `system/persona/...`.

Write targets (all imports should produce at least the first two):
- `system/human.md` — condensed durable user facts and collaboration preferences that should be in-context every turn
- `reference/chatgpt/import-YYYY-MM-DD.md` — **always create** — import audit trail, exclusions, uncertainty notes, source path
- `reference/chatgpt/work-and-technical-background.md` — create when historical work context is found
- `reference/chatgpt/collaboration-preferences.md` — create when detailed interaction/style patterns are found
- `reference/chatgpt/transcripts/` — curated transcript exports for fidelity/auditability

If `system/human.md` already exists, update that file instead of inventing a sibling folder.
If `system/persona.md` already exists, update that file instead of inventing a sibling folder.

Use progressive disclosure aggressively: keep active memory small, and link outward with `[[reference/chatgpt/...]]` paths so future agents can discover the archive.

### 3. Write memory — active AND progressive

This step writes to **both** `system/` and `reference/chatgpt/`. Not just active memory. The progressive memory layer is where the import's long-term value lives — without it, historical context, audit trails, and collaboration preferences are lost.

#### 3a. Active memory (`system/human.md`)

Write immediately when the fact is explicit, current, and low-sensitivity:
- name and stable identity basics
- current role or project context
- explicit response preferences from hidden saved memory
- repeated formatting preferences
- collaboration preferences like directness, question volume, anti-sycophancy

Keep `system/human.md` compact. Only what should be in-context every turn.

#### 3b. Import audit file (`reference/chatgpt/import-YYYY-MM-DD.md`)

**Always create this file.** It records what happened during the import:
- export path and conversation count
- what was written to active memory and why
- what was excluded and why
- contradictions found and how they were resolved
- what still needs confirmation
- source of each decision (which saved-memory field, which conversation index)

This is the receipt. Future agents can read it to understand where the memory came from.

#### 3c. Progressive memory files

Create these when the preview or enrichment surfaces material that doesn't belong in `system/` but is worth keeping:

- **`reference/chatgpt/work-and-technical-background.md`** — historical roles, past projects, technical background, older work context that's useful for understanding the user but not needed every turn
- **`reference/chatgpt/collaboration-preferences.md`** — detailed interaction patterns, formatting preferences, correction patterns, anti-patterns — anything too granular for `system/human.md` but valuable when the agent needs to calibrate tone or style

If the preview shows historical alternatives (older saved-memory versions, previous profiles), those go here too.

#### 3d. Link progressive files from active memory

After creating progressive memory files, add `[[reference/chatgpt/...]]` links in `system/human.md` so future agents can discover them. Example:

```
See also: [[reference/chatgpt/work-and-technical-background.md]], [[reference/chatgpt/collaboration-preferences.md]]
```

#### Writing pattern

For each write:
1. keep it small and specific
2. tell the user what you wrote and where
3. tell the user what you are reviewing next
4. continue

### 4. Optional archive enrichment

Only after the saved-memory clone is handled, optionally mine broader conversation history for:
- work/project context
- collaboration patterns
- historical background
- other durable facts the user wants preserved

#### Confirm before exhaustive mining

Archive enrichment dispatches subagents — potentially many of them. For a 500-conversation archive, that's ~10 parallel agents. **Always confirm with the user before starting**, and tell them what it will cost in concrete terms:

- How many conversations will be mined
- How many subagents will be dispatched
- That this is the expensive part of the import

Use AskUserQuestion with options like:
- **Full archive mining** — "Mine all N conversations (~X subagents). Most thorough, most expensive."
- **Targeted mining** — "Mine conversations matching specific topics you care about. Cheaper, still good coverage."
- **Skip enrichment** — "The saved-memory clone already captured the essentials. Stop here."

Do not automatically dispatch subagents just because the user selected "full history mining" at intake. The intake scope question establishes *willingness*; this checkpoint confirms the *specific cost* now that you know the archive size.

For small archives (under 50 conversations), mine directly — no subagents needed, no confirmation needed:

```bash
python3 scripts/render-conversation.py <export.zip> --index 12 --output /tmp/chatgpt-12.md
```

For archives of 50+ conversations, **use parallel chunk-based mining** (see below).

#### Topic-based filtering

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

Use content search with `--role user` to focus on what the user actually said:

```bash
python3 scripts/search-conversations.py <export.zip> --query "not doing" --query "no longer" --query "forget that" --query "remove from memory" --role user
python3 scripts/search-conversations.py <export.zip> --query "used to" --query "don't assume" --role user --json --limit 20
```

Typical signals:
- the user says a project is no longer active
- the user says to forget or remove old context
- the user says a role, employer, affiliation, or plan is outdated

When old context conflicts with a newer explicit correction, prefer the newer correction.

### 5. Validate with /doctor

After the import completes — whether it was a simple saved-memory clone or a full archive enrichment — **run `/doctor`**. This is not optional. It validates:
- memory structure integrity
- no overlapping file/folder paths
- prompt hygiene
- block size sanity

If /doctor flags issues, fix them before declaring the import complete.

### 6. Transcript preservation

Transcript preservation happens **during mining**, not as a separate step afterward. When you or a subagent encounter a high-signal conversation, store it immediately — don't queue it up as a question for later.

**Anti-pattern:** Do not collect transcript candidates during mining and then present them as a menu ("Which transcripts do you want me to export?"). This forces the user to make decisions about conversations they haven't read. Instead, store high-signal transcripts as you find them, mention what you stored in your progress narration, and move on. The user can always delete what they don't want — that's easier than re-mining what wasn't stored.

#### Store automatically (don't ask)

Preserve a conversation when it contains:
- **Career transitions or major life decisions** — role changes, company moves, pivots. These are the user's own narration of their trajectory and are rarely redundant with memory blocks.
- **Deep technical design discussions** — architecture decisions, system design, research methodology. The nuance matters and can't be distilled to a bullet point.
- **Detailed project context** — goals, constraints, collaborators, timelines for projects the user worked on seriously.
- **Explicit preference statements in context** — not just "be direct" but the full exchange where they explained *why* and *when* they want directness.

For these, **summarize** into a 2–5 paragraph reference file at `reference/chatgpt/transcripts/NNN-slug.md`. Include a frontmatter description so the file is discoverable. Only use verbatim export when fidelity genuinely matters (exact decisions, nuanced technical context where summarizing would lose signal).

#### Ask before storing

- Conversations focused on health/mental health specifics, intimate relationship dynamics, or financial details
- Conversations where the signal is genuinely ambiguous (might be useful, might be noise)

#### Don't store

- Conversations already fully captured by memory blocks
- One-off tasks with no durable context
- Conversations that are mostly assistant output with little user input

#### How subagents handle transcripts

Subagents should store transcripts during their mining pass, not report candidates back. The subagent prompt already assigns them `reference/chatgpt/transcripts/` as a write target. When a subagent encounters a high-signal conversation in its chunk, it should:
1. Write a summarized reference file to `reference/chatgpt/transcripts/NNN-title-slug.md`
2. Note in its chunk summary that it preserved the transcript and why
3. Continue mining

The primary agent does **not** need to approve each transcript. The subagent's judgment is sufficient for the "store automatically" category above.

#### Bulk archival export

For users who want maximum fidelity or a complete archival copy, use `export-transcripts.py`:

```bash
python3 scripts/export-transcripts.py <export.zip> \
  --indexes 229,288 \
  --output-dir /tmp/chatgpt-transcripts \
  --skip-empty-hidden \
  --compact-nontext
```

This is a separate archival feature, not the default. Most imports should use the selective summarization pattern above.

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

### Store by default

Personal details are part of knowing the user. Store them:
- family members' names, pets, hobbies, interests
- life circumstances, where they live, background
- personality traits, communication style
- personal projects, side interests, goals
- relationship status, partner's name (the fact of it, not the dynamics)

The user imported their ChatGPT memory because they want to be known. Don't exclude context they expected the agent to have.

### Ask before storing

Stop and confirm only for material with real consequences if mishandled:
- **Health/mental health specifics** — diagnosis, medication, treatment details (not "handle sensitively" flags, which are fine to store)
- **Intimate relationship dynamics** — not "has a partner named X" but conflict details, emotional specifics
- **Financial specifics** — debt, income, specific amounts
- **Contradictions** where the current truth is unclear

The intake question about sensitivity ("anything I should avoid storing?") is the user's chance to set boundaries. If they don't flag anything, store personal details by default.

## Parallel mining with subagents

For archives of **50+ conversations**, use chunk-based parallel mining instead of processing everything sequentially. This is the default enrichment strategy for non-trivial archives.

### How it works

1. **Primary agent** handles the explicit saved-memory clone (steps 0–3 of the workflow)
2. **Primary agent** partitions the remaining archive into chunks of ~30–50 conversations
3. **Primary agent** dispatches one `general-purpose` subagent per chunk
4. **Each subagent**:
   - Renders its assigned conversations using `render-range.py` or individual `render-conversation.py` calls
   - Extracts durable facts, preferences, project context, and retractions
   - Writes findings directly to its assigned memory path (e.g. `reference/chatgpt/mining/chunk-NNN.md`)
   - May write curated transcripts to `reference/chatgpt/transcripts/` if warranted
   - Returns a summary separating safe-to-promote and proposal-only findings
5. **Primary agent**:
   - Reads all chunk summaries from `reference/chatgpt/mining/`
   - Merges high-confidence findings into `system/human.md`
   - Resolves contradictions across chunks
   - Runs `/doctor` to validate the resulting memory structure

### Subagent design rules

- **Give each subagent the full script paths** — they don't inherit your skill knowledge
- **Limit scope to 30–50 conversations per subagent** — more risks context overflow or timeouts
- **Use `general-purpose` subagent type** — these subagents need to run scripts via Bash
- **Partition output paths up front** — each subagent owns a non-overlapping destination
- **Allow direct progressive-memory writes** — subagents write to `reference/chatgpt/mining/chunk-NNN.md` and `reference/chatgpt/transcripts/` directly
- **Keep active-memory writes coordinated** — only the primary agent merges into `system/human.md` / `system/persona.md`
- **Subagents must not modify existing memory files** — they create new files only (`reference/chatgpt/mining/chunk-NNN.md`, `reference/chatgpt/transcripts/NNN-slug.md`). They must never read, edit, or overwrite anything in `system/` or any pre-existing file in `reference/`
- **Always provide a fallback plan** — if a subagent fails, mine its chunk directly using `list-conversations.py --title-contains` followed by targeted `render-conversation.py` calls

### Subagent prompt template

Keep it compact. The subagent needs: export path, script paths, chunk range, output paths, and what to extract. Everything else is overhead.

```
Mine conversations [START]-[END] from [EXPORT_PATH] for durable memory.

Render: python3 [SCRIPTS_DIR]/render-range.py "[EXPORT_PATH]" --start-index [START] --end-index [END] --output-dir /tmp/chatgpt-chunk-[N] --skip-empty-hidden --compact-nontext --skip-thoughts --progress

Read each rendered conversation. Extract: user facts, project/work context, collaboration preferences, explicit retractions ("forget this", "no longer", "not doing").

Write findings to [MEMORY_DIR]/reference/chatgpt/mining/chunk-[NNN].md with sections:
- Safe to promote (high-confidence, explicit, current, low-sensitivity)
- Proposal only (historical, uncertain, sensitive, contradictory)
- Retractions (older context the user said to forget)

High-signal conversations (career transitions, deep technical design, detailed project context, explicit preference discussions) → summarize into [MEMORY_DIR]/reference/chatgpt/transcripts/NNN-title-slug.md. Do this during mining, not after. Use 2-5 paragraph summaries, not verbatim transcripts. Include frontmatter with a description.

IMPORTANT: Only create NEW files. Do not read, edit, or overwrite any existing files in the memory directory. Do not touch system/.
```

### When subagents fail

Subagents can fail silently due to timeouts or context limits. If a mining subagent fails:
1. Don't retry with the same broad scope
2. Use `list-conversations.py --title-contains` directly to find relevant conversations
3. Render 3–5 of the highest-signal ones yourself
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

Use when you need the raw extraction JSON (e.g. for subagent dispatch or audit).

It extracts and deduplicates:
- `about_user_message`
- `about_model_message`
- `user_profile`
- `user_instructions`

It also reports first/last seen timestamps and source samples.

Supports:
- `--json`
- `--output`
- `--progress`

### `scripts/build-memory-preview.py`

The primary extraction + categorisation tool. Accepts either a zip file (runs extraction internally) or the JSON output from `extract-saved-memory.py`.

It separates:
- likely active-memory candidates
- historical/progressive-memory candidates
- runtime-only context
- contradictions / review items

Supports:
- `--json`
- `--output`
- `--progress`
- Direct zip input (one-step: extract + preview)
- JSON input (two-step: preview from existing extraction)

### `scripts/render-conversation.py`

Use for deep review of one conversation. Efficiently streams to the target conversation instead of loading the entire archive.

Useful mining flags:
- `--skip-thoughts`
- `--skip-empty-tool-messages`
- `--user-only`
- `--assistant-only`

### `scripts/render-range.py`

Use for batch rendering during archive enrichment. Opens the zip once and renders all conversations in-process — no subprocess per conversation.

Supports:
- `--output-dir` (one file per conversation) or `--concat-output` (single file)
- `--progress` (prints rendering progress to stderr)
- Same noise-reduction flags as `render-conversation.py`

### `scripts/search-conversations.py`

Use when title search is not enough.

Good fits:
- stale-context / retraction sweeps
- finding buried project mentions inside generic titles
- locating "forget this" / "not doing this anymore" corrections
- searching for specific phrases before choosing which conversations to render

Supports:
- `--role user|assistant|tool|system` — filter which message roles to search (repeatable)
- `--progress` — print search progress to stderr
- `--json`

### `scripts/export-transcripts.py`

Use for optional high-fidelity archival exports.

Supports:
- selected indexes or ranges
- transcript chunking
- optional memory-style frontmatter
- a generated transcript index file

## Final user-facing summary

At the end of a run, lead with a **narrative snapshot** — a short, natural-language paragraph of what you now know about the user. This is more engaging than a categorical list and lets the user immediately see whether the import landed correctly.

Then follow with the structured breakdown:

1. **Snapshot** — "Here's what I know about you now" in 3–5 sentences, written as if you're introducing yourself to future-you
2. **What ChatGPT explicitly remembered** — the raw saved-memory fields
3. **What got cloned into active Letta memory** — what's now in `system/`
4. **What was preserved as progressive memory** — what's in `reference/chatgpt/`
5. **What was excluded and why**
6. **What still needs confirmation**
7. **Results of the /doctor validation**

The snapshot is the part the user actually reads. The rest is for auditability.

## Export structure reference

A ChatGPT export zip typically contains:
- `conversations-000.json`, `conversations-001.json`, etc. (sharded conversation history)
- `shared_conversations.json`
- `user.json`, `user_settings.json` (account metadata — usually audit material, not active memory)
- `export_manifest.json`
- images, audio, and other attachments

The `mapping` field in each conversation is a graph, not a flat message array. The scripts handle this — you don't need to parse it manually.

If the user needs help obtaining their export: <https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data>

## References

- `references/memory-import-workflow.md` — condensed checklist for the import workflow
