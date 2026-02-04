#!/usr/bin/env python3
"""
Basic Model Configuration Example

Demonstrates how to create a Letta agent with custom model settings.

Usage:
    export LETTA_API_KEY="your-api-key"
    python basic_config.py
"""

import os
from letta_client import Letta

# Initialize client
client = Letta(api_key=os.getenv("LETTA_API_KEY"))

# Create agent with model configuration
agent = client.agents.create(
    name="configured-agent",
    # Model handle format: provider/model-name
    model="openai/gpt-4o",
    # Model behavior settings (provider_type required!)
    model_settings={
        "provider_type": "openai",  # Must match model provider
        "temperature": 0.7,         # 0.0-2.0, lower = more deterministic
        "max_output_tokens": 4096   # Maximum response length
    },
    # Context window (set at agent level, not in model_settings)
    context_window_limit=128000,
    # Memory blocks
    memory_blocks=[
        {"label": "persona", "value": "You are a helpful assistant."},
        {"label": "human", "value": "The user hasn't shared any information yet."}
    ]
)

print(f"Created agent: {agent.id}")
print(f"Model: {agent.model}")

# Send a test message
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Hello! What model are you running on?"}]
)

# Print response
for message in response.messages:
    if hasattr(message, "content") and message.content:
        print(f"Agent: {message.content}")
