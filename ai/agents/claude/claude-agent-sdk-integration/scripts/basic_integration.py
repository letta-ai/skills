#!/usr/bin/env python3
"""
Basic Claude Agent SDK Integration Example
Demonstrates the 3-line pattern for adding memory to Claude agents
"""

import asyncio
import os
from anthropic import Anthropic
from agentic_learning import learning_async

async def basic_integration_example():
    """Example showing the core 3-line integration pattern"""
    
    # Initialize Claude client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    client = Anthropic(api_key=api_key)
    
    print("=== Basic Integration Example ===")
    
    # First message - will establish memory context
    async with learning_async(agent="demo-agent"):
        response1 = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user", 
                "content": "Hi! I'm working on a Python project about memory integration. Please remember this context."
            }]
        )
        print(f"Claude (first response): {response1.content[0].text}")
    
    print("\n--- Memory separator ---\n")
    
    # Second message - will recall previous context
    async with learning_async(agent="demo-agent"):
        response2 = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user", 
                "content": "Can you suggest some best practices for my project?"
            }]
        )
        print(f"Claude (with memory): {response2.content[0].text}")

if __name__ == "__main__":
    asyncio.run(basic_integration_example())