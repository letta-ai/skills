# Client-Side Tool Execution

Execute tools locally in your application while the agent runs on the Letta API. This is how [Letta Code](https://github.com/letta-ai/letta-code) executes `Bash`, `Read`, and `Write` tools on your local machine.

## When to Use Client-Side Tools

- **Local resources**: Access files, databases, or services on the client machine
- **Sensitive data**: Keep credentials and private APIs out of the server
- **Human-in-the-loop**: Review tool calls before execution
- **Custom environments**: Run tools in specific runtime environments

## How It Works

```
Agent (Letta API) → Requests tool call → Client receives approval request
                                              ↓
                                        Execute locally
                                              ↓
Agent continues ← Receives result ← Client sends result back
```

1. Mark tools with `default_requires_approval=True`
2. Agent requests tool → server pauses and returns `approval_request_message`
3. Your app executes the tool locally
4. Send result back with `type: "tool"` (not `approve: true/false`)
5. Agent receives result and continues

## Creating Client-Side Tools

The tool needs `source_code` (required by API) but it never runs server-side:

```python
from letta_client import Letta
import os

client = Letta(api_key=os.getenv("LETTA_API_KEY"))

# Create tool with approval requirement
def run_local_command(command: str) -> str:
    """
    Run a shell command on the local machine.
    
    Args:
        command: The shell command to execute
    
    Returns:
        Command output
    """
    raise Exception("This tool executes client-side only")

tool = client.tools.upsert_from_function(
    func=run_local_command,
    default_requires_approval=True,
)
```

```typescript
const tool = await client.tools.upsert({
  name: "run_local_command",
  defaultRequiresApproval: true,
  jsonSchema: {
    type: "function",
    function: {
      name: "run_local_command",
      description: "Run a shell command on the local machine",
      parameters: {
        type: "object",
        properties: {
          command: { type: "string", description: "The shell command to execute" },
        },
        required: ["command"],
      },
    },
  },
  // Stub - never executed server-side
  sourceCode: `def run_local_command(command: str):
    """Run a shell command on the local machine."""
    raise Exception("This tool executes client-side only")`,
});
```

## Handling Tool Execution

```python
import json
import subprocess

# Send message to agent
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "List files in current directory"}]
)

# Check for approval requests
for msg in response.messages:
    if msg.message_type == "approval_request_message":
        tool_call = msg.tool_call
        
        # Parse arguments
        args = json.loads(tool_call.arguments)
        command = args["command"]
        
        # Execute locally
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True
            )
            tool_return = result.stdout or result.stderr
            status = "success" if result.returncode == 0 else "error"
        except Exception as e:
            tool_return = str(e)
            status = "error"
        
        # Send result back to agent
        response = client.agents.messages.create(
            agent_id=agent.id,
            messages=[{
                "type": "approval",
                "approvals": [{
                    "type": "tool",  # Key difference from regular approval
                    "tool_call_id": tool_call.tool_call_id,
                    "tool_return": tool_return,
                    "status": status,
                }]
            }]
        )
        
        # Agent continues with result
        for msg in response.messages:
            if msg.message_type == "assistant_message":
                print(msg.content)
```

## TypeScript Example

```typescript
import { execSync } from "child_process";

// Send message
let response = await client.agents.messages.create(agent.id, {
  messages: [{ role: "user", content: "List files in current directory" }],
});

// Handle approval requests
for (const msg of response.messages) {
  if (msg.message_type === "approval_request_message") {
    const toolCall = msg.tool_call;
    const args = JSON.parse(toolCall.arguments);
    
    // Execute locally
    let toolReturn: string;
    let status: "success" | "error";
    
    try {
      toolReturn = execSync(args.command, { encoding: "utf-8" });
      status = "success";
    } catch (error: any) {
      toolReturn = error.message;
      status = "error";
    }
    
    // Send result back
    response = await client.agents.messages.create(agent.id, {
      messages: [{
        type: "approval",
        approvals: [{
          type: "tool",
          tool_call_id: toolCall.tool_call_id,
          tool_return: toolReturn,
          status: status,
        }],
      }],
    });
  }
}
```

## Including stdout/stderr

For shell commands, include output streams:

```python
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{
        "type": "approval",
        "approvals": [{
            "type": "tool",
            "tool_call_id": tool_call.tool_call_id,
            "tool_return": result.stdout,
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout.splitlines(),
            "stderr": result.stderr.splitlines(),
        }]
    }]
)
```

## Comparison: Client-Side vs Server-Side

| Feature | Client-Side | Server-Side (Sandbox) |
|---------|-------------|----------------------|
| Execution location | Your machine | Letta API sandbox |
| Local file access | Yes | No |
| Private APIs | Yes | No (must expose) |
| Setup complexity | Higher | Lower |
| Latency | + network round-trip | Minimal |
| Security | You manage | Sandboxed |

## Real-World Example: Letta Code

[Letta Code](https://github.com/letta-ai/letta-code) uses client-side tools for:
- `Bash` - Run shell commands locally
- `Read` - Read local files
- `Write` - Write local files
- `Edit` - Edit local files

The agent runs on the Letta API but all file/shell operations happen on your machine, giving you full control and access to your local environment.

See: https://docs.letta.com/guides/agents/tool-execution-client-side/
