#!/usr/bin/env python3
"""
Provider-Specific Settings Example

Demonstrates how to configure OpenAI reasoning models and
Anthropic extended thinking capabilities.

Usage:
    export LETTA_API_KEY="your-api-key"
    python provider_specific.py
"""

import os
from letta_client import Letta

# Initialize client
client = Letta(api_key=os.getenv("LETTA_API_KEY"))

# ============================================================
# OpenAI Reasoning Models (o1, o3, o3-mini)
# ============================================================

print("=== OpenAI Reasoning Model ===")

reasoning_agent = client.agents.create(
    name="reasoning-demo",
    model="openai/o3-mini",
    model_settings={
        "provider_type": "openai",  # Required field
        # Reasoning settings must be nested under "reasoning" key
        "reasoning": {
            "reasoning_effort": "medium"  # "low", "medium", or "high"
        }
    },
    memory_blocks=[
        {"label": "persona", "value": "You are a logical problem solver."},
        {"label": "human", "value": ""}
    ]
)

print(f"Created reasoning agent: {reasoning_agent.id}")

# Test with a reasoning task
response = client.agents.messages.create(
    agent_id=reasoning_agent.id,
    messages=[{
        "role": "user",
        "content": "If all cats are mammals, and some mammals are black, can we conclude that some cats are black?"
    }]
)

for message in response.messages:
    if hasattr(message, "content") and message.content:
        print(f"Reasoning agent: {message.content}")

# ============================================================
# Anthropic Extended Thinking
# ============================================================

print("\n=== Anthropic Extended Thinking ===")

thinking_agent = client.agents.create(
    name="thinking-demo",
    model="anthropic/claude-sonnet-4-5-20250929",
    model_settings={
        "provider_type": "anthropic",  # Required field
        # Thinking settings must be nested under "thinking" key
        "thinking": {
            "type": "enabled",     # Required field
            "budget_tokens": 10000  # How many tokens for internal reasoning
        }
    },
    memory_blocks=[
        {"label": "persona", "value": "You are a thoughtful analyst."},
        {"label": "human", "value": ""}
    ]
)

print(f"Created thinking agent: {thinking_agent.id}")

# Test with a complex task
response = client.agents.messages.create(
    agent_id=thinking_agent.id,
    messages=[{
        "role": "user",
        "content": "What are three non-obvious implications of widespread AI adoption in healthcare?"
    }]
)

for message in response.messages:
    if hasattr(message, "content") and message.content:
        print(f"Thinking agent: {message.content}")

# ============================================================
# Combined Settings
# ============================================================

print("\n=== Combined Settings ===")

# You can combine provider-specific settings with standard settings
combined_agent = client.agents.create(
    name="combined-demo",
    model="openai/o3-mini",
    model_settings={
        "provider_type": "openai",  # Required field
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "reasoning": {
            "reasoning_effort": "high"
        }
    },
    context_window_limit=128000,
    memory_blocks=[
        {"label": "persona", "value": "You solve complex problems step by step."},
        {"label": "human", "value": ""}
    ]
)

print(f"Created combined agent: {combined_agent.id}")
print("Agent configured with temperature, max_output_tokens, and reasoning_effort")
