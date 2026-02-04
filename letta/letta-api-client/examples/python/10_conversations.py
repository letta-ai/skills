"""
Working with conversations for parallel sessions with shared memory.

Conversations allow:
- Multiple parallel sessions with the same agent
- Shared memory blocks across all conversations
- Separate context windows per conversation
- Thread-safe concurrent messaging

Run: python 10_conversations.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Create an agent
# =============================================================================

agent = client.agents.create(
    name="multi-session-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am a helpful coding assistant. I remember context across sessions."
        },
        {
            "label": "human",
            "value": "User working on multiple tasks."
        },
        {
            "label": "project",
            "value": "Project notes shared across all conversations."
        }
    ]
)

print(f"Created agent: {agent.id}")


# =============================================================================
# Create multiple conversations
# =============================================================================

print("\n--- Creating Conversations ---")

# Conversation 1: API refactoring task
conv_api = client.conversations.create(
    agent_id=agent.id,
    name="API Refactoring"
)

# Conversation 2: Writing tests task  
conv_tests = client.conversations.create(
    agent_id=agent.id,
    name="Writing Tests"
)

# Conversation 3: Documentation task
conv_docs = client.conversations.create(
    agent_id=agent.id,
    name="Documentation"
)

print(f"Created conversation for API work: {conv_api.id}")
print(f"Created conversation for tests: {conv_tests.id}")
print(f"Created conversation for docs: {conv_docs.id}")


# =============================================================================
# Send messages to different conversations
# =============================================================================

print("\n--- Sending Messages to Different Conversations ---")

# Note: conversations.messages.create returns a stream
stream1 = client.conversations.messages.create(
    conv_api.id,
    messages=[{"role": "user", "content": "I'm working on refactoring the user API. The main file is user_api.py."}]
)

print("API conversation:")
for chunk in stream1:
    if chunk.message_type == "assistant_message":
        print(f"  Agent: {chunk.content[:100]}...")
        break


stream2 = client.conversations.messages.create(
    conv_tests.id,
    messages=[{"role": "user", "content": "I need to write tests for the authentication module."}]
)

print("\nTests conversation:")
for chunk in stream2:
    if chunk.message_type == "assistant_message":
        print(f"  Agent: {chunk.content[:100]}...")
        break


# =============================================================================
# Conversations share memory - updates visible to all
# =============================================================================

print("\n--- Memory Sharing Demo ---")

# Update memory in API conversation
stream = client.conversations.messages.create(
    conv_api.id,
    messages=[{"role": "user", "content": "Remember: the API uses REST with JSON responses. Update your project notes."}]
)

for chunk in stream:
    if chunk.message_type == "assistant_message":
        print(f"API conv learned: {chunk.content[:80]}...")
        break

# Now the tests conversation can see the same memory
stream = client.conversations.messages.create(
    conv_tests.id,
    messages=[{"role": "user", "content": "What do you know about our API format?"}]
)

print("\nTests conv can access shared knowledge:")
for chunk in stream:
    if chunk.message_type == "assistant_message":
        print(f"  {chunk.content[:150]}...")
        break


# =============================================================================
# Stream with token-level output
# =============================================================================

print("\n--- Token Streaming in Conversations ---")

stream = client.conversations.messages.create(
    conv_docs.id,
    messages=[{"role": "user", "content": "Write a one-sentence summary of REST APIs."}],
    stream_tokens=True
)

print("Streaming response: ", end="")
for chunk in stream:
    if chunk.message_type == "assistant_message":
        print(chunk.content, end="", flush=True)
print()


# =============================================================================
# List all conversations for an agent
# =============================================================================

print("\n--- List Conversations ---")

conversations = client.conversations.list(agent_id=agent.id)

for conv in conversations:
    print(f"  - {conv.id}: {conv.name or '(unnamed)'}")


# =============================================================================
# List messages in a conversation
# =============================================================================

print("\n--- Message History for API Conversation ---")

messages = client.conversations.messages.list(conv_api.id)

for msg in messages:
    if msg.message_type == "user_message":
        print(f"  User: {msg.content[:50]}...")
    elif msg.message_type == "assistant_message":
        print(f"  Agent: {msg.content[:50]}...")


# =============================================================================
# Concurrent messaging (thread-safe with conversations)
# =============================================================================

print("\n--- Concurrent Messaging ---")

import asyncio
from letta_client import AsyncLetta

async def concurrent_conversations():
    async_client = AsyncLetta(api_key=os.getenv("LETTA_API_KEY"))
    
    # These run in parallel - each conversation has its own stream
    # This is thread-safe, unlike agents.messages.create
    
    async def send_to_conv(conv_id: str, message: str):
        stream = await async_client.conversations.messages.create(
            conv_id,
            messages=[{"role": "user", "content": message}]
        )
        async for chunk in stream:
            if chunk.message_type == "assistant_message":
                return chunk.content[:50]
        return ""
    
    results = await asyncio.gather(
        send_to_conv(conv_api.id, "Quick question about REST"),
        send_to_conv(conv_tests.id, "Quick question about testing"),
        send_to_conv(conv_docs.id, "Quick question about documentation"),
    )
    
    print(f"Got {len(results)} concurrent responses")
    for i, result in enumerate(results):
        print(f"  Response {i+1}: {result}...")

# Uncomment to run:
# asyncio.run(concurrent_conversations())


# =============================================================================
# When to use conversations vs separate agents
# =============================================================================

"""
USE CONVERSATIONS when:
- Same user, multiple parallel tasks (coding + testing + docs)
- Need thread-safe concurrent messaging
- Want shared memory across sessions
- Different "threads" of the same overall project

USE SEPARATE AGENTS when:
- Different users (need full isolation)
- Completely unrelated contexts
- Different personas/capabilities needed
- Privacy/data separation required
"""
