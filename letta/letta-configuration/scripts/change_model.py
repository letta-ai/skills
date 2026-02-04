#!/usr/bin/env python3
"""
Change Model Example

Demonstrates how to change the model on an existing Letta agent.
The agent retains all memory and tools when switching models.

Usage:
    export LETTA_API_KEY="your-api-key"
    python change_model.py
"""

import os
from letta_client import Letta

# Initialize client
client = Letta(api_key=os.getenv("LETTA_API_KEY"))

# Create initial agent with GPT-4o
agent = client.agents.create(
    name="model-switch-demo",
    model="openai/gpt-4o-mini",
    memory_blocks=[
        {"label": "persona", "value": "You are a helpful assistant."},
        {"label": "human", "value": "User prefers concise answers."}
    ]
)

print(f"Created agent: {agent.id}")
print(f"Initial model: {agent.model}")

# Chat with the agent to create some memory
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Remember that my favorite color is blue."}]
)
print("Added memory about favorite color")

# Change to a different model
client.agents.update(
    agent_id=agent.id,
    model="anthropic/claude-sonnet-4-5-20250929"
)

# Verify the change
updated_agent = client.agents.retrieve(agent.id)
print(f"Updated model: {updated_agent.model}")

# Verify memory was retained
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "What's my favorite color?"}]
)

for message in response.messages:
    if hasattr(message, "content") and message.content:
        print(f"Agent (on new model): {message.content}")

# Change model with settings adjustment
client.agents.update(
    agent_id=agent.id,
    model="openai/gpt-4o",
    model_settings={
        "provider_type": "openai",  # Required field
        "temperature": 0.5  # More deterministic
    },
    context_window_limit=64000  # Smaller context
)

final_agent = client.agents.retrieve(agent.id)
print(f"Final model: {final_agent.model}")
print("Model change complete - memory and tools retained")
