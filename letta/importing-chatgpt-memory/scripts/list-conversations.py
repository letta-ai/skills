#!/usr/bin/env python3
"""List conversations from a ChatGPT export zip.

This script stays intentionally simple: it opens the export, walks the
conversation shards, and prints a readable table that helps an agent choose
what to render next.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import zipfile
from pathlib import Path


def iso(ts: object) -> str:
    if ts in (None, ""):
        return "-"
    try:
        return dt.datetime.fromtimestamp(float(ts), dt.timezone.utc).isoformat()
    except Exception:
        return str(ts)


def count_messages(conversation: dict) -> int:
    total = 0
    for node in (conversation.get("mapping") or {}).values():
        if isinstance(node, dict) and node.get("message"):
            total += 1
    return total


def count_hidden_context(conversation: dict) -> int:
    total = 0
    for node in (conversation.get("mapping") or {}).values():
        message = (node or {}).get("message") or {}
        metadata = message.get("metadata") or {}
        if metadata.get("is_user_system_message") or metadata.get("user_context_message_data"):
            total += 1
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="List conversations in a ChatGPT export zip.")
    parser.add_argument("zip_path", help="Path to the ChatGPT export zip file")
    parser.add_argument("--title-contains", help="Only show conversations whose title contains this string")
    parser.add_argument("--start-index", type=int, help="Only show conversations with index >= this value")
    parser.add_argument("--end-index", type=int, help="Only show conversations with index <= this value")
    parser.add_argument("--min-hidden", type=int, help="Only show conversations with hidden-context count >= this value")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to print (default: 50)")
    parser.add_argument(
        "--sort",
        choices=["updated", "created", "hidden", "messages"],
        default="updated",
        help="Sort by updated, created, hidden-context count, or message count (default: updated)",
    )
    parser.add_argument("--oldest-first", action="store_true", help="Print oldest rows first")
    parser.add_argument("--json", action="store_true", help="Emit matching rows as JSON instead of a table")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    rows: list[dict] = []
    global_index = 0

    with zipfile.ZipFile(zip_path) as zf:
        shard_names = sorted(
            name for name in zf.namelist() if name.startswith("conversations-") and name.endswith(".json")
        )
        for shard_name in shard_names:
            conversations = json.loads(zf.read(shard_name))
            for shard_index, conversation in enumerate(conversations):
                title = conversation.get("title") or "(untitled)"
                messages = count_messages(conversation)
                hidden = count_hidden_context(conversation)
                if args.title_contains and args.title_contains.lower() not in title.lower():
                    global_index += 1
                    continue
                if args.start_index is not None and global_index < args.start_index:
                    global_index += 1
                    continue
                if args.end_index is not None and global_index > args.end_index:
                    global_index += 1
                    continue
                if args.min_hidden is not None and hidden < args.min_hidden:
                    global_index += 1
                    continue
                rows.append(
                    {
                        "index": global_index,
                        "shard": shard_name,
                        "shard_index": shard_index,
                        "id": conversation.get("id") or "",
                        "conversation_id": conversation.get("conversation_id") or "",
                        "title": title,
                        "created": conversation.get("create_time"),
                        "updated": conversation.get("update_time"),
                        "messages": messages,
                        "hidden": hidden,
                    }
                )
                global_index += 1

    sort_key = args.sort
    rows.sort(key=lambda row: (row.get(sort_key) or 0, row["index"]), reverse=not args.oldest_first)

    if args.json:
        payload = {
            "zip_path": str(zip_path),
            "total_matching": len(rows),
            "returned": min(len(rows), args.limit),
            "rows": rows[: args.limit],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print(f"Found {len(rows)} matching conversations in {zip_path}")
    print()
    print(f"{'IDX':>5}  {'UPDATED':<25}  {'MSGS':>4}  {'HID':>3}  TITLE")
    print(f"{'-' * 5}  {'-' * 25}  {'-' * 4}  {'-' * 3}  {'-' * 80}")
    for row in rows[: args.limit]:
        title = row["title"].replace("\n", " ").strip()
        if len(title) > 80:
            title = title[:77] + "..."
        print(
            f"{row['index']:>5}  {iso(row['updated']):<25}  {row['messages']:>4}  {row['hidden']:>3}  {title}"
        )

    if len(rows) > args.limit:
        print()
        print(f"Showing {args.limit} of {len(rows)} conversations. Increase --limit to see more.")


if __name__ == "__main__":
    main()
