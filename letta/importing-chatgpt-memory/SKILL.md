---
name: importing-chatgpt-memory
description: Formats conversations from a ChatGPT export into readable markdown documents so an agent can inspect them before writing durable memory. Use when migrating memory from ChatGPT exports, reviewing hidden saved-memory/context blocks, or mining conversation history for durable facts.
license: MIT
---

# Importing ChatGPT Memory

Format ChatGPT conversations into long markdown documents, read them, and only then decide what belongs in Letta memory.

## When to use

Use this skill when a user wants a Letta agent to learn from a ChatGPT export without blindly importing the whole archive.

Good fits:
- migrate ChatGPT memory into Letta
- inspect hidden saved profile / custom-instruction context
- mine old conversations for durable facts and preferences
- review a large export in parallel before writing memory files

## Core rule

Keep the workflow procedural.

Do **not** build a large parser or an auto-import pipeline. Instead:
1. inspect the export
2. render the relevant conversation(s)
3. read the markdown
4. separate durable memory from noise
5. propose updates
6. write memory only after review

## Need an export first?

If the user has not exported their ChatGPT data yet, send them to OpenAI’s official help article:

- <https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data>

Link to the official doc instead of restating the export steps in detail, since the workflow may change.

## Workflow

### 1. Inspect the export

These examples assume the skills repo is cloned into `.skills/` in the current project, as described in this repo's README.

List conversations first:

```bash
python3 .skills/letta/importing-chatgpt-memory/scripts/list-conversations.py <export.zip>
python3 .skills/letta/importing-chatgpt-memory/scripts/list-conversations.py <export.zip> --title-contains memory
python3 .skills/letta/importing-chatgpt-memory/scripts/list-conversations.py <export.zip> --start-index 200 --end-index 260
```

Use this step to find the right title, date range, and conversation indices.

### 2. Render one conversation

Render a single conversation when you want to inspect it closely:

```bash
python3 .skills/letta/importing-chatgpt-memory/scripts/render-conversation.py <export.zip> --index 12 --output /tmp/chatgpt-12.md
```

Useful cleanup flags:

```bash
python3 .skills/letta/importing-chatgpt-memory/scripts/render-conversation.py <export.zip> \
  --index 12 \
  --skip-empty-hidden \
  --compact-nontext \
  --output /tmp/chatgpt-12.md
```

Use `--skip-empty-hidden` when the transcript is cluttered with empty hidden system placeholders.
Use `--compact-nontext` when image/file metadata blobs are drowning out the human-readable conversation.

### 3. Render a batch or partition

When the export is large, render a range procedurally instead of inventing a parser framework:

```bash
python3 .skills/letta/importing-chatgpt-memory/scripts/render-range.py <export.zip> \
  --start-index 220 \
  --end-index 274 \
  --output-dir /tmp/chatgpt-range \
  --skip-empty-hidden \
  --compact-nontext
```

Or create one concatenated markdown document:

```bash
python3 .skills/letta/importing-chatgpt-memory/scripts/render-range.py <export.zip> \
  --start-index 220 \
  --end-index 274 \
  --concat-output /tmp/chatgpt-range.md \
  --skip-empty-hidden \
  --compact-nontext
```

## Hidden context to watch for

Recent ChatGPT exports often carry the clearest explicit saved memory in hidden system/context messages.

Common fields:
- `metadata.is_user_system_message`
- `metadata.is_visually_hidden_from_conversation`
- `metadata.user_context_message_data.about_user_message`
- `metadata.user_context_message_data.about_model_message`

Read these blocks carefully. They often contain the strongest explicit memory signal in the whole export.

## After reading the rendered markdown

Separate findings into two buckets:

### Put in active memory
- stable identity facts
- durable response preferences
- recurring work/project context
- long-lived tool/workflow preferences
- facts the user clearly wants remembered going forward

### Keep in audit/import files only
- stale historical identities
- one-off moods or temporary plans
- sensitive material that is not necessary for future collaboration
- bulky evidence excerpts and raw transcript detail

Default to **proposal-first** behavior. Summarize what seems durable, call out uncertainty, and ask before broad imports.

## Working at scale

If the archive is large:
- split by conversation range or shard
- use `Task` with cheap subagents
- have each subagent render and review a disjoint partition
- merge only high-confidence findings into system memory

## Scripts

### `scripts/list-conversations.py`

List conversations with:
- global index
- timestamps
- visible message count
- hidden-context count
- title

Use this before rendering anything.

### `scripts/render-conversation.py`

Render one conversation into long markdown.

Default behavior:
- follow the current branch in the conversation graph
- include hidden context
- include `user_context_message_data`
- preserve message order and timestamps

Useful optional cleanup:
- `--skip-empty-hidden`
- `--compact-nontext`

### `scripts/render-range.py`

Render a range of conversations either:
- into one markdown file per conversation, or
- into one concatenated markdown document

Use this for partitioned review and subagent workflows.

## References

- Read `references/chatgpt-export-notes.md` for export structure and hidden-context quirks.
- Read `references/memory-import-workflow.md` when deciding what belongs in active Letta memory versus an audit/import file.
