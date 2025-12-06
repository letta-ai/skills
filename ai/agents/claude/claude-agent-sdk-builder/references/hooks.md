# Hooks Reference

Complete guide to using hooks for advanced event handling and behavior modification in Claude Agent SDK.

## Overview

Hooks intercept agent events (tool use, user prompts, etc.) to add custom logic like logging, validation, or behavior modification.

## Available Hook Events

### Python

```python
- PreToolUse      # Before tool execution
- PostToolUse     # After tool execution
- UserPromptSubmit  # When user submits prompt
- Stop           # When stopping execution
- SubagentStop   # When subagent stops
- PreCompact     # Before message compaction
```

**Note:** Python SDK does not support SessionStart, SessionEnd, and Notification hooks due to setup limitations.

### TypeScript

```typescript
- PreToolUse
- PostToolUse
- Notification
- UserPromptSubmit
- SessionStart
- SessionEnd
- Stop
- SubagentStop
- PreCompact
```

## Basic Hook Usage

### Python Example

```python
from claude_agent_sdk import ClaudeAgentOptions

async def log_tool_use(input_data, tool_use_id, context):
    """Log all tool calls."""
    tool_name = input_data.get("tool_name")
    print(f"Tool used: {tool_name}")
    return {}  # Continue execution

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"hooks": [log_tool_use]}
        ]
    }
)
```

### TypeScript Example

```typescript
import type { HookCallback } from '@anthropic-ai/claude-agent-sdk';

const logToolUse: HookCallback = async (input, toolUseId, { signal }) => {
    console.log(`Tool used: ${input.tool_name}`);
    return {};  // Continue execution
};

const options = {
    hooks: {
        PreToolUse: [
            { hooks: [logToolUse] }
        ]
    }
};
```

## Hook Input Data

### PreToolUse

```python
{
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {
        "command": "ls -la",
        "timeout": 30000
    },
    "session_id": "abc123",
    "transcript_path": "/path/to/transcript",
    "cwd": "/working/directory"
}
```

### PostToolUse

```python
{
    "hook_event_name": "PostToolUse",
    "tool_name": "Read",
    "tool_input": {"file_path": "/path/to/file.txt"},
    "tool_response": {
        "content": "File contents...",
        "total_lines": 100
    },
    "session_id": "abc123"
}
```

### UserPromptSubmit

```python
{
    "hook_event_name": "UserPromptSubmit",
    "prompt": "What files are in this directory?",
    "session_id": "abc123"
}
```

## Hook Return Values

### Continue Execution

```python
return {}  # or return {"continue": True}
```

### Block Execution

```python
return {
    "decision": "block",
    "systemMessage": "Operation blocked for security reasons",
    "reason": "Dangerous command detected"
}
```

### Tool Permission Decision (PreToolUse only)

```python
return {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",  # "allow", "deny", "ask"
        "permissionDecisionReason": "Command not allowed"
    }
}
```

### Add Context (PostToolUse, UserPromptSubmit, SessionStart)

```python
return {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "Note: This file was recently modified"
    }
}
```

## Common Hook Patterns

### 1. Command Validation

Block dangerous commands:

```python
async def validate_bash(input_data, tool_use_id, context):
    """Block dangerous bash commands."""
    if input_data.get("tool_name") != "Bash":
        return {}
    
    command = input_data.get("tool_input", {}).get("command", "")
    
    dangerous_patterns = [
        "rm -rf /",
        ":(){ :|:& };:",  # Fork bomb
        "dd if=/dev/zero",
        "mkfs."
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous command blocked: {pattern}"
                }
            }
    
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [validate_bash]}
        ]
    }
)
```

### 2. Audit Logging

Log all tool usage:

```python
import json
from datetime import datetime

async def audit_log(input_data, tool_use_id, context):
    """Log all tool usage to audit trail."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": input_data.get("hook_event_name"),
        "tool_name": input_data.get("tool_name"),
        "tool_input": input_data.get("tool_input"),
        "session_id": input_data.get("session_id")
    }
    
    with open("audit.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [{"hooks": [audit_log]}],
        "PostToolUse": [{"hooks": [audit_log]}]
    }
)
```

### 3. Rate Limiting

Limit tool usage frequency:

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Global rate limit tracker
rate_tracker = defaultdict(list)

async def rate_limit_hook(input_data, tool_use_id, context):
    """Enforce rate limits on tool usage."""
    tool_name = input_data.get("tool_name")
    max_calls = 10
    window_seconds = 60
    
    now = datetime.now()
    cutoff = now - timedelta(seconds=window_seconds)
    
    # Clean old entries
    rate_tracker[tool_name] = [
        t for t in rate_tracker[tool_name] if t > cutoff
    ]
    
    # Check limit
    if len(rate_tracker[tool_name]) >= max_calls:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Rate limit exceeded: max {max_calls} calls per {window_seconds}s"
            }
        }
    
    # Record this call
    rate_tracker[tool_name].append(now)
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [{"hooks": [rate_limit_hook]}]
    }
)
```

### 4. Input Sanitization

Modify tool inputs:

```python
async def sanitize_paths(input_data, tool_use_id, context):
    """Ensure file paths are within allowed directory."""
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name in ["Read", "Write", "Edit"]:
        file_path = tool_input.get("file_path", "")
        
        # Ensure path is in sandbox
        if not file_path.startswith("/sandbox/"):
            # Block or redirect
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "File path must be in /sandbox/ directory"
                }
            }
    
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {
                "matcher": "Read|Write|Edit",
                "hooks": [sanitize_paths]
            }
        ]
    }
)
```

### 5. Performance Monitoring

Track tool execution time:

```python
from time import time

# Global metrics
metrics = {}

async def start_timer(input_data, tool_use_id, context):
    """Record tool start time."""
    if tool_use_id:
        metrics[tool_use_id] = time()
    return {}

async def end_timer(input_data, tool_use_id, context):
    """Calculate and log tool duration."""
    if tool_use_id and tool_use_id in metrics:
        duration = time() - metrics[tool_use_id]
        tool_name = input_data.get("tool_name")
        print(f"{tool_name} took {duration:.2f}s")
        del metrics[tool_use_id]
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [{"hooks": [start_timer]}],
        "PostToolUse": [{"hooks": [end_timer]}]
    }
)
```

### 6. Context Enhancement

Add helpful context after tool use:

```python
async def enhance_context(input_data, tool_use_id, context):
    """Add context based on tool results."""
    tool_name = input_data.get("tool_name")
    tool_response = input_data.get("tool_response", {})
    
    additional_context = ""
    
    if tool_name == "Read":
        # Add file metadata
        file_path = input_data.get("tool_input", {}).get("file_path", "")
        additional_context = f"Note: {file_path} was last modified recently. Consider checking version history."
    
    elif tool_name == "Bash":
        # Add execution context
        exit_code = tool_response.get("exitCode")
        if exit_code != 0:
            additional_context = "The command failed. Consider checking logs or error output."
    
    if additional_context:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": additional_context
            }
        }
    
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PostToolUse": [{"hooks": [enhance_context]}]
    }
)
```

## Hook Matchers

Match specific tools or patterns:

### Single Tool

```python
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [validate_bash]}
        ]
    }
)
```

### Multiple Tools (OR pattern)

```python
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"matcher": "Read|Write|Edit", "hooks": [file_hook]}
        ]
    }
)
```

### All Tools

```python
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"hooks": [log_all]}  # No matcher = all tools
        ]
    }
)
```

### Multiple Hooks for Same Event

```python
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [validate_bash]},
            {"matcher": "Write|Edit", "hooks": [validate_writes]},
            {"hooks": [log_all]}  # Runs for all tools
        ]
    }
)
```

## Advanced Patterns

### Conditional Execution

```python
async def conditional_hook(input_data, tool_use_id, context):
    """Only execute hook under certain conditions."""
    session_id = input_data.get("session_id")
    
    # Check if this is a production session
    if is_production_session(session_id):
        # Extra validation for production
        return validate_production(input_data)
    
    return {}  # Skip validation for dev/test
```

### Async External Validation

```python
import httpx

async def external_validation(input_data, tool_use_id, context):
    """Call external service for validation."""
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://validator.example.com/validate",
            json={"tool": tool_name, "input": tool_input}
        )
        
        if not response.json().get("allowed"):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "External validation failed"
                }
            }
    
    return {}
```

### State Management

```python
class HookState:
    """Maintain state across hook calls."""
    def __init__(self):
        self.tool_count = 0
        self.errors = []
    
    async def count_tools(self, input_data, tool_use_id, context):
        self.tool_count += 1
        
        if self.tool_count > 100:
            return {
                "decision": "block",
                "systemMessage": "Tool usage limit reached",
                "reason": "Maximum 100 tool calls per session"
            }
        
        return {}
    
    async def track_errors(self, input_data, tool_use_id, context):
        tool_response = input_data.get("tool_response", {})
        
        if tool_response.get("isError"):
            self.errors.append({
                "tool": input_data.get("tool_name"),
                "time": datetime.now()
            })
        
        return {}

# Use in agent
hook_state = HookState()

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [{"hooks": [hook_state.count_tools]}],
        "PostToolUse": [{"hooks": [hook_state.track_errors]}]
    }
)
```

## Testing Hooks

### Unit Testing

```python
import pytest

@pytest.mark.asyncio
async def test_validate_bash_blocks_dangerous_command():
    input_data = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /"}
    }
    
    result = await validate_bash(input_data, None, None)
    
    assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

@pytest.mark.asyncio
async def test_validate_bash_allows_safe_command():
    input_data = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"}
    }
    
    result = await validate_bash(input_data, None, None)
    
    assert result == {}  # No blocking
```

### Integration Testing

```python
from claude_agent_sdk import query, ClaudeAgentOptions

@pytest.mark.asyncio
async def test_hook_blocks_dangerous_command():
    options = ClaudeAgentOptions(
        hooks={
            "PreToolUse": [{"matcher": "Bash", "hooks": [validate_bash]}]
        },
        allowed_tools=["Bash"],
        permission_mode="bypassPermissions"
    )
    
    messages = []
    async for message in query(
        prompt="Run: rm -rf /",
        options=options
    ):
        messages.append(message)
    
    # Assert command was blocked
    # Check messages for permission denial
```

## Best Practices

### 1. Keep Hooks Fast

Hooks run synchronously in the tool execution path. Minimize latency:

```python
async def fast_hook(input_data, tool_use_id, context):
    """Quick validation only."""
    # Do minimal work
    if simple_check(input_data):
        return {"decision": "block"}
    
    return {}
```

### 2. Handle Errors Gracefully

```python
async def safe_hook(input_data, tool_use_id, context):
    """Hook with error handling."""
    try:
        result = await process(input_data)
        return result
    except Exception as e:
        # Log error but don't block execution
        print(f"Hook error: {e}")
        return {}  # Allow execution to continue
```

### 3. Use Matchers Efficiently

```python
# Good: Specific matcher
{"matcher": "Bash|Write", "hooks": [expensive_validation]}

# Bad: Runs for all tools
{"hooks": [expensive_validation]}
```

### 4. Document Hook Behavior

```python
async def documented_hook(input_data, tool_use_id, context):
    """
    Validates file paths for Read/Write/Edit operations.
    
    Blocks operations on:
    - System directories (/etc, /sys, /proc)
    - Hidden files (starting with .)
    - Paths outside /sandbox/
    
    Returns:
        - {} to allow operation
        - {"hookSpecificOutput": {...}} to deny with reason
    """
    # Implementation
    pass
```

## Troubleshooting

### Hook Not Executing

**Problem:** Hook doesn't run.

**Solution:** Check matcher and event name:
```python
# Verify tool name matches
{"matcher": "Bash", "hooks": [my_hook]}  # Exact match

# Verify event name
hooks={"PreToolUse": [...]}  # Correct spelling
```

### Hook Blocks All Tools

**Problem:** No tools work.

**Solution:** Check return value:
```python
# Wrong: Blocks execution
return {"decision": "block"}

# Right: Allows execution
return {}
```

### Async Context Not Working

**Problem:** Can't use await in hook.

**Solution:** Define hook as async:
```python
# Wrong
def my_hook(input_data, tool_use_id, context):
    result = await some_async_call()  # Error!

# Right
async def my_hook(input_data, tool_use_id, context):
    result = await some_async_call()  # Works!
```

## Next Steps

- Review [Tool Permissions Reference](./tool_permissions.md) for complementary permission control
- Check [System Prompts Guide](./system_prompts.md) for behavioral guidelines
- Explore [MCP Integration Guide](./mcp_integration.md) for custom tools
