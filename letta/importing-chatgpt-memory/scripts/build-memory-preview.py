#!/usr/bin/env python3
"""Build a Letta-oriented preview from extracted ChatGPT saved memory.

This script consumes JSON output from `extract-saved-memory.py` and produces a
clean markdown or JSON preview that separates:

- likely current active-memory candidates
- historical / progressive-memory candidates
- runtime-only context
- contradictions / open questions
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RUNTIME_PROFILE_PATTERNS = (
    re.compile(r"\btimezone\b", re.IGNORECASE),
    re.compile(r"\bcurrent date\b", re.IGNORECASE),
    re.compile(r"\bcurrent time\b", re.IGNORECASE),
    re.compile(r"\buser'?s location\b", re.IGNORECASE),
    re.compile(r"\blocation is\b", re.IGNORECASE),
)


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def runtime_lines_from_profile(text: str) -> tuple[list[str], list[str]]:
    runtime: list[str] = []
    durable: list[str] = []
    for line in split_lines(text):
        if any(pattern.search(line) for pattern in RUNTIME_PROFILE_PATTERNS):
            runtime.append(line)
        else:
            durable.append(line)
    return runtime, durable


def pick_latest(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    return max(rows, key=lambda row: row["last_seen"])


def previous_rows(rows: list[dict], current_text: str | None) -> list[dict]:
    if current_text is None:
        return rows
    return [row for row in rows if row["text"] != current_text]


def build_preview(payload: dict) -> dict:
    fields = payload["fields"]

    latest_about_user = pick_latest(fields.get("about_user_message", []))
    latest_about_model = pick_latest(fields.get("about_model_message", []))
    latest_user_profile = pick_latest(fields.get("user_profile", []))
    latest_user_instructions = pick_latest(fields.get("user_instructions", []))

    runtime_profile: list[str] = []
    durable_profile: list[str] = []
    if latest_user_profile:
        runtime_profile, durable_profile = runtime_lines_from_profile(latest_user_profile["text"])

    active_memory = {
        "human": [],
        "persona": [],
        "collaboration": [],
    }
    progressive_memory = {
        "history": [],
    }
    runtime_context = []
    contradictions = []

    if latest_about_user:
        active_memory["human"].append(latest_about_user["text"])

    if latest_about_model:
        active_memory["persona"].append(latest_about_model["text"])

    if durable_profile:
        durable_profile_text = "\n".join(durable_profile)
        if durable_profile_text not in active_memory["human"]:
            active_memory["human"].append(durable_profile_text)

    if latest_user_instructions:
        active_memory["collaboration"].append(latest_user_instructions["text"])

    seen_runtime = set()
    for row in fields.get("user_profile", []):
        row_runtime, _row_durable = runtime_lines_from_profile(row["text"])
        for item in row_runtime:
            if item not in seen_runtime:
                runtime_context.append(item)
                seen_runtime.add(item)

    for field in ("about_user_message", "about_model_message", "user_profile", "user_instructions"):
        rows = fields.get(field, [])
        if len(rows) > 1:
            contradictions.append(
                {
                    "field": field,
                    "count": len(rows),
                    "latest_text": pick_latest(rows)["text"],
                    "historical_texts": [row["text"] for row in previous_rows(rows, pick_latest(rows)["text"])],
                }
            )

    for field in ("about_user_message", "about_model_message", "user_profile", "user_instructions"):
        latest = pick_latest(fields.get(field, []))
        for row in previous_rows(fields.get(field, []), latest["text"] if latest else None):
            historical_text = row["text"]
            if field == "user_profile":
                row_runtime, row_durable = runtime_lines_from_profile(row["text"])
                for item in row_runtime:
                    if item not in seen_runtime:
                        runtime_context.append(item)
                        seen_runtime.add(item)
                historical_text = "\n".join(row_durable).strip()
                if not historical_text:
                    continue
            progressive_memory["history"].append(
                {
                    "field": field,
                    "last_seen": row["last_seen"],
                    "text": historical_text,
                }
            )

    progressive_memory["history"].sort(key=lambda row: row["last_seen"], reverse=True)

    return {
        "active_memory": active_memory,
        "progressive_memory": progressive_memory,
        "runtime_context": runtime_context,
        "contradictions": contradictions,
        "canonical": payload.get("canonical", {}),
        "field_occurrences": payload.get("field_occurrences", {}),
    }


def render_markdown(preview: dict, *, source_path: Path) -> str:
    lines: list[str] = []
    lines.append("# Letta memory preview from ChatGPT saved memory")
    lines.append("")
    lines.append(f"- Source: `{source_path}`")
    lines.append("")

    lines.append("## Likely active memory candidates")
    lines.append("")
    for section in ("human", "persona", "collaboration"):
        lines.append(f"### {section}")
        lines.append("")
        values = preview["active_memory"][section]
        if not values:
            lines.append("*(none)*")
            lines.append("")
            continue
        for value in values:
            lines.append("```text")
            lines.append(value)
            lines.append("```")
            lines.append("")

    lines.append("## Runtime-only context")
    lines.append("")
    if preview["runtime_context"]:
        for item in preview["runtime_context"]:
            lines.append(f"- {item}")
    else:
        lines.append("*(none detected)*")

    lines.append("")
    lines.append("## Historical / progressive-memory candidates")
    lines.append("")
    if preview["progressive_memory"]["history"]:
        for row in preview["progressive_memory"]["history"]:
            lines.append(f"### {row['field']}  ({row['last_seen']})")
            lines.append("")
            lines.append("```text")
            lines.append(row["text"])
            lines.append("```")
            lines.append("")
    else:
        lines.append("*(no historical alternatives found)*")

    lines.append("")
    lines.append("## Contradictions / review items")
    lines.append("")
    if preview["contradictions"]:
        for item in preview["contradictions"]:
            lines.append(f"### {item['field']}")
            lines.append("")
            lines.append("Latest value:")
            lines.append("```text")
            lines.append(item["latest_text"])
            lines.append("```")
            if item["historical_texts"]:
                lines.append("")
                lines.append("Historical alternatives:")
                for text in item["historical_texts"]:
                    lines.append("```text")
                    lines.append(text)
                    lines.append("```")
            lines.append("")
    else:
        lines.append("*(no contradictions found)*")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Letta-oriented preview from extracted ChatGPT saved memory JSON.")
    parser.add_argument("input_path", help="Path to JSON output from extract-saved-memory.py")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    parser.add_argument("--output", help="Write output to this file instead of stdout")
    args = parser.parse_args()

    input_path = Path(args.input_path).expanduser()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    payload = load_payload(input_path)
    preview = build_preview(payload)
    output = json.dumps(preview, indent=2, ensure_ascii=False) if args.json else render_markdown(preview, source_path=input_path)

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()