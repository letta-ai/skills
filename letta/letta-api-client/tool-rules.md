# Tool Rules

Constrain how and when tools are executed.

## Basic Tool Rules

Tool rules control the order and conditions under which tools can be called.

```python
from letta_client import Letta
from letta_client.types import InitToolRule, ChildToolRule, TerminalToolRule

client = Letta(api_key=os.getenv("LETTA_API_KEY"))

agent = client.agents.create(
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[...],
    tool_ids=[tool_a.id, tool_b.id, tool_c.id],
    tool_rules=[
        # tool_a must be called first
        InitToolRule(tool_name="tool_a"),
        
        # After tool_a, only tool_b can be called
        ChildToolRule(tool_name="tool_a", children=["tool_b"]),
        
        # tool_c ends the agent's turn
        TerminalToolRule(tool_name="tool_c")
    ]
)
```

## Rule Types

### InitToolRule
Forces a tool to be called at the start of execution.

```python
InitToolRule(tool_name="initialize_context")
```

### ChildToolRule
Specifies which tools can be called after a given tool.

```python
ChildToolRule(
    tool_name="search",
    children=["process_results", "refine_search"]
)
```

### TerminalToolRule
Marks a tool as ending the agent's turn (no more tool calls after).

```python
TerminalToolRule(tool_name="submit_answer")
```

### ConditionalToolRule
Call a tool only when a condition is met.

```python
ConditionalToolRule(
    tool_name="escalate_to_human",
    condition="confidence < 0.5"
)
```

## Common Patterns

### Sequential Pipeline

Force tools to run in a specific order:

```python
tool_rules=[
    InitToolRule(tool_name="fetch_data"),
    ChildToolRule(tool_name="fetch_data", children=["process_data"]),
    ChildToolRule(tool_name="process_data", children=["format_output"]),
    TerminalToolRule(tool_name="format_output")
]
```

### Approval Workflow

Require confirmation before sensitive actions:

```python
tool_rules=[
    # Can't call execute directly, must go through confirm first
    ChildToolRule(tool_name="propose_action", children=["confirm_action"]),
    ChildToolRule(tool_name="confirm_action", children=["execute_action"]),
    TerminalToolRule(tool_name="execute_action")
]
```

### Branching Logic

Allow different paths based on tool output:

```python
tool_rules=[
    InitToolRule(tool_name="classify_request"),
    ChildToolRule(
        tool_name="classify_request", 
        children=["handle_billing", "handle_technical", "handle_general"]
    ),
    TerminalToolRule(tool_name="handle_billing"),
    TerminalToolRule(tool_name="handle_technical"),
    TerminalToolRule(tool_name="handle_general")
]
```

## TypeScript Example

```typescript
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY });

const agent = await client.agents.create({
  model: "anthropic/claude-sonnet-4-5-20250929",
  embedding: "openai/text-embedding-3-small",
  memory_blocks: [...],
  tool_ids: [toolA.id, toolB.id],
  tool_rules: [
    { type: "InitToolRule", tool_name: "tool_a" },
    { type: "ChildToolRule", tool_name: "tool_a", children: ["tool_b"] },
    { type: "TerminalToolRule", tool_name: "tool_b" }
  ]
});
```

## Important Notes

1. **Don't over-constrain** - Too many rules can confuse the model
2. **Test thoroughly** - Rules can have unexpected interactions
3. **Terminal tools end turns** - Agent won't call more tools after a terminal tool
4. **Init tools run first** - But only on the first tool call of a turn
