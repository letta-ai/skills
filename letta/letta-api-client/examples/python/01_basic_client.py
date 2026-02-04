"""
Basic client initialization for Letta.

Run: python 01_basic_client.py
"""
import os
from letta_client import Letta

# =============================================================================
# Option 1: Letta Cloud
# =============================================================================
# Get your API key from https://app.letta.com/api-keys

cloud_client = Letta(api_key=os.getenv("LETTA_API_KEY"))

# Verify connection by listing agents
agents = cloud_client.agents.list(limit=5)
print(f"Connected to Letta Cloud. Found {len(list(agents))} agents.")


# =============================================================================
# Option 2: Self-Hosted (Docker)
# =============================================================================
# Start local server: docker run -p 8283:8283 letta/letta:latest

local_client = Letta(base_url="http://localhost:8283")

# Verify connection
try:
    agents = local_client.agents.list(limit=5)
    print(f"Connected to local server. Found {len(list(agents))} agents.")
except Exception as e:
    print(f"Local server not running: {e}")


# =============================================================================
# Option 3: Async Client
# =============================================================================
import asyncio
from letta_client import AsyncLetta

async def async_example():
    async_client = AsyncLetta(api_key=os.getenv("LETTA_API_KEY"))
    
    # Async operations
    agents = async_client.agents.list(limit=5)
    count = 0
    async for agent in agents:
        count += 1
    print(f"Async client found {count} agents.")

# asyncio.run(async_example())
