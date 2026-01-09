#!/usr/bin/env python3
"""
Conversations API Demo Script

This script demonstrates the full capabilities of Letta's Conversations API,
which allows multiple isolated message threads on a single agent.

Use cases:
- Multi-user chat: Each user gets their own conversation with the same agent
- Session management: Separate conversations for different topics/contexts
- A/B testing: Compare agent responses across isolated conversations

Requirements:
- pip install letta-client
- Set LETTA_API_KEY environment variable (or pass token directly)

Usage:
    uv run examples/conversations_demo.py
"""

import os
import time

from letta_client import Letta


def create_client() -> Letta:
    """Create a Letta client using environment variables or defaults."""
    base_url = os.getenv("LETTA_BASE_URL", "https://api.letta.com")
    api_key = os.getenv("LETTA_API_KEY")
    
    if api_key:
        return Letta(base_url=base_url, api_key=api_key)
    else:
        # For local development without auth
        return Letta(base_url=base_url)


def create_demo_agent(client: Letta) -> str:
    """Create a demo agent for testing conversations."""
    print("\n" + "=" * 60)
    print("CREATING DEMO AGENT")
    print("=" * 60)
    
    agent = client.agents.create(
        name=f"conversations-demo-{int(time.time())}",
        model="openai/gpt-4o-mini",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "human",
                "value": "The user is testing the conversations API.",
            },
            {
                "label": "persona",
                "value": (
                    "You are a helpful assistant demonstrating the conversations API. "
                    "Keep responses brief and friendly. When asked to remember something, "
                    "acknowledge it clearly."
                ),
            },
        ],
    )
    
    print(f"Created agent: {agent.name}")
    print(f"Agent ID: {agent.id}")
    return agent.id


def demo_basic_conversation(client: Letta, agent_id: str) -> str:
    """Demonstrate basic conversation creation and messaging."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Conversation Flow")
    print("=" * 60)
    
    # Create a new conversation
    print("\n[1] Creating a new conversation...")
    conversation = client.conversations.create(agent_id=agent_id)
    print(f"    Conversation ID: {conversation.id}")
    print(f"    Agent ID: {conversation.agent_id}")
    print(f"    Created at: {conversation.created_at}")
    
    # Send a message and stream the response
    print("\n[2] Sending message: 'Hello! What can you help me with today?'")
    print("    Streaming response:")
    
    stream = client.conversations.messages.create(
        conversation_id=conversation.id,
        messages=[{"role": "user", "content": "Hello! What can you help me with today?"}],
    )
    
    # Collect and display streamed messages
    for msg in stream:
        if hasattr(msg, "message_type"):
            if msg.message_type == "assistant_message":
                print(f"    Assistant: {msg.content}")
            elif msg.message_type == "reasoning_message":
                print(f"    [Reasoning]: {msg.content[:100]}..." if len(msg.content) > 100 else f"    [Reasoning]: {msg.content}")
    
    # Send a follow-up message
    print("\n[3] Sending follow-up: 'Remember that my favorite color is blue.'")
    stream = client.conversations.messages.create(
        conversation_id=conversation.id,
        messages=[{"role": "user", "content": "Remember that my favorite color is blue."}],
    )
    
    for msg in stream:
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message":
            print(f"    Assistant: {msg.content}")
    
    # List all messages in the conversation
    print("\n[4] Listing all messages in conversation:")
    messages = client.conversations.messages.list(conversation_id=conversation.id)
    
    for i, msg in enumerate(messages):
        msg_type = getattr(msg, "message_type", "unknown")
        content = getattr(msg, "content", "")
        if content:
            # Truncate long content for display
            display_content = content[:80] + "..." if len(content) > 80 else content
            print(f"    [{i+1}] {msg_type}: {display_content}")
    
    return conversation.id


def demo_conversation_isolation(client: Letta, agent_id: str):
    """Demonstrate that conversations are isolated from each other."""
    print("\n" + "=" * 60)
    print("DEMO 2: Conversation Isolation")
    print("=" * 60)
    print("This demo shows that different conversations maintain separate contexts.")
    
    # Create two conversations
    print("\n[1] Creating two separate conversations...")
    conv_alice = client.conversations.create(agent_id=agent_id)
    conv_bob = client.conversations.create(agent_id=agent_id)
    print(f"    Alice's conversation: {conv_alice.id}")
    print(f"    Bob's conversation: {conv_bob.id}")
    
    # Alice tells the agent something
    print("\n[2] Alice says: 'My name is Alice and I love pizza.'")
    list(client.conversations.messages.create(
        conversation_id=conv_alice.id,
        messages=[{"role": "user", "content": "My name is Alice and I love pizza."}],
    ))
    
    # Bob tells the agent something different
    print("    Bob says: 'My name is Bob and I love sushi.'")
    list(client.conversations.messages.create(
        conversation_id=conv_bob.id,
        messages=[{"role": "user", "content": "My name is Bob and I love sushi."}],
    ))
    
    # Ask each conversation what they remember
    print("\n[3] Asking each conversation what they remember...")
    
    print("\n    Alice's conversation - 'What's my name and favorite food?'")
    alice_stream = client.conversations.messages.create(
        conversation_id=conv_alice.id,
        messages=[{"role": "user", "content": "What's my name and favorite food?"}],
    )
    for msg in alice_stream:
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message":
            print(f"    Response: {msg.content}")
    
    print("\n    Bob's conversation - 'What's my name and favorite food?'")
    bob_stream = client.conversations.messages.create(
        conversation_id=conv_bob.id,
        messages=[{"role": "user", "content": "What's my name and favorite food?"}],
    )
    for msg in bob_stream:
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message":
            print(f"    Response: {msg.content}")
    
    print("\n[4] Notice how each conversation maintains its own context!")
    print("    Alice's conversation knows about Alice and pizza.")
    print("    Bob's conversation knows about Bob and sushi.")
    print("    They don't leak information between each other.")


def demo_list_and_retrieve(client: Letta, agent_id: str, conversation_id: str):
    """Demonstrate listing and retrieving conversations."""
    print("\n" + "=" * 60)
    print("DEMO 3: Listing and Retrieving Conversations")
    print("=" * 60)
    
    # List all conversations for the agent
    print("\n[1] Listing all conversations for this agent:")
    conversations = client.conversations.list(agent_id=agent_id)
    
    for conv in conversations:
        print(f"    - {conv.id}")
        print(f"      Created: {conv.created_at}")
        print(f"      In-context messages: {len(conv.in_context_message_ids)}")
    
    # Retrieve a specific conversation
    print(f"\n[2] Retrieving conversation {conversation_id}:")
    conv = client.conversations.retrieve(conversation_id=conversation_id)
    print(f"    ID: {conv.id}")
    print(f"    Agent ID: {conv.agent_id}")
    print(f"    Summary: {conv.summary or '(none)'}")
    print(f"    In-context message IDs: {len(conv.in_context_message_ids)} messages")
    
    if conv.in_context_message_ids:
        print("    First few message IDs:")
        for msg_id in conv.in_context_message_ids[:3]:
            print(f"      - {msg_id}")


def demo_pagination(client: Letta, agent_id: str):
    """Demonstrate message pagination."""
    print("\n" + "=" * 60)
    print("DEMO 4: Message Pagination")
    print("=" * 60)
    
    # Create a conversation with multiple messages
    print("\n[1] Creating conversation with multiple message exchanges...")
    conversation = client.conversations.create(agent_id=agent_id)
    
    # Send several messages to build up history
    test_messages = [
        "Count to 3.",
        "Now count to 5.",
        "What numbers did you count to?",
    ]
    
    for msg in test_messages:
        print(f"    Sending: '{msg}'")
        list(client.conversations.messages.create(
            conversation_id=conversation.id,
            messages=[{"role": "user", "content": msg}],
        ))
    
    # Get all messages
    print("\n[2] Getting all messages (no limit):")
    all_messages = client.conversations.messages.list(conversation_id=conversation.id)
    print(f"    Total messages: {len(all_messages)}")
    
    # Get messages with limit
    print("\n[3] Getting first 3 messages (limit=3):")
    limited_messages = client.conversations.messages.list(
        conversation_id=conversation.id,
        limit=3,
    )
    print(f"    Returned: {len(limited_messages)} messages")
    for msg in limited_messages:
        msg_type = getattr(msg, "message_type", "unknown")
        print(f"    - {msg.id}: {msg_type}")
    
    # Demonstrate cursor-based pagination using 'after'
    if len(limited_messages) >= 3:
        last_id = limited_messages[-1].id
        print(f"\n[4] Getting messages after {last_id}:")
        next_page = client.conversations.messages.list(
            conversation_id=conversation.id,
            after=last_id,
            limit=3,
        )
        print(f"    Returned: {len(next_page)} messages")
        for msg in next_page:
            msg_type = getattr(msg, "message_type", "unknown")
            print(f"    - {msg.id}: {msg_type}")


def demo_shared_memory(client: Letta, agent_id: str):
    """Demonstrate that conversations share agent memory blocks."""
    print("\n" + "=" * 60)
    print("DEMO 5: Shared Memory Blocks")
    print("=" * 60)
    print("Conversations are isolated, but they share the agent's memory blocks.")
    print("Memory updates in one conversation are visible in others.")
    
    # Create two conversations
    print("\n[1] Creating two conversations...")
    conv1 = client.conversations.create(agent_id=agent_id)
    conv2 = client.conversations.create(agent_id=agent_id)
    
    # In conversation 1, ask the agent to update its memory
    print("\n[2] In conversation 1, asking agent to remember something in core memory...")
    print("    'Please update your core memory to note that the project deadline is Friday.'")
    list(client.conversations.messages.create(
        conversation_id=conv1.id,
        messages=[{
            "role": "user",
            "content": "Please update your core memory to note that the project deadline is Friday."
        }],
    ))
    
    # In conversation 2, ask about the deadline
    print("\n[3] In conversation 2, asking about the deadline...")
    print("    'What is the project deadline according to your memory?'")
    stream = client.conversations.messages.create(
        conversation_id=conv2.id,
        messages=[{
            "role": "user",
            "content": "What is the project deadline according to your memory?"
        }],
    )
    
    for msg in stream:
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message":
            print(f"    Response: {msg.content}")
    
    print("\n[4] Memory blocks are shared across conversations!")
    print("    - Conversation history is isolated (different users)")
    print("    - Core memory is shared (agent's persistent knowledge)")


def cleanup_agent(client: Letta, agent_id: str):
    """Clean up the demo agent."""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)
    
    try:
        client.agents.delete(agent_id=agent_id)
        print(f"Deleted agent: {agent_id}")
    except Exception as e:
        print(f"Failed to delete agent: {e}")


def main():
    """Run all conversation demos."""
    print("=" * 60)
    print("LETTA CONVERSATIONS API DEMO")
    print("=" * 60)
    print("This script demonstrates the Conversations API features.")
    print("Conversations allow multiple isolated message threads on one agent.")
    
    # Create client
    client = create_client()
    
    # Create a demo agent
    agent_id = create_demo_agent(client)
    
    try:
        # Run demos
        conversation_id = demo_basic_conversation(client, agent_id)
        demo_conversation_isolation(client, agent_id)
        demo_list_and_retrieve(client, agent_id, conversation_id)
        demo_pagination(client, agent_id)
        demo_shared_memory(client, agent_id)
        
        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ask before cleanup
        print("\n")
        cleanup = input("Delete the demo agent? [y/N]: ").strip().lower()
        if cleanup == "y":
            cleanup_agent(client, agent_id)
        else:
            print(f"Agent preserved: {agent_id}")
            print("You can continue experimenting with it.")


if __name__ == "__main__":
    main()
