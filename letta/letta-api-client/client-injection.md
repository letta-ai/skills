# Client Injection & Agent Secrets

On Letta Cloud, tools have access to a pre-injected `client` variable and environment variables. This enables powerful patterns like custom memory tools.

## The Injected Client

**On Letta Cloud, every tool has access to:**
- `client` - A pre-configured Letta client (no need to instantiate)
- `os.getenv("LETTA_AGENT_ID")` - The current agent's ID

This lets tools call the Letta API to modify the agent's own state.

## Example: Custom Memory Tool

```python
def remember_important_fact(fact: str, category: str) -> str:
    """
    Store an important fact in the agent's memory with categorization.
    
    Args:
        fact: The fact to remember
        category: Category for organization (e.g., "preference", "task", "context")
    
    Returns:
        Confirmation message
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Get current memory block
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="notes"
    )
    
    # Append the new fact
    updated_value = f"{block.value}\n[{category}] {fact}"
    
    # Update the block
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="notes",
        value=updated_value
    )
    
    return f"Remembered: {fact} (category: {category})"
```

## Example: Clear Memory Block

```python
def clear_memory_block(label: str) -> str:
    """
    Clear the contents of a memory block.
    
    Args:
        label: The label of the block to clear
    
    Returns:
        Confirmation message
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label=label,
        value=""
    )
    
    return f"Cleared memory block: {label}"
```

## Example: Search and Store Pattern

```python
def search_and_remember(query: str) -> str:
    """
    Search archival memory and optionally promote results to core memory.
    
    Args:
        query: Search query
    
    Returns:
        Search results
    """
    import os
    import json
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Search archival memory
    results = client.agents.passages.list(
        agent_id=agent_id,
        query_text=query,
        limit=5
    )
    
    passages = [{"text": p.text, "score": p.score} for p in results]
    
    return json.dumps(passages, indent=2)
```

## Agent Secrets (Environment Variables)

Tools access secrets via `os.getenv()`. Set them when creating or updating an agent:

### Setting Secrets

```python
# When creating
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...],
    tool_ids=[my_tool.id],
    secrets={
        "EXTERNAL_API_KEY": "sk-xxx",
        "DATABASE_URL": "postgres://...",
        "CUSTOM_VAR": "value"
    }
)

# When updating
client.agents.update(
    agent_id=agent.id,
    secrets={
        "EXTERNAL_API_KEY": "new-key"
    }
)
```

### Using Secrets in Tools

```python
def call_external_api(query: str) -> str:
    """Call an external API using configured credentials."""
    import os
    import requests
    
    api_key = os.getenv("EXTERNAL_API_KEY")
    if not api_key:
        return "Error: EXTERNAL_API_KEY not configured"
    
    response = requests.get(
        "https://api.example.com/search",
        params={"q": query},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return response.text
```

## Available Environment Variables

| Variable | Description | Availability |
|----------|-------------|--------------|
| `LETTA_AGENT_ID` | Current agent's ID | Always available |
| Custom secrets | Set via `secrets` parameter | Must be configured |

## Common Patterns

### Pattern 1: Self-Modifying Agent

Agent can update its own persona based on interactions:

```python
def update_personality_trait(trait: str, value: str) -> str:
    """Update a personality trait in the persona block."""
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    block = client.agents.blocks.retrieve(agent_id=agent_id, block_label="persona")
    
    # Simple append (in practice, you'd want smarter merging)
    updated = f"{block.value}\n{trait}: {value}"
    
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="persona",
        value=updated
    )
    
    return f"Updated personality: {trait} = {value}"
```

### Pattern 2: Structured Memory Management

```python
def add_to_task_list(task: str, priority: str = "medium") -> str:
    """Add a task to the structured task list."""
    import os
    import json
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    block = client.agents.blocks.retrieve(agent_id=agent_id, block_label="tasks")
    
    try:
        tasks = json.loads(block.value) if block.value else []
    except json.JSONDecodeError:
        tasks = []
    
    tasks.append({"task": task, "priority": priority, "status": "pending"})
    
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="tasks",
        value=json.dumps(tasks, indent=2)
    )
    
    return f"Added task: {task} (priority: {priority})"
```

### Pattern 3: Cross-Agent Communication

```python
def notify_supervisor(message: str) -> str:
    """Send a message to the supervisor agent."""
    import os
    
    supervisor_id = os.getenv("SUPERVISOR_AGENT_ID")  # Set in secrets
    
    response = client.agents.messages.create(
        agent_id=supervisor_id,
        messages=[{"role": "user", "content": f"[Worker Report] {message}"}]
    )
    
    # Extract supervisor's response
    for msg in response.messages:
        if msg.message_type == "assistant_message":
            return f"Supervisor replied: {msg.content}"
    
    return "Notification sent"
```

## Important Notes

1. **Cloud only** - The injected `client` is only available on Letta Cloud, not self-hosted
2. **No instantiation needed** - Don't do `client = Letta(...)` inside tools on Cloud
3. **Secrets are agent-scoped** - Each agent has its own secrets, not shared across agents
4. **LETTA_AGENT_ID is automatic** - Always available, no need to add it to secrets
5. **Imports inside function** - Still required, even with client injection
