---
name: claude-agent-sdk-builder
description: Guide for building production-ready AI agents using the Claude Agent SDK (formerly Claude Code SDK). This skill should be used when creating agents with tool permissions, system prompts, MCP servers, subagents, hooks, or any interactive Claude-powered application in Python or TypeScript.
---

# Claude Agent SDK Builder

## Overview

Build production-ready AI agents using the Claude Agent SDK - the same framework that powers Claude Code. This skill covers agent configuration, tool permissions, MCP integration, system prompts, and advanced features like subagents and hooks.

## Quick Start

### Installation

**TypeScript:**
```bash
npm install @anthropic-ai/claude-agent-sdk
```

**Python:**
```bash
pip install claude-agent-sdk
```

### Basic Agent (Python)

```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What's the capital of France?"):
        print(message)

asyncio.run(main())
```

### Basic Agent (TypeScript)

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

for await (const message of query({ prompt: "What's the capital of France?" })) {
    console.log(message);
}
```

## Core Concepts

### 1. query() vs Client Pattern

**Python - Two Approaches:**
- `query()` - One-off tasks, creates new session each time
- `ClaudeSDKClient` - Continuous conversations, maintains session across multiple exchanges

**TypeScript - Single Approach:**
- `query()` - Returns Query object with session methods (interrupt, setPermissionMode)

### 2. System Prompts

Define agent's role, expertise, and behavior:

**Custom system prompt:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt="You are an expert Python developer focused on clean code and testing."
)

async for message in query(prompt="Review my code", options=options):
    print(message)
```

**Use Claude Code's preset prompt:**
```python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Always add detailed comments."
    }
)
```

### 3. Tool Permissions

Control which tools your agent can use:

**Permission Modes:**
- `'default'` - Standard permission behavior (asks for approval)
- `'acceptEdits'` - Auto-accept file edits
- `'plan'` - Planning mode (no execution)
- `'bypassPermissions'` - Bypass all permission checks (use with caution)

**Example:**
```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash", "Grep"],
    disallowed_tools=["WebFetch"],  # Block web access
    permission_mode="acceptEdits"
)
```

**Custom Permission Logic:**
```python
async def custom_permissions(tool_name, input_data, context):
    # Block system directory writes
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return {
            "behavior": "deny",
            "message": "System directory write not allowed"
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

## Building Production Agents

### Workflow Decision Tree

```
┌─────────────────────────────────────┐
│ What type of agent are you building?│
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
   One-off Task    Continuous Chat
       │                │
   Use query()    Use ClaudeSDKClient
       │                │
       │            ┌───┴─────┐
       │            │         │
       │        Basic    Advanced
       │            │         │
       │       Session   Interrupts
       │       Context    + Hooks
       └────────┬────────┘
                │
         ┌──────┴──────┐
    Add System      Add Tool
     Prompts      Permissions
                      │
              ┌───────┴────────┐
           Simple          Custom
         allowedTools   can_use_tool
                              │
                      ┌───────┴────────┐
                  Add MCP         Add Subagents
                  Servers           + Skills
```

### Step 1: Define Agent Purpose

Start with a clear system prompt that defines:
- Agent's role and expertise
- Specific capabilities
- Behavioral guidelines

### Step 2: Configure Tool Access

Determine which tools the agent needs:
- File operations: Read, Write, Edit, Glob, Grep
- Code execution: Bash, NotebookEdit
- Web access: WebFetch, WebSearch
- Task management: Task (subagents), TodoWrite

See [Tool Permissions Reference](./references/tool_permissions.md) for detailed guidance.

### Step 3: Add MCP Servers (Optional)

Integrate external services through MCP:

**Load from file:**
```python
options = ClaudeAgentOptions(
    mcp_servers="./mcp-config.json"  # Path to config file
)
```

**Define programmatically:**
```python
options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "type": "stdio",
            "command": "node",
            "args": ["path/to/github-mcp-server"]
        }
    }
)
```

See [MCP Integration Guide](./references/mcp_integration.md) for complete examples.

### Step 4: Define Subagents (Optional)

Create specialized agents for specific tasks:

```python
options = ClaudeAgentOptions(
    agents={
        "code-reviewer": {
            "description": "Reviews code for bugs and best practices",
            "prompt": "You are an expert code reviewer...",
            "tools": ["Read", "Grep"],
            "model": "sonnet"
        },
        "test-writer": {
            "description": "Writes comprehensive tests",
            "prompt": "You are a test automation expert...",
            "tools": ["Read", "Write"],
            "model": "sonnet"
        }
    }
)
```

### Step 5: Implement Interactive Loop (If Needed)

For continuous conversations:

**Python:**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interactive_agent():
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful coding assistant",
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    
    async with ClaudeSDKClient(options=options) as client:
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break
            
            await client.query(user_input)
            
            async for message in client.receive_response():
                # Process messages
                print(message)
```

**TypeScript:**
```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

async function* userInputGenerator() {
    // Implement input streaming
    yield { type: "text", text: await getUserInput() };
}

const result = query({
    prompt: userInputGenerator(),
    options: {
        systemPrompt: "You are a helpful coding assistant",
        allowedTools: ["Read", "Write", "Bash"],
        permissionMode: "acceptEdits"
    }
});

for await (const message of result) {
    console.log(message);
}
```

## Common Agent Patterns

### 1. SRE/DevOps Agent

Diagnose and fix production issues:

```python
options = ClaudeAgentOptions(
    system_prompt="You are an SRE expert. Diagnose issues, check logs, and propose fixes.",
    allowed_tools=["Read", "Bash", "Grep", "Glob"],
    permission_mode="default",  # Require approval for changes
    cwd="/var/log/application"
)
```

### 2. Code Review Agent

Review code for quality and security:

```python
options = ClaudeAgentOptions(
    system_prompt="You are a senior code reviewer. Check for bugs, security issues, and best practices.",
    allowed_tools=["Read", "Grep", "Glob"],
    disallowed_tools=["Write", "Edit", "Bash"],  # Read-only
    permission_mode="bypassPermissions"
)
```

### 3. Full-Stack Development Agent

Build applications with file operations:

```python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Focus on TypeScript and React best practices."
    },
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep"],
    permission_mode="acceptEdits",
    agents={
        "frontend": {
            "description": "Builds React UIs",
            "prompt": "You are a React expert...",
            "tools": ["Read", "Write", "Edit"]
        },
        "backend": {
            "description": "Builds Node.js APIs",
            "prompt": "You are a Node.js backend expert...",
            "tools": ["Read", "Write", "Edit", "Bash"]
        }
    }
)
```

### 4. Data Analysis Agent

Analyze data with custom tools:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("analyze_csv", "Analyze CSV file and return statistics", {"file_path": str})
async def analyze_csv(args):
    # Custom analysis logic
    return {"content": [{"type": "text", "text": "Analysis results..."}]}

mcp_server = create_sdk_mcp_server(
    name="data_tools",
    tools=[analyze_csv]
)

options = ClaudeAgentOptions(
    system_prompt="You are a data analyst. Use the analyze_csv tool to process data.",
    mcp_servers={"data": mcp_server},
    allowed_tools=["Read", "mcp__data__analyze_csv"]
)
```

## Advanced Features

### Hooks

Intercept and modify agent behavior at specific events:

```python
async def log_tool_use(input_data, tool_use_id, context):
    print(f"Tool used: {input_data.get('tool_name')}")
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [validate_bash]},
            {"hooks": [log_tool_use]}  # All tools
        ]
    }
)
```

See [Hooks Reference](./references/hooks.md) for all hook types and examples.

### Agent Skills

Load reusable capabilities from `.claude/skills/` directory:

1. Create skill folder: `.claude/skills/my-skill/`
2. Add `SKILL.md` with instructions
3. Agent automatically discovers and uses skills

### Session Management

**Continue previous conversation:**
```python
# Python
options = ClaudeAgentOptions(continue_conversation=True)

// TypeScript  
options = { continue: true }
```

**Resume specific session:**
```python
# Python
options = ClaudeAgentOptions(resume="session-id-123")

// TypeScript
options = { resume: "session-id-123" }
```

### Settings Sources

Control which filesystem settings to load:

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],  # Load .claude/settings.json
    system_prompt={"type": "preset", "preset": "claude_code"}
)
```

Options: `"user"` (~/.claude/settings.json), `"project"` (.claude/settings.json), `"local"` (.claude/settings.local.json)

## Testing and Debugging

### 1. Start with Read-Only Mode

Test agent behavior without side effects:

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],
    permission_mode="bypassPermissions"
)
```

### 2. Use Planning Mode

Review agent's plan before execution:

```python
options = ClaudeAgentOptions(
    permission_mode="plan"
)
```

### 3. Monitor Tool Usage

Add hooks to log all tool calls:

```python
async def log_hook(input_data, tool_use_id, context):
    with open("tool_log.txt", "a") as f:
        f.write(f"{input_data}\n")
    return {}

options = ClaudeAgentOptions(
    hooks={"PreToolUse": [{"hooks": [log_hook]}]}
)
```

## Resources

This skill includes detailed reference documentation:

### [Tool Permissions Reference](./references/tool_permissions.md)
Complete guide to tool permissions, custom permission logic, and security best practices.

### [MCP Integration Guide](./references/mcp_integration.md)  
Detailed guide for integrating MCP servers, creating custom tools, and connecting external services.

### [System Prompts Guide](./references/system_prompts.md)
Best practices for writing effective system prompts, examples for different agent types, and prompt engineering tips.

### [Hooks Reference](./references/hooks.md)
Complete documentation on hooks, event types, and advanced behavior modification.

## Example Scripts

This skill includes ready-to-use templates:

### [scripts/basic_agent.py](./scripts/basic_agent.py)
Template for a basic interactive agent with file operations.

### [scripts/agent_with_mcp.py](./scripts/agent_with_mcp.py)
Example agent with custom MCP server integration.

### [scripts/production_agent.py](./scripts/production_agent.py)
Production-ready agent template with error handling, logging, and advanced features.

## Next Steps

1. **Start Simple**: Begin with basic `query()` and system prompts
2. **Add Permissions**: Configure `allowed_tools` and `permission_mode`  
3. **Test Thoroughly**: Use read-only mode and planning mode
4. **Add MCP**: Integrate external services as needed
5. **Scale Up**: Add subagents, hooks, and advanced features

For detailed implementation examples, load the reference files as needed.
