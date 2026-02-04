# Streaming

Real-time streaming of agent responses for better user experience.

## Basic Streaming

### Python

```python
from letta_client import Letta

client = Letta(api_key="...")

# Stream responses
stream = client.agents.messages.stream(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Tell me a story"}]
)

for chunk in stream:
    if chunk.message_type == "assistant_message":
        print(chunk.content, end="", flush=True)
    elif chunk.message_type == "reasoning_message":
        print(f"[Thinking: {chunk.reasoning}]")
    elif chunk.message_type == "tool_call_message":
        print(f"[Calling: {chunk.tool_call.name}]")
```

### TypeScript

```typescript
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY });

const stream = await client.agents.messages.stream(agent.id, {
  messages: [{ role: "user", content: "Tell me a story" }]
});

for await (const chunk of stream) {
  switch (chunk.message_type) {
    case "assistant_message":
      process.stdout.write(chunk.content);
      break;
    case "reasoning_message":
      console.log(`[Thinking: ${chunk.reasoning}]`);
      break;
    case "tool_call_message":
      console.log(`[Calling: ${chunk.tool_call.name}]`);
      break;
  }
}
```

## Message Types in Streams

| Type | Description | Key Field |
|------|-------------|-----------|
| `reasoning_message` | Agent's internal reasoning | `reasoning` |
| `tool_call_message` | Agent calling a tool | `tool_call.name`, `tool_call.arguments` |
| `tool_return_message` | Tool execution result | `tool_return` |
| `assistant_message` | Final response to user | `content` |

## Long-Running Operations

For operations that may take > 100 seconds (complex tool chains, large context), use `include_pings` to prevent timeout.

### The Problem

Cloudflare (used by Letta Cloud) kills connections with no data after ~100 seconds.

### The Solution

```python
# Python - Enable pings for long operations
stream = client.agents.messages.stream(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Analyze this large dataset"}],
    include_pings=True  # Send keepalive pings every 30 seconds
)

for chunk in stream:
    # Filter out ping events
    if chunk.message_type == "ping":
        continue  # Keepalive, ignore
    
    # Process actual messages
    if chunk.message_type == "assistant_message":
        print(chunk.content)
```

```typescript
// TypeScript
const stream = await client.agents.messages.stream(agent.id, {
  messages: [{ role: "user", content: "Analyze this large dataset" }],
  include_pings: true
});

for await (const chunk of stream) {
  if (chunk.message_type === "ping") {
    continue; // Keepalive, ignore
  }
  
  if (chunk.message_type === "assistant_message") {
    console.log(chunk.content);
  }
}
```

## Background Execution

For fire-and-forget operations or resumable streams.

### Starting Background Execution

```python
# Python
stream = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Process this in background"}],
    background=True  # Run in background
)

run_id = None
last_seq_id = None

for chunk in stream:
    run_id = chunk.run_id
    last_seq_id = chunk.seq_id
    print(chunk)
```

### Resuming After Disconnect

```python
# If connection drops, resume from where you left off
for chunk in client.runs.stream(
    run_id=run_id,
    starting_after=last_seq_id
):
    print(chunk)
```

```typescript
// TypeScript
const stream = await client.agents.messages.create(agent.id, {
  messages: [{ role: "user", content: "Process this in background" }],
  background: true
});

let runId: string;
let lastSeqId: string;

for await (const chunk of stream) {
  runId = chunk.run_id;
  lastSeqId = chunk.seq_id;
  console.log(chunk);
}

// Resume after disconnect
for await (const chunk of client.runs.stream(runId, { 
  starting_after: lastSeqId 
})) {
  console.log(chunk);
}
```

## Token-Level Streaming

Stream individual tokens as they're generated (not just complete messages).

```python
# Python
stream = client.agents.messages.stream(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Hello"}],
    stream_tokens=True  # Enable token streaming
)

for chunk in stream:
    if hasattr(chunk, 'token'):
        print(chunk.token, end="", flush=True)
```

**Note**: Token streaming may show tool calls as partial JSON chunks.

## Server-Sent Events (SSE) Format

The streaming API uses SSE. Each event has:

```
event: message
data: {"message_type": "assistant_message", "content": "Hello", ...}

event: message  
data: {"message_type": "tool_call_message", "tool_call": {...}, ...}
```

### Raw SSE Handling (Advanced)

```python
import httpx

def stream_raw_sse(agent_id: str, message: str, api_key: str):
    with httpx.stream(
        "POST",
        f"https://api.letta.com/v1/agents/{agent_id}/messages/stream",
        json={"messages": [{"role": "user", "content": message}]},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=None
    ) as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                yield data
```

## Streaming to Web Clients

### Next.js API Route

```typescript
// app/api/chat/route.ts
import { Letta } from "@letta-ai/letta-client";
import { NextRequest } from "next/server";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY! });

export async function POST(req: NextRequest) {
  const { agentId, message } = await req.json();
  
  const stream = await client.agents.messages.stream(agentId, {
    messages: [{ role: "user", content: message }]
  });
  
  // Create a readable stream for the response
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        if (chunk.message_type === "assistant_message") {
          controller.enqueue(encoder.encode(chunk.content));
        }
      }
      controller.close();
    }
  });
  
  return new Response(readable, {
    headers: { "Content-Type": "text/plain; charset=utf-8" }
  });
}
```

### React Client

```typescript
// components/Chat.tsx
async function sendMessage(message: string) {
  const response = await fetch("/api/chat", {
    method: "POST",
    body: JSON.stringify({ agentId, message }),
    headers: { "Content-Type": "application/json" }
  });
  
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    setResponse(prev => prev + text);
  }
}
```

## Best Practices

1. **Always handle all message types** - Don't just look for assistant_message
2. **Use `include_pings=True` for long operations** - Prevents 524 timeouts
3. **Filter ping events in your UI** - They're just keepalives
4. **Store `run_id` and `seq_id`** - Enables resume after disconnect
5. **Set appropriate timeouts** - Streaming can run for minutes
