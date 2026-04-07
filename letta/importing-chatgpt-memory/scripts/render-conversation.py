#!/usr/bin/env python3
"""Render one conversation from a ChatGPT export zip as markdown.

The goal is not to fully parse or summarize the export. The goal is to turn a
single conversation into a long document another agent can read.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import zipfile
from pathlib import Path


COMPACT_KEYS = (
    "content_type",
    "asset_pointer",
    "name",
    "filename",
    "mime_type",
    "size_bytes",
    "width",
    "height",
    "duration_seconds",
)


def iso(ts: object) -> str:
    if ts in (None, ""):
        return "-"
    try:
        return dt.datetime.fromtimestamp(float(ts), dt.timezone.utc).isoformat()
    except Exception:
        return str(ts)


def compact_content_payload(content: dict) -> str:
    summary: dict[str, object] = {}
    for key in COMPACT_KEYS:
        if key in content:
            summary[key] = content[key]

    metadata = content.get("metadata")
    if isinstance(metadata, dict):
        compact_metadata = {}
        for key in ("sanitized", "dalle", "generation", "gizmo", "asset_pointer_link"):
            if key in metadata and metadata[key] is not None:
                compact_metadata[key] = metadata[key]
        if compact_metadata:
            summary["metadata"] = compact_metadata

    if not summary:
        summary = {
            "content_type": content.get("content_type") or "unknown",
            "keys": sorted(content.keys()),
        }

    return json.dumps(summary, indent=2, ensure_ascii=False)


def stringify_content(content: dict, *, compact_nontext: bool) -> str:
    if not isinstance(content, dict):
        return json.dumps(content, indent=2, ensure_ascii=False)

    content_type = content.get("content_type")
    parts = content.get("parts")

    if content_type == "user_editable_context":
        sections = []
        user_profile = content.get("user_profile")
        user_instructions = content.get("user_instructions")
        if isinstance(user_profile, str) and user_profile.strip():
            sections.append("User profile:\n\n" + user_profile.strip())
        if isinstance(user_instructions, str) and user_instructions.strip():
            sections.append("User instructions:\n\n" + user_instructions.strip())
        if sections:
            return "\n\n".join(sections)
        return ""

    if isinstance(parts, list):
        rendered_parts = []
        for part in parts:
            if isinstance(part, str):
                rendered_parts.append(part)
            elif isinstance(part, dict) and compact_nontext:
                rendered_parts.append(compact_content_payload(part))
            else:
                rendered_parts.append(json.dumps(part, indent=2, ensure_ascii=False))
        text = "\n\n".join(part for part in rendered_parts if part.strip())
        if text.strip():
            return text
        if content_type == "text":
            return ""

    if content_type:
        if compact_nontext:
            return compact_content_payload(content)
        return json.dumps(content, indent=2, ensure_ascii=False)

    return ""


def load_rows(zf: zipfile.ZipFile) -> list[dict]:
    rows: list[dict] = []
    global_index = 0
    shard_names = sorted(name for name in zf.namelist() if name.startswith("conversations-") and name.endswith(".json"))
    for shard_name in shard_names:
        conversations = json.loads(zf.read(shard_name))
        for shard_index, conversation in enumerate(conversations):
            rows.append(
                {
                    "index": global_index,
                    "shard": shard_name,
                    "shard_index": shard_index,
                    "conversation": conversation,
                }
            )
            global_index += 1
    return rows


def choose_conversation(rows: list[dict], args: argparse.Namespace) -> dict:
    if args.index is not None:
        for row in rows:
            if row["index"] == args.index:
                return row
        raise SystemExit(f"No conversation found at global index {args.index}")

    if args.id:
        matches = [row for row in rows if row["conversation"].get("id") == args.id]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise SystemExit(f"No conversation found with id {args.id}")
        raise SystemExit(f"Found {len(matches)} conversations with id {args.id}; use --index instead")

    if args.conversation_id:
        matches = [row for row in rows if row["conversation"].get("conversation_id") == args.conversation_id]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise SystemExit(f"No conversation found with conversation_id {args.conversation_id}")
        raise SystemExit(
            f"Found {len(matches)} conversations with conversation_id {args.conversation_id}; use --index instead"
        )

    matches = [
        row for row in rows if args.title_contains.lower() in (row["conversation"].get("title") or "").lower()
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"No conversation title contains {args.title_contains!r}")

    preview = "\n".join(
        f"  index={row['index']}  title={row['conversation'].get('title') or '(untitled)'}" for row in matches[:10]
    )
    raise SystemExit(
        f"Found {len(matches)} matching titles for {args.title_contains!r}. Narrow the query or use --index.\n{preview}"
    )


def ordered_message_nodes(conversation: dict) -> list[tuple[str, dict]]:
    mapping = conversation.get("mapping") or {}
    current_node = conversation.get("current_node")

    if current_node in mapping:
        ordered_ids: list[str] = []
        seen: set[str] = set()
        node_id = current_node
        while node_id and node_id in mapping and node_id not in seen:
            seen.add(node_id)
            ordered_ids.append(node_id)
            node_id = (mapping[node_id] or {}).get("parent")
        ordered_ids.reverse()
        return [(node_id, mapping[node_id]) for node_id in ordered_ids if (mapping[node_id] or {}).get("message")]

    fallback: list[tuple[str, dict]] = []
    for node_id, node in mapping.items():
        if (node or {}).get("message"):
            fallback.append((node_id, node))
    fallback.sort(key=lambda item: ((((item[1] or {}).get("message") or {}).get("create_time") or 0), item[0]))
    return fallback


def message_has_displayable_content(message: dict, *, compact_nontext: bool) -> tuple[bool, str]:
    content = stringify_content(message.get("content") or {}, compact_nontext=compact_nontext)
    user_context = (message.get("metadata") or {}).get("user_context_message_data")
    has_content = bool(content.strip()) or bool(user_context)
    return has_content, content


def should_render_message(
    message: dict,
    *,
    role: str,
    has_content: bool,
    skip_empty_hidden: bool,
    hidden: bool,
    skip_empty_tool_messages: bool,
    skip_thoughts: bool,
    user_only: bool,
    assistant_only: bool,
) -> bool:
    if user_only and role != "user":
        return False
    if assistant_only and role != "assistant":
        return False
    if skip_empty_hidden and hidden and not has_content:
        return False
    if skip_empty_tool_messages and role == "tool" and not has_content:
        return False

    content = message.get("content") or {}
    if skip_thoughts and isinstance(content, dict) and content.get("content_type") == "thoughts":
        return False

    return True


def render_markdown(
    row: dict,
    *,
    skip_empty_hidden: bool,
    compact_nontext: bool,
    skip_empty_tool_messages: bool,
    skip_thoughts: bool,
    user_only: bool,
    assistant_only: bool,
) -> str:
    conversation = row["conversation"]
    lines: list[str] = []
    title = conversation.get("title") or "(untitled)"

    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Conversation metadata")
    lines.append("")
    lines.append(f"- Global index: {row['index']}")
    lines.append(f"- Shard: {row['shard']}")
    lines.append(f"- Shard index: {row['shard_index']}")
    lines.append(f"- Export id: {conversation.get('id') or '-'}")
    lines.append(f"- Conversation id: {conversation.get('conversation_id') or '-'}")
    lines.append(f"- Created: {iso(conversation.get('create_time'))}")
    lines.append(f"- Updated: {iso(conversation.get('update_time'))}")
    lines.append(f"- Default model: {conversation.get('default_model_slug') or '-'}")
    lines.append(f"- Memory scope: {conversation.get('memory_scope') or '-'}")
    lines.append(f"- Current node: {conversation.get('current_node') or '-'}")
    lines.append("")
    lines.append("## Messages")
    lines.append("")

    ordered_nodes = ordered_message_nodes(conversation)
    rendered_count = 0
    for node_id, node in ordered_nodes:
        message = (node or {}).get("message") or {}
        metadata = message.get("metadata") or {}
        author = message.get("author") or {}
        role = author.get("role") or "unknown"
        hidden = bool(metadata.get("is_user_system_message") or metadata.get("is_visually_hidden_from_conversation"))
        has_content, content = message_has_displayable_content(message, compact_nontext=compact_nontext)
        user_context = metadata.get("user_context_message_data")

        if not should_render_message(
            message,
            role=role,
            has_content=has_content,
            skip_empty_hidden=skip_empty_hidden,
            hidden=hidden,
            skip_empty_tool_messages=skip_empty_tool_messages,
            skip_thoughts=skip_thoughts,
            user_only=user_only,
            assistant_only=assistant_only,
        ):
            continue

        rendered_count += 1
        heading = f"### {rendered_count}. {role}"
        if hidden:
            heading += " [hidden]"
        lines.append(heading)
        lines.append("")
        lines.append(f"- Node id: {node_id}")
        lines.append(f"- Message id: {message.get('id') or '-'}")
        lines.append(f"- Timestamp: {iso(message.get('create_time'))}")
        if message.get("recipient"):
            lines.append(f"- Recipient: {message.get('recipient')}")
        if message.get("status"):
            lines.append(f"- Status: {message.get('status')}")
        if user_context:
            lines.append("- Hidden user context:")
            lines.append("```json")
            lines.append(json.dumps(user_context, indent=2, ensure_ascii=False))
            lines.append("```")
        lines.append("")
        lines.append("#### Content")
        lines.append("")
        if content.strip():
            lines.append(content)
        else:
            lines.append("*(empty content)*")
        lines.append("")

    if rendered_count == 0:
        lines.append("*(No messages were rendered on the current branch.)*")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one ChatGPT export conversation as markdown.")
    parser.add_argument("zip_path", help="Path to the ChatGPT export zip file")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--index", type=int, help="Global index from list-conversations.py")
    selector.add_argument("--id", help="Conversation export id")
    selector.add_argument("--conversation-id", help="Conversation id field from the export")
    selector.add_argument("--title-contains", help="Case-insensitive title substring")
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
    parser.add_argument("--output", help="Write markdown to this file instead of stdout")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    with zipfile.ZipFile(zip_path) as zf:
        rows = load_rows(zf)
        row = choose_conversation(rows, args)
        markdown = render_markdown(
            row,
            skip_empty_hidden=args.skip_empty_hidden,
            compact_nontext=args.compact_nontext,
            skip_empty_tool_messages=args.skip_empty_tool_messages,
            skip_thoughts=args.skip_thoughts,
            user_only=args.user_only,
            assistant_only=args.assistant_only,
        )

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
