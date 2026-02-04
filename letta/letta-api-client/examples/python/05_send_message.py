"""
Send messages to an agent and handle different response types.

Run: python 05_send_message.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Create an agent (or use existing)
# =============================================================================

agent = client.agents.create(
    name="chat-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a helpful assistant."},
        {"label": "human", "value": "User info."}
    ],
    tools=["web_search"]
)

print(f"Agent: {agent.id}")


# =============================================================================
# Send a simple message
# =============================================================================

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[
        {"role": "user", "content": "Hello! How are you today?"}
    ]
)

print("\n--- Simple Message ---")
for message in response.messages:
    print(f"[{message.message_type}]")
    if message.message_type == "assistant_message":
        print(f"  Content: {message.content}")
    elif message.message_type == "reasoning_message":
        print(f"  Reasoning: {message.reasoning[:200]}...")


# =============================================================================
# Send a message that triggers tool use
# =============================================================================

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[
        {"role": "user", "content": "Search the web for the latest news about AI agents."}
    ]
)

print("\n--- Message with Tool Use ---")
for message in response.messages:
    if message.message_type == "reasoning_message":
        print(f"[Reasoning] {message.reasoning[:100]}...")
    elif message.message_type == "tool_call_message":
        print(f"[Tool Call] {message.tool_call.name}")
        print(f"  Args: {message.tool_call.arguments}")
    elif message.message_type == "tool_return_message":
        print(f"[Tool Return] {message.tool_return[:200]}...")
    elif message.message_type == "assistant_message":
        print(f"[Response] {message.content}")


# =============================================================================
# Helper function to extract assistant message
# =============================================================================

def get_assistant_response(response) -> str:
    """Extract the assistant's text response from a message response."""
    for message in response.messages:
        if message.message_type == "assistant_message":
            return message.content
    return ""


response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "What's 2 + 2?"}]
)

print(f"\n--- Extracted Response ---")
print(get_assistant_response(response))


# =============================================================================
# List message history
# =============================================================================

print("\n--- Message History ---")
messages = client.agents.messages.list(agent_id=agent.id, limit=10)

for msg in messages:
    if msg.message_type == "user_message":
        print(f"User: {msg.content[:50]}...")
    elif msg.message_type == "assistant_message":
        print(f"Agent: {msg.content[:50]}...")
