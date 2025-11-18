# MCP Integration Guide

Complete guide for integrating Model Context Protocol (MCP) servers with Claude Agent SDK applications.

## Overview

MCP servers extend agent capabilities by providing custom tools and resources. Use MCP to connect agents to databases, APIs, file systems, and external services.

## MCP Server Types

### 1. Stdio Servers (Most Common)

Communicate via standard input/output:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "type": "stdio",
            "command": "node",
            "args": ["path/to/github-mcp-server/index.js"],
            "env": {"GITHUB_TOKEN": "your-token"}
        }
    }
)
```

### 2. SSE Servers

Server-Sent Events over HTTP:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "remote": {
            "type": "sse",
            "url": "https://mcp-server.example.com/sse",
            "headers": {"Authorization": "Bearer token"}
        }
    }
)
```

### 3. HTTP Servers

Standard HTTP/HTTPS:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "api": {
            "type": "http",
            "url": "https://mcp-server.example.com",
            "headers": {"X-API-Key": "key"}
        }
    }
)
```

### 4. SDK Servers (In-Process)

Run server in same process:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("greet", "Greet a user", {"name": str})
async def greet(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {args['name']}!"
        }]
    }

server = create_sdk_mcp_server(
    name="greeter",
    version="1.0.0",
    tools=[greet]
)

options = ClaudeAgentOptions(
    mcp_servers={"greeter": server}
)
```

## Creating Custom MCP Tools

### Python Example

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    result = args["a"] + args["b"]
    return {
        "content": [{
            "type": "text",
            "text": f"Sum: {result}"
        }]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    result = args["a"] * args["b"]
    return {
        "content": [{
            "type": "text",
            "text": f"Product: {result}"
        }]
    }

# Create MCP server
calculator = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[add, multiply]
)

# Use in agent
options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=[
        "mcp__calc__add",
        "mcp__calc__multiply"
    ]
)
```

### TypeScript Example

```typescript
import { tool, createSdkMcpServer } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

const addTool = tool(
    "add",
    "Add two numbers",
    z.object({ a: z.number(), b: z.number() }),
    async (args) => {
        return {
            content: [{
                type: "text",
                text: `Sum: ${args.a + args.b}`
            }]
        };
    }
);

const calculator = createSdkMcpServer({
    name: "calculator",
    version: "1.0.0",
    tools: [addTool]
});

const options = {
    mcpServers: { calc: calculator },
    allowedTools: ["mcp__calc__add"]
};
```

## MCP Tool Naming

Tools from MCP servers use the format:
```
mcp__<server_name>__<tool_name>
```

**Example:**
- Server name: `github`
- Tool name: `create_issue`  
- Full name: `mcp__github__create_issue`

```python
options = ClaudeAgentOptions(
    allowed_tools=[
        "Read",
        "mcp__github__create_issue",
        "mcp__github__list_repos"
    ]
)
```

## Loading MCP Config from File

Create `mcp-config.json`:

```json
{
    "mcpServers": {
        "github": {
            "command": "node",
            "args": ["path/to/github-mcp/index.js"],
            "env": {
                "GITHUB_TOKEN": "${GITHUB_TOKEN}"
            }
        },
        "postgres": {
            "command": "python",
            "args": ["-m", "postgres_mcp_server"],
            "env": {
                "DATABASE_URL": "${DATABASE_URL}"
            }
        }
    }
}
```

Load in agent:

```python
options = ClaudeAgentOptions(
    mcp_servers="./mcp-config.json"
)
```

## Advanced Tool Schema

### Complex Input Validation

**Python - JSON Schema:**
```python
@tool(
    "search_users",
    "Search users with filters",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "filters": {
                "type": "object",
                "properties": {
                    "active": {"type": "boolean"},
                    "role": {"type": "string", "enum": ["admin", "user"]}
                }
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 100}
        },
        "required": ["query"]
    }
)
async def search_users(args):
    # Implementation
    pass
```

**TypeScript - Zod Schema:**
```typescript
const searchTool = tool(
    "search_users",
    "Search users with filters",
    z.object({
        query: z.string().min(1),
        filters: z.object({
            active: z.boolean().optional(),
            role: z.enum(["admin", "user"]).optional()
        }).optional(),
        limit: z.number().int().min(1).max(100).optional()
    }),
    async (args) => {
        // Implementation
    }
);
```

### Rich Content Responses

Return multiple content types:

```python
@tool("analyze_image", "Analyze image file", {"path": str})
async def analyze_image(args):
    # Process image
    return {
        "content": [
            {
                "type": "text",
                "text": "Image analysis:"
            },
            {
                "type": "text",
                "text": "- Size: 1920x1080\n- Format: PNG"
            },
            {
                "type": "image",
                "data": base64_encoded_image,
                "mimeType": "image/png"
            }
        ]
    }
```

## Common MCP Server Examples

### Database Query Server

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
import asyncpg

@tool("query_db", "Execute SQL query", {"sql": str})
async def query_db(args):
    conn = await asyncpg.connect("postgresql://...")
    results = await conn.fetch(args["sql"])
    await conn.close()
    
    return {
        "content": [{
            "type": "text",
            "text": f"Results: {results}"
        }]
    }

db_server = create_sdk_mcp_server(
    name="database",
    tools=[query_db]
)
```

### API Integration Server

```python
import httpx

@tool("fetch_weather", "Get weather data", {"city": str})
async def fetch_weather(args):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/v1/{args['city']}"
        )
        data = response.json()
    
    return {
        "content": [{
            "type": "text",
            "text": f"Weather: {data}"
        }]
    }

weather_server = create_sdk_mcp_server(
    name="weather",
    tools=[fetch_weather]
)
```

### File System Server

```python
import os
import aiofiles

@tool("list_directory", "List directory contents", {"path": str})
async def list_directory(args):
    files = os.listdir(args["path"])
    return {
        "content": [{
            "type": "text",
            "text": f"Files: {', '.join(files)}"
        }]
    }

@tool("read_file", "Read file contents", {"path": str})
async def read_file(args):
    async with aiofiles.open(args["path"]) as f:
        content = await f.read()
    
    return {
        "content": [{
            "type": "text",
            "text": content
        }]
    }

fs_server = create_sdk_mcp_server(
    name="filesystem",
    tools=[list_directory, read_file]
)
```

## Error Handling

### Tool-Level Errors

```python
@tool("divide", "Divide two numbers", {"a": float, "b": float})
async def divide(args):
    try:
        result = args["a"] / args["b"]
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {result}"
            }]
        }
    except ZeroDivisionError:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Division by zero"
            }],
            "isError": True
        }
```

### Server-Level Errors

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

try:
    options = ClaudeAgentOptions(
        mcp_servers={"broken": {"type": "stdio", "command": "invalid"}}
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Use the broken server")
except Exception as e:
    print(f"MCP server error: {e}")
```

## Testing MCP Tools

### Unit Testing

```python
import pytest

@pytest.mark.asyncio
async def test_calculator_add():
    result = await add({"a": 2, "b": 3})
    assert result["content"][0]["text"] == "Sum: 5"

@pytest.mark.asyncio
async def test_calculator_multiply():
    result = await multiply({"a": 4, "b": 5})
    assert result["content"][0]["text"] == "Product: 20"
```

### Integration Testing

```python
from claude_agent_sdk import query, ClaudeAgentOptions

@pytest.mark.asyncio
async def test_agent_uses_calculator():
    calculator = create_sdk_mcp_server(
        name="calc",
        tools=[add, multiply]
    )
    
    options = ClaudeAgentOptions(
        mcp_servers={"calc": calculator},
        allowed_tools=["mcp__calc__add"],
        permission_mode="bypassPermissions"
    )
    
    async for message in query(
        prompt="What is 2 + 3?",
        options=options
    ):
        print(message)
```

## Best Practices

### 1. Clear Tool Descriptions

```python
@tool(
    "search_users",
    "Search for users in the database by name, email, or role. "
    "Returns user details including ID, name, email, and role. "
    "Use this when you need to find specific users or list users matching criteria.",
    {"query": str, "limit": int}
)
async def search_users(args):
    pass
```

### 2. Input Validation

```python
@tool("get_user", "Get user by ID", {"user_id": int})
async def get_user(args):
    user_id = args["user_id"]
    
    # Validate input
    if user_id <= 0:
        return {
            "content": [{"type": "text", "text": "Invalid user ID"}],
            "isError": True
        }
    
    # Fetch user
    user = await db.fetch_user(user_id)
    return {"content": [{"type": "text", "text": str(user)}]}
```

### 3. Consistent Response Format

```python
def success_response(data):
    return {
        "content": [{"type": "text", "text": str(data)}]
    }

def error_response(message):
    return {
        "content": [{"type": "text", "text": f"Error: {message}"}],
        "isError": True
    }

@tool("example", "Example tool", {})
async def example(args):
    try:
        result = process()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))
```

### 4. Resource Cleanup

```python
@tool("query_db", "Query database", {"sql": str})
async def query_db(args):
    conn = None
    try:
        conn = await asyncpg.connect("postgresql://...")
        results = await conn.fetch(args["sql"])
        return {"content": [{"type": "text", "text": str(results)}]}
    finally:
        if conn:
            await conn.close()
```

### 5. Rate Limiting

```python
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

rate_limits = defaultdict(list)

async def rate_limited_tool(tool_name, max_calls=10, window_seconds=60):
    now = datetime.now()
    cutoff = now - timedelta(seconds=window_seconds)
    
    # Remove old calls
    rate_limits[tool_name] = [
        call_time for call_time in rate_limits[tool_name]
        if call_time > cutoff
    ]
    
    # Check limit
    if len(rate_limits[tool_name]) >= max_calls:
        return {
            "content": [{
                "type": "text",
                "text": f"Rate limit exceeded. Max {max_calls} calls per {window_seconds}s"
            }],
            "isError": True
        }
    
    # Record call
    rate_limits[tool_name].append(now)
    return None  # No error

@tool("expensive_api", "Call expensive API", {"query": str})
async def expensive_api(args):
    # Check rate limit
    limit_error = await rate_limited_tool("expensive_api", max_calls=5, window_seconds=60)
    if limit_error:
        return limit_error
    
    # Make API call
    result = await call_api(args["query"])
    return {"content": [{"type": "text", "text": str(result)}]}
```

## Troubleshooting

### MCP Server Not Starting

**Problem:** Server fails to initialize.

**Solution:** Check command and arguments:
```python
# Test command manually first
import subprocess
result = subprocess.run(["node", "path/to/server.js"], capture_output=True)
print(result.stderr)
```

### Tool Not Found

**Problem:** Agent can't find MCP tool.

**Solution:** Verify tool name format and permissions:
```python
options = ClaudeAgentOptions(
    mcp_servers={"myserver": server},
    allowed_tools=["mcp__myserver__mytool"]  # Correct format
)
```

### Environment Variables Not Loading

**Problem:** Server can't access env vars.

**Solution:** Pass env explicitly:
```python
import os

options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "type": "stdio",
            "command": "node",
            "args": ["server.js"],
            "env": {
                "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
                "NODE_ENV": "production"
            }
        }
    }
)
```

## Next Steps

- Review [Tool Permissions Reference](./tool_permissions.md) for securing MCP tools
- Check [Hooks Reference](./hooks.md) for intercepting MCP calls
- Explore official MCP servers: https://github.com/modelcontextprotocol/servers
