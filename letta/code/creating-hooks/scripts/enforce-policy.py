#!/usr/bin/env python3
"""
Enforce policy - PreToolUse hook

Advanced policy enforcement with:
- Pattern-based command blocking
- Agent ID detection (for multi-agent setups)
- Configurable allow/block lists
- Helpful feedback messages

Usage: Configure in .letta/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "python hooks/enforce-policy.py"}]
    }]
  }
}
"""

import sys
import json
import os
import re

# ============================================================================
# CONFIGURATION - Customize these for your policy
# ============================================================================

# Agent IDs that are allowed to bypass this policy
# Useful for multi-agent setups where some agents have elevated permissions
ALLOWED_AGENTS = {
    # "agent-xxx-yyy-zzz",  # Example: comms agent allowed to post
}

# Patterns to block (case-insensitive regex)
BLOCKED_PATTERNS = [
    (r"tools\.thread", "Use comms subagent for posting threads"),
    (r"create_post", "Use comms subagent for creating posts"),
    (r"git\s+push.*--force", "Force push requires manual approval"),
    (r"rm\s+-rf\s+/", "Cannot rm -rf root paths"),
]

# Patterns to always allow (checked before blocked patterns)
ALLOWED_PATTERNS = [
    r"git\s+status",
    r"git\s+diff",
    r"git\s+log",
    r"echo\s+",
]

# ============================================================================
# HOOK IMPLEMENTATION
# ============================================================================


def main():
    """Process PreToolUse hook input."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"POLICY: Failed to parse input: {e}", file=sys.stderr)
        sys.exit(0)  # Allow on parse failure (fail open)
    
    event_type = input_data.get("event_type")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only process PreToolUse events
    if event_type != "PreToolUse":
        sys.exit(0)
    
    # Only check Bash commands (modify matcher in settings for other tools)
    if tool_name != "Bash":
        sys.exit(0)
    
    # Check agent identity - allow specific agents to bypass
    agent_id = os.environ.get("LETTA_AGENT_ID", "")
    if agent_id in ALLOWED_AGENTS:
        print(f"POLICY: Agent {agent_id[:20]}... is allowed", file=sys.stderr)
        sys.exit(0)
    
    # Get the command being run
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    # Check allowed patterns first
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            sys.exit(0)
    
    # Check blocked patterns
    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Truncate command for display
            cmd_display = command[:100] + ("..." if len(command) > 100 else "")
            
            block_message = f"""POLICY VIOLATION: Command blocked.

Command: {cmd_display}
Reason: {message}

If this is intentional, modify the policy in hooks/enforce-policy.py
or ask the user to run the command manually.
"""
            print(block_message, file=sys.stderr)
            sys.exit(2)  # Block the action
    
    # No policy violation, allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
