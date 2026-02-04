# Memory Architecture

Letta agents have a hierarchical memory system inspired by the MemGPT research paper. Understanding when to use each memory type is crucial for building effective agents.

## Memory Hierarchy

```
┌─────────────────────────────────────────────┐
│           CORE MEMORY (In-Context)          │
│  Always visible to the agent in every turn  │
│  ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ persona │ │  human  │ │ custom blocks│  │
│  └─────────┘ └─────────┘ └──────────────┘  │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│        EXTERNAL MEMORY (Out-of-Context)     │
│   Retrieved on-demand via tool calls        │
│  ┌────────────────┐ ┌────────────────────┐  │
│  │ Archival Memory│ │ Conversation Search│  │
│  │ (semantic)     │ │ (hybrid search)    │  │
│  └────────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Core Memory Blocks

**What**: Persistent, editable sections always in the agent's context window.

**When to use**: 
- Agent identity and personality (persona)
- Current user information and preferences (human)
- Frequently-accessed working knowledge (custom blocks)

**Limits**: 
- Character-limited (typically 2000-5000 chars per block)
- Recommend 5-15 blocks max for reliability

### Creating an Agent with Memory Blocks

```python
# Python
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am a helpful customer support agent for Acme Corp."
        },
        {
            "label": "human", 
            "value": "User preferences and history will be stored here."
        },
        {
            "label": "product_knowledge",
            "value": "Key product facts: ..."
        }
    ]
)
```

```typescript
// TypeScript
const agent = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  embedding: "openai/text-embedding-3-small",
  memory_blocks: [
    { label: "persona", value: "I am a helpful customer support agent." },
    { label: "human", value: "User preferences stored here." },
    { label: "product_knowledge", value: "Key product facts: ..." }
  ]
});
```

### Updating Memory Blocks

```python
# Python - Update a block's value
client.agents.blocks.update(
    agent_id=agent.id,
    block_label="human",
    value="User name: Alice. Prefers email communication."
)

# Retrieve a block
block = client.agents.blocks.retrieve(
    agent_id=agent.id, 
    block_label="human"
)
print(block.value)
```

```typescript
// TypeScript
await client.agents.blocks.update("human", {
  agent_id: agent.id,
  value: "User name: Alice. Prefers email communication."
});

const block = await client.agents.blocks.retrieve("human", { 
  agent_id: agent.id 
});
console.log(block.value);
```

## Archival Memory

**What**: Large-scale persistent storage with semantic search.

**When to use**:
- Knowledge bases (documents, FAQs, product catalogs)
- Historical data that's too large for core memory
- Information that needs semantic retrieval

**Access**: Via `archival_memory_insert` and `archival_memory_search` tools (must be attached to agent).

### Inserting into Archival Memory

```python
# Python - Insert a passage
client.agents.passages.create(
    agent_id=agent.id,
    text="The refund policy allows returns within 30 days of purchase.",
    metadata={"category": "policy", "topic": "refunds"}
)

# Insert with specific tags for filtering
client.agents.passages.create(
    agent_id=agent.id,
    text="Premium users get priority support via phone.",
    metadata={"tier": "premium", "topic": "support"}
)
```

### Searching Archival Memory

The agent uses `archival_memory_search` tool during conversations. You can also search programmatically:

```python
# Python - Search passages
results = client.agents.passages.list(
    agent_id=agent.id,
    query_text="refund policy",
    limit=5
)

for passage in results:
    print(f"Score: {passage.score}, Text: {passage.text}")
```

## Shared Memory Blocks

**What**: Memory blocks attached to multiple agents, enabling coordination.

**When to use**:
- Supervisor/worker agent patterns
- Agents that need shared state
- Team knowledge that multiple agents access

### Creating Shared Blocks

```python
# Python
# Create a shared block
shared_block = client.blocks.create(
    label="team_context",
    value="Current project: Q1 launch. Priority: high."
)

# Create agents that share the block
supervisor = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    memory_blocks=[{"label": "persona", "value": "I am the supervisor."}],
    block_ids=[shared_block.id]
)

worker = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929", 
    memory_blocks=[{"label": "persona", "value": "I am a worker agent."}],
    block_ids=[shared_block.id]
)

# When supervisor updates the shared block, worker sees it immediately
```

```typescript
// TypeScript
const sharedBlock = await client.blocks.create({
  label: "team_context",
  value: "Current project: Q1 launch. Priority: high."
});

const supervisor = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  memory_blocks: [{ label: "persona", value: "I am the supervisor." }],
  block_ids: [sharedBlock.id]
});

const worker = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  memory_blocks: [{ label: "persona", value: "I am a worker agent." }],
  block_ids: [sharedBlock.id]
});
```

## Conversation History

**What**: Searchable history of all messages in the conversation.

**When to use**:
- Finding what was discussed earlier
- Recalling user requests from past turns

**Access**: Via `conversation_search` tool.

```python
# Python - List messages programmatically
messages = client.agents.messages.list(agent_id=agent.id, limit=100)

for msg in messages:
    if msg.message_type == "user_message":
        print(f"User: {msg.content}")
    elif msg.message_type == "assistant_message":
        print(f"Agent: {msg.content}")
```

## Memory Design Patterns

### Pattern 1: Personal Assistant
```
Core Memory:
  - persona: Assistant personality and capabilities
  - human: User profile, preferences, schedule
  - tasks: Current active tasks

Archival Memory:
  - Past completed tasks
  - User history and interactions
```

### Pattern 2: Customer Support Bot
```
Core Memory:
  - persona: Company voice and policies
  - human: Current user, their issue
  - current_ticket: Active support context

Archival Memory:
  - Knowledge base articles
  - FAQ entries
  - Past ticket resolutions
```

### Pattern 3: Multi-Agent Team
```
Shared Block: team_context (project state, priorities)

Supervisor Agent:
  - Core: persona, team_context (shared)
  - Role: Coordinate workers, track progress

Worker Agents:
  - Core: persona, team_context (shared), assigned_task
  - Role: Execute specific tasks
```

## Enabling Archival Memory Tools

By default, agents don't have archival memory tools. Enable them with `include_base_tools`:

```python
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...],
    include_base_tools=True  # Adds archival_memory_insert, archival_memory_search
)
```

This adds:
- `archival_memory_insert` - Store information in archival memory
- `archival_memory_search` - Semantic search over archival memory

## Shared Memory Concurrency

When multiple agents write to shared blocks simultaneously:

| Tool | Behavior | Best For |
|------|----------|----------|
| `memory_insert` | Append operation | Concurrent writes (safest) |
| `memory_replace` | Find and replace | Single writer, specific edits |
| `memory_rethink` | Complete overwrite | Reorganization (last-writer-wins) |

**Race condition example:**
```
Agent A reads block: "Tasks: buy milk"
Agent B reads block: "Tasks: buy milk"
Agent A writes: "Tasks: buy milk, call mom"
Agent B writes: "Tasks: buy milk, send email"  # Overwrites A's change!
```

**Safe pattern with memory_insert:**
```
Agent A appends: "- call mom"
Agent B appends: "- send email"
Result: Both changes preserved
```

## Best Practices

1. **Keep core memory focused** - 5-15 blocks, essential info only
2. **Use archival for large data** - Move detailed info out of context
3. **Structure blocks clearly** - Agent can edit them, make format obvious
4. **Add block descriptions** - Help agent understand when to use each block
5. **Use `memory_insert` for shared blocks** - Safest for concurrent writes
6. **Enable `include_base_tools`** - If you need archival memory access
