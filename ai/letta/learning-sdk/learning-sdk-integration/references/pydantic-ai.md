# PydanticAI Integration

This reference documents patterns for adding persistent memory to PydanticAI agents using the Learning SDK. The integration works with all PydanticAI-supported providers including Anthropic, OpenAI, Gemini, and others.

## When to Use

Use this skill when:
- Building PydanticAI agents that need memory across sessions
- Adding conversation history persistence to PydanticAI applications
- Creating PydanticAI agents with context-aware capabilities
- Working with any PydanticAI-supported model provider

## Core Integration Pattern

### Basic 3-Line Integration

```python
from pydantic_ai import Agent
from agentic_learning import learning

agent = Agent('anthropic:claude-sonnet-4-20250514')

# Wrap agent execution to enable persistent memory
with learning(agent="my-agent"):
    result = agent.run_sync("Hello!")
```

The SDK automatically:
- Captures all agent conversations
- Stores them in persistent memory
- Injects relevant context into future calls

## Provider Examples

### Anthropic (Claude)

```python
from pydantic_ai import Agent
from agentic_learning import learning

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='Be concise, reply with one sentence.',
)

def ask_agent(message: str):
    with learning(agent="pydantic-anthropic-demo"):
        result = agent.run_sync(message)
        return result.output

# Memory persists across calls
ask_agent("My name is Alice.")
ask_agent("What's my name?")  # Returns "Alice"
```

### OpenAI (GPT)

```python
from pydantic_ai import Agent
from agentic_learning import learning

agent = Agent(
    'openai:gpt-4o',
    instructions='Be concise, reply with one sentence.',
)

def ask_agent(message: str):
    with learning(agent="pydantic-openai-demo"):
        result = agent.run_sync(message)
        return result.output

ask_agent("My name is Bob.")
ask_agent("What's my name?")  # Returns "Bob"
```

### Gemini

```python
from pydantic_ai import Agent
from agentic_learning import learning

agent = Agent(
    'google-gla:gemini-1.5-pro',
    instructions='Be helpful and concise.',
)

def ask_agent(message: str):
    with learning(agent="pydantic-gemini-demo"):
        result = agent.run_sync(message)
        return result.output
```

## Advanced Patterns

### Async Usage

```python
from pydantic_ai import Agent
from agentic_learning import learning

agent = Agent('anthropic:claude-sonnet-4-20250514')

async def ask_agent_async(message: str):
    with learning(agent="async-demo"):
        result = await agent.run(message)
        return result.output
```

### Capture-Only Mode

To save conversations without injecting memory context:

```python
with learning(agent="research-agent", capture_only=True):
    # Conversation saved but no memory injection
    result = agent.run_sync("Research this topic")
```

### Custom Memory Blocks

```python
custom_memory = [
    {"label": "project_context", "description": "Current project details"},
    {"label": "user_preferences", "description": "User's working preferences"}
]

with learning(agent="my-agent", memory=custom_memory):
    result = agent.run_sync("Continue our work")
```

### Structured Output with Memory

```python
from pydantic import BaseModel
from pydantic_ai import Agent
from agentic_learning import learning

class UserInfo(BaseModel):
    name: str
    interests: list[str]

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=UserInfo,
)

with learning(agent="structured-demo"):
    result = agent.run_sync("Extract user info from our conversation")
    user_info: UserInfo = result.output
```

### Tool Usage with Memory

```python
from pydantic_ai import Agent, Tool
from agentic_learning import learning

def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    tools=[Tool(search_web)],
)

with learning(agent="tool-demo"):
    # Memory helps agent decide when to use tools
    result = agent.run_sync("Search for latest AI news")
```

## Best Practices

### 1. Consistent Agent Names
Use the same agent name across related calls to maintain memory continuity:

```python
AGENT_NAME = "customer-support-bot"

# All calls share the same memory
with learning(agent=AGENT_NAME):
    result1 = agent.run_sync("User reports issue")
    
with learning(agent=AGENT_NAME):
    result2 = agent.run_sync("Follow up on the issue")
```

### 2. Descriptive Agent Names
Use names that reflect the agent's purpose:
- `email-processor`
- `code-reviewer`
- `research-assistant`

### 3. Error Handling

```python
def robust_agent_call(message: str):
    try:
        with learning(agent="my-agent"):
            return agent.run_sync(message)
    except Exception as e:
        # Fallback without memory
        return agent.run_sync(message)
```

## Troubleshooting

### Memory Not Persisting
- Ensure agent name is consistent across calls
- Verify `LETTA_API_KEY` environment variable is set
- Check that `learning` context wraps the agent call

### Performance Issues
- Use `capture_only=True` for logging-only scenarios
- Consider clearing memory for long-running sessions

### Provider Not Intercepted
- Ensure Agentic Learning SDK is imported before PydanticAI
- Verify the provider SDK version is compatible

## Environment Setup

```bash
# Install dependencies
pip install agentic-learning pydantic-ai

# Set API keys
export LETTA_API_KEY="your-letta-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"  # For Anthropic
export OPENAI_API_KEY="your-openai-api-key"        # For OpenAI
```

## References

- [Learning SDK](https://github.com/letta-ai/learning-sdk)
- [PydanticAI Documentation](https://ai.pydantic.dev)
- [PydanticAI Models](https://ai.pydantic.dev/models/)
