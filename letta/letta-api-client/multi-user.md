# Multi-User Patterns

Building applications where multiple users interact with Letta agents.

## Architecture Decision

| Pattern | Personalization | Isolation | Cost | Use Case |
|---------|----------------|-----------|------|----------|
| 1 Agent per User | High | Full | Higher | Personal assistants, companions |
| Shared Agent + Conversations | Low | Partial | Lower | Support bots, FAQ agents |
| Shared Agent + Identities | Medium | Partial | Lower | Multi-tenant with context |

## Pattern 1: One Agent Per User

Each user gets their own agent with personalized memory.

### When to Use
- Personal assistants that learn user preferences
- Companion apps with relationship building
- Applications requiring full conversation isolation

### Implementation

```python
from letta_client import Letta

client = Letta(api_key="...")

def create_agent_for_user(user_id: str, user_name: str):
    """Create a dedicated agent for a new user."""
    agent = client.agents.create(
        model="anthropic/claude-sonnet-4-5-20250929",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "persona",
                "value": "I am a personal assistant."
            },
            {
                "label": "human",
                "value": f"User ID: {user_id}\nName: {user_name}\nPreferences: (to be learned)"
            }
        ],
        tags=[f"user:{user_id}"]  # Tag for easy lookup
    )
    
    # Store agent_id in your database
    save_user_agent_mapping(user_id, agent.id)
    return agent

def get_user_agent(user_id: str):
    """Retrieve existing agent for a user."""
    agent_id = get_agent_id_from_database(user_id)
    if agent_id:
        return client.agents.retrieve(agent_id)
    return None

def chat_with_user_agent(user_id: str, message: str):
    """Send message to user's agent."""
    agent_id = get_agent_id_from_database(user_id)
    
    response = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": message}]
    )
    
    return extract_assistant_message(response)
```

```typescript
// TypeScript
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY });

async function createAgentForUser(userId: string, userName: string) {
  const agent = await client.agents.create({
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am a personal assistant." },
      { label: "human", value: `User: ${userName}` }
    ],
    tags: [`user:${userId}`]
  });
  
  await saveUserAgentMapping(userId, agent.id);
  return agent;
}

async function chatWithUserAgent(userId: string, message: string) {
  const agentId = await getAgentIdFromDatabase(userId);
  
  const response = await client.agents.messages.create(agentId, {
    messages: [{ role: "user", content: message }]
  });
  
  return extractAssistantMessage(response);
}
```

## Pattern 2: Shared Agent with Conversations API

Single agent handles multiple users through separate conversation threads.

### When to Use
- Stateless support bots
- FAQ or knowledge base agents
- Cost-sensitive applications

### Implementation

```python
from letta_client import Letta

client = Letta(api_key="...")

# Create a single shared agent
support_agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona", 
            "value": "I am a customer support agent for Acme Corp."
        },
        {
            "label": "knowledge",
            "value": "Product info, policies, etc."
        }
    ]
)

def start_user_conversation(user_id: str):
    """Start a new conversation for a user."""
    conversation = client.conversations.create(
        agent_id=support_agent.id,
        name=f"Support chat for {user_id}"
    )
    
    save_user_conversation_mapping(user_id, conversation.id)
    return conversation

def chat_in_conversation(user_id: str, message: str):
    """Send message in user's conversation."""
    conversation_id = get_conversation_id_for_user(user_id)
    
    response = client.agents.messages.create(
        agent_id=support_agent.id,
        messages=[{"role": "user", "content": message}],
        conversation_id=conversation_id
    )
    
    return extract_assistant_message(response)
```

### Conversation Concurrency

Different conversations run in parallel:

```python
import asyncio
from letta_client import AsyncLetta

async_client = AsyncLetta(api_key="...")

async def handle_concurrent_users():
    # These run fully parallel - no blocking
    responses = await asyncio.gather(
        async_client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": "User 1 message"}],
            conversation_id="conv-user-1"
        ),
        async_client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": "User 2 message"}],
            conversation_id="conv-user-2"
        ),
        async_client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": "User 3 message"}],
            conversation_id="conv-user-3"
        )
    )
    return responses
```

## Pattern 3: Identities

Inject user context into a shared agent without separate agents.

### When to Use
- Multi-tenant SaaS with user-specific context
- Applications needing user identification without full personalization

### Implementation

```python
from letta_client import Letta

client = Letta(api_key="...")

# Create identities for users
def create_user_identity(user_id: str, user_data: dict):
    identity = client.identities.create(
        identifier_key=user_id,
        name=user_data["name"],
        properties={
            "email": user_data["email"],
            "plan": user_data["subscription_plan"],
            "company": user_data["company"]
        }
    )
    return identity

# Attach identity to agent
def setup_agent_with_identity(agent_id: str, identity_id: str):
    client.agents.identities.attach(
        agent_id=agent_id,
        identity_id=identity_id
    )

# Agent can now access user context via agent_state.identities
```

## Multi-User Best Practices

### 1. Agent Lookup Optimization

```python
# Use tags for efficient user->agent lookup
def find_user_agent(user_id: str):
    agents = client.agents.list(tags=[f"user:{user_id}"], limit=1)
    return next(iter(agents), None)
```

### 2. Cleanup Inactive Agents

```python
from datetime import datetime, timedelta

def cleanup_inactive_agents(days_inactive: int = 90):
    cutoff = datetime.now() - timedelta(days=days_inactive)
    
    agents = client.agents.list(limit=1000)
    for agent in agents:
        if agent.last_message_at < cutoff:
            # Archive or delete
            client.agents.delete(agent.id)
```

### 3. Rate Limiting Per User

```python
from collections import defaultdict
from time import time

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        now = time()
        # Clean old requests
        self.requests[user_id] = [
            t for t in self.requests[user_id] 
            if now - t < self.window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True

rate_limiter = RateLimiter()

def chat(user_id: str, message: str):
    if not rate_limiter.is_allowed(user_id):
        raise Exception("Rate limit exceeded")
    
    # Proceed with agent call
    ...
```

### 4. User Context Isolation

```python
def get_response_for_user(user_id: str, message: str):
    """Ensure responses only contain user's data."""
    agent_id = get_agent_id_for_user(user_id)
    
    # Verify agent belongs to user
    agent = client.agents.retrieve(agent_id)
    if f"user:{user_id}" not in agent.tags:
        raise PermissionError("Agent does not belong to user")
    
    return client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": message}]
    )
```

## Scaling Considerations

| Users | Recommended Pattern | Notes |
|-------|---------------------|-------|
| < 100 | 1 Agent per User | Simple, full personalization |
| 100-10K | Mixed | Personal agents for active users, shared for occasional |
| > 10K | Shared + Conversations | Cost-effective, use identities for context |

For high-scale deployments, consider:
- Agent pooling for shared patterns
- Background cleanup of inactive agents
- Caching of frequently-accessed agent metadata
