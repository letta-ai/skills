#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import json
import re
import zipfile
from pathlib import Path
from typing import Any


def normalize_iso(value: object) -> str:
    if value in (None, ""):
        return "-"
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(float(value), dt.timezone.utc).isoformat()
        except Exception:
            return str(value)

    text = str(value).strip()
    if not text:
        return "-"

    try:
        if text.endswith("Z"):
            return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
        return dt.datetime.fromisoformat(text).isoformat()
    except Exception:
        return text


def sort_key_for_time(value: object) -> tuple[int, str]:
    text = normalize_iso(value)
    if text != "-":
        try:
            instant = dt.datetime.fromisoformat(text)
            if instant.tzinfo is None:
                instant = instant.replace(tzinfo=dt.timezone.utc)
            text = instant.astimezone(dt.timezone.utc).isoformat()
        except (ValueError, OverflowError):
            pass  # Keep unrecognized timestamps sortable without changing their display.
    return (1 if text != "-" else 0, text)


def load_json(export_path: Path, name: str) -> Any:
    export_path = export_path.expanduser()
    if export_path.is_dir():
        path = export_path / name
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    if export_path.is_file() and export_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(export_path) as zf:
            if name not in zf.namelist():
                return None
            return json.loads(zf.read(name))

    raise SystemExit(f"Unsupported export path: {export_path}")


def load_conversations(export_path: Path) -> tuple[list[dict], str]:
    export_path = export_path.expanduser()

    if export_path.is_dir():
        data = load_json(export_path, "conversations.json")
        if not isinstance(data, list):
            raise SystemExit(f"Expected conversations.json list in {export_path}")
        return data, detect_schema(data)

    if export_path.is_file() and export_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(export_path) as zf:
            names = set(zf.namelist())
            if "conversations.json" in names:
                data = json.loads(zf.read("conversations.json"))
                if not isinstance(data, list):
                    raise SystemExit(f"Expected conversations.json list in {export_path}")
                return data, detect_schema(data)

            shard_names = sorted(name for name in names if name.startswith("conversations-") and name.endswith(".json"))
            if shard_names:
                rows: list[dict] = []
                for shard_name in shard_names:
                    shard = json.loads(zf.read(shard_name))
                    if isinstance(shard, list):
                        rows.extend(shard)
                return rows, detect_schema(rows)

    raise SystemExit(f"Could not find conversation data in {export_path}")


def detect_schema(conversations: list[dict]) -> str:
    if not conversations:
        return "unknown"
    first = conversations[0]
    if isinstance(first, dict) and "chat_messages" in first:
        return "modern"
    if isinstance(first, dict) and "mapping" in first:
        return "legacy"
    return "unknown"


def conversation_title(conversation: dict, schema: str) -> str:
    if schema == "modern":
        return conversation.get("name") or "(untitled)"
    return conversation.get("title") or "(untitled)"


def conversation_created(conversation: dict, schema: str) -> object:
    return conversation.get("created_at") if schema == "modern" else conversation.get("create_time")


def conversation_updated(conversation: dict, schema: str) -> object:
    return conversation.get("updated_at") if schema == "modern" else conversation.get("update_time")


def conversation_uuid(conversation: dict, schema: str) -> str:
    return str(conversation.get("uuid") or conversation.get("id") or "")


def modern_message_types(message: dict) -> list[str]:
    types: list[str] = []
    content = message.get("content") or []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type") or "unknown"
                if item_type not in types:
                    types.append(item_type)
    return types


def modern_message_text(message: dict) -> str:
    text = message.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    chunks: list[str] = []
    content = message.get("content") or []
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "text" and isinstance(item.get("text"), str) and item.get("text").strip():
                chunks.append(item["text"].strip())
            elif item_type == "voice_note":
                transcript = item.get("transcript") or item.get("text")
                if isinstance(transcript, str) and transcript.strip():
                    chunks.append("Voice note:\n" + transcript.strip())
            elif isinstance(item.get("message"), str) and item.get("message").strip():
                chunks.append(item["message"].strip())
            elif isinstance(item.get("display_content"), str) and item.get("display_content").strip():
                chunks.append(item["display_content"].strip())
    return "\n\n".join(chunks).strip()


def legacy_content_to_text(content: object) -> str:
    if not isinstance(content, dict):
        return ""

    content_type = content.get("content_type")
    if content_type == "user_editable_context":
        sections: list[str] = []
        user_profile = content.get("user_profile")
        user_instructions = content.get("user_instructions")
        if isinstance(user_profile, str) and user_profile.strip():
            sections.append("User profile:\n\n" + user_profile.strip())
        if isinstance(user_instructions, str) and user_instructions.strip():
            sections.append("User instructions:\n\n" + user_instructions.strip())
        return "\n\n".join(sections).strip()

    parts = content.get("parts")
    if isinstance(parts, list):
        chunks: list[str] = []
        for part in parts:
            if isinstance(part, str):
                if part.strip():
                    chunks.append(part.strip())
            elif isinstance(part, dict):
                chunks.append(json.dumps(part, ensure_ascii=False))
        return "\n\n".join(chunk for chunk in chunks if chunk.strip()).strip()

    if isinstance(content.get("text"), str) and content.get("text").strip():
        return content["text"].strip()

    return ""


def legacy_message_types(message: dict) -> list[str]:
    content = message.get("content") or {}
    if isinstance(content, dict) and content.get("content_type"):
        return [str(content.get("content_type"))]
    return []


def normalize_message(message: dict, schema: str, *, node_id: str | None = None) -> dict:
    if schema == "modern":
        sender = str(message.get("sender") or "unknown")
        return {
            "sender": canonical_role(sender),
            "raw_sender": sender,
            "created_at": message.get("created_at"),
            "updated_at": message.get("updated_at"),
            "text": modern_message_text(message),
            "item_types": modern_message_types(message),
            "content": message.get("content") or [],
            "uuid": message.get("uuid"),
        }

    author = (message.get("author") or {}) if isinstance(message, dict) else {}
    sender = str(author.get("role") or author.get("name") or "unknown")
    content = message.get("content") or {}
    metadata = message.get("metadata") or {}
    return {
        "sender": canonical_role(sender),
        "raw_sender": sender,
        "created_at": message.get("create_time"),
        "updated_at": message.get("create_time"),
        "text": legacy_content_to_text(content),
        "item_types": legacy_message_types(message),
        "content": content,
        "metadata": metadata,
        "node_id": node_id,
    }


def conversation_messages(conversation: dict, schema: str) -> list[dict]:
    rows: list[dict] = []

    if schema == "modern":
        for message in conversation.get("chat_messages") or []:
            if isinstance(message, dict):
                rows.append(normalize_message(message, schema))
        rows.sort(key=lambda row: (sort_key_for_time(row.get("created_at")), str(row.get("uuid") or "")))
        return rows

    for node_id, node in (conversation.get("mapping") or {}).items():
        message = (node or {}).get("message") or {}
        if not message:
            continue
        rows.append(normalize_message(message, schema, node_id=node_id))
    rows.sort(key=lambda row: (sort_key_for_time(row.get("created_at")), str(row.get("node_id") or "")))
    return rows


def canonical_role(role: str) -> str:
    lowered = (role or "unknown").lower()
    if lowered in {"human", "user"}:
        return "user"
    return lowered


def role_matches(message_role: str, allowed_roles: set[str] | None) -> bool:
    if not allowed_roles:
        return True
    canonical = canonical_role(message_role)
    expanded = {canonical}
    if canonical == "user":
        expanded.add("human")
    return not allowed_roles.isdisjoint(expanded)


def message_has_thinking(message: dict) -> bool:
    return "thinking" in set(message.get("item_types") or [])


def message_has_nontext(message: dict) -> bool:
    for item_type in message.get("item_types") or []:
        if item_type != "text":
            return True
    return False


def compact_json(data: object, *, limit: int = 1200) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n..."


def snippet(text: str, *, length: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= length:
        return cleaned
    return cleaned[: length - 1].rstrip() + "…"
