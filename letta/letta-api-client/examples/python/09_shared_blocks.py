"""
Multi-agent shared memory blocks.

Run: python 09_shared_blocks.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Create a shared memory block
# =============================================================================

print("--- Creating Shared Block ---")

shared_block = client.blocks.create(
    label="team_status",
    value="""Project: Q1 Product Launch
Status: In Progress
Priority: High
Current Tasks:
- Design review (assigned to Worker 1)
- Code implementation (assigned to Worker 2)
- Testing (pending)

Notes: Deadline is end of month."""
)

print(f"Created shared block: {shared_block.id}")
print(f"Label: {shared_block.label}")


# =============================================================================
# Create multiple agents that share the block
# =============================================================================

print("\n--- Creating Agents with Shared Block ---")

# Supervisor agent
supervisor = client.agents.create(
    name="supervisor",
    model="anthropic/claude-sonnet-4-5-20250929",  # More capable model for supervisor
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am the project supervisor. I coordinate the team and track progress."
        }
    ],
    block_ids=[shared_block.id]  # Attach shared block
)

# Worker agents
worker1 = client.agents.create(
    name="worker-1",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am Worker 1, responsible for design tasks."
        }
    ],
    block_ids=[shared_block.id]  # Same shared block
)

worker2 = client.agents.create(
    name="worker-2",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am Worker 2, responsible for implementation tasks."
        }
    ],
    block_ids=[shared_block.id]  # Same shared block
)

print(f"Created supervisor: {supervisor.id}")
print(f"Created worker 1: {worker1.id}")
print(f"Created worker 2: {worker2.id}")


# =============================================================================
# Demonstrate shared memory - workers see supervisor's updates
# =============================================================================

print("\n--- Supervisor Updates Shared Block ---")

# Supervisor updates the shared status
response = client.agents.messages.create(
    agent_id=supervisor.id,
    messages=[{
        "role": "user",
        "content": "Update the team status: Design review is now complete. Move Worker 1 to help with testing."
    }]
)

for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(f"Supervisor: {msg.content[:200]}...")

# Check the shared block was updated
updated_block = client.blocks.retrieve(shared_block.id)
print(f"\nShared block after supervisor update:")
print(updated_block.value)


# =============================================================================
# Worker sees the update immediately
# =============================================================================

print("\n--- Worker Sees Update ---")

response = client.agents.messages.create(
    agent_id=worker1.id,
    messages=[{
        "role": "user",
        "content": "What's my current assignment according to the team status?"
    }]
)

for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(f"Worker 1: {msg.content}")


# =============================================================================
# Pattern: Supervisor/Worker coordination
# =============================================================================

print("\n--- Full Coordination Example ---")

# Worker 2 reports progress
response = client.agents.messages.create(
    agent_id=worker2.id,
    messages=[{
        "role": "user",
        "content": "I've completed 50% of the code implementation. Update the team status."
    }]
)

for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(f"Worker 2: {msg.content[:150]}...")

# Supervisor can now see the update
response = client.agents.messages.create(
    agent_id=supervisor.id,
    messages=[{
        "role": "user",
        "content": "What's the current progress on implementation?"
    }]
)

for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(f"Supervisor: {msg.content[:150]}...")


# =============================================================================
# Attaching a block to an existing agent
# =============================================================================

print("\n--- Attaching Block to Existing Agent ---")

# Create a new shared block
new_shared_block = client.blocks.create(
    label="announcements",
    value="No new announcements."
)

# Attach to existing agent
client.agents.blocks.attach(
    agent_id=worker1.id,
    block_id=new_shared_block.id
)

print(f"Attached announcements block to worker 1")


# =============================================================================
# Detaching a block
# =============================================================================

# client.agents.blocks.detach(
#     agent_id=worker1.id,
#     block_id=new_shared_block.id
# )


# =============================================================================
# Clean up
# =============================================================================
# client.agents.delete(supervisor.id)
# client.agents.delete(worker1.id)
# client.agents.delete(worker2.id)
# client.blocks.delete(shared_block.id)
