---
name: creating-hooks
license: MIT
description: Guide for creating and managing Letta Code hooks - custom scripts that run at key points in the agent lifecycle. Use when implementing policy enforcement, automated workflows, logging, integrations, or quality checks. Includes quick-start templates, comprehensive reference, and real-world examples. Triggers on queries about hooks, blocking commands, auto-linting, policy enforcement, or hook debugging.
---

# Creating Letta Code Hooks

Hooks let you run custom scripts at key points during Letta Code's execution. Use them to enforce policies, automate workflows, log activity, or integrate with external tools.

## Quick Start

Create a hook in 3 steps:

### 1. Create the hook script

```bash
#!/bin/bash
# hooks/block-rm-rf.sh - Block dangerous rm -rf commands

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if echo "$command" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)'; then
  echo "Blocked: rm -rf commands require manual execution." >&2
  exit 2
fi

exit 0
```

Make it executable: `chmod +x hooks/block-rm-rf.sh`

### 2. Configure the hook

Add to `.letta/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./hooks/block-rm-rf.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. Restart session

Hooks load at session start. Use `/restart` or start a new session.

## Hook Lifecycle

| Hook | When it fires | Can block? | Use case |
|------|---------------|------------|----------|
| `PreToolUse` | Before tool execution | Yes | Policy enforcement, validation |
| `PostToolUse` | After tool completes | No | Logging, broadcasting |
| `Stop` | Agent finishes responding | Yes | Quality checks, auto-fix |
| `SubagentStop` | Subagent task completes | Yes | Capture subagent output |
| `PermissionRequest` | Permission dialog appears | Yes | Auto-approve patterns |
| `UserPromptSubmit` | User submits a prompt | Yes | Input validation |
| `Notification` | Letta sends notification | No | Desktop alerts |
| `PreCompact` | Before context compaction | No | Save state before compaction |
| `SessionStart` | Session begins | No | Initialization |
| `SessionEnd` | Session terminates | No | Cleanup, final logging |
| `Setup` | CLI invoked with `--init` | No | One-time setup |

## Configuration

Hooks are configured in settings files (checked in priority order):

1. `.letta/settings.local.json` - Local (not committed)
2. `.letta/settings.json` - Project (shareable)
3. `~/.letta/settings.json` - Global user settings

Hooks from all locations are **merged**, with local hooks running first.

### Matchers

Tool-related hooks (`PreToolUse`, `PostToolUse`, `PermissionRequest`) use matchers:

| Pattern | Matches |
|---------|---------|
| `"Bash"` | Exact tool name |
| `"Edit\|Write"` | Multiple tools (regex) |
| `"Notebook.*"` | Regex pattern |
| `"*"` or `""` | All tools |

Simple hooks (`Stop`, `Notification`) don't need matchers.

## Writing Hooks

### Input Format

Hooks receive JSON via stdin:

```json
{
  "event_type": "PreToolUse",
  "working_directory": "/path/to/project",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite"
  }
}
```

**PostToolUse** and **Stop** also include reasoning context:
- `preceding_reasoning` - Agent's thinking
- `assistant_message` - Agent's response (Stop only)

### Exit Codes

| Exit Code | Behavior |
|-----------|----------|
| `0` | Success - action proceeds |
| `1` | Non-blocking error - logged, continues |
| `2` | **Blocking** - action stopped, stderr sent to agent |

Exit code 2 is powerful: it blocks the action AND sends your stderr message as feedback to the agent, allowing it to adjust.

### Languages

Hooks can be any executable. Common choices:

**Bash** - Simple, fast, good for pattern matching:
```bash
#!/bin/bash
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
```

**Python** - Complex logic, API calls:
```python
#!/usr/bin/env python3
import sys, json
input_data = json.load(sys.stdin)
```

### Timeouts

Default: 60 seconds. Configure custom timeout:

```json
{
  "type": "command",
  "command": "./hooks/slow-check.sh",
  "timeout": 120000
}
```

## Common Patterns

### Pattern 1: Block dangerous commands (PreToolUse)

See `scripts/block-dangerous.sh` - prevents `rm -rf`, `git push --force`, etc.

### Pattern 2: Auto-lint on changes (Stop)

See `scripts/auto-lint.sh` - runs linter when files changed, blocks if errors.

### Pattern 3: Log activity (PostToolUse)

See `scripts/log-activity.py` - logs tool usage with timestamps.

### Pattern 4: Policy enforcement (PreToolUse)

See `scripts/enforce-policy.py` - advanced pattern matching with agent detection.

## Detailed References

- **Hook types**: See `references/hook-types.md` for all fields per event type
- **Advanced patterns**: See `references/patterns.md` for secret redaction, API integration, deduplication
- **Troubleshooting**: See `references/troubleshooting.md` for common issues

## Best Practices

1. **Make scripts executable** - `chmod +x hooks/*.sh`
2. **Use description, not raw commands** - For security, prefer `tool_input.description`
3. **Keep hooks fast** - They block synchronously
4. **Test manually first** - `echo '{"event_type":"PreToolUse",...}' | ./hooks/test.sh`
5. **Use exit 2 sparingly** - Only block when you have actionable feedback
6. **Redact secrets** - Apply patterns before logging (see patterns.md)

## Security

Hooks execute arbitrary shell commands. Only use hooks from trusted sources. Review scripts before enabling.
