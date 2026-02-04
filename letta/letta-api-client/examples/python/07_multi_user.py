"""
Multi-user patterns: one agent per user vs shared agent with conversations.

Run: python 07_multi_user.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Pattern 1: One Agent Per User
# =============================================================================
# Best for: personalization, isolation, learning user preferences

print("--- Pattern 1: One Agent Per User ---")

def create_user_agent(user_id: str, user_name: str):
    """Create a dedicated agent for a user."""
    agent = client.agents.create(
        name=f"assistant-{user_id}",
        model="anthropic/claude-sonnet-4-5-20250929",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "persona",
                "value": "I am a personal assistant. I remember your preferences."
            },
            {
                "label": "human",
                "value": f"Name: {user_name}\nUser ID: {user_id}\nPreferences: (learning...)"
            }
        ],
        tags=[f"user:{user_id}"]  # Tag for easy lookup
    )
    return agent

def find_user_agent(user_id: str):
    """Find existing agent for a user by tag."""
    agents = client.agents.list(tags=[f"user:{user_id}"], limit=1)
    for agent in agents:
        return agent
    return None


# Create agents for two users
user1_agent = create_user_agent("user-001", "Alice")
user2_agent = create_user_agent("user-002", "Bob")

print(f"Created agent for Alice: {user1_agent.id}")
print(f"Created agent for Bob: {user2_agent.id}")

# Each user has isolated conversations
response1 = client.agents.messages.create(
    agent_id=user1_agent.id,
    messages=[{"role": "user", "content": "I prefer short answers. Remember that."}]
)

response2 = client.agents.messages.create(
    agent_id=user2_agent.id,
    messages=[{"role": "user", "content": "I like detailed explanations. Remember that."}]
)

print("\nAlice's agent learned her preference.")
print("Bob's agent learned his preference (independently).")


# =============================================================================
# Pattern 2: Shared Agent with Conversations API
# =============================================================================
# Best for: support bots, FAQ agents, cost-effective scaling

print("\n--- Pattern 2: Shared Agent with Conversations ---")

# Create ONE shared support agent
support_agent = client.agents.create(
    name="support-bot",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am a customer support agent for TechCorp."
        },
        {
            "label": "knowledge",
            "value": "Product info: TechWidget costs $99. Returns within 30 days."
        }
    ]
)

print(f"Created shared support agent: {support_agent.id}")

# Create separate conversations for different users
conv_alice = client.conversations.create(
    agent_id=support_agent.id,
    name="Support chat - Alice"
)

conv_bob = client.conversations.create(
    agent_id=support_agent.id,
    name="Support chat - Bob"
)

print(f"Created conversation for Alice: {conv_alice.id}")
print(f"Created conversation for Bob: {conv_bob.id}")

# Users chat in isolated conversations (but share the same agent)
response_alice = client.agents.messages.create(
    agent_id=support_agent.id,
    messages=[{"role": "user", "content": "What's your return policy?"}],
    conversation_id=conv_alice.id
)

response_bob = client.agents.messages.create(
    agent_id=support_agent.id,
    messages=[{"role": "user", "content": "How much does TechWidget cost?"}],
    conversation_id=conv_bob.id
)

# Extract responses
for msg in response_alice.messages:
    if msg.message_type == "assistant_message":
        print(f"\nAlice's support response: {msg.content[:100]}...")

for msg in response_bob.messages:
    if msg.message_type == "assistant_message":
        print(f"Bob's support response: {msg.content[:100]}...")


# =============================================================================
# Concurrent requests work in parallel
# =============================================================================

print("\n--- Concurrent Requests ---")

import asyncio
from letta_client import AsyncLetta

async def concurrent_example():
    async_client = AsyncLetta(api_key=os.getenv("LETTA_API_KEY"))
    
    # These run fully parallel - no blocking between conversations
    responses = await asyncio.gather(
        async_client.agents.messages.create(
            agent_id=support_agent.id,
            messages=[{"role": "user", "content": "Question from user 1"}],
            conversation_id=conv_alice.id
        ),
        async_client.agents.messages.create(
            agent_id=support_agent.id,
            messages=[{"role": "user", "content": "Question from user 2"}],
            conversation_id=conv_bob.id
        )
    )
    
    print(f"Processed {len(responses)} concurrent requests")
    return responses

# asyncio.run(concurrent_example())


# =============================================================================
# Clean up
# =============================================================================
# client.agents.delete(user1_agent.id)
# client.agents.delete(user2_agent.id)
# client.agents.delete(support_agent.id)
