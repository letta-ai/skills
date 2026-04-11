#!/usr/bin/env python3
"""Search ChatGPT export conversation contents for keywords or phrases.

This is intentionally lightweight: it helps agents find conversations by what
was actually said, rather than relying only on titles.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import zipfile
from pathlib import Path


def iso(ts: object) -> str:
    if ts in (None, ""):
        return "-"
    try:
        return dt.datetime.fromtimestamp(float(ts), dt.timezone.utc).isoformat()
    except Exception:
        return str(ts)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def stringify_content(content: object) -> str:
    if not isinstance(content, dict):
        return ""

    content_type = content.get("content_type")
    parts = content.get("parts")

    if content_type == "user_editable_context":
        sections: list[str] = []
        for key, label in (("user_profile", "User profile"), ("user_instructions", "User instructions")):
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                sections.append(f"{label}:\n{value.strip()}")
        return "\n\n".join(sections)

    if isinstance(parts, list):
        chunks: list[str] = []
        for part in parts:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict):
                chunks.append(json.dumps(part, ensure_ascii=False))
        return "\n\n".join(chunk for chunk in chunks if chunk.strip())

    if content_type:
        return json.dumps(content, ensure_ascii=False)

    return ""


def iter_conversations(zip_path: Path):
    with zipfile.ZipFile(zip_path) as zf:
        global_index = 0
        shard_names = sorted(name for name in zf.namelist() if name.startswith("conversations-") and name.endswith(".json"))
        for shard_name in shard_names:
            conversations = json.loads(zf.read(shard_name))
            for shard_index, conversation in enumerate(conversations):
                yield global_index, shard_name, shard_index, conversation
                global_index += 1


def conversation_messages(conversation: dict) -> list[dict]:
    rows: list[dict] = []
    for node_id, node in (conversation.get("mapping") or {}).items():
        message = (node or {}).get("message") or {}
        if not message:
            continue
        rows.append({"node_id": node_id, "message": message})
    rows.sort(key=lambda row: ((row["message"].get("create_time") or 0), row["node_id"]))
    return rows


def build_search_blob(title: str, message: dict, *, include_title: bool) -> str:
    metadata = message.get("metadata") or {}
    pieces: list[str] = []
    if include_title and title:
        pieces.append(title)

    user_context = metadata.get("user_context_message_data") or {}
    for value in user_context.values():
        if isinstance(value, str) and value.strip():
            pieces.append(value)

    content = stringify_content(message.get("content") or {})
    if content.strip():
        pieces.append(content)

    return "\n\n".join(pieces)


def build_snippet(text: str, start: int, end: int, *, radius: int = 110) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    snippet = normalize_text(text[left:right])
    if left > 0:
        snippet = "…" + snippet
    if right < len(text):
        snippet = snippet + "…"
    return snippet


def main() -> None:
    parser = argparse.ArgumentParser(description="Search ChatGPT export conversations by message content.")
    parser.add_argument("zip_path", help="Path to the ChatGPT export zip file")
    parser.add_argument("--query", action="append", required=True, help="Query string to search for. Repeat for multiple queries.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print (default: 20)")
    parser.add_argument("--json", action="store_true", help="Emit matching rows as JSON instead of a table")
    parser.add_argument("--case-sensitive", action="store_true", help="Use case-sensitive matching")
    parser.add_argument("--include-title", action="store_true", help="Also search conversation titles")
    parser.add_argument(
        "--role",
        action="append",
        help="Only search messages from this role (user, assistant, tool, system). Repeat for multiple roles.",
    )
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    queries = [query for query in args.query if query]
    if not queries:
        raise SystemExit("Provide at least one --query")

    regex_flags = 0 if args.case_sensitive else re.IGNORECASE
    patterns = [(query, re.compile(re.escape(query), regex_flags)) for query in queries]
    allowed_roles: set[str] | None = set(r.lower() for r in args.role) if args.role else None

    rows: list[dict] = []
    conversation_count = 0
    for index, shard_name, shard_index, conversation in iter_conversations(zip_path):
        conversation_count += 1
        if args.progress and conversation_count % 100 == 0:
            print(f"Searched {conversation_count} conversations...", file=sys.stderr)
        title = conversation.get("title") or "(untitled)"
        message_hits: list[dict] = []
        matched_queries: set[str] = set()

        for row in conversation_messages(conversation):
            message = row["message"]
            role = ((message.get("author") or {}).get("role") or "unknown")
            if allowed_roles is not None and role not in allowed_roles:
                continue
            blob = build_search_blob(title, message, include_title=args.include_title)
            if not blob:
                continue

            for query, pattern in patterns:
                match = pattern.search(blob)
                if not match:
                    continue
                matched_queries.add(query)
                snippet = build_snippet(blob, match.start(), match.end())
                message_hits.append(
                    {
                        "node_id": row["node_id"],
                        "message_id": message.get("id") or "",
                        "role": ((message.get("author") or {}).get("role") or "unknown"),
                        "timestamp": iso(message.get("create_time") or conversation.get("update_time") or conversation.get("create_time")),
                        "query": query,
                        "snippet": snippet,
                    }
                )

        if not message_hits:
            continue

        rows.append(
            {
                "index": index,
                "shard": shard_name,
                "shard_index": shard_index,
                "title": title,
                "created": iso(conversation.get("create_time")),
                "updated": iso(conversation.get("update_time")),
                "matched_queries": sorted(matched_queries),
                "match_count": len(message_hits),
                "hits": message_hits[:5],
            }
        )

    rows.sort(key=lambda row: (row["updated"], row["match_count"], row["index"]), reverse=True)
    limited = rows[: args.limit]

    if args.json:
        payload = {
            "zip_path": str(zip_path),
            "queries": queries,
            "total_matching": len(rows),
            "returned": len(limited),
            "rows": limited,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print(f"Found {len(rows)} matching conversations in {zip_path}")
    print()
    print("  IDX  MATCHES  UPDATED                    TITLE")
    print("-----  -------  -------------------------  ------------------------------------------------------------")
    for row in limited:
        print(f"{row['index']:>5}  {row['match_count']:>7}  {row['updated']:<25}  {row['title'][:60]}")
        for hit in row["hits"][:2]:
            print(f"       - {hit['role']} [{hit['query']}]: {hit['snippet']}")
    if len(rows) > len(limited):
        print()
        print(f"Showing {len(limited)} of {len(rows)} conversations. Increase --limit to see more.")


if __name__ == "__main__":
    main()