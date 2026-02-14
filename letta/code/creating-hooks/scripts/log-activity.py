#!/usr/bin/env python3
"""
Log activity - PostToolUse hook

Logs tool usage to a file with timestamps for analysis.
Non-blocking (always exits 0).

Usage: Configure in .letta/settings.json:
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash|Edit|Write|Task",
      "hooks": [{"type": "command", "command": "python hooks/log-activity.py"}]
    }]
  }
}
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Log file location
LOG_FILE = Path.home() / ".letta" / "activity.log"

# Redaction patterns for secrets
REDACT_PATTERNS = [
    (r'[A-Za-z_]*API_KEY[=:]\s*\S+', '[REDACTED_KEY]'),
    (r'[A-Za-z_]*PASSWORD[=:]\s*\S+', '[REDACTED]'),
    (r'[A-Za-z_]*SECRET[=:]\s*\S+', '[REDACTED]'),
    (r'[A-Za-z_]*TOKEN[=:]\s*\S+', '[REDACTED]'),
    (r'Bearer\s+\S+', 'Bearer [REDACTED]'),
    (r'sk-[A-Za-z0-9]+', '[REDACTED_SK]'),
    (r'ghp_[A-Za-z0-9]+', '[REDACTED_GH]'),
]


def redact(text: str) -> str:
    """Redact potential secrets from text."""
    for pattern, replacement in REDACT_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    event_type = input_data.get("event_type", "")
    if event_type != "PostToolUse":
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    working_dir = input_data.get("working_directory", "")
    
    # Build summary based on tool type
    if tool_name == "Bash":
        # Prefer description over raw command for security
        summary = tool_input.get("description", "")
        if not summary:
            cmd = tool_input.get("command", "")[:100]
            summary = f"ran: {redact(cmd)}"
    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "unknown")
        summary = f"edited {Path(file_path).name}"
    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "unknown")
        summary = f"wrote {Path(file_path).name}"
    elif tool_name == "Task":
        desc = tool_input.get("description", "task")
        agent_type = tool_input.get("subagent_type", "")
        summary = f"{desc} ({agent_type})" if agent_type else desc
    else:
        summary = tool_input.get("description", tool_name)
    
    # Format log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {tool_name}: {redact(summary)}\n"
    
    # Append to log file
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Logged: {tool_name}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
