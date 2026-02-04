# Sleeptime Agents

Sleeptime agents run background processing to refine and organize memory between conversations.

## Enabling Sleeptime

```python
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a helpful assistant."},
        {"label": "human", "value": "User information."}
    ],
    enable_sleeptime=True  # Creates a background sleeptime agent
)
```

```typescript
const agent = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  embedding: "openai/text-embedding-3-small",
  memory_blocks: [
    { label: "persona", value: "I am a helpful assistant." },
    { label: "human", value: "User information." }
  ],
  enable_sleeptime: true
});
```

## How It Works

1. **Main agent** handles real-time conversations
2. **Sleeptime agent** runs in background between conversations
3. Sleeptime agent reviews conversation history and refines memory blocks
4. Both agents share the same memory blocks

```
User conversation
       ↓
   Main Agent (real-time)
       ↓
   Memory blocks updated
       ↓
   [Time passes...]
       ↓
   Sleeptime Agent (background)
       ↓
   Memory blocks refined/organized
```

## Enabling on Existing Agent

```python
# Enable sleeptime on an existing agent
client.agents.update(
    agent_id=agent.id,
    enable_sleeptime=True
)
```

## When to Use Sleeptime

**Good for:**
- Personal assistants that learn over time
- Agents that need to consolidate information
- Long-running agents with many conversations
- Memory organization and deduplication

**Not needed for:**
- Stateless support bots
- Single-session interactions
- Agents where memory doesn't evolve

## Sleeptime Frequency

The sleeptime agent runs periodically based on conversation activity. You can configure frequency:

```python
client.agents.update(
    agent_id=agent.id,
    sleeptime_agent_frequency=5  # Run after every 5 conversations
)
```

## Monitoring Sleeptime

Check sleeptime agent activity in ADE:
1. Open your agent
2. Look for the sleeptime agent indicator
3. View memory block changes over time

## Example: Learning Assistant

```python
# Create an agent that learns and improves over time
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am a learning assistant. I remember what works and what doesn't."
        },
        {
            "label": "human",
            "value": "User preferences and learning style."
        },
        {
            "label": "lessons_learned",
            "value": "Insights from past interactions:"
        }
    ],
    enable_sleeptime=True
)

# After many conversations, the sleeptime agent will:
# - Consolidate repeated information
# - Organize the lessons_learned block
# - Update human block with patterns it notices
```
