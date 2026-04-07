#!/usr/bin/env python3
"""Render a range of ChatGPT export conversations.

This stays intentionally procedural: it shells out to render-conversation.py for
one conversation at a time instead of inventing a larger parsing framework.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_base_command(
    render_script: Path,
    zip_path: Path,
    *,
    skip_empty_hidden: bool,
    compact_nontext: bool,
    skip_empty_tool_messages: bool,
    skip_thoughts: bool,
    user_only: bool,
    assistant_only: bool,
) -> list[str]:
    command = [sys.executable, str(render_script), str(zip_path)]
    if skip_empty_hidden:
        command.append("--skip-empty-hidden")
    if compact_nontext:
        command.append("--compact-nontext")
    if skip_empty_tool_messages:
        command.append("--skip-empty-tool-messages")
    if skip_thoughts:
        command.append("--skip-thoughts")
    if user_only:
        command.append("--user-only")
    if assistant_only:
        command.append("--assistant-only")
    return command


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

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output-dir", help="Directory for one markdown file per conversation")
    output_group.add_argument("--concat-output", help="Write one concatenated markdown file for the whole range")
    args = parser.parse_args()

    if args.end_index < args.start_index:
        raise SystemExit("--end-index must be greater than or equal to --start-index")

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    render_script = Path(__file__).resolve().parent / "render-conversation.py"
    base_command = build_base_command(
        render_script,
        zip_path,
        skip_empty_hidden=args.skip_empty_hidden,
        compact_nontext=args.compact_nontext,
        skip_empty_tool_messages=args.skip_empty_tool_messages,
        skip_thoughts=args.skip_thoughts,
        user_only=args.user_only,
        assistant_only=args.assistant_only,
    )

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        for index in range(args.start_index, args.end_index + 1):
            output_path = output_dir / f"chatgpt-{index:04d}.md"
            command = [*base_command, "--index", str(index), "--output", str(output_path)]
            subprocess.run(command, check=True)
        print(f"Wrote conversations {args.start_index}-{args.end_index} to {output_dir}")
        return

    concat_output = Path(args.concat_output).expanduser()
    concat_output.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for index in range(args.start_index, args.end_index + 1):
        command = [*base_command, "--index", str(index)]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        chunks.append(result.stdout.rstrip())

    separator = "\n\n---\n\n"
    concat_output.write_text(separator.join(chunks) + "\n", encoding="utf-8")
    print(f"Wrote conversations {args.start_index}-{args.end_index} to {concat_output}")


if __name__ == "__main__":
    main()
