# Getting Started

Quick setup for Letta Cloud and common onboarding issues.

**Quick Links:**
- [Letta Cloud (ADE)](https://app.letta.com) - Visual agent builder
- [API Keys](https://app.letta.com/api-keys) - Get your API key
- [Documentation](https://docs.letta.com) - Full docs

## Installation

```bash
# Python
pip install letta-client

# TypeScript
npm install @letta-ai/letta-client
```

## First Connection

### Python
```python
from letta_client import Letta
import os

client = Letta(api_key=os.getenv("LETTA_API_KEY"))
```

### TypeScript
```typescript
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY });
```

Get your API key from [app.letta.com/api-keys](https://app.letta.com/api-keys).

## Creating Your First Agent

```python
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a helpful assistant."},
        {"label": "human", "value": "User information."}
    ]
)

# Send a message
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Hello!"}]
)

# Get the response
for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(msg.content)
```

## Common Creation Errors

| Error | Fix |
|-------|-----|
| "model is required" | Add `model="anthropic/claude-sonnet-4-5-20250929"` |
| "embedding is required" | Add `embedding="openai/text-embedding-3-small"` |
| "memory_blocks cannot be empty" | Add at least one memory block |

## Understanding Responses

Agent responses contain multiple message types:

```python
for msg in response.messages:
    match msg.message_type:
        case "reasoning_message":
            print(f"Thinking: {msg.reasoning}")
        case "tool_call_message":
            print(f"Calling: {msg.tool_call.name}")
        case "tool_return_message":
            print(f"Result: {msg.tool_return}")
        case "assistant_message":
            print(f"Response: {msg.content}")  # ← Final answer
```

## Model Selection

**Recommended default:**
- `anthropic/claude-sonnet-4-5-20250929` - Best balance of quality and speed

**Anthropic:**
- `anthropic/claude-opus-4-5-20251101` - Anthropic's best model
- `anthropic/claude-haiku-4-5-20251001` - Anthropic's fastest model

**OpenAI:**
- `openai/gpt-5.2` - Latest general-purpose GPT
- `openai/gpt-5.2-codex` - GPT-5.2 optimized for coding

**Google:**
- `google_ai/gemini-3-pro-preview` - Google's smartest model
- `google_ai/gemini-3-flash-preview` - Google's fastest Gemini 3 model

**Open weights:**
- `zai/glm-4.7` - Best open weights coding model

## Next Steps

1. **Add custom tools** - See [custom-tools.md](./custom-tools.md)
2. **Use client injection for advanced tools** - See [client-injection.md](./client-injection.md)
3. **Understand memory** - See [memory-architecture.md](./memory-architecture.md)
4. **Enable streaming** - See [streaming.md](./streaming.md)
