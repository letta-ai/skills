# Tool Permissions Reference

Complete guide to managing tool permissions in Claude Agent SDK applications.

## Overview

Tool permissions control which operations your agent can perform. Proper permission management ensures security while enabling agent capabilities.

## Permission Modes

### 1. default
Standard permission behavior - agent asks for approval before executing tools.

**When to use:**
- Production agents with human oversight
- Testing new agent behaviors
- Agents that modify critical resources

**Example:**
```python
options = ClaudeAgentOptions(
    permission_mode="default"
)
```

### 2. acceptEdits
Auto-approve file edit operations (Edit, Write tools). Other tools still require approval.

**When to use:**
- Code generation agents
- Content creation workflows
- Trusted development environments

**Example:**
```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",
    allowed_tools=["Read", "Write", "Edit", "Bash"]
)
```

### 3. plan
Planning mode - agent creates execution plan without running commands.

**When to use:**
- Preview agent's intended actions
- Generate implementation plans
- Educational/demonstration purposes

**Example:**
```python
options = ClaudeAgentOptions(
    permission_mode="plan"
)
```

### 4. bypassPermissions
Bypass all permission checks - agent executes all tools without approval.

**When to use (with caution):**
- Fully automated CI/CD pipelines
- Read-only operations
- Sandboxed environments

**Example:**
```python
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    allowed_tools=["Read", "Grep", "Glob"]  # Limit to safe tools
)
```

## Tool Allowlists and Denylists

### Simple Allowlist

Specify exactly which tools the agent can use:

```python
options = ClaudeAgentOptions(
    allowed_tools=[
        "Read",      # Read files
        "Write",     # Write files
        "Edit",      # Edit files
        "Bash",      # Execute commands
        "Grep",      # Search files
        "Glob"       # Find files by pattern
    ]
)
```

### Denylist Pattern

Allow all tools except specific ones:

```python
options = ClaudeAgentOptions(
    disallowed_tools=[
        "WebFetch",   # Block web access
        "WebSearch",  # Block web search
        "Bash"        # Block command execution
    ]
)
```

### Combined Approach

Use both for fine-grained control:

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep"],
    disallowed_tools=["Bash"]  # Override - block Bash even if in allowed_tools
)
```

## Available Tools

### File Operations
- `Read` - Read file contents
- `Write` - Write/create files
- `Edit` - Modify existing files
- `Glob` - Find files by pattern
- `Grep` - Search file contents

### Code Execution
- `Bash` - Execute shell commands
- `BashOutput` - Retrieve output from background shells
- `KillBash` - Terminate background shells
- `NotebookEdit` - Edit Jupyter notebooks

### Web Access
- `WebFetch` - Fetch and process web pages
- `WebSearch` - Search the web

### Task Management
- `Task` - Launch subagents
- `TodoWrite` - Manage task lists
- `ExitPlanMode` - Exit planning mode

### MCP Resources
- `ListMcpResources` - List MCP server resources
- `ReadMcpResource` - Read MCP resources

## Custom Permission Logic

Implement fine-grained permission control with custom functions:

### Basic Example

```python
async def custom_permissions(tool_name, input_data, context):
    """Block dangerous operations."""
    
    # Block system directory writes
    if tool_name == "Write":
        path = input_data.get("file_path", "")
        if path.startswith("/system/") or path.startswith("/etc/"):
            return {
                "behavior": "deny",
                "message": "Cannot write to system directories",
                "interrupt": True
            }
    
    # Block dangerous bash commands
    if tool_name == "Bash":
        command = input_data.get("command", "")
        if "rm -rf" in command:
            return {
                "behavior": "deny",
                "message": "Dangerous command blocked"
            }
    
    # Allow everything else
    return {
        "behavior": "allow",
        "updatedInput": input_data
    }

options = ClaudeAgentOptions(
    can_use_tool=custom_permissions
)
```

### Advanced Example - Path Redirection

```python
async def sandbox_permissions(tool_name, input_data, context):
    """Redirect operations to sandbox directory."""
    
    SANDBOX_DIR = "/home/user/sandbox/"
    
    # Redirect file operations to sandbox
    if tool_name in ["Read", "Write", "Edit"]:
        original_path = input_data.get("file_path", "")
        
        # Block absolute paths outside sandbox
        if original_path.startswith("/") and not original_path.startswith(SANDBOX_DIR):
            sandboxed_path = os.path.join(SANDBOX_DIR, original_path.lstrip("/"))
            return {
                "behavior": "allow",
                "updatedInput": {
                    **input_data,
                    "file_path": sandboxed_path
                }
            }
    
    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(
    can_use_tool=sandbox_permissions
)
```

### Logging and Auditing

```python
import logging

logger = logging.getLogger("agent_permissions")

async def audit_permissions(tool_name, input_data, context):
    """Log all tool usage for audit trail."""
    
    logger.info(f"Tool: {tool_name}, Input: {input_data}")
    
    # Allow all but log everything
    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(
    can_use_tool=audit_permissions
)
```

## Permission Return Values

Custom permission functions return dictionaries with:

### Allow Pattern

```python
return {
    "behavior": "allow",
    "updatedInput": input_data  # Modified or original input
}
```

### Deny Pattern

```python
return {
    "behavior": "deny",
    "message": "Reason for denial",
    "interrupt": True  # Optional: stop agent execution
}
```

## Security Best Practices

### 1. Start Restrictive

Begin with minimal permissions and expand as needed:

```python
# Start with read-only
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],
    permission_mode="bypassPermissions"
)
```

### 2. Separate Concerns

Use different permission configurations for different agent types:

```python
# Read-only analysis agent
analysis_options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep"],
    permission_mode="bypassPermissions"
)

# Development agent with edits
dev_options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    permission_mode="acceptEdits"
)
```

### 3. Use Subagents for Isolation

Delegate risky operations to subagents with limited permissions:

```python
options = ClaudeAgentOptions(
    agents={
        "file-reader": {
            "description": "Reads and analyzes files",
            "prompt": "You can only read files, not modify them",
            "tools": ["Read", "Grep", "Glob"]
        },
        "file-writer": {
            "description": "Writes files after review",
            "prompt": "Only write files after explicit user approval",
            "tools": ["Write", "Edit"]
        }
    }
)
```

### 4. Validate Input

Always validate tool inputs in custom permission functions:

```python
async def validate_inputs(tool_name, input_data, context):
    if tool_name == "Bash":
        command = input_data.get("command", "")
        
        # Validate command length
        if len(command) > 1000:
            return {"behavior": "deny", "message": "Command too long"}
        
        # Validate no shell injection patterns
        if ";" in command or "&&" in command:
            return {"behavior": "deny", "message": "Command chaining not allowed"}
    
    return {"behavior": "allow", "updatedInput": input_data}
```

### 5. Combine with Hooks

Use PreToolUse hooks for additional validation:

```python
async def pre_tool_hook(input_data, tool_use_id, context):
    """Additional validation before tool execution."""
    tool_name = input_data.get("tool_name")
    
    if tool_name == "Bash":
        # Log command for review
        log_command(input_data.get("tool_input"))
    
    return {}  # Continue execution

options = ClaudeAgentOptions(
    can_use_tool=custom_permissions,
    hooks={
        "PreToolUse": [{"hooks": [pre_tool_hook]}]
    }
)
```

## Common Patterns

### Read-Only Agent

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],
    disallowed_tools=["Write", "Edit", "Bash"],
    permission_mode="bypassPermissions"
)
```

### Development Agent

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    permission_mode="acceptEdits"
)
```

### Web-Enabled Research Agent

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "WebFetch", "WebSearch", "Grep"],
    permission_mode="default"  # Require approval for web access
)
```

### CI/CD Agent

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Bash", "Grep"],
    disallowed_tools=["Write", "Edit"],  # No file modifications
    permission_mode="bypassPermissions"
)
```

## Troubleshooting

### Agent Can't Access Tool

**Problem:** Agent reports tool not available.

**Solution:** Add tool to `allowed_tools`:
```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "YourToolName"]
)
```

### Permission Denied Errors

**Problem:** Agent gets permission denied even with `bypassPermissions`.

**Solution:** Check custom permission function:
```python
async def debug_permissions(tool_name, input_data, context):
    print(f"Tool: {tool_name}, Input: {input_data}")
    return {"behavior": "allow", "updatedInput": input_data}
```

### MCP Tool Not Found

**Problem:** MCP tools not accessible.

**Solution:** Use correct tool name format: `mcp__server_name__tool_name`
```python
options = ClaudeAgentOptions(
    allowed_tools=["mcp__github__create_issue"]
)
```

## Next Steps

- Review [MCP Integration Guide](./mcp_integration.md) for custom tools
- Check [Hooks Reference](./hooks.md) for advanced event handling
- See [System Prompts Guide](./system_prompts.md) for effective agent instructions
