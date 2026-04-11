#!/usr/bin/env python3
"""Render a range of ChatGPT export conversations.

Opens the zip once and renders in-process instead of shelling out per
conversation.  For a 50-conversation range this is ~50x fewer zip reads.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import zipfile
from pathlib import Path

# Import rendering functions from render-conversation.py (same directory).
_rc_path = Path(__file__).resolve().parent / "render-conversation.py"
_spec = importlib.util.spec_from_file_location("render_conversation", _rc_path)
_rc = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_rc)  # type: ignore[union-attr]

load_range = _rc.load_range
render_markdown = _rc.render_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a range of ChatGPT export conversations.")
    parser.add_argument("zip_path", help="Path to the ChatGPT export zip file")
    parser.add_argument("--start-index", type=int, required=True, help="First global conversation index to render")
    parser.add_argument("--end-index", type=int, required=True, help="Last global conversation index to render")
    parser.add_argument(
        "--skip-empty-hidden",
        action="store_true",
        help="Drop hidden messages with no visible content or user-context data",
    )
    parser.add_argument(
        "--compact-nontext",
        action="store_true",
        help="Compact bulky non-text payloads such as attachment metadata",
    )
    parser.add_argument(
        "--skip-empty-tool-messages",
        action="store_true",
        help="Drop tool messages whose rendered content is empty",
    )
    parser.add_argument(
        "--skip-thoughts",
        action="store_true",
        help="Drop messages whose content_type is 'thoughts'",
    )
    role_filter = parser.add_mutually_exclusive_group()
    role_filter.add_argument("--user-only", action="store_true", help="Render only user messages")
    role_filter.add_argument("--assistant-only", action="store_true", help="Render only assistant messages")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr")

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output-dir", help="Directory for one markdown file per conversation")
    output_group.add_argument("--concat-output", help="Write one concatenated markdown file for the whole range")
    args = parser.parse_args()

    if args.end_index < args.start_index:
        raise SystemExit("--end-index must be greater than or equal to --start-index")

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    render_kwargs = dict(
        skip_empty_hidden=args.skip_empty_hidden,
        compact_nontext=args.compact_nontext,
        skip_empty_tool_messages=args.skip_empty_tool_messages,
        skip_thoughts=args.skip_thoughts,
        user_only=args.user_only,
        assistant_only=args.assistant_only,
    )

    with zipfile.ZipFile(zip_path) as zf:
        rows = load_range(zf, args.start_index, args.end_index)

    total = len(rows)
    if args.progress:
        print(f"Loaded {total} conversations ({args.start_index}-{args.end_index})", file=sys.stderr)

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        for i, row in enumerate(rows, start=1):
            output_path = output_dir / f"chatgpt-{row['index']:04d}.md"
            markdown = render_markdown(row, **render_kwargs)
            output_path.write_text(markdown, encoding="utf-8")
            if args.progress:
                print(f"Rendered {i}/{total}: {row['conversation'].get('title', '(untitled)')}", file=sys.stderr)
        print(f"Wrote {total} conversations to {output_dir}")
        return

    concat_output = Path(args.concat_output).expanduser()
    concat_output.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for i, row in enumerate(rows, start=1):
        markdown = render_markdown(row, **render_kwargs)
        chunks.append(markdown.rstrip())
        if args.progress:
            print(f"Rendered {i}/{total}: {row['conversation'].get('title', '(untitled)')}", file=sys.stderr)

    separator = "\n\n---\n\n"
    concat_output.write_text(separator.join(chunks) + "\n", encoding="utf-8")
    print(f"Wrote {total} conversations to {concat_output}")


if __name__ == "__main__":
    main()
