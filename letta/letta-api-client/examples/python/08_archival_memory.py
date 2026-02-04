"""
Working with archival memory (large-scale semantic search).

Run: python 08_archival_memory.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Create an agent with archival memory tools
# =============================================================================

agent = client.agents.create(
    name="knowledge-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a knowledge assistant with access to a document library."},
        {"label": "human", "value": "User queries."}
    ],
    include_base_tools=True  # Includes archival_memory_insert and archival_memory_search
)

print(f"Created agent: {agent.id}")


# =============================================================================
# Insert passages into archival memory
# =============================================================================

print("\n--- Inserting Knowledge ---")

# Insert multiple knowledge passages
passages = [
    "The TechWidget 3000 is our flagship product. It features AI-powered automation, "
    "voice control, and seamless integration with smart home devices. Price: $299.",
    
    "Return Policy: All products can be returned within 30 days of purchase for a full refund. "
    "Items must be in original packaging. Contact support@techcorp.com to initiate a return.",
    
    "Warranty Information: All TechWidgets come with a 2-year manufacturer warranty covering "
    "defects in materials and workmanship. Battery is covered for 1 year.",
    
    "Troubleshooting: If your TechWidget won't turn on, try these steps: 1) Check the power "
    "connection 2) Hold the reset button for 10 seconds 3) Try a different outlet.",
    
    "TechWidget Pro is our premium offering with extended battery life (48 hours), "
    "water resistance (IP67), and priority customer support. Price: $499.",
]

for text in passages:
    results = client.agents.passages.create(
        agent_id=agent.id,
        text=text
    )
    # passages.create returns a list
    print(f"Inserted passage: {results[0].id}")


# =============================================================================
# Search archival memory programmatically
# =============================================================================

print("\n--- Searching Archival Memory ---")

# Search by query
results = client.agents.passages.list(
    agent_id=agent.id,
    search="return policy refund",
    limit=3
)

print("\nSearch results for 'return policy refund':")
for passage in results:
    print(f"  - {passage.text[:80]}...")


# =============================================================================
# Let the agent use archival memory
# =============================================================================

print("\n--- Agent Using Archival Memory ---")

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "What's the warranty on TechWidgets?"}]
)

for msg in response.messages:
    if msg.message_type == "tool_call_message":
        print(f"[Agent searching: {msg.tool_call.name}]")
    elif msg.message_type == "tool_return_message":
        print(f"[Found: {msg.tool_return[:100]}...]")
    elif msg.message_type == "assistant_message":
        print(f"\nAgent: {msg.content}")


# =============================================================================
# Query with metadata filtering
# =============================================================================

print("\n--- Filtering by Metadata ---")

# Get all product-related passages
product_passages = client.agents.passages.list(
    agent_id=agent.id,
    search="price features",
    limit=10
)

print("\nAll passages about products:")
for passage in product_passages:
    if passage.metadata and passage.metadata.get("category") == "product":
        print(f"  - {passage.text[:60]}...")


# =============================================================================
# List all passages
# =============================================================================

print("\n--- Listing All Passages ---")

all_passages = list(client.agents.passages.list(agent_id=agent.id, limit=5))
print(f"Total passages: {len(all_passages)}")
for p in all_passages[:3]:
    print(f"  - {p.text[:60]}...")


# =============================================================================
# Delete a passage
# =============================================================================

# client.agents.passages.delete(agent_id=agent.id, passage_id=passage_id)
