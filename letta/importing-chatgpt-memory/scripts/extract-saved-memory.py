#!/usr/bin/env python3
"""Extract hidden ChatGPT saved-memory and editable-context blocks from an export.

This script is intentionally narrow. It does not attempt to summarize the whole
archive. It focuses on the highest-signal onboarding inputs:

- metadata.user_context_message_data.about_user_message
- metadata.user_context_message_data.about_model_message
- content.user_profile from user_editable_context messages
- content.user_instructions from user_editable_context messages

The output is designed to help an agent answer:
"What did ChatGPT explicitly remember about this user, and what looks current?"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import zipfile
from pathlib import Path


FIELDS = (
    "about_user_message",
    "about_model_message",
    "user_profile",
    "user_instructions",
)


def iso(ts: object) -> str:
    if ts in (None, ""):
        return "-"
    try:
        return dt.datetime.fromtimestamp(float(ts), dt.timezone.utc).isoformat()
    except Exception:
        return str(ts)


def normalize_text(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").strip().splitlines()).strip()


def clean_editable_context_value(field: str, value: str) -> str:
    text = normalize_text(value)
    fenced_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)

    if field == "user_profile":
        if text.startswith("The user provided the following information about themselves") and fenced_match:
            return normalize_text(fenced_match.group(1))
        if text.lower().startswith("user profile:") and fenced_match:
            return normalize_text(fenced_match.group(1))

    if field == "user_instructions":
        if text.lower().startswith("user instructions:") and fenced_match:
            return normalize_text(fenced_match.group(1))

    return text


def blank_stats() -> dict:
    return {
        "occurrences": 0,
        "conversation_indexes": set(),
        "first_seen": None,
        "last_seen": None,
        "samples": [],
    }


def update_stats(stats: dict, *, ts: object, sample: dict, max_samples: int) -> None:
    stats["occurrences"] += 1
    stats["conversation_indexes"].add(sample["index"])

    if ts not in (None, ""):
        if stats["first_seen"] is None or float(ts) < float(stats["first_seen"]):
            stats["first_seen"] = ts
        if stats["last_seen"] is None or float(ts) > float(stats["last_seen"]):
            stats["last_seen"] = ts

    seen_sample_keys = {(row["index"], row["message_id"], row["field"]) for row in stats["samples"]}
    sample_key = (sample["index"], sample["message_id"], sample["field"])
    if sample_key not in seen_sample_keys and len(stats["samples"]) < max_samples:
        stats["samples"].append(sample)


def iter_conversations(zf: zipfile.ZipFile):
    global_index = 0
    shard_names = sorted(name for name in zf.namelist() if name.startswith("conversations-") and name.endswith(".json"))
    for shard_name in shard_names:
        conversations = json.loads(zf.read(shard_name))
        for shard_index, conversation in enumerate(conversations):
            yield {
                "index": global_index,
                "shard": shard_name,
                "shard_index": shard_index,
                "conversation": conversation,
            }
            global_index += 1


def iter_messages(conversation: dict):
    for node_id, node in (conversation.get("mapping") or {}).items():
        message = (node or {}).get("message")
        if message:
            yield node_id, message


def extract(zf: zipfile.ZipFile, *, max_samples: int) -> dict:
    aggregates = {field: {} for field in FIELDS}
    field_occurrences = {field: 0 for field in FIELDS}
    other_user_context_fields: dict[str, int] = {}

    for row in iter_conversations(zf):
        conversation = row["conversation"]
        title = conversation.get("title") or "(untitled)"
        conversation_ts = conversation.get("update_time") or conversation.get("create_time")

        for node_id, message in iter_messages(conversation):
            metadata = message.get("metadata") or {}
            content = message.get("content") or {}
            user_context = metadata.get("user_context_message_data") or {}

            sample_base = {
                "index": row["index"],
                "title": title,
                "node_id": node_id,
                "message_id": message.get("id") or "",
                "timestamp": iso(message.get("create_time") or conversation_ts),
            }

            for key, value in user_context.items():
                if key not in FIELDS:
                    other_user_context_fields[key] = other_user_context_fields.get(key, 0) + 1

                if key not in ("about_user_message", "about_model_message"):
                    continue
                if not isinstance(value, str):
                    continue
                text = normalize_text(value)
                if not text:
                    continue

                stats = aggregates[key].setdefault(text, blank_stats())
                update_stats(
                    stats,
                    ts=message.get("create_time") or conversation_ts,
                    sample={**sample_base, "field": key},
                    max_samples=max_samples,
                )
                field_occurrences[key] += 1

            if content.get("content_type") == "user_editable_context":
                for key in ("user_profile", "user_instructions"):
                    value = content.get(key)
                    if not isinstance(value, str):
                        continue
                    text = clean_editable_context_value(key, value)
                    if not text:
                        continue

                    stats = aggregates[key].setdefault(text, blank_stats())
                    update_stats(
                        stats,
                        ts=message.get("create_time") or conversation_ts,
                        sample={**sample_base, "field": key},
                        max_samples=max_samples,
                    )
                    field_occurrences[key] += 1

    fields_payload = {}
    canonical = {}
    for field, entries in aggregates.items():
        rows = []
        for text, stats in entries.items():
            samples = sorted(stats["samples"], key=lambda row: (row["timestamp"], row["index"]))
            rows.append(
                {
                    "text": text,
                    "occurrences": stats["occurrences"],
                    "conversation_count": len(stats["conversation_indexes"]),
                    "first_seen": iso(stats["first_seen"]),
                    "last_seen": iso(stats["last_seen"]),
                    "samples": samples,
                }
            )

        rows.sort(key=lambda row: (row["last_seen"], row["occurrences"], row["conversation_count"]), reverse=True)
        fields_payload[field] = rows

        if rows:
            most_common = max(rows, key=lambda row: (row["occurrences"], row["conversation_count"], row["last_seen"]))
            latest = max(rows, key=lambda row: row["last_seen"])
            canonical[field] = {
                "latest_text": latest["text"],
                "latest_last_seen": latest["last_seen"],
                "most_common_text": most_common["text"],
                "most_common_occurrences": most_common["occurrences"],
                "agreement": latest["text"] == most_common["text"],
            }
        else:
            canonical[field] = None

    return {
        "fields": fields_payload,
        "field_occurrences": field_occurrences,
        "other_user_context_fields": other_user_context_fields,
        "canonical": canonical,
    }


def render_markdown(payload: dict, *, zip_path: Path) -> str:
    lines: list[str] = []
    lines.append("# ChatGPT saved memory extraction")
    lines.append("")
    lines.append(f"- Export: `{zip_path}`")
    lines.append("")
    lines.append("## Occurrence summary")
    lines.append("")
    for field in FIELDS:
        lines.append(f"- `{field}`: {payload['field_occurrences'].get(field, 0)} occurrences")
    if payload["other_user_context_fields"]:
        lines.append("")
        lines.append("## Other user_context_message_data fields")
        lines.append("")
        for key, count in sorted(payload["other_user_context_fields"].items()):
            lines.append(f"- `{key}`: {count}")

    for field in FIELDS:
        rows = payload["fields"][field]
        lines.append("")
        lines.append(f"## {field}")
        lines.append("")
        if not rows:
            lines.append("*(none found)*")
            continue

        canonical = payload["canonical"].get(field)
        if canonical:
            lines.append(f"- Latest last seen: {canonical['latest_last_seen']}")
            lines.append(f"- Latest and most common agree: {'yes' if canonical['agreement'] else 'no'}")
            lines.append("")

        for i, row in enumerate(rows, start=1):
            lines.append(f"### {i}. {field}")
            lines.append("")
            lines.append(f"- Occurrences: {row['occurrences']}")
            lines.append(f"- Conversations: {row['conversation_count']}")
            lines.append(f"- First seen: {row['first_seen']}")
            lines.append(f"- Last seen: {row['last_seen']}")
            lines.append("")
            lines.append("```text")
            lines.append(row["text"])
            lines.append("```")
            if row["samples"]:
                lines.append("")
                lines.append("Samples:")
                for sample in row["samples"]:
                    lines.append(
                        f"- idx={sample['index']}  time={sample['timestamp']}  title={sample['title']}"
                    )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract ChatGPT saved memory and editable-context blocks from an export.")
    parser.add_argument("zip_path", help="Path to the ChatGPT export zip file")
    parser.add_argument("--samples", type=int, default=5, help="Maximum sample source rows per unique value (default: 5)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    parser.add_argument("--output", help="Write output to this file instead of stdout")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    with zipfile.ZipFile(zip_path) as zf:
        payload = extract(zf, max_samples=args.samples)

    output = json.dumps({"zip_path": str(zip_path), **payload}, indent=2, ensure_ascii=False) if args.json else render_markdown(payload, zip_path=zip_path)

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()