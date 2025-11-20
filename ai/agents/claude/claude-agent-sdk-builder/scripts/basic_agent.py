#!/usr/bin/env python3
"""
Basic Interactive Agent Template

A simple interactive agent with file operations and basic configuration.
Perfect starting point for building custom agents.

Usage:
    python basic_agent.py
"""

import asyncio
import os
import sys
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock

async def main():
    """Run interactive agent session."""
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)
    
    # Configure agent
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful coding assistant with expertise in Python and JavaScript.",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        permission_mode="acceptEdits",  # Auto-approve file edits
        cwd=os.getcwd()
    )
    
    print("=" * 80)
    print("Basic Interactive Agent")
    print("=" * 80)
    print("\nCommands:")
    print("  'exit' or 'quit' - Exit the agent")
    print("  Any other input - Send to agent")
    print("\n" + "=" * 80 + "\n")
    
    # Start agent
    async with ClaudeSDKClient(options=options) as client:
        while True:
            # Get user input
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
            
            # Send to agent
            try:
                await client.query(user_input)
                
                print("\nClaude: ", end="", flush=True)
                
                # Process response
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
