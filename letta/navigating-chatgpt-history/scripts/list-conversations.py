#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    canonical_role,
    conversation_created,
    conversation_messages,
    conversation_title,
    conversation_updated,
    load_conversations,
    normalize_iso,
    sort_key_for_time,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="List conversations in a chat history export.")
    parser.add_argument("export_path", help="Path to export folder or zip file")
    parser.add_argument("--title-contains", help="Only show conversations whose title contains this string")
    parser.add_argument("--start-index", type=int, help="Only show conversations with index >= this value")
    parser.add_argument("--end-index", type=int, help="Only show conversations with index <= this value")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to print (default: 50)")
    parser.add_argument("--sort", choices=["updated", "created", "messages", "title"], default="updated")
    parser.add_argument("--oldest-first", action="store_true", help="Print oldest rows first")
    parser.add_argument("--json", action="store_true", help="Emit matching rows as JSON instead of a table")
    args = parser.parse_args()

    export_path = Path(args.export_path).expanduser()
    conversations, schema = load_conversations(export_path)

    rows: list[dict] = []
    for index, conversation in enumerate(conversations):
        if args.start_index is not None and index < args.start_index:
            continue
        if args.end_index is not None and index > args.end_index:
            continue

        title = conversation_title(conversation, schema)
        if args.title_contains and args.title_contains.lower() not in title.lower():
            continue

        messages = conversation_messages(conversation, schema)
        sender_counts = {"user": 0, "assistant": 0, "other": 0}
        for message in messages:
            role = canonical_role(message.get("sender") or "unknown")
            if role in sender_counts:
                sender_counts[role] += 1
            else:
                sender_counts["other"] += 1

        rows.append(
            {
                "index": index,
                "title": title,
                "created": normalize_iso(conversation_created(conversation, schema)),
                "updated": normalize_iso(conversation_updated(conversation, schema)),
                "messages": len(messages),
                "user_messages": sender_counts["user"],
                "assistant_messages": sender_counts["assistant"],
                "other_messages": sender_counts["other"],
            }
        )

    reverse = not args.oldest_first
    if args.sort == "title":
        rows.sort(key=lambda row: row["title"].lower(), reverse=reverse)
    elif args.sort == "messages":
        rows.sort(key=lambda row: row["messages"], reverse=reverse)
    else:
        rows.sort(key=lambda row: sort_key_for_time(row[args.sort]), reverse=reverse)

    total = len(rows)
    rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    print(f"Found {total} matching conversations in {export_path}\n")
    print(f"{'IDX':>5}  {'UPDATED':<25}  {'MSGS':>4}  {'USR':>3}  {'AST':>3}  {'OTH':>3}  TITLE")
    print(f"{'-' * 5}  {'-' * 25}  {'-' * 4}  {'-' * 3}  {'-' * 3}  {'-' * 3}  {'-' * 80}")
    for row in rows:
        print(
            f"{row['index']:>5}  {row['updated']:<25}  {row['messages']:>4}  {row['user_messages']:>3}  {row['assistant_messages']:>3}  {row['other_messages']:>3}  {row['title'][:80]}"
        )

    if total > len(rows):
        print(f"\nShowing {len(rows)} of {total} conversations. Increase --limit to see more.")


if __name__ == "__main__":
    main()
