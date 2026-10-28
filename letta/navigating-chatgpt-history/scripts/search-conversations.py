#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    conversation_messages,
    conversation_title,
    conversation_updated,
    load_conversations,
    normalize_iso,
    role_matches,
    snippet,
    sort_key_for_time,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search conversation contents for keywords or phrases.")
    parser.add_argument("export_path", help="Path to export folder or zip file")
    parser.add_argument("--query", action="append", required=True, help="Query string to search for (repeatable)")
    parser.add_argument("--role", action="append", help="Restrict to roles such as user, human, assistant, tool, or system")
    parser.add_argument("--title-contains", help="Only search conversations whose title contains this string")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to print (default: 50)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    export_path = Path(args.export_path).expanduser()
    conversations, schema = load_conversations(export_path)
    queries = [query.lower() for query in args.query]
    allowed_roles = {role.lower() for role in (args.role or [])} or None

    rows: list[dict] = []
    for index, conversation in enumerate(conversations):
        if args.progress and index and index % 100 == 0:
            print(f"Scanned {index} conversations...", file=sys.stderr)

        title = conversation_title(conversation, schema)
        if args.title_contains and args.title_contains.lower() not in title.lower():
            continue

        for message in conversation_messages(conversation, schema):
            if not role_matches(message.get("sender") or "unknown", allowed_roles):
                continue
            text = message.get("text") or ""
            if not text:
                continue
            haystack = text.lower()
            matched = [query for query in queries if query in haystack]
            if not matched:
                continue
            rows.append(
                {
                    "index": index,
                    "title": title,
                    "updated": normalize_iso(conversation_updated(conversation, schema)),
                    "sender": message.get("sender") or "unknown",
                    "created": normalize_iso(message.get("created_at")),
                    "matched_queries": matched,
                    "snippet": snippet(text),
                }
            )

    rows.sort(key=lambda row: (sort_key_for_time(row["updated"]), sort_key_for_time(row["created"])), reverse=True)
    total = len(rows)
    rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    print(f"Found {total} matching messages in {export_path}\n")
    print(f"{'IDX':>5}  {'UPDATED':<25}  {'ROLE':<9}  {'MATCHED':<20}  {'TITLE':<36}  SNIPPET")
    print(f"{'-' * 5}  {'-' * 25}  {'-' * 9}  {'-' * 20}  {'-' * 36}  {'-' * 60}")
    for row in rows:
        matched = ", ".join(row["matched_queries"])[:20]
        print(
            f"{row['index']:>5}  {row['updated']:<25}  {row['sender']:<9}  {matched:<20}  {row['title'][:36]:<36}  {row['snippet'][:60]}"
        )

    if total > len(rows):
        print(f"\nShowing {len(rows)} of {total} matches. Increase --limit to see more.")


if __name__ == "__main__":
    main()
