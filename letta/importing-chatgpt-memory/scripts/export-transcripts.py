#!/usr/bin/env python3
"""Export rendered ChatGPT conversations into an output directory.

This is intended for optional high-fidelity archival. It can write plain
markdown transcripts or memory-ready markdown files with frontmatter.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


def sanitize_title(title: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return cleaned or "untitled"


def load_titles(zip_path: Path) -> dict[int, str]:
    titles: dict[int, str] = {}
    with zipfile.ZipFile(zip_path) as zf:
        idx = 0
        shard_names = sorted(name for name in zf.namelist() if name.startswith("conversations-") and name.endswith(".json"))
        for shard_name in shard_names:
            conversations = json.loads(zf.read(shard_name))
            for conversation in conversations:
                titles[idx] = conversation.get("title") or "(untitled)"
                idx += 1
    return titles


def parse_indexes(args: argparse.Namespace) -> list[int]:
    if args.indexes:
        indexes = []
        for raw in args.indexes.split(","):
            raw = raw.strip()
            if raw:
                indexes.append(int(raw))
        return sorted(set(indexes))

    if args.start_index is None or args.end_index is None:
        raise SystemExit("Provide either --indexes or both --start-index and --end-index")
    if args.end_index < args.start_index:
        raise SystemExit("--end-index must be >= --start-index")
    return list(range(args.start_index, args.end_index + 1))


def chunk_markdown(text: str, *, max_chars: int) -> list[str]:
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]

    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        if current and current_len + len(line) > max_chars:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("".join(current))
    return chunks


def add_frontmatter(markdown: str, *, description: str, limit: int) -> str:
    frontmatter = [
        "---",
        f"description: {description}",
        f"limit: {limit}",
        "---",
        "",
    ]
    return "\n".join(frontmatter) + markdown.lstrip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rendered ChatGPT conversation transcripts.")
    parser.add_argument("zip_path", help="Path to the ChatGPT export zip file")
    parser.add_argument("--output-dir", required=True, help="Directory to write transcript files into")
    parser.add_argument("--indexes", help="Comma-separated global conversation indexes to export")
    parser.add_argument("--start-index", type=int, help="First global index to export")
    parser.add_argument("--end-index", type=int, help="Last global index to export")
    parser.add_argument("--skip-empty-hidden", action="store_true", help="Pass through to render-conversation.py")
    parser.add_argument("--compact-nontext", action="store_true", help="Pass through to render-conversation.py")
    parser.add_argument("--memory-frontmatter", action="store_true", help="Write memory-ready markdown with frontmatter")
    parser.add_argument("--max-chars", type=int, default=40000, help="Maximum characters per output file chunk (default: 40000)")
    parser.add_argument("--limit-value", type=int, default=500, help="Frontmatter limit value when --memory-frontmatter is used (default: 500)")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    indexes = parse_indexes(args)
    titles = load_titles(zip_path)
    render_script = Path(__file__).resolve().parent / "render-conversation.py"

    manifest_lines = ["# ChatGPT transcript export", "", f"- Export: `{zip_path}`", "", "## Files", ""]

    for index in indexes:
        title = titles.get(index, "(untitled)")
        command = [sys.executable, str(render_script), str(zip_path), "--index", str(index)]
        if args.skip_empty_hidden:
            command.append("--skip-empty-hidden")
        if args.compact_nontext:
            command.append("--compact-nontext")

        result = subprocess.run(command, check=True, capture_output=True, text=True)
        chunks = chunk_markdown(result.stdout, max_chars=args.max_chars)
        title_slug = sanitize_title(title)

        for part, chunk in enumerate(chunks, start=1):
            if len(chunks) == 1:
                filename = f"chatgpt-{index:04d}-{title_slug}.md"
                description = f"Transcript export for ChatGPT conversation {index}: {title}"
            else:
                filename = f"chatgpt-{index:04d}-{title_slug}-part-{part:02d}.md"
                description = f"Transcript export for ChatGPT conversation {index} part {part}/{len(chunks)}: {title}"
            output_path = output_dir / filename
            text = add_frontmatter(chunk, description=description, limit=args.limit_value) if args.memory_frontmatter else chunk
            output_path.write_text(text, encoding="utf-8")
            manifest_lines.append(f"- `{output_path.name}` — index {index}, title: {title}")

    index_md = output_dir / "index.md"
    index_text = "\n".join(manifest_lines).rstrip() + "\n"
    if args.memory_frontmatter:
        index_text = add_frontmatter(index_text, description="Index of exported ChatGPT transcript files", limit=args.limit_value)
    index_md.write_text(index_text, encoding="utf-8")
    print(f"Wrote {len(indexes)} conversation exports to {output_dir}")


if __name__ == "__main__":
    main()