#!/usr/bin/env python3
"""
Agent with Custom MCP Server

Example agent with custom MCP tools for calculations and data processing.
Demonstrates how to create and integrate MCP servers.

Usage:
    python agent_with_mcp.py
"""

import asyncio
import os
import sys
from typing import Any
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock
)

# Define custom MCP tools
@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args: dict[str, Any]) -> dict[str, Any]:
    """Add two numbers and return the result."""
    result = args["a"] + args["b"]
    return {
        "content": [{
            "type": "text",
            "text": f"Sum: {result}"
        }]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args: dict[str, Any]) -> dict[str, Any]:
    """Multiply two numbers and return the result."""
    result = args["a"] * args["b"]
    return {
        "content": [{
            "type": "text",
            "text": f"Product: {result}"
        }]
    }

@tool("factorial", "Calculate factorial", {"n": int})
async def factorial(args: dict[str, Any]) -> dict[str, Any]:
    """Calculate factorial of a number."""
    n = args["n"]
    
    if n < 0:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Factorial not defined for negative numbers"
            }],
            "isError": True
        }
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return {
        "content": [{
            "type": "text",
            "text": f"Factorial of {n}: {result}"
        }]
    }

@tool("is_prime", "Check if number is prime", {"n": int})
async def is_prime(args: dict[str, Any]) -> dict[str, Any]:
    """Check if a number is prime."""
    n = args["n"]
    
    if n < 2:
        return {
            "content": [{
                "type": "text",
                "text": f"{n} is not prime"
            }]
        }
    
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return {
                "content": [{
                    "type": "text",
                    "text": f"{n} is not prime (divisible by {i})"
                }]
            }
    
    return {
        "content": [{
            "type": "text",
            "text": f"{n} is prime"
        }]
    }

async def main():
    """Run agent with custom MCP server."""
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    # Create MCP server with custom tools
    calculator = create_sdk_mcp_server(
        name="calculator",
        version="1.0.0",
        tools=[add, multiply, factorial, is_prime]
    )
    
    # Configure agent
    options = ClaudeAgentOptions(
        system_prompt="You are a math assistant. Use the calculator tools to help with calculations.",
        mcp_servers={"calc": calculator},
        allowed_tools=[
            "Read",
            "mcp__calc__add",
            "mcp__calc__multiply",
            "mcp__calc__factorial",
            "mcp__calc__is_prime"
        ],
        permission_mode="bypassPermissions"
    )
    
    print("=" * 80)
    print("Agent with Custom MCP Calculator")
    print("=" * 80)
    print("\nAvailable tools:")
    print("  - add: Add two numbers")
    print("  - multiply: Multiply two numbers")
    print("  - factorial: Calculate factorial")
    print("  - is_prime: Check if number is prime")
    print("\nTry: 'What is 15 factorial?' or 'Is 97 a prime number?'")
    print("=" * 80 + "\n")
    
    # Start agent
    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting...")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            try:
                await client.query(user_input)
                
                print("\nClaude: ", end="", flush=True)
                
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(block.text, end="", flush=True)
                
                print("\n")
            
            except Exception as e:
                print(f"\nError: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
