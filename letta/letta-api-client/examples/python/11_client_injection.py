"""
Client injection patterns for Letta Cloud.

On Letta Cloud, tools have access to:
- `client` - Pre-configured Letta client (no need to instantiate)
- `os.getenv("LETTA_AGENT_ID")` - Current agent's ID

This enables powerful custom memory tools.

Run: python 11_client_injection.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Tool 1: Custom memory tool using injected client
# =============================================================================

CUSTOM_REMEMBER_TOOL = '''
def remember_with_tags(content: str, tags: str) -> str:
    """
    Store information in the notes memory block with tags.
    
    Args:
        content: The information to remember
        tags: Comma-separated tags for categorization
    
    Returns:
        Confirmation message
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Get current notes block
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="notes"
    )
    
    # Format and append
    tag_list = [t.strip() for t in tags.split(",")]
    entry = f"[{', '.join(tag_list)}] {content}"
    updated_value = f"{block.value}\\n{entry}" if block.value else entry
    
    # Update the block
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="notes",
        value=updated_value
    )
    
    return f"Remembered: {content} (tags: {tag_list})"
'''


# =============================================================================
# Tool 2: Search archival and promote to core memory
# =============================================================================

PROMOTE_FROM_ARCHIVAL_TOOL = '''
def promote_to_core_memory(query: str, target_block: str) -> str:
    """
    Search archival memory and add top result to a core memory block.
    
    Args:
        query: Search query for archival memory
        target_block: Label of the core memory block to update
    
    Returns:
        Result of the operation
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Search archival
    results = list(client.agents.passages.list(
        agent_id=agent_id,
        query_text=query,
        limit=1
    ))
    
    if not results:
        return f"No results found for: {query}"
    
    top_result = results[0].text
    
    # Get and update target block
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label=target_block
    )
    
    updated = f"{block.value}\\n\\nFrom archival: {top_result}"
    
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label=target_block,
        value=updated
    )
    
    return f"Promoted to {target_block}: {top_result[:100]}..."
'''


# =============================================================================
# Tool 3: Structured task management
# =============================================================================

TASK_MANAGER_TOOL = '''
def manage_tasks(action: str, task: str = "", task_id: int = -1) -> str:
    """
    Manage a structured task list in memory.
    
    Args:
        action: One of "add", "complete", "list"
        task: Task description (for "add" action)
        task_id: Task index to complete (for "complete" action)
    
    Returns:
        Result of the operation
    """
    import os
    import json
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Get tasks block
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="tasks"
    )
    
    try:
        tasks = json.loads(block.value) if block.value else []
    except json.JSONDecodeError:
        tasks = []
    
    if action == "add":
        tasks.append({"task": task, "done": False})
        result = f"Added task: {task}"
    
    elif action == "complete":
        if 0 <= task_id < len(tasks):
            tasks[task_id]["done"] = True
            result = f"Completed: {tasks[task_id]['task']}"
        else:
            return f"Invalid task_id: {task_id}"
    
    elif action == "list":
        if not tasks:
            return "No tasks"
        lines = [f"{'[x]' if t['done'] else '[ ]'} {i}: {t['task']}" 
                 for i, t in enumerate(tasks)]
        return "\\n".join(lines)
    
    else:
        return f"Unknown action: {action}"
    
    # Save updated tasks
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="tasks",
        value=json.dumps(tasks)
    )
    
    return result
'''


# =============================================================================
# Create tools and agent
# =============================================================================

print("Creating tools...")

remember_tool = client.tools.create(source_code=CUSTOM_REMEMBER_TOOL)
promote_tool = client.tools.create(source_code=PROMOTE_FROM_ARCHIVAL_TOOL)
task_tool = client.tools.create(source_code=TASK_MANAGER_TOOL)

print(f"Created: {remember_tool.name}, {promote_tool.name}, {task_tool.name}")

# Create agent with custom memory tools
agent = client.agents.create(
    name="self-modifying-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am an assistant that actively manages my own memory."
        },
        {
            "label": "human",
            "value": "User preferences and information."
        },
        {
            "label": "notes",
            "value": "Tagged notes and observations:"
        },
        {
            "label": "tasks",
            "value": "[]"  # JSON array for structured tasks
        }
    ],
    tool_ids=[remember_tool.id, promote_tool.id, task_tool.id]
)

print(f"\nCreated agent: {agent.id}")


# =============================================================================
# Test the custom memory tools
# =============================================================================

print("\n--- Testing Custom Memory Tools ---")

# Test remember with tags
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{
        "role": "user",
        "content": "Remember that I prefer dark mode and short responses. Tag these as 'preference'."
    }]
)

for msg in response.messages:
    if msg.message_type == "tool_call_message":
        print(f"[Tool: {msg.tool_call.name}]")
    elif msg.message_type == "assistant_message":
        print(f"Agent: {msg.content}")

# Check the notes block was updated
notes_block = client.agents.blocks.retrieve(agent_id=agent.id, block_label="notes")
print(f"\nNotes block now contains:\n{notes_block.value}")


# Test task management
print("\n--- Testing Task Management ---")

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{
        "role": "user",
        "content": "Add a task to review the API documentation."
    }]
)

for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(f"Agent: {msg.content}")

# Check tasks block
tasks_block = client.agents.blocks.retrieve(agent_id=agent.id, block_label="tasks")
print(f"Tasks block: {tasks_block.value}")
