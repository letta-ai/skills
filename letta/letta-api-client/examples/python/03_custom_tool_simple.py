"""
Create a simple custom tool.

IMPORTANT: All imports must be inside the function body!
Tools run in a sandbox without access to top-level imports.

Run: python 03_custom_tool_simple.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Define a custom tool function
# =============================================================================
# Note: Type hints and docstring are used to generate the tool schema

def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """
    Calculate Body Mass Index (BMI) from weight and height.
    
    Args:
        weight_kg: Weight in kilograms
        height_m: Height in meters
    
    Returns:
        BMI value and category as a formatted string
    """
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "normal weight"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obese"
    
    return f"BMI: {bmi:.1f} ({category})"


# =============================================================================
# Create the tool from the function
# =============================================================================

tool = client.tools.create_from_function(func=calculate_bmi)

print(f"Created tool: {tool.id}")
print(f"Name: {tool.name}")
print(f"Description: {tool.description}")


# =============================================================================
# Create an agent with the custom tool
# =============================================================================

agent = client.agents.create(
    name="health-assistant",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a health assistant that can calculate BMI."},
        {"label": "human", "value": "User health data."}
    ],
    tool_ids=[tool.id]
)

print(f"\nCreated agent: {agent.id}")


# =============================================================================
# Test the tool
# =============================================================================

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[
        {"role": "user", "content": "I weigh 70 kg and I'm 1.75 meters tall. What's my BMI?"}
    ]
)

for message in response.messages:
    if message.message_type == "tool_call_message":
        print(f"\n[Tool call: {message.tool_call.name}]")
        print(f"Arguments: {message.tool_call.arguments}")
    elif message.message_type == "tool_return_message":
        print(f"[Tool result: {message.tool_return}]")
    elif message.message_type == "assistant_message":
        print(f"\nAgent: {message.content}")


# =============================================================================
# Clean up
# =============================================================================
# client.agents.delete(agent.id)
# client.tools.delete(tool.id)
