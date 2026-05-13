# Design notes

## Why not write full PDFs into `system/`?

Everything in `system/` is pinned into the agent prompt. Full PDFs there recreate the old context-overflow problem. Keep only a corpus index in `system/` and store chunks outside `system/`.

## Semantic search

The deprecated Filesystem did automatic embeddings for `search_file`. MemFS does not embed documents by itself. Use the bundled CLI's QMD subcommands to index generated markdown chunks locally.

Recommended search stack:

- `rg` or `search_corpus.py` for exact terms and grep-like workflows.
- `letta_fs_to_memfs.py qmd search` for QMD keyword lookup over one corpus.
- `letta_fs_to_memfs.py qmd vsearch` for semantic lookup over one corpus.
- `letta_fs_to_memfs.py qmd query` for hybrid keyword + vector retrieval over one corpus.

Only use an external vector DB if the product needs server-side search outside the agent's local MemFS checkout.

## QMD collection strategy

The CLI creates one QMD collection per `(memory_dir, corpus)` pair. The default collection name is deterministic:

```txt
memfs-<corpus>-<hash8(memory_dir)>
```

The collection mask only indexes chunk files:

```txt
documents/<corpus>/**/chunks/*.md
```

This avoids the noisy behavior of indexing manifests, pinned system indexes, and unrelated memory files. Use `--collection` only when you need a custom stable name.

The CLI also hardens QMD runtime launch by unsetting `BUN_INSTALL` and preferring the Node binary next to the `qmd` executable. This avoids Bun sqlite extension failures and broken Homebrew Node installs.

## Frontmatter rules

MemFS markdown files should include YAML frontmatter. Safe keys:

- `description`
- `limit`
- `metadata`
- `read_only` only if set by server/user; do not invent it during migration.

## Recommended corpus strategy

For each old folder:

1. Create one corpus with the old folder name.
2. Ingest the old folder path directly with `--source /path/to/folder`, or pass individual files/URLs.
3. Push MemFS changes.
4. Run `letta_fs_to_memfs.py qmd setup` so QMD indexes the generated markdown chunks.
5. Update the application or agent workflow to query QMD/grep over MemFS and read relevant chunk files by path.

Re-ingesting a document with the same slug replaces that document's chunk directory. This prevents stale chunks from surviving after chunk-size changes or improved extraction.

## Useful CLI patterns

Ingest a directory but only PDFs and markdown:

```bash
uv run --with pymupdf scripts/letta_fs_to_memfs.py ingest \
  --memory-dir "$MEMORY_DIR" \
  --corpus product-docs \
  --source ./docs \
  --glob "**/*.pdf" \
  --glob "**/*.md"
```

Skip generated/vendor folders:

```bash
uv run --with pymupdf scripts/letta_fs_to_memfs.py ingest \
  --memory-dir "$MEMORY_DIR" \
  --corpus product-docs \
  --source ./docs \
  --exclude "**/vendor/**" \
  --exclude "**/dist/**"
```

QMD lifecycle:

```bash
uv run scripts/letta_fs_to_memfs.py qmd setup --memory-dir "$MEMORY_DIR" --corpus product-docs
uv run scripts/letta_fs_to_memfs.py qmd reindex --memory-dir "$MEMORY_DIR" --corpus product-docs
uv run scripts/letta_fs_to_memfs.py qmd query --memory-dir "$MEMORY_DIR" --corpus product-docs "refund policy"
```
