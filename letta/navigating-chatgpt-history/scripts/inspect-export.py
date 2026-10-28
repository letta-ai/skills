#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    conversation_created,
    conversation_title,
    conversation_updated,
    detect_schema,
    load_conversations,
    load_json,
    normalize_iso,
    sort_key_for_time,
)


def render_markdown(export_path: Path, conversations: list[dict], schema: str) -> str:
    created_values = [normalize_iso(conversation_created(c, schema)) for c in conversations if normalize_iso(conversation_created(c, schema)) != "-"]
    updated_values = [normalize_iso(conversation_updated(c, schema)) for c in conversations if normalize_iso(conversation_updated(c, schema)) != "-"]
    memories = load_json(export_path, "memories.json")
    projects = load_json(export_path, "projects.json")
    users = load_json(export_path, "users.json")

    lines = [
        "# Chat history export summary",
        "",
        f"- Source: `{export_path}`",
        f"- Schema: `{schema}`",
        f"- Conversations: {len(conversations)}",
        f"- Created span: {min(created_values, key=sort_key_for_time) if created_values else '-'} → {max(created_values, key=sort_key_for_time) if created_values else '-'}",
        f"- Updated span: {min(updated_values, key=sort_key_for_time) if updated_values else '-'} → {max(updated_values, key=sort_key_for_time) if updated_values else '-'}",
        "",
    ]

    if isinstance(users, list) and users:
        lines.extend([
            "## Users",
            "",
        ])
        for user in users:
            if not isinstance(user, dict):
                continue
            full_name = user.get("full_name") or "(unknown)"
            uuid = user.get("uuid") or "-"
            lines.append(f"- {full_name} — `{uuid}`")
        lines.append("")

    if isinstance(memories, list) and memories:
        lines.extend([
            "## memories.json",
            "",
        ])
        for index, entry in enumerate(memories, 1):
            lines.append(f"### Entry {index}")
            lines.append("")
            if isinstance(entry, dict):
                text = entry.get("conversations_memory") or json.dumps(entry, ensure_ascii=False, indent=2)
            else:
                text = json.dumps(entry, ensure_ascii=False, indent=2)
            lines.append(text.strip())
            lines.append("")

    if isinstance(projects, list) and projects:
        lines.extend([
            "## Projects",
            "",
        ])
        for project in projects:
            if not isinstance(project, dict):
                continue
            name = project.get("name") or "(unnamed project)"
            updated = project.get("updated_at") or "-"
            description = (project.get("description") or "").strip().replace("\n", " ")
            lines.append(f"- **{name}** — updated {updated}")
            if description:
                lines.append(f"  - {description}")
        lines.append("")

    lines.extend([
        "## Sample recent conversations",
        "",
    ])
    recent = sorted(conversations, key=lambda c: sort_key_for_time(conversation_updated(c, schema)), reverse=True)[:10]
    for conversation in recent:
        title = conversation_title(conversation, schema)
        updated = normalize_iso(conversation_updated(conversation, schema))
        lines.append(f"- {title} — {updated}")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a chat history export and summarize sidecar files.")
    parser.add_argument("export_path", help="Path to export folder or zip file")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    parser.add_argument("--output", help="Write output to this file instead of stdout")
    args = parser.parse_args()

    export_path = Path(args.export_path).expanduser()
    conversations, schema = load_conversations(export_path)

    if args.json:
        payload = {
            "source": str(export_path),
            "schema": schema,
            "conversation_count": len(conversations),
            "users": load_json(export_path, "users.json"),
            "memories": load_json(export_path, "memories.json"),
            "projects": load_json(export_path, "projects.json"),
        }
        output = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        output = render_markdown(export_path, conversations, schema)

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
