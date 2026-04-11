---
name: memfs-search
description: Semantic search over agent memory files. Use when you need to find conceptually related memory blocks, discover forgotten reference files, check what you already know before creating new memory, or search beyond exact keyword matching. Currently supports QMD (local, no API keys).
---

# MemFS Search

Semantic search over your memory filesystem. Useful when Grep isn't enough — finding conceptually related blocks, discovering forgotten reference files, or answering "what do I know about X" across all memory.

## Setup

First time only. Run the setup script to create the index and generate embeddings:

```bash
bash <SKILL_DIR>/scripts/memfs-search.sh setup
```

This creates a QMD collection over `$MEMORY_DIR`, adds context annotations, and embeds all `.md` files. First run downloads ~2GB of local GGUF models to `~/.cache/qmd/models/`.

For installation, embedding model options, and troubleshooting: [references/qmd-setup.md](references/qmd-setup.md).

## Searching

Three tiers. Pick based on what you know about your query:

| You have... | Use | Command | Speed |
|-------------|-----|---------|-------|
| An exact term or phrase | **keyword** | `search` | ~0.3s |
| A vague concept ("what do I know about X") | **semantic** | `vsearch` | ~2s cold, <1s warm |
| No idea, need the best results | **hybrid** | `query` | ~3s cold, <1s warm |

```bash
S="bash <SKILL_DIR>/scripts/memfs-search.sh"

# Keyword — fast, use first
$S search "lettabot architecture"

# Semantic — conceptual, use when keyword misses
$S vsearch "how does the user feel about code reviews"

# Hybrid — best quality, uses keyword + vectors + reranking
$S query "projects cameron is working on"
```

**Always start with keyword search.** Only escalate when it misses. Hybrid is 10x slower than keyword.

### Output Formats

All commands accept output flags forwarded to QMD:

```bash
$S search "topic" --json       # structured (for processing)
$S search "topic" --files      # file paths only (pipe into Read)
$S search "topic" --full       # full document, not snippet
$S search "topic" -n 15        # more results (default: 5)
```

`--json` returns an array of objects with `file`, `score`, `snippet`, and `context` fields.

### Retrieval

Fetch a specific file or batch of files without searching:

```bash
# Single file
qmd get "system/human/identity.md" -c memory --full

# Batch by glob
qmd multi-get "reference/projects/*" -c memory
```

## When to Search Proactively

Don't wait to be asked. Search memory when:

1. **Before creating a new memory file** — check if the topic already exists. `$S search "topic" --files` tells you instantly.
2. **User asks "do you know about X"** — search before saying no. Reference files you haven't loaded recently might have it.
3. **During `/init` or memory reorg** — verify coverage. Search for key concepts and confirm they're stored somewhere.
4. **Debugging "I told you about this"** — the user thinks you should know something. Search memory before falling back to message history.

## Maintenance

After bulk memory changes (e.g. after `/init`, reorganization, creating many files):

```bash
bash <SKILL_DIR>/scripts/memfs-search.sh reindex
```

Check index health:

```bash
bash <SKILL_DIR>/scripts/memfs-search.sh status
```

## When NOT to Use

- Exact string matching — use Grep.
- Finding files by name/pattern — use Glob.
- Reading a file you already know the path to — use Read.
- Searching message history — use the `searching-messages` skill.
- The query is a single word that would match literally — keyword Grep is faster.
