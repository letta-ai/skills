"""
Stream agent responses in real-time.

Run: python 06_send_message_stream.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Create an agent
# =============================================================================

agent = client.agents.create(
    name="streaming-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a storytelling assistant."},
        {"label": "human", "value": "User preferences."}
    ]
)

print(f"Agent: {agent.id}\n")


# =============================================================================
# Basic streaming
# =============================================================================

print("--- Basic Streaming ---")
stream = client.agents.messages.stream(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Tell me a very short story about a robot."}]
)

for chunk in stream:
    if chunk.message_type == "reasoning_message":
        print(f"\n[Thinking...]\n")
    elif chunk.message_type == "assistant_message":
        # Print content as it arrives
        print(chunk.content, end="", flush=True)

print("\n")


# =============================================================================
# Streaming with include_pings (for long operations)
# =============================================================================
# Use include_pings=True for operations that might take > 100 seconds
# This prevents Cloudflare 524 timeout errors

print("--- Streaming with Pings ---")
stream = client.agents.messages.stream(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Write a haiku about programming."}],
    include_pings=True  # Keepalive pings every 30 seconds
)

for chunk in stream:
    # Filter out ping events (they're just keepalives)
    if chunk.message_type == "ping":
        print("[ping]", end=" ", flush=True)
        continue
    
    if chunk.message_type == "assistant_message":
        print(chunk.content, end="", flush=True)

print("\n")


# =============================================================================
# Handle all message types while streaming
# =============================================================================

print("--- Full Message Type Handling ---")
stream = client.agents.messages.stream(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "What do you remember about me?"}]
)

for chunk in stream:
    match chunk.message_type:
        case "reasoning_message":
            print(f"🧠 Thinking: {chunk.reasoning[:80]}...")
        case "tool_call_message":
            print(f"🔧 Tool: {chunk.tool_call.name}({chunk.tool_call.arguments})")
        case "tool_return_message":
            print(f"📤 Result: {chunk.tool_return[:100]}...")
        case "assistant_message":
            print(f"💬 {chunk.content}")
        case "ping":
            pass  # Ignore pings


# =============================================================================
# Background execution with resumable streams
# =============================================================================

print("\n--- Background Execution ---")
stream = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Count to 5."}],
    background=True  # Run in background
)

run_id = None
last_seq_id = None

for chunk in stream:
    run_id = chunk.run_id
    last_seq_id = chunk.seq_id
    
    if chunk.message_type == "assistant_message":
        print(f"Content: {chunk.content}")

print(f"\nRun ID: {run_id}")
print(f"Last Seq ID: {last_seq_id}")

# If connection dropped, you could resume with:
# for chunk in client.runs.stream(run_id=run_id, starting_after=last_seq_id):
#     print(chunk)
