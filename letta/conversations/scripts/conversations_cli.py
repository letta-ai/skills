#!/usr/bin/env python3
"""
Conversations CLI - Interactive TUI for Letta Conversations API

A simple terminal interface for managing and chatting across multiple
conversations with a single agent.

Commands:
    /new [name]     - Create a new conversation (optional name for display)
    /list           - List all conversations
    /switch <num>   - Switch to conversation by number
    /history [n]    - Show last n messages (default: 10)
    /info           - Show current conversation info
    /agents         - List available agents
    /agent <id>     - Switch to a different agent
    /quit           - Exit the CLI

Usage:
    LETTA_API_KEY=your-key uv run examples/conversations_cli.py
    LETTA_API_KEY=your-key uv run examples/conversations_cli.py --agent agent-xxx
"""

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from letta_client import Letta


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_BLUE = "\033[44m"


def colored(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{Colors.RESET}"


@dataclass
class ConversationInfo:
    """Track conversation metadata for display."""
    id: str
    name: str
    created_at: datetime
    message_count: int = 0


@dataclass
class AppState:
    """Application state."""
    client: Letta
    agent_id: str
    agent_name: str
    conversations: list[ConversationInfo] = field(default_factory=list)
    current_conversation: Optional[ConversationInfo] = None


def print_header(state: AppState):
    """Print the app header with current context."""
    print()
    print(colored("=" * 60, Colors.DIM))
    print(colored("  LETTA CONVERSATIONS CLI", Colors.BOLD + Colors.CYAN))
    print(colored(f"  Agent: {state.agent_name}", Colors.DIM))
    if state.current_conversation:
        print(colored(f"  Conversation: {state.current_conversation.name}", Colors.GREEN))
    else:
        print(colored("  Conversation: (none selected)", Colors.YELLOW))
    print(colored("=" * 60, Colors.DIM))
    print(colored("  Commands: /new /list /switch /history /info /agents /agent /quit", Colors.DIM))
    print(colored("=" * 60, Colors.DIM))
    print()


def print_error(msg: str):
    """Print an error message."""
    print(colored(f"Error: {msg}", Colors.RED))


def print_success(msg: str):
    """Print a success message."""
    print(colored(f"✓ {msg}", Colors.GREEN))


def print_info(msg: str):
    """Print an info message."""
    print(colored(f"ℹ {msg}", Colors.CYAN))


def refresh_conversations(state: AppState):
    """Refresh the list of conversations from the server."""
    convs = state.client.conversations.list(agent_id=state.agent_id)
    state.conversations = []
    
    for i, conv in enumerate(convs):
        # Generate a friendly name
        created = conv.created_at
        name = f"Conversation {i + 1} ({created.strftime('%m/%d %H:%M')})"
        
        info = ConversationInfo(
            id=conv.id,
            name=name,
            created_at=created,
            message_count=len(conv.in_context_message_ids),
        )
        state.conversations.append(info)
        
        # Update current conversation reference if it matches
        if state.current_conversation and state.current_conversation.id == conv.id:
            state.current_conversation = info


def cmd_new(state: AppState, args: list[str]):
    """Create a new conversation."""
    conv = state.client.conversations.create(agent_id=state.agent_id)
    
    # Create friendly name
    name = " ".join(args) if args else f"Conversation {len(state.conversations) + 1}"
    
    info = ConversationInfo(
        id=conv.id,
        name=name,
        created_at=conv.created_at,
        message_count=0,
    )
    state.conversations.append(info)
    state.current_conversation = info
    
    print_success(f"Created and switched to: {name}")
    print_info(f"ID: {conv.id}")


def cmd_list(state: AppState):
    """List all conversations."""
    refresh_conversations(state)
    
    if not state.conversations:
        print_info("No conversations yet. Use /new to create one.")
        return
    
    print()
    print(colored("  # │ Name                              │ Messages │ Created", Colors.BOLD))
    print(colored("  ──┼───────────────────────────────────┼──────────┼─────────────", Colors.DIM))
    
    for i, conv in enumerate(state.conversations):
        num = f"{i + 1:>2}"
        name = conv.name[:33].ljust(33)
        msgs = f"{conv.message_count:>8}"
        created = conv.created_at.strftime("%m/%d %H:%M")
        
        # Highlight current conversation
        if state.current_conversation and state.current_conversation.id == conv.id:
            line = colored(f"  {num} │ {name} │ {msgs} │ {created}", Colors.GREEN)
            line += colored(" ◀", Colors.GREEN + Colors.BOLD)
        else:
            line = f"  {num} │ {name} │ {msgs} │ {created}"
        
        print(line)
    
    print()


def cmd_switch(state: AppState, args: list[str]):
    """Switch to a conversation by number."""
    if not args:
        print_error("Usage: /switch <number>")
        return
    
    try:
        num = int(args[0])
    except ValueError:
        print_error("Please provide a valid number")
        return
    
    if num < 1 or num > len(state.conversations):
        print_error(f"Invalid conversation number. Use 1-{len(state.conversations)}")
        return
    
    state.current_conversation = state.conversations[num - 1]
    print_success(f"Switched to: {state.current_conversation.name}")


def cmd_history(state: AppState, args: list[str]):
    """Show conversation history."""
    if not state.current_conversation:
        print_error("No conversation selected. Use /new or /switch first.")
        return
    
    limit = 10
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            # Invalid limit provided; keep default of 10 messages
            pass
    
    messages = state.client.conversations.messages.list(
        conversation_id=state.current_conversation.id,
        limit=limit,
    )
    
    if not messages:
        print_info("No messages in this conversation yet.")
        return
    
    print()
    print(colored(f"  Last {len(messages)} messages:", Colors.BOLD))
    print(colored("  " + "─" * 56, Colors.DIM))
    
    for msg in messages:
        msg_type = getattr(msg, "message_type", "unknown")
        content = getattr(msg, "content", "")
        
        if not content:
            continue
        
        # Truncate long messages
        if len(content) > 200:
            content = content[:200] + "..."
        
        # Color based on message type
        if msg_type == "user_message":
            prefix = colored("  You: ", Colors.CYAN + Colors.BOLD)
        elif msg_type == "assistant_message":
            prefix = colored("  Bot: ", Colors.GREEN + Colors.BOLD)
        elif msg_type == "system_message":
            prefix = colored("  Sys: ", Colors.DIM)
            content = content[:80] + "..." if len(content) > 80 else content
        else:
            prefix = colored(f"  {msg_type}: ", Colors.DIM)
        
        # Wrap content for display
        print(f"{prefix}{content}")
    
    print()


def cmd_info(state: AppState):
    """Show current conversation info."""
    if not state.current_conversation:
        print_error("No conversation selected.")
        return
    
    # Refresh to get latest
    conv = state.client.conversations.retrieve(
        conversation_id=state.current_conversation.id
    )
    
    print()
    print(colored("  Current Conversation", Colors.BOLD))
    print(colored("  " + "─" * 40, Colors.DIM))
    print(f"  ID:       {conv.id}")
    print(f"  Agent:    {conv.agent_id}")
    print(f"  Created:  {conv.created_at}")
    print(f"  Messages: {len(conv.in_context_message_ids)} in context")
    if conv.summary:
        print(f"  Summary:  {conv.summary}")
    print()


def cmd_agents(state: AppState):
    """List available agents."""
    agents = state.client.agents.list(limit=20).items
    
    print()
    print(colored("  Available Agents:", Colors.BOLD))
    print(colored("  " + "─" * 56, Colors.DIM))
    
    for agent in agents:
        if agent.id == state.agent_id:
            print(colored(f"  • {agent.name} ({agent.id}) ◀ current", Colors.GREEN))
        else:
            print(f"  • {agent.name} ({agent.id})")
    
    print()
    print_info("Use /agent <id> to switch agents")


def cmd_agent(state: AppState, args: list[str]):
    """Switch to a different agent."""
    if not args:
        print_error("Usage: /agent <agent-id>")
        return
    
    agent_id = args[0]
    
    try:
        agent = state.client.agents.retrieve(agent_id=agent_id)
        state.agent_id = agent.id
        state.agent_name = agent.name
        state.conversations = []
        state.current_conversation = None
        
        print_success(f"Switched to agent: {agent.name}")
        refresh_conversations(state)
        
    except Exception as e:
        print_error(f"Could not find agent: {e}")


def send_message(state: AppState, message: str):
    """Send a message to the current conversation."""
    if not state.current_conversation:
        print_error("No conversation selected. Use /new or /switch first.")
        return
    
    print()
    
    try:
        stream = state.client.conversations.messages.create(
            conversation_id=state.current_conversation.id,
            messages=[{"role": "user", "content": message}],
        )
        
        # Stream and display the response
        print(colored("  Bot: ", Colors.GREEN + Colors.BOLD), end="", flush=True)
        
        for msg in stream:
            if hasattr(msg, "message_type"):
                if msg.message_type == "assistant_message":
                    # Print content as it streams
                    print(msg.content, end="", flush=True)
                elif msg.message_type == "reasoning_message":
                    # Show reasoning in dim color
                    reasoning = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    print(colored(f"\n  [Thinking: {reasoning}]", Colors.DIM))
                    print(colored("  Bot: ", Colors.GREEN + Colors.BOLD), end="", flush=True)
        
        print()  # Newline after response
        
        # Update message count
        state.current_conversation.message_count += 2  # user + assistant
        
    except Exception as e:
        print_error(f"Failed to send message: {e}")


def get_or_create_agent(client: Letta, agent_id: Optional[str]) -> tuple[str, str]:
    """Get an existing agent or create a demo one."""
    if agent_id:
        try:
            agent = client.agents.retrieve(agent_id=agent_id)
            return agent.id, agent.name
        except Exception:
            print_error(f"Agent {agent_id} not found")
            sys.exit(1)
    
    # Try to find an existing agent
    agents = client.agents.list(limit=1).items
    if agents:
        return agents[0].id, agents[0].name
    
    # Create a demo agent
    print_info("No agents found. Creating a demo agent...")
    agent = client.agents.create(
        name="conversations-cli-agent",
        model="openai/gpt-4o-mini",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {"label": "human", "value": "A user testing the conversations CLI."},
            {"label": "persona", "value": "You are a helpful assistant. Keep responses concise."},
        ],
    )
    return agent.id, agent.name


def main():
    parser = argparse.ArgumentParser(description="Letta Conversations CLI")
    parser.add_argument("--agent", "-a", help="Agent ID to use")
    parser.add_argument("--base-url", "-u", default=os.getenv("LETTA_BASE_URL", "https://api.letta.com"))
    args = parser.parse_args()
    
    # Create client
    api_key = os.getenv("LETTA_API_KEY")
    if api_key:
        client = Letta(base_url=args.base_url, api_key=api_key)
    else:
        client = Letta(base_url=args.base_url)
    
    # Get or create agent
    agent_id, agent_name = get_or_create_agent(client, args.agent)
    
    # Initialize state
    state = AppState(
        client=client,
        agent_id=agent_id,
        agent_name=agent_name,
    )
    
    # Load existing conversations
    refresh_conversations(state)
    
    # Print header
    print_header(state)
    
    # If no conversations exist, prompt to create one
    if not state.conversations:
        print_info("No conversations yet. Creating one for you...")
        cmd_new(state, [])
        print()
    else:
        # Auto-select the most recent conversation
        state.current_conversation = state.conversations[0]
        print_info(f"Resumed: {state.current_conversation.name}")
        print()
    
    # Main loop
    while True:
        try:
            # Build prompt
            if state.current_conversation:
                prompt = colored(f"[{state.current_conversation.name}]", Colors.GREEN) + " > "
            else:
                prompt = colored("[no conversation]", Colors.YELLOW) + " > "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                parts = user_input[1:].split()
                cmd = parts[0].lower() if parts else ""
                cmd_args = parts[1:] if len(parts) > 1 else []
                
                if cmd == "quit" or cmd == "q" or cmd == "exit":
                    print_info("Goodbye!")
                    break
                elif cmd == "new" or cmd == "n":
                    cmd_new(state, cmd_args)
                elif cmd == "list" or cmd == "l" or cmd == "ls":
                    cmd_list(state)
                elif cmd == "switch" or cmd == "s":
                    cmd_switch(state, cmd_args)
                elif cmd == "history" or cmd == "h":
                    cmd_history(state, cmd_args)
                elif cmd == "info" or cmd == "i":
                    cmd_info(state)
                elif cmd == "agents":
                    cmd_agents(state)
                elif cmd == "agent":
                    cmd_agent(state, cmd_args)
                elif cmd == "help" or cmd == "?":
                    print_header(state)
                else:
                    print_error(f"Unknown command: /{cmd}")
            else:
                # Send as message
                send_message(state, user_input)
                
        except KeyboardInterrupt:
            print()
            print_info("Use /quit to exit")
        except EOFError:
            print()
            print_info("Goodbye!")
            break


if __name__ == "__main__":
    main()
