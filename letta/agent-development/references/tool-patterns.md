# Common Tool Configurations

## Memory-Only Agent

```python
tools = [
  "memory_insert",
  "memory_replace",
  "memory_rethink"
]
```

**Use cases:**

- Personal assistants
- Note-taking agents
- Context managers

## File System Agent

```
# Tools auto-attached when folder connected:
# - read_file
# - write_file
# - list_files
# - grep
# - search_files
```

**Use cases:**

- Code analysis
- Document processing
- Project management

## Database Agent

```
tools = [
  "memory_insert",
  "memory_replace",
  "query_database", # Custom tool
  "update_record" # Custom tool
]
```

**Use cases:**

- Data analysis
- Report generation
- Database management

## Multi-Agent System

```
# Supervisor agent:
tools = [
  "memory_insert",
  "send_message_to_agent_and_wait_for_reply"
]

# Worker agents:
tools = [
  "memory_insert",
  "domain_specific_tool"
]
```

**Note:** Use `send_message_to_agent_and_wait_for_reply` for agent-to-agent communication. Check docs for latest multi-agent patterns.

## Tool Rules

Constrain tool sequences without hardcoded workflows:

```
tool_rules = [
  {
    "tool_name": "answer_question",
    "children": [] # Must be terminal call
  },
  {
    "tool_name": "search_files",
    "children": ["search_files", "answer_question"]
  }
]
```

**Pattern:** Agent must search before answering, but can search multiple times.

## Custom Tool Development

**Critical requirements:**

- ALL imports must be INSIDE function body
- Tools execute in sandbox without top-level imports
- Return strings or JSON-serializable objects

**Example - Creating and attaching a custom tool:**

```python
from letta_client import Letta

client = Letta()

# Define tool with imports INSIDE the function
tool_source = '''
def fetch_weather(city: str) -> str:
    """Fetch current weather for a city.
    
    Args:
        city: Name of the city
        
    Returns:
        Weather description string
    """
    import requests  # Import INSIDE function
    
    response = requests.get(f"https://wttr.in/{city}?format=3")
    return response.text
'''

# Create and attach to agent
tool = client.tools.create(source_code=tool_source)
client.agents.tools.attach(agent_id=agent.id, tool_id=tool.id)
```
