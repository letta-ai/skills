# Custom Tools

Custom tools extend your agent's capabilities beyond built-in functions. This guide covers creating, registering, and using custom tools.

## Critical Rule: Sandboxed Execution

**All imports must be inside the function body.** Tools execute in a sandboxed environment without access to top-level imports.

```python
# ❌ WRONG - imports at top level
import requests

def fetch_weather(city: str) -> str:
    return requests.get(f"https://api.weather.com/{city}").text

# ✅ CORRECT - imports inside function
def fetch_weather(city: str) -> str:
    """Fetch current weather for a city."""
    import requests
    response = requests.get(f"https://api.weather.com/{city}")
    return response.text
```

## Method 1: Simple Function (Recommended)

The easiest way to create tools. Schema is auto-generated from type hints and docstring.

```python
from letta_client import Letta

client = Letta(api_key="...")

# Define the tool function
def calculate_mortgage(
    principal: float,
    annual_rate: float, 
    years: int
) -> str:
    """
    Calculate monthly mortgage payment.
    
    Args:
        principal: Loan amount in dollars
        annual_rate: Annual interest rate as decimal (e.g., 0.05 for 5%)
        years: Loan term in years
    
    Returns:
        Monthly payment amount as formatted string
    """
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    return f"Monthly payment: ${payment:.2f}"

# Create the tool
tool = client.tools.create_from_function(func=calculate_mortgage)

# Attach to agent
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[{"label": "persona", "value": "I help with mortgage calculations."}],
    tool_ids=[tool.id]
)
```

## Method 2: Using Environment Variables (Secrets)

For tools that need API keys or other secrets, use `os.getenv()` inside the function.

```python
def search_database(query: str) -> str:
    """
    Search the product database.
    
    Args:
        query: Search query string
    
    Returns:
        Search results as JSON string
    """
    import os
    import requests
    
    api_key = os.getenv("DATABASE_API_KEY")
    if not api_key:
        return "Error: DATABASE_API_KEY not configured"
    
    response = requests.get(
        "https://api.example.com/search",
        params={"q": query},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return response.text

# Create tool
tool = client.tools.create_from_function(func=search_database)

# Create agent with the secret configured
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...],
    tool_ids=[tool.id],
    secrets={"DATABASE_API_KEY": "your-actual-key"}  # Agent-level secret
)
```

## Method 3: Using Injected Client (Cloud Only)

On Letta Cloud, a pre-configured `client` variable is available in tool execution context for self-modification.

```python
def remember_preference(preference: str) -> str:
    """
    Store a user preference in the agent's memory.
    
    Args:
        preference: The preference to remember
    
    Returns:
        Confirmation message
    """
    import os
    
    # client is pre-injected on Letta Cloud
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Get current block
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="human"
    )
    
    # Update with new preference
    updated_value = f"{block.value}\nPreference: {preference}"
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="human", 
        value=updated_value
    )
    
    return f"Remembered: {preference}"
```

## Method 4: BaseTool Class (Complex Schemas)

For tools with complex nested argument types, use `BaseTool` with Pydantic models.

```python
from letta_client import Letta
from letta_client.types.tool import BaseTool
from pydantic import BaseModel
from typing import List, Type

# Define complex argument types
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    customer_id: str
    items: List[OrderItem]
    shipping_address: str

class ProcessOrderArgs(BaseModel):
    order: Order
    priority: bool = False

# Define the tool class
class ProcessOrderTool(BaseTool):
    name: str = "process_order"
    args_schema: Type[BaseModel] = ProcessOrderArgs
    description: str = "Process a customer order"
    tags: List[str] = ["orders", "ecommerce"]
    
    def run(self, order: Order, priority: bool = False) -> str:
        """Process the order."""
        import json
        
        total = sum(item.price * item.quantity for item in order.items)
        
        return json.dumps({
            "status": "processed",
            "customer": order.customer_id,
            "total": total,
            "priority": priority
        })

# Register the tool
client = Letta(api_key="...")
tool = client.tools.add(tool=ProcessOrderTool())
```

## Method 5: Source Code String

For dynamic tool creation, pass source code as a string.

```python
source_code = '''
def greet_user(name: str, language: str = "english") -> str:
    """
    Greet a user in their preferred language.
    
    Args:
        name: User's name
        language: Language for greeting (english, spanish, french)
    
    Returns:
        Greeting message
    """
    greetings = {
        "english": f"Hello, {name}!",
        "spanish": f"¡Hola, {name}!",
        "french": f"Bonjour, {name}!"
    }
    return greetings.get(language, greetings["english"])
'''

tool = client.tools.create(source_code=source_code)
```

## TypeScript Tool Creation

```typescript
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY });

// Create tool from source code
const tool = await client.tools.create({
  source_code: `
def calculate_tip(bill_amount: float, tip_percent: float = 0.18) -> str:
    """
    Calculate tip amount.
    
    Args:
        bill_amount: Total bill in dollars
        tip_percent: Tip percentage as decimal (default 18%)
    
    Returns:
        Tip amount and total
    """
    tip = bill_amount * tip_percent
    total = bill_amount + tip
    return f"Tip: ${tip:.2f}, Total: ${total:.2f}"
  `,
  description: "Calculate tip for a restaurant bill"
});

// Create agent with tool
const agent = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  embedding: "openai/text-embedding-3-small",
  memory_blocks: [{ label: "persona", value: "I help calculate tips." }],
  tool_ids: [tool.id]
});
```

## Attaching Built-in Tools

Letta provides several built-in tools:

```python
agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...],
    tools=["web_search", "run_code"]  # Built-in tools by name
)
```

Available built-in tools:
- `web_search` - Search the web (requires EXA_API_KEY)
- `run_code` - Execute Python code in sandbox

## Tool Rules

Control tool execution order with rules:

```python
from letta_client.types import InitToolRule, TerminalToolRule

agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...],
    tool_ids=[lookup_tool.id, respond_tool.id],
    tool_rules=[
        # Always run lookup first
        InitToolRule(tool_name="lookup_context"),
        # respond_to_user ends the turn
        TerminalToolRule(tool_name="respond_to_user")
    ]
)
```

## Common Pitfalls

### 1. Top-level imports
```python
# ❌ Will fail
import json
def my_tool(data: str) -> str:
    return json.dumps({"data": data})

# ✅ Correct
def my_tool(data: str) -> str:
    import json
    return json.dumps({"data": data})
```

### 2. Passing secrets as arguments
```python
# ❌ Secrets exposed in logs/history
def call_api(api_key: str, query: str) -> str:
    ...

# ✅ Use environment variables
def call_api(query: str) -> str:
    import os
    api_key = os.getenv("API_KEY")
    ...
```

### 3. Missing type hints
```python
# ❌ No schema generated
def add(a, b):
    return a + b

# ✅ Schema auto-generated from types
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

### 4. Large return values
```python
# ❌ May exceed limits
def get_all_data() -> str:
    return massive_json_string

# ✅ Paginate or summarize
def get_data_page(page: int, limit: int = 10) -> str:
    ...
```
