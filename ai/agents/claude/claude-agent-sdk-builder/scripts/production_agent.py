#!/usr/bin/env python3
"""
Production-Ready Agent Template

Full-featured agent with logging, error handling, hooks, and session management.
Suitable for production deployments.

Usage:
    python production_agent.py [--session-id SESSION_ID] [--continue]
"""

import asyncio
import argparse
import logging
import os
import sys
import json
from datetime import datetime
from typing import Any
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Hooks for advanced behavior
async def audit_hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    """Log all tool usage to audit trail."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": input_data.get("hook_event_name"),
        "tool_name": input_data.get("tool_name"),
        "session_id": input_data.get("session_id"),
        "tool_use_id": tool_use_id
    }
    
    # Don't log sensitive tool inputs
    logger.info(f"Tool usage: {log_entry}")
    
    with open("audit.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return {}

async def validate_commands(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    """Validate bash commands before execution."""
    if input_data.get("tool_name") != "Bash":
        return {}
    
    command = input_data.get("tool_input", {}).get("command", "")
    
    # Block dangerous commands
    dangerous_patterns = [
        "rm -rf /",
        "dd if=/dev/zero",
        ":(){ :|:& };:",  # Fork bomb
        "mkfs."
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command:
            logger.warning(f"Blocked dangerous command: {command}")
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous command pattern detected: {pattern}"
                }
            }
    
    return {}

async def run_agent(args: argparse.Namespace):
    """Run the production agent with full configuration."""
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    # Configure agent with production settings
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": "Always follow security best practices. Log all significant actions."
        },
        allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        permission_mode="acceptEdits",
        cwd=args.working_dir,
        resume=args.session_id if args.session_id else None,
        continue_conversation=args.continue_session,
        hooks={
            "PreToolUse": [
                {"hooks": [audit_hook]},
                {"matcher": "Bash", "hooks": [validate_commands]}
            ],
            "PostToolUse": [
                {"hooks": [audit_hook]}
            ]
        }
    )
    
    logger.info("Starting production agent")
    logger.info(f"Working directory: {args.working_dir}")
    if args.session_id:
        logger.info(f"Resuming session: {args.session_id}")
    
    print("=" * 80)
    print("Production Agent - Running with full logging and security")
    print("=" * 80)
    print(f"\nWorking directory: {args.working_dir}")
    print(f"Logs: agent.log, audit.log")
    if args.session_id:
        print(f"Session: {args.session_id}")
    print("\nCommands:")
    print("  'exit' or 'quit' - Exit agent")
    print("  'session' - Show current session ID")
    print("=" * 80 + "\n")
    
    current_session_id = None
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                # Get user input
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    logger.info("User interrupted session")
                    print("\n\nExiting...")
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ["exit", "quit"]:
                    logger.info("User exited session")
                    print("Goodbye!")
                    break
                
                if user_input.lower() == "session":
                    if current_session_id:
                        print(f"Current session ID: {current_session_id}")
                    else:
                        print("No active session yet")
                    continue
                
                # Send to agent
                try:
                    logger.info(f"User query: {user_input}")
                    await client.query(user_input)
                    
                    print("\nClaude: ", end="", flush=True)
                    
                    # Process response
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    print(block.text, end="", flush=True)
                        
                        elif isinstance(message, ResultMessage):
                            # Store session ID
                            current_session_id = message.session_id
                            
                            # Log session metrics
                            logger.info(f"Session completed - ID: {message.session_id}")
                            logger.info(f"Turns: {message.num_turns}, Duration: {message.duration_ms}ms")
                            if message.total_cost_usd:
                                logger.info(f"Cost: ${message.total_cost_usd:.4f}")
                    
                    print("\n")
                
                except Exception as e:
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    print(f"\nError: {e}\n")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Agent session ended")

def main():
    """Parse arguments and run agent."""
    parser = argparse.ArgumentParser(description="Production-ready Claude agent")
    parser.add_argument(
        "--session-id",
        type=str,
        help="Resume a specific session by ID"
    )
    parser.add_argument(
        "--continue",
        dest="continue_session",
        action="store_true",
        help="Continue the most recent session"
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        default=os.getcwd(),
        help="Working directory for agent (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_agent(args))
    except KeyboardInterrupt:
        logger.info("Agent terminated by user")
        print("\n\nAgent terminated")
        sys.exit(0)

if __name__ == "__main__":
    main()
