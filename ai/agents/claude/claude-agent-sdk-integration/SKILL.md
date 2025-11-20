---
name: claude-agent-sdk-integration
description: Patterns and best practices for integrating persistent memory with Claude Agent SDK using Agentic Learning SDK
---

# Claude Agent SDK Integration

## Overview
This skill provides patterns for adding persistent memory to Claude agents using the Agentic Learning SDK through a 3-line integration pattern.

## When to Use
Use this skill when:
- Building Claude agents that need memory across sessions
- Implementing conversation history persistence
- Adding context-aware capabilities to existing Claude agents
- Creating multi-agent systems with shared memory

## Core Integration Pattern

### Basic 3-Line Integration
```python
from agentic_learning import learning

# Wrap Claude SDK calls to enable memory
with learning(agent="my-agent"):
    response = await claude.messages.create(...)
```

### Async Integration
```python
from agentic_learning import learning_async

# For async Claude SDK usage
async with learning_async(agent="my-agent"):
    response = await claude.messages.create(...)
```

## Implementation Patterns

### 1. Simple Memory Wrapper
```python
from anthropic import Anthropic
from agentic_learning import learning_async

class MemoryEnhancedClaudeAgent:
    def __init__(self, api_key: str, agent_name: str):
        self.client = Anthropic(api_key=api_key)
        self.agent_name = agent_name
    
    async def chat(self, message: str, model: str = "claude-3-5-sonnet-20241022"):
        async with learning_async(agent=self.agent_name):
            response = await self.client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text
```

### 2. Memory-Only Mode (Capture Without Injection)
```python
# Use capture_only=True to save conversations without memory injection
async with learning_async(agent="research-agent", capture_only=True):
    # Conversation will be saved but no memory will be retrieved/injected
    response = await claude.messages.create(...)
```

### 3. Custom Memory Blocks
```python
# Define custom memory blocks for specific context
custom_memory = [
    {"label": "project_context", "description": "Current project details"},
    {"label": "user_preferences", "description": "User's working preferences"}
]

async with learning_async(agent="my-agent", memory=custom_memory):
    response = await claude.messages.create(...)
```

## Advanced Patterns

### Multi-Agent Memory Sharing
```python
# Multiple agents can share memory by using the same agent name
agent1 = MemoryEnhancedClaudeAgent(api_key, "shared-agent")
agent2 = MemoryEnhancedClaudeAgent(api_key, "shared-agent")

# Both agents will access the same memory context
response1 = await agent1.chat("Research topic X")
response2 = await agent2.chat("Summarize our research")
```

### Context-Aware Tool Selection
```python
async def context_aware_tool_use():
    async with learning_async(agent="tool-selector"):
        # Memory will help agent choose appropriate tools
        memories = await get_memories("tool-selector")
        
        if "web_search_needed" in str(memories):
            return use_web_search()
        elif "data_analysis" in str(memories):
            return use_data_tools()
        else:
            return use_default_tools()
```

## Best Practices

### 1. Agent Naming
- Use descriptive agent names that reflect their purpose
- For related functionality, use consistent naming patterns
- Example: `email-processor`, `research-assistant`, `code-reviewer`

### 2. Memory Structure
```python
# Good: Specific, purposeful memory blocks
memory_blocks = [
    {"label": "conversation_history", "description": "Recent conversation context"},
    {"label": "task_context", "description": "Current task and goals"},
    {"label": "user_preferences", "description": "User interaction preferences"}
]
```

### 3. Error Handling
```python
async def robust_claude_call(message: str):
    try:
        async with learning_async(agent="my-agent"):
            return await claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": message}]
            )
    except Exception as e:
        # Fallback without memory if learning fails
        return await claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": message}]
        )
```

## Memory Management

### Retrieving Conversation History
```python
from agentic_learning import AsyncAgenticLearning

async def get_conversation_context(agent_name: str):
    client = AsyncAgenticLearning()
    memories = await client.get_memories(agent_name)
    return memories
```

### Clearing Memory
```python
# When starting fresh contexts
client = AsyncAgenticLearning()
await client.clear_memory(agent_name)
```

## Integration Examples

### Research Agent with Memory
```python
class ResearchAgent:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    async def research(self, topic: str):
        async with learning_async(
            agent="research-agent",
            memory=[
                {"label": "research_history", "description": "Previous research topics"},
                {"label": "current_session", "description": "Current research session"}
            ]
        ):
            prompt = f"Research the topic: {topic}. Consider previous research context."
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
```

### Code Review Assistant
```python
class CodeReviewAssistant:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    async def review_code(self, code: str, context: str = ""):
        async with learning_async(
            agent="code-reviewer",
            memory=[
                {"label": "review_history", "description": "Past code reviews and feedback"},
                {"label": "coding_standards", "description": "Project coding standards"}
            ]
        ):
            prompt = f"""
            Review the following code considering previous reviews and project standards:
            
            Context: {context}
            Code: {code}
            """
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
```

## Testing Integration

### Unit Test Pattern
```python
import pytest
from agentic_learning import learning

async def test_memory_integration():
    async with learning_async(agent="test-agent"):
        # Test that memory is working
        response = await claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "Remember this test"}]
        )
        
        # Verify memory was captured
        client = AsyncAgenticLearning()
        memories = await client.get_memories("test-agent")
        assert len(memories) > 0
```

## Troubleshooting

### Common Issues
1. **Memory not appearing**: Ensure agent name is consistent across calls
2. **Performance issues**: Use `capture_only=True` for logging-only scenarios
3. **Context overflow**: Regularly clear memory for long-running sessions
4. **Async conflicts**: Always use `learning_async` with async Claude SDK calls

### Debug Mode
```python
# Enable debug logging to see memory operations
import logging
logging.basicConfig(level=logging.DEBUG)

async with learning_async(agent="debug-agent"):
    # Memory operations will be logged
    response = await claude.messages.create(...)
```

## References

- [Agentic Learning SDK Documentation](https://github.com/letta-ai/agentic-learning-sdk)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [Example Implementation](https://github.com/letta-ai/agentic-learning-sdk/tree/main/examples/claude_agent_research_demo)