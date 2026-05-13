---
name: letta-filesystem-to-memfs
description: Migrates deprecated Letta Filesystem folders/files to MemFS using markdown document corpora, chunking, local lexical search, and QMD semantic search via the memfs-search skill. Use when replacing folders.files.upload, working with PDFs or document QA, or emulating open_file, grep_file, and search_file behavior.
license: MIT
---

# Letta Filesystem to MemFS

Use this skill when a user wants the old Letta Filesystem behavior: upload documents, chunk them, attach them to an agent, and let the agent search/open them.

MemFS is not the same product. It is git-backed markdown memory. To mimic the old workflow, use the bundled CLI:

1. Extract PDFs/docs to markdown text.
2. Chunk the text into stable markdown files under `documents/<corpus>/<doc>/chunks/`.
3. Write a small pinned index under `system/filesystem/<corpus>.md`.
4. Index only the corpus chunk files in QMD for semantic search.
5. Review the MemFS git diff. Commit only if asked.

## Quick workflow

```bash
# Set this to the skill directory shown in the skill load header.
SKILL_DIR="/path/to/letta-filesystem-to-memfs"

# From any directory. MEMORY_DIR should point at the target agent's memfs repo.
uv run --with pymupdf \
  "$SKILL_DIR/scripts/letta_fs_to_memfs.py" ingest \
  --memory-dir "$MEMORY_DIR" \
  --corpus product-docs \
  --source ./docs/ \
  --source ./guide.pdf \
  --source https://arxiv.org/pdf/2310.08560

cd "$MEMORY_DIR"
git status --short
git diff --stat
```

Search the chunk corpus lexically:

```bash
uv run "$SKILL_DIR/scripts/letta_fs_to_memfs.py" search \
  --memory-dir "$MEMORY_DIR" \
  --corpus product-docs \
  "memory hierarchy" \
  -n 5
```

Semantic search with QMD. The CLI creates a corpus-scoped QMD collection over chunk files only:

```bash
uv run "$SKILL_DIR/scripts/letta_fs_to_memfs.py" qmd setup \
  --memory-dir "$MEMORY_DIR" \
  --corpus product-docs

uv run "$SKILL_DIR/scripts/letta_fs_to_memfs.py" qmd query \
  --memory-dir "$MEMORY_DIR" \
  --corpus product-docs \
  "memory hierarchy" \
  -n 5
```

Use `qmd reindex` after changing corpus files, and `qmd search` / `qmd vsearch` when you specifically want keyword-only or vector-only search.

## Layout

The ingest script writes:

```txt
system/filesystem/<corpus>.md
  Pinned index and operating instructions for the corpus.

documents/<corpus>/manifest.md
  Corpus manifest.

documents/<corpus>/<doc-slug>/manifest.md
  Per-document metadata and chunk table.

documents/<corpus>/<doc-slug>/chunks/chunk-0001.md
  Chunk content with frontmatter metadata.

documents/<corpus>/chunks.jsonl
  Machine-readable chunk export for custom indexing or debugging.
```

## Old API mapping

| Old Filesystem | MemFS mimic |
|---|---|
| `folders.create` | `--corpus <name>` creates `documents/<corpus>/` |
| `folders.files.upload` | `letta_fs_to_memfs.py ingest --source <file-or-directory-or-url>` |
| OCR/chunk/embed job | Extract + chunk locally; `qmd setup` / `qmd reindex` for semantic search |
| `agents.folders.attach` | Enable MemFS, then review and sync repo changes when appropriate |
| `open_file` | Read chunk markdown files by path |
| `grep_file` | `rg` or `letta_fs_to_memfs.py search` |
| `search_file` | `letta_fs_to_memfs.py qmd query` over the corpus chunk collection |

## Heuristics

- Use `system/filesystem/<corpus>.md` for the small always-visible index only.
- Do not pin full documents into `system/`; it will bloat the prompt.
- Keep chunks outside `system/`, usually under `documents/<corpus>/...`.
- Passing a directory to `--source` recursively ingests supported files (`.pdf`, `.md`, `.txt`, `.json`, `.csv`, `.html`, `.xml`).
- Use `--glob` / `--exclude` for messy directories. Defaults exclude `.git`, `node_modules`, `.venv`, and `__pycache__`.
- URL downloads default to `--max-download-mb 100`; set `0` for unlimited.
- Re-ingesting the same document slug replaces that document's old chunk directory, so stale chunks do not survive chunk-size changes.
- Use chunk sizes around 2,000-4,000 characters with 200-500 character overlap.
- Use the CLI's `qmd` subcommands when the user needs semantic search over many chunks.
- Preserve source URLs, checksums, page markers, chunk numbers, and corpus names in the generated files.

## CLI reference

```bash
uv run --with pymupdf "$SKILL_DIR/scripts/letta_fs_to_memfs.py" ingest --help
uv run "$SKILL_DIR/scripts/letta_fs_to_memfs.py" search --help
uv run "$SKILL_DIR/scripts/letta_fs_to_memfs.py" qmd setup --help
uv run "$SKILL_DIR/scripts/letta_fs_to_memfs.py" qmd query --help
```

Compatibility wrappers remain for older examples:

```bash
uv run --with pymupdf "$SKILL_DIR/scripts/ingest_documents.py" --memory-dir "$MEMORY_DIR" --corpus docs --source ./docs
uv run "$SKILL_DIR/scripts/search_corpus.py" --memory-dir "$MEMORY_DIR" --corpus docs --query "refund policy"
```

## PDF notes

The ingest script uses PyMuPDF when it sees a PDF. Run it with `uv run --with pymupdf ...`.

For scanned PDFs or complex tables, use the `tools/extracting-pdf-text` skill first, then ingest the extracted markdown/text file with this skill.

See `references/design.md` for design notes and edge cases.
