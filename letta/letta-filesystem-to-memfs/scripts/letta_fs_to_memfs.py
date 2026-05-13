#!/usr/bin/env python3
"""Migrate deprecated Letta Filesystem folders/files to MemFS + QMD."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {
    ".pdf",
    ".md",
    ".markdown",
    ".txt",
    ".text",
    ".json",
    ".csv",
    ".log",
    ".html",
    ".xml",
}

DEFAULT_EXCLUDES = [
    ".git/**",
    "**/.git/**",
    "node_modules/**",
    "**/node_modules/**",
    ".venv/**",
    "**/.venv/**",
    "__pycache__/**",
    "**/__pycache__/**",
]

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]{2,}")


@dataclass
class SourceDoc:
    source: str
    local_path: Path
    title: str
    slug: str
    kind: str
    sha256: str
    text: str


@dataclass
class Chunk:
    index: int
    text: str
    char_start: int
    char_end: int


@dataclass
class IngestResult:
    corpus: str
    documents: int
    chunks: int
    corpus_dir: Path
    system_index: Path | None


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\.(pdf|md|markdown|txt|text|json|csv|log|html|xml)$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80] or "document"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter(description: str, metadata: dict) -> str:
    lines = ["---", f"description: {yaml_scalar(description)}", "metadata:"]
    for key in sorted(metadata):
        lines.append(f"  {key}: {yaml_scalar(metadata[key])}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def unique_slug(base: str, used: set[str]) -> str:
    slug = slugify(base)
    candidate = slug
    i = 2
    while candidate in used:
        candidate = f"{slug}-{i}"
        i += 1
    used.add(candidate)
    return candidate


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    i = 2
    while True:
        candidate = path.with_name(f"{stem}-{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def download_source(url: str, tmpdir: Path, max_download_mb: float) -> Path:
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or "download"
    if Path(name).suffix.lower() not in SUPPORTED_SUFFIXES:
        name += ".pdf"
    dest = unique_path(tmpdir / name)
    max_bytes = int(max_download_mb * 1024 * 1024) if max_download_mb and max_download_mb > 0 else 0
    req = urllib.request.Request(url, headers={"User-Agent": "letta-fs-to-memfs/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, dest.open("wb") as f:
        length = resp.headers.get("Content-Length")
        if max_bytes and length and int(length) > max_bytes:
            raise SystemExit(f"Download too large ({int(length)} bytes > {max_bytes} bytes): {url}")
        total = 0
        while True:
            block = resp.read(1024 * 1024)
            if not block:
                break
            total += len(block)
            if max_bytes and total > max_bytes:
                raise SystemExit(f"Download exceeded --max-download-mb={max_download_mb}: {url}")
            f.write(block)
    return dest


def extract_pdf(path: Path) -> str:
    try:
        import fitz  # PyMuPDF
    except Exception as exc:
        raise SystemExit("PDF extraction requires PyMuPDF. Run with: uv run --with pymupdf scripts/letta_fs_to_memfs.py ingest ...") from exc

    parts: list[str] = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            text = re.sub(r"[ \t]+\n", "\n", text).strip()
            if text:
                parts.append(f"\n\n## Page {i}\n\n{text}")
    return "\n".join(parts).strip() + "\n"


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path), "pdf"
    if suffix in {".md", ".markdown"}:
        return path.read_text(encoding="utf-8", errors="replace"), "markdown"
    if suffix in {".txt", ".text", ".json", ".csv", ".log", ".html", ".xml"}:
        return path.read_text(encoding="utf-8", errors="replace"), suffix.removeprefix(".") or "text"

    guessed, _ = mimetypes.guess_type(path)
    if guessed and guessed.startswith("text/"):
        return path.read_text(encoding="utf-8", errors="replace"), "text"

    raise SystemExit(f"Unsupported source type for {path}. Extract it to .md/.txt first.")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def chunk_text(text: str, max_chars: int, overlap: int) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be non-negative and smaller than chunk size")

    text = normalize_text(text)
    paragraphs = re.split(r"(\n\s*\n)", text)
    units: list[str] = []
    for i in range(0, len(paragraphs), 2):
        para = paragraphs[i]
        sep = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""
        unit = para + sep
        if not unit.strip():
            continue
        if len(unit) <= max_chars:
            units.append(unit)
        else:
            start = 0
            while start < len(unit):
                units.append(unit[start : start + max_chars])
                start += max_chars

    chunks: list[Chunk] = []
    current = ""
    approx_start = 0
    consumed = 0

    def emit(buf: str, start: int) -> None:
        if not buf.strip():
            return
        idx = len(chunks) + 1
        chunks.append(Chunk(index=idx, text=buf.strip() + "\n", char_start=start, char_end=start + len(buf)))

    for unit in units:
        if current and len(current) + len(unit) > max_chars:
            if len(current.strip()) < max(200, overlap):
                current += unit
                consumed += len(unit)
                continue
            emit(current, approx_start)
            tail = current[-overlap:] if overlap else ""
            approx_start = max(0, consumed - len(tail))
            current = tail + unit
        else:
            if not current:
                approx_start = consumed
            current += unit
        consumed += len(unit)

    emit(current, approx_start)
    return chunks


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch("/" + path, pattern) for pattern in patterns)


def iter_supported_files(root: Path, include_globs: list[str], exclude_globs: list[str], use_default_excludes: bool) -> list[Path]:
    excludes = list(exclude_globs)
    if use_default_excludes:
        excludes.extend(DEFAULT_EXCLUDES)

    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if include_globs and not matches_any(rel, include_globs):
            continue
        if excludes and matches_any(rel, excludes):
            continue
        paths.append(path)
    return paths


def resolve_sources(
    sources: list[str],
    tmpdir: Path,
    include_globs: list[str],
    exclude_globs: list[str],
    no_default_excludes: bool,
    max_download_mb: float,
) -> list[tuple[str, Path]]:
    resolved: list[tuple[str, Path]] = []
    for source in sources:
        if re.match(r"^https?://", source):
            resolved.append((source, download_source(source, tmpdir, max_download_mb)))
            continue

        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Source not found: {source}")
        if path.is_dir():
            files = iter_supported_files(path, include_globs, exclude_globs, not no_default_excludes)
            if not files:
                raise SystemExit(f"No supported files found in directory: {source}")
            resolved.extend((str(file), file) for file in files)
        else:
            resolved.append((source, path))
    return resolved


def load_docs(
    sources: list[str],
    tmpdir: Path,
    include_globs: list[str],
    exclude_globs: list[str],
    no_default_excludes: bool,
    max_download_mb: float,
) -> list[SourceDoc]:
    resolved_sources = resolve_sources(sources, tmpdir, include_globs, exclude_globs, no_default_excludes, max_download_mb)
    used: set[str] = set()
    docs: list[SourceDoc] = []
    for source, path in resolved_sources:
        text, kind = extract_text(path)
        title = Path(urllib.parse.urlparse(source).path).name if re.match(r"^https?://", source) else path.name
        title = title or path.name
        docs.append(
            SourceDoc(
                source=source,
                local_path=path,
                title=title,
                slug=unique_slug(title, used),
                kind=kind,
                sha256=sha256_file(path),
                text=normalize_text(text),
            )
        )
    return docs


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def write_doc(out: Path, corpus: str, doc: SourceDoc, chunks: list[Chunk], chunk_size: int, overlap: int) -> list[dict]:
    doc_dir = out / "documents" / corpus / doc.slug
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
    chunk_dir = doc_dir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    total = len(chunks)
    for chunk in chunks:
        path = chunk_dir / f"chunk-{chunk.index:04d}.md"
        metadata = {
            "corpus": corpus,
            "document": doc.slug,
            "title": doc.title,
            "source": doc.source,
            "source_kind": doc.kind,
            "source_sha256": doc.sha256,
            "chunk_index": chunk.index,
            "total_chunks": total,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
        }
        body = f"# {doc.title} — chunk {chunk.index}/{total}\n\n{chunk.text}"
        path.write_text(frontmatter(f"Chunk {chunk.index}/{total} from {doc.title}", metadata) + body, encoding="utf-8")
        rows.append(
            {
                "path": rel(path, out),
                "content": chunk.text,
                "tags": [f"corpus:{corpus}", f"source:{doc.slug}", doc.kind],
                "metadata": metadata,
            }
        )

    table = "\n".join(
        f"| {c.index} | `{rel(chunk_dir / f'chunk-{c.index:04d}.md', out)}` | {c.char_start}-{c.char_end} |"
        for c in chunks
    )
    manifest = f"""# {doc.title}

Source: `{doc.source}`

Kind: `{doc.kind}`

SHA256: `{doc.sha256}`

Chunks: {total}

Chunking: max {chunk_size} chars, {overlap} char overlap.

| Chunk | Path | Character range |
|---:|---|---:|
{table}
"""
    (doc_dir / "manifest.md").write_text(
        frontmatter(
            f"Manifest for {doc.title} in corpus {corpus}",
            {"corpus": corpus, "document": doc.slug, "source": doc.source, "total_chunks": total},
        )
        + manifest,
        encoding="utf-8",
    )
    return rows


def write_corpus_files(out: Path, corpus: str, docs: list[SourceDoc], all_rows: list[dict], chunk_size: int, overlap: int, system_index: bool) -> Path | None:
    corpus_dir = out / "documents" / corpus
    corpus_dir.mkdir(parents=True, exist_ok=True)

    with (corpus_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    doc_lines = []
    for doc in docs:
        count = sum(1 for row in all_rows if row["metadata"]["document"] == doc.slug)
        doc_lines.append(f"- `{doc.slug}`: {doc.title} ({doc.kind}, {count} chunks). Source: `{doc.source}`")

    manifest = f"""# Corpus: {corpus}

Documents: {len(docs)}

Chunks: {len(all_rows)}

Chunking: max {chunk_size} chars, {overlap} char overlap.

JSONL export: `documents/{corpus}/chunks.jsonl`

## Documents

{chr(10).join(doc_lines)}
"""
    (corpus_dir / "manifest.md").write_text(
        frontmatter(f"Manifest for document corpus {corpus}", {"corpus": corpus, "documents": len(docs), "chunks": len(all_rows)}) + manifest,
        encoding="utf-8",
    )

    if not system_index:
        return None

    sys_dir = out / "system" / "filesystem"
    sys_dir.mkdir(parents=True, exist_ok=True)
    index = f"""# Filesystem corpus: {corpus}

This is a MemFS replacement for a deprecated Letta Filesystem folder.

## How to use

- Full content is chunked under `documents/{corpus}/<document>/chunks/`.
- Start with `documents/{corpus}/manifest.md` to see all sources.
- Use local grep/search for keyword lookup.
- Use QMD via the `letta-filesystem-to-memfs` CLI for semantic lookup over chunk files.
- Do not copy all chunks into this pinned system file.

## Documents

{chr(10).join(doc_lines)}
"""
    index_path = sys_dir / f"{corpus}.md"
    index_path.write_text(
        frontmatter(f"Pinned index for document corpus {corpus}", {"corpus": corpus, "documents": len(docs), "chunks": len(all_rows)}) + index,
        encoding="utf-8",
    )
    return index_path


def run_ingest(args: argparse.Namespace) -> IngestResult:
    memory_dir = Path(args.memory_dir or args.out).expanduser().resolve()
    memory_dir.mkdir(parents=True, exist_ok=True)
    corpus = slugify(args.corpus)

    with tempfile.TemporaryDirectory(prefix="memfs-ingest-") as td:
        docs = load_docs(
            args.source,
            Path(td),
            args.glob or [],
            args.exclude or [],
            args.no_default_excludes,
            args.max_download_mb,
        )
        all_rows: list[dict] = []
        for doc in docs:
            chunks = chunk_text(doc.text, args.chunk_size, args.overlap)
            all_rows.extend(write_doc(memory_dir, corpus, doc, chunks, args.chunk_size, args.overlap))
        system_index = write_corpus_files(memory_dir, corpus, docs, all_rows, args.chunk_size, args.overlap, not args.no_system_index)

    return IngestResult(
        corpus=corpus,
        documents=len(docs),
        chunks=len(all_rows),
        corpus_dir=memory_dir / "documents" / corpus,
        system_index=system_index,
    )


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def snippet(text: str, query_terms: list[str], width: int = 420) -> str:
    lower = text.lower()
    positions = [lower.find(t) for t in query_terms if lower.find(t) != -1]
    start = max(0, min(positions) - width // 3) if positions else 0
    out = re.sub(r"\s+", " ", text[start : start + width]).strip()
    if start > 0:
        out = "…" + out
    if start + width < len(text):
        out += "…"
    return out


def find_chunks(memory_dir: Path, corpus: str | None) -> list[Path]:
    root = memory_dir / "documents"
    if corpus:
        root = root / slugify(corpus)
    return sorted(root.glob("**/chunks/chunk-*.md"))


def run_search(memory_dir: Path, corpus: str | None, query: str, top_k: int) -> list[dict]:
    paths = find_chunks(memory_dir, corpus)
    if not paths:
        raise SystemExit("No chunks found")

    docs: list[tuple[Path, str, list[str], Counter[str]]] = []
    df: Counter[str] = Counter()
    for path in paths:
        text = strip_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        toks = tokenize(text)
        counts = Counter(toks)
        docs.append((path, text, toks, counts))
        df.update(set(counts))

    query_terms = tokenize(query)
    if not query_terms:
        raise SystemExit("No searchable terms in query")

    n = len(docs)
    avg_len = sum(len(toks) for _, _, toks, _ in docs) / max(1, n)
    k1 = 1.5
    b = 0.75
    results = []
    phrase = query.lower().strip()

    for path, text, toks, counts in docs:
        score = 0.0
        doc_len = max(1, len(toks))
        for term in query_terms:
            tf = counts.get(term, 0)
            if tf == 0:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_len))
        if phrase and phrase in text.lower():
            score += 2.0
        if score > 0:
            results.append(
                {
                    "score": round(score, 4),
                    "path": path.relative_to(memory_dir).as_posix(),
                    "snippet": snippet(text, query_terms),
                }
            )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


def qmd_collection_name(memory_dir: Path, corpus: str, override: str | None = None) -> str:
    if override:
        return override
    digest = hashlib.sha1(str(memory_dir.resolve()).encode("utf-8")).hexdigest()[:8]
    return f"memfs-{slugify(corpus)[:36]}-{digest}"


def qmd_mask(corpus: str) -> str:
    return f"documents/{slugify(corpus)}/**/chunks/*.md"


def qmd_env() -> tuple[str, dict[str, str]]:
    qmd_bin = shutil.which("qmd")
    if not qmd_bin:
        raise SystemExit("qmd is not installed. Install it with: npm install -g @tobilu/qmd")
    env = os.environ.copy()
    env.pop("BUN_INSTALL", None)
    # qmd's shim resolves itself into the package dir and then calls `node`.
    # Prefer the node next to the qmd symlink (usually an nvm bin dir), not a
    # broken Homebrew node that may appear earlier in PATH.
    qmd_link_dir = Path(qmd_bin).parent
    if (qmd_link_dir / "node").exists():
        env["PATH"] = str(qmd_link_dir) + os.pathsep + env.get("PATH", "")
    return qmd_bin, env


def qmd_run(args: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    qmd_bin, env = qmd_env()
    return subprocess.run(
        [qmd_bin, *args],
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=check,
    )


def qmd_args(index: str, rest: list[str]) -> list[str]:
    return ["--index", index, *rest]


def qmd_collection_exists(index: str, collection: str) -> bool:
    proc = qmd_run(qmd_args(index, ["collection", "show", collection]), check=False, capture=True)
    return proc.returncode == 0


def qmd_common(args: argparse.Namespace) -> tuple[Path, str, str, str]:
    memory_dir = Path(args.memory_dir).expanduser().resolve()
    corpus = slugify(args.corpus)
    collection = qmd_collection_name(memory_dir, corpus, args.collection)
    index = args.qmd_index
    return memory_dir, corpus, collection, index


def run_qmd_setup(args: argparse.Namespace) -> int:
    memory_dir, corpus, collection, index = qmd_common(args)
    mask = qmd_mask(corpus)
    if args.reset and qmd_collection_exists(index, collection):
        qmd_run(qmd_args(index, ["collection", "remove", collection]), check=False)

    if not qmd_collection_exists(index, collection):
        qmd_run(qmd_args(index, ["collection", "add", str(memory_dir), "--name", collection, "--mask", mask]))
    else:
        print(f"Collection already exists: {collection}", file=sys.stderr)

    context = f"MemFS document corpus '{corpus}' chunk files under {memory_dir / 'documents' / corpus}"
    qmd_run(qmd_args(index, ["context", "add", f"qmd://{collection}", context]), check=False)
    qmd_run(qmd_args(index, ["update"]))
    qmd_run(qmd_args(index, ["embed"]))
    print(f"QMD collection: {collection}")
    print(f"QMD index: {index}")
    print(f"QMD mask: {mask}")
    return 0


def run_qmd_reindex(args: argparse.Namespace) -> int:
    _, _, collection, index = qmd_common(args)
    if not qmd_collection_exists(index, collection):
        raise SystemExit(f"QMD collection not found: {collection}. Run qmd setup first.")
    qmd_run(qmd_args(index, ["update"]))
    qmd_run(qmd_args(index, ["embed"]))
    return 0


def run_qmd_status(args: argparse.Namespace) -> int:
    _, corpus, collection, index = qmd_common(args)
    print(f"Corpus: {corpus}", flush=True)
    print(f"Collection: {collection}", flush=True)
    print(f"Index: {index}", flush=True)
    print(f"Mask: {qmd_mask(corpus)}", flush=True)
    print(flush=True)
    qmd_run(qmd_args(index, ["collection", "show", collection]), check=False)
    print(flush=True)
    qmd_run(qmd_args(index, ["status"]))
    return 0


def run_qmd_search(args: argparse.Namespace, command: str) -> int:
    _, _, collection, index = qmd_common(args)
    if not qmd_collection_exists(index, collection):
        raise SystemExit(f"QMD collection not found: {collection}. Run qmd setup first.")

    cmd = qmd_args(index, [command, args.query, "-c", collection, "-n", str(args.top_k)])
    if args.json:
        cmd.append("--json")
    if args.files:
        cmd.append("--files")
    if args.full:
        cmd.append("--full")
    if args.line_numbers:
        cmd.append("--line-numbers")
    if args.candidate_limit is not None:
        cmd.extend(["--candidate-limit", str(args.candidate_limit)])
    qmd_run(cmd)
    return 0


def add_ingest_parser(subparsers) -> None:
    p = subparsers.add_parser("ingest", help="Ingest files/directories/URLs into a MemFS corpus")
    p.add_argument("--source", action="append", required=True, help="File, directory, or http(s) URL. Repeatable.")
    p.add_argument("--memory-dir", "--out", dest="memory_dir", required=True, help="MemFS repo root or output directory")
    p.add_argument("--corpus", required=True, help="Corpus/folder name, e.g. product-docs")
    p.add_argument("--chunk-size", type=int, default=3000, help="Max characters per chunk")
    p.add_argument("--overlap", type=int, default=300, help="Character overlap between chunks")
    p.add_argument("--glob", action="append", help="Include glob for directory sources, relative to each source dir. Repeatable.")
    p.add_argument("--exclude", action="append", help="Exclude glob for directory sources, relative to each source dir. Repeatable.")
    p.add_argument("--no-default-excludes", action="store_true", help="Do not exclude .git, node_modules, .venv, __pycache__ by default")
    p.add_argument("--max-download-mb", type=float, default=100.0, help="Maximum URL download size in MB. Use 0 for unlimited.")
    p.add_argument("--no-system-index", action="store_true", help="Do not write system/filesystem/<corpus>.md")
    p.add_argument("--json", action="store_true", help="Emit JSON summary")
    p.set_defaults(command="ingest")


def add_search_parser(subparsers) -> None:
    p = subparsers.add_parser("search", help="Lexically search generated chunk files")
    p.add_argument("query", nargs="?", help="Search query")
    p.add_argument("--query", dest="query_flag", help="Search query, compatibility alias")
    p.add_argument("--memory-dir", required=True, help="MemFS repo root")
    p.add_argument("--corpus", help="Corpus name. If omitted, searches all corpora.")
    p.add_argument("--top-k", "-n", type=int, default=8)
    p.add_argument("--json", action="store_true", help="Emit JSON")
    p.set_defaults(command="search")


def add_qmd_common(p) -> None:
    p.add_argument("--memory-dir", required=True, help="MemFS repo root")
    p.add_argument("--corpus", required=True, help="Corpus name")
    p.add_argument("--qmd-index", default="memfs-corpora", help="QMD index name")
    p.add_argument("--collection", help="Override QMD collection name")


def add_qmd_search_options(p) -> None:
    p.add_argument("query")
    p.add_argument("--top-k", "-n", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.add_argument("--files", action="store_true")
    p.add_argument("--full", action="store_true")
    p.add_argument("--line-numbers", action="store_true")
    p.add_argument("--candidate-limit", type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate deprecated Letta Filesystem folders/files to MemFS + QMD")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_ingest_parser(subparsers)
    add_search_parser(subparsers)

    qmd = subparsers.add_parser("qmd", help="Manage/search a corpus-scoped QMD collection")
    qmd_sub = qmd.add_subparsers(dest="qmd_command", required=True)

    setup = qmd_sub.add_parser("setup", help="Create/reindex/embed corpus QMD collection")
    add_qmd_common(setup)
    setup.add_argument("--reset", action="store_true", help="Remove and recreate the collection first")

    reindex = qmd_sub.add_parser("reindex", help="Update and embed corpus QMD collection")
    add_qmd_common(reindex)

    status = qmd_sub.add_parser("status", help="Show corpus QMD collection status")
    add_qmd_common(status)

    for name in ["search", "vsearch", "query"]:
        p = qmd_sub.add_parser(name, help=f"Run qmd {name} against the corpus collection")
        add_qmd_common(p)
        add_qmd_search_options(p)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest":
        result = run_ingest(args)
        if args.json:
            print(
                json.dumps(
                    {
                        "corpus": result.corpus,
                        "documents": result.documents,
                        "chunks": result.chunks,
                        "corpus_dir": str(result.corpus_dir),
                        "system_index": str(result.system_index) if result.system_index else None,
                    },
                    indent=2,
                )
            )
        else:
            print(f"Ingested {result.documents} document(s) into {result.corpus_dir}")
            print(f"Wrote {result.chunks} chunks")
            if result.system_index:
                print(f"Pinned index: {result.system_index}")
        return 0

    if args.command == "search":
        query = args.query or args.query_flag
        if not query:
            raise SystemExit("search query is required")
        memory_dir = Path(args.memory_dir).expanduser().resolve()
        results = run_search(memory_dir, args.corpus, query, args.top_k)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for i, r in enumerate(results, start=1):
                print(f"{i}. score={r['score']} {r['path']}")
                print(f"   {r['snippet']}")
        return 0

    if args.command == "qmd":
        if args.qmd_command == "setup":
            return run_qmd_setup(args)
        if args.qmd_command == "reindex":
            return run_qmd_reindex(args)
        if args.qmd_command == "status":
            return run_qmd_status(args)
        if args.qmd_command in {"search", "vsearch", "query"}:
            return run_qmd_search(args, args.qmd_command)

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)
