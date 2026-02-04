"""
Create an agent with memory blocks.

Run: python 02_create_agent.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))

# =============================================================================
# Create a basic agent with memory blocks
# =============================================================================

agent = client.agents.create(
    name="my-assistant",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": """I am a helpful assistant named Alex. 
I am friendly, concise, and always try to provide accurate information.
I remember user preferences and adapt my communication style accordingly."""
        },
        {
            "label": "human",
            "value": """User information will be stored here as I learn about them.
Currently unknown - will update as we interact."""
        },
        {
            "label": "notes",
            "value": """Important notes and reminders:
- (empty)"""
        }
    ],
    tools=["web_search"],  # Built-in web search tool
    tags=["example", "assistant"]
)

print(f"Created agent: {agent.id}")
print(f"Name: {agent.name}")
print(f"Model: {agent.model}")


# =============================================================================
# Send a message to the agent
# =============================================================================

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[
        {"role": "user", "content": "Hi! My name is Sarah and I prefer concise responses."}
    ]
)

# Extract and print the assistant's response
for message in response.messages:
    if message.message_type == "assistant_message":
        print(f"\nAgent: {message.content}")
    elif message.message_type == "reasoning_message":
        print(f"[Reasoning: {message.reasoning[:100]}...]")


# =============================================================================
# Check if the agent updated its memory
# =============================================================================

human_block = client.agents.blocks.retrieve(
    agent_id=agent.id,
    block_label="human"
)

print(f"\n--- Human memory block ---")
print(human_block.value)


# =============================================================================
# Clean up (optional)
# =============================================================================
# client.agents.delete(agent.id)
# print(f"\nDeleted agent: {agent.id}")
