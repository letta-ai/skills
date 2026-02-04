# Client Setup

## Python SDK

### Installation
```bash
pip install letta-client
```

### Letta Cloud
```python
from letta_client import Letta

# Basic initialization
client = Letta(api_key="your-api-key")

# With environment variables (recommended)
import os
client = Letta(api_key=os.getenv("LETTA_API_KEY"))
```

### Self-Hosted (Docker)
```python
from letta_client import Letta

# Local server (no auth required by default)
client = Letta(base_url="http://localhost:8283")

# With authentication enabled
client = Letta(
    base_url="http://localhost:8283",
    api_key=os.getenv("LETTA_SERVER_PASSWORD")
)
```

### Async Client
```python
from letta_client import AsyncLetta

async_client = AsyncLetta(api_key=os.getenv("LETTA_API_KEY"))

# Usage
agent = await async_client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...]
)
```

## TypeScript SDK

### Installation
```bash
npm install @letta-ai/letta-client
```

### Letta Cloud
```typescript
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ 
  apiKey: process.env.LETTA_API_KEY 
});
```

### Self-Hosted
```typescript
const client = new Letta({ 
  baseUrl: "http://localhost:8283" 
});
```

### Next.js Singleton Pattern

Create a singleton client to reuse across API routes:

```typescript
// lib/letta.ts
import { Letta } from "@letta-ai/letta-client";

// Singleton pattern for Next.js
let lettaClient: Letta | null = null;

export function getLettaClient(): Letta {
  if (!lettaClient) {
    lettaClient = new Letta({
      apiKey: process.env.LETTA_API_KEY!,
    });
  }
  return lettaClient;
}

// For direct import
export const letta = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});
```

```typescript
// app/api/chat/route.ts
import { letta } from "@/lib/letta";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { agentId, message } = await req.json();
  
  const response = await letta.agents.messages.create(agentId, {
    messages: [{ role: "user", content: message }]
  });
  
  return NextResponse.json(response);
}
```

## Running Letta Locally with Docker

```bash
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY="your-openai-key" \
  letta/letta:latest
```

With multiple providers:
```bash
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY="your-openai-key" \
  -e ANTHROPIC_API_KEY="your-anthropic-key" \
  letta/letta:latest
```

## Error Handling

### Python
```python
from letta_client.core.api_error import ApiError

try:
    response = client.agents.messages.create(agent_id=agent_id, messages=[...])
except ApiError as e:
    print(f"Status: {e.status_code}")
    print(f"Message: {e.message}")
    print(f"Body: {e.body}")
```

### TypeScript
```typescript
import { LettaError } from "@letta-ai/letta-client";

try {
  const response = await client.agents.messages.create(agentId, {...});
} catch (err) {
  if (err instanceof LettaError) {
    console.log(err.statusCode);
    console.log(err.message);
    console.log(err.body);
  }
}
```

## Advanced Configuration

### Retries
```python
# Python
response = client.agents.create(
    {...},
    request_options={"max_retries": 3}  # Default: 2
)
```

```typescript
// TypeScript
const response = await client.agents.create({...}, {
  maxRetries: 3
});
```

### Timeouts
```python
# Python
response = client.agents.create(
    {...},
    request_options={"timeout_in_seconds": 120}  # Default: 60
)
```

```typescript
// TypeScript  
const response = await client.agents.create({...}, {
  timeoutInSeconds: 120
});
```
