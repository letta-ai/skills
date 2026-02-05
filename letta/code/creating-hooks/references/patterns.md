# Advanced Hook Patterns

Real-world patterns from production hooks.

## Secret Redaction

Always redact secrets before logging or broadcasting:

```python
import re

REDACT_PATTERNS = [
    (r'[A-Za-z_]*API_KEY[=:]\s*\S+', '[REDACTED_KEY]'),
    (r'[A-Za-z_]*PASSWORD[=:]\s*\S+', '[REDACTED]'),
    (r'[A-Za-z_]*SECRET[=:]\s*\S+', '[REDACTED]'),
    (r'[A-Za-z_]*TOKEN[=:]\s*\S+', '[REDACTED]'),
    (r'Bearer\s+\S+', 'Bearer [REDACTED]'),
    (r'sk-[A-Za-z0-9]+', '[REDACTED_SK]'),     # OpenAI keys
    (r'ghp_[A-Za-z0-9]+', '[REDACTED_GH]'),    # GitHub tokens
    (r'xoxb-[A-Za-z0-9-]+', '[REDACTED_SLACK]'), # Slack tokens
]

def redact(text: str) -> str:
    for pattern, replacement in REDACT_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text
```

## Message Deduplication

Track published messages to avoid duplicates:

```python
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".letta" / "hooks.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS published_messages (
            message_id TEXT PRIMARY KEY,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_published(message_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute(
        "SELECT 1 FROM published_messages WHERE message_id = ?",
        (message_id,)
    ).fetchone()
    conn.close()
    return result is not None

def mark_published(message_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO published_messages (message_id) VALUES (?)",
        (message_id,)
    )
    conn.commit()
    conn.close()
```

## Letta API Integration

Fetch messages from Letta API in hooks:

```python
import os
import httpx

LETTA_API_KEY = os.environ.get("LETTA_API_KEY")
LETTA_AGENT_ID = os.environ.get("LETTA_AGENT_ID")
LETTA_API_BASE = "https://api.letta.com/v1"

def get_recent_messages(limit: int = 20) -> list:
    if not LETTA_API_KEY:
        return []
    
    resp = httpx.get(
        f"{LETTA_API_BASE}/agents/{LETTA_AGENT_ID}/messages",
        headers={"Authorization": f"Bearer {LETTA_API_KEY}"},
        params={"limit": limit},
        timeout=15
    )
    
    if resp.status_code != 200:
        return []
    
    messages = resp.json()
    result = []
    
    for msg in messages:
        msg_type = msg.get("message_type")
        
        if msg_type == "assistant_message":
            content = msg.get("content", "")
        elif msg_type == "reasoning_message":
            content = msg.get("reasoning", "")  # Different field!
        else:
            continue
        
        if content and len(content) > 10:
            result.append({
                "content": content,
                "type": msg_type,
                "id": msg.get("id")
            })
    
    return result
```

## Multi-Agent Policy

Different policies for different agents:

```python
import os

# Agent-specific permissions
AGENT_PERMISSIONS = {
    "agent-comms-xxx": {"can_post": True, "can_edit_memory": False},
    "agent-central-yyy": {"can_post": False, "can_edit_memory": True},
}

def check_permission(action: str) -> bool:
    agent_id = os.environ.get("LETTA_AGENT_ID", "")
    permissions = AGENT_PERMISSIONS.get(agent_id, {})
    return permissions.get(action, False)

def main():
    input_data = json.load(sys.stdin)
    command = input_data.get("tool_input", {}).get("command", "")
    
    if "create_post" in command and not check_permission("can_post"):
        print("BLOCKED: This agent cannot post directly.", file=sys.stderr)
        sys.exit(2)
```

## External API Broadcasting

Post activity to external services:

```python
import httpx
from datetime import datetime, timezone

def broadcast_activity(tool_name: str, summary: str):
    """Post to external API (e.g., ATProtocol, Slack, Discord)."""
    
    # Example: ATProtocol
    session = get_atproto_session()  # Your auth function
    
    record = {
        "$type": "network.comind.activity",
        "tool": tool_name,
        "summary": summary[:200],
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    resp = httpx.post(
        f"{PDS}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {session['accessJwt']}"},
        json={"repo": DID, "collection": "network.comind.activity", "record": record},
        timeout=10
    )
    
    return resp.status_code == 200
```

## Conditional Hook Execution

Skip hooks based on conditions:

```python
def should_skip(input_data: dict) -> bool:
    tool_input = input_data.get("tool_input", {})
    description = tool_input.get("description", "").lower()
    
    # Skip noisy operations
    skip_patterns = ["status", "check", "list", "queue"]
    if any(p in description for p in skip_patterns):
        return True
    
    # Skip if no meaningful content
    command = tool_input.get("command", "")
    if len(command) < 5:
        return True
    
    return False

def main():
    input_data = json.load(sys.stdin)
    
    if should_skip(input_data):
        sys.exit(0)
    
    # Continue with hook logic...
```

## Capturing Subagent Output

Use SubagentStop to capture and process subagent results:

```python
def main():
    input_data = json.load(sys.stdin)
    
    if input_data.get("event_type") != "SubagentStop":
        sys.exit(0)
    
    subagent_type = input_data.get("subagent_type", "")
    output = input_data.get("output", "")
    
    # Example: Save comms drafts to file
    if subagent_type == "comms":
        draft_path = Path("drafts") / f"{datetime.now():%Y%m%d-%H%M%S}.md"
        draft_path.parent.mkdir(exist_ok=True)
        draft_path.write_text(output)
        print(f"Saved draft: {draft_path}", file=sys.stderr)
    
    sys.exit(0)
```

## Debug Logging

Log hook inputs for debugging:

```python
from pathlib import Path
import json

LOG_DIR = Path.home() / ".letta" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_debug(input_data: dict, hook_name: str):
    log_file = LOG_DIR / f"hook_{hook_name}_debug.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(input_data) + "\n")
```

Enable during development, disable in production for performance.
