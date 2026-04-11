# QMD Setup

## Install

```bash
# Node.js (recommended)
npm install -g @tobilu/qmd

# Or Bun
bun install -g @tobilu/qmd

# Or run without installing
npx @tobilu/qmd ...
```

Requires Node.js >= 22. On macOS, also needs Homebrew SQLite (`brew install sqlite`).

## First-Time Indexing

```bash
# Create collection pointing at your memory directory
qmd collection add "$MEMORY_DIR" --name memory --mask "**/*.md"

# Add context to improve search relevance
qmd context add qmd://memory "Agent memory blocks — system prompt files and reference materials"
qmd context add qmd://memory/system "In-context memory blocks rendered in the system prompt every turn"
qmd context add qmd://memory/reference "Reference materials loaded on-demand via tools"

# Generate vector embeddings (downloads ~2GB of GGUF models on first run)
qmd embed
```

First `qmd embed` downloads three local models (~2GB total) to `~/.cache/qmd/models/`. Subsequent runs are fast.

## Embedding Models

QMD embeds locally using bundled GGUF models. No API keys needed.

| Model | Env/Flag | Size | Notes |
|-------|----------|------|-------|
| embeddinggemma-300M | default | ~328MB | English-optimized, small footprint |
| Qwen3-Embedding-0.6B | `QMD_EMBED_MODEL` | ~640MB | Multilingual (119 languages) |

```bash
# Switch to Qwen3 for multilingual support
export QMD_EMBED_MODEL="hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
qmd embed -f  # re-embed with new model (vectors aren't cross-compatible)
```

No cloud embedding providers (OpenAI, etc.) are supported yet. Gemini support is in-progress upstream (tobi/qmd#365).

**Important**: When switching embedding models, always re-embed with `qmd embed -f` — vectors from different models are not compatible.

## Verify

```bash
qmd status
qmd search "test query" -c memory
```

## Re-Indexing

Run after bulk memory changes (e.g. after `/init`, memory reorganization, or creating many new files):

```bash
qmd update && qmd embed
```

## Troubleshooting

**"No collections configured"**: Run `qmd collection add "$MEMORY_DIR" --name memory`

**Slow first search**: Models are loading into memory. Subsequent searches are fast. Use `qmd mcp --http --daemon` for a persistent server.

**SQLite errors / sqlite-vec crash on macOS**: `brew install sqlite` and retry. If `BUN_INSTALL` is set in your env, QMD's launcher will use Bun instead of Node — Bun's SQLite doesn't support extension loading. Fix: `unset BUN_INSTALL` before running QMD, or install via npm (not bun).
