"""
Tool rules for constraining tool execution order.

Tool rules let you:
- Force tools to run in a specific order
- Create approval workflows
- Build sequential pipelines

Run: python 12_tool_rules.py
"""
import os
from letta_client import Letta
from letta_client.types import InitToolRule, ChildToolRule, TerminalToolRule

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Create tools for a data processing pipeline
# =============================================================================

FETCH_TOOL = '''
def fetch_data(query: str) -> str:
    """Fetch data based on a query. Must be called first."""
    return f"Fetched data for: {query}"
'''

PROCESS_TOOL = '''
def process_data(data: str) -> str:
    """Process the fetched data. Can only be called after fetch_data."""
    return f"Processed: {data}"
'''

FORMAT_TOOL = '''
def format_output(processed: str) -> str:
    """Format the final output. Ends the agent's turn."""
    return f"Final output: {processed}"
'''

print("Creating tools...")
fetch_tool = client.tools.create(source_code=FETCH_TOOL)
process_tool = client.tools.create(source_code=PROCESS_TOOL)
format_tool = client.tools.create(source_code=FORMAT_TOOL)


# =============================================================================
# Create agent with sequential pipeline rules
# =============================================================================

print("\n--- Creating Agent with Tool Rules ---")

agent = client.agents.create(
    name="pipeline-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I process data in a strict pipeline: fetch -> process -> format."
        },
        {
            "label": "human", 
            "value": "User requesting data processing."
        }
    ],
    tool_ids=[fetch_tool.id, process_tool.id, format_tool.id],
    tool_rules=[
        # fetch_data must be called first
        InitToolRule(tool_name="fetch_data"),
        
        # After fetch_data, only process_data can be called
        ChildToolRule(tool_name="fetch_data", children=["process_data"]),
        
        # After process_data, only format_output can be called
        ChildToolRule(tool_name="process_data", children=["format_output"]),
        
        # format_output ends the turn
        TerminalToolRule(tool_name="format_output")
    ]
)

print(f"Created agent: {agent.id}")


# =============================================================================
# Test the pipeline
# =============================================================================

print("\n--- Testing Pipeline ---")

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{
        "role": "user",
        "content": "Process data about 'AI agents'"
    }]
)

print("Tool execution order:")
for msg in response.messages:
    if msg.message_type == "tool_call_message":
        print(f"  → {msg.tool_call.name}")
    elif msg.message_type == "tool_return_message":
        print(f"    Result: {msg.tool_return[:50]}...")
    elif msg.message_type == "assistant_message":
        print(f"\nFinal response: {msg.content}")


# =============================================================================
# Example 2: Approval workflow
# =============================================================================

print("\n\n--- Creating Approval Workflow Agent ---")

PROPOSE_TOOL = '''
def propose_action(action: str) -> str:
    """Propose an action that needs approval."""
    return f"Proposed action: {action}. Awaiting confirmation."
'''

CONFIRM_TOOL = '''
def confirm_action(approved: bool, reason: str = "") -> str:
    """Confirm or reject the proposed action."""
    if approved:
        return f"Action approved. {reason}"
    return f"Action rejected. {reason}"
'''

EXECUTE_TOOL = '''
def execute_action() -> str:
    """Execute the approved action. Only callable after confirmation."""
    return "Action executed successfully!"
'''

propose_tool = client.tools.create(source_code=PROPOSE_TOOL)
confirm_tool = client.tools.create(source_code=CONFIRM_TOOL)
execute_tool = client.tools.create(source_code=EXECUTE_TOOL)

approval_agent = client.agents.create(
    name="approval-workflow-agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I follow a strict approval workflow: propose -> confirm -> execute."
        },
        {"label": "human", "value": "User."}
    ],
    tool_ids=[propose_tool.id, confirm_tool.id, execute_tool.id],
    tool_rules=[
        # Must propose first
        InitToolRule(tool_name="propose_action"),
        
        # After proposing, must confirm
        ChildToolRule(tool_name="propose_action", children=["confirm_action"]),
        
        # After confirming, can execute
        ChildToolRule(tool_name="confirm_action", children=["execute_action"]),
        
        # Execute ends the turn
        TerminalToolRule(tool_name="execute_action")
    ]
)

print(f"Created approval agent: {approval_agent.id}")

# Test approval workflow
response = client.agents.messages.create(
    agent_id=approval_agent.id,
    messages=[{
        "role": "user",
        "content": "Send an email to the team about the project update"
    }]
)

print("\nApproval workflow execution:")
for msg in response.messages:
    if msg.message_type == "tool_call_message":
        print(f"  → {msg.tool_call.name}({msg.tool_call.arguments})")
    elif msg.message_type == "assistant_message":
        print(f"\nAgent: {msg.content}")
