"""
Create a custom tool that uses secrets (environment variables).

Secrets should never be passed as function arguments - use os.getenv() instead.

Run: python 04_custom_tool_secrets.py
"""
import os
from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


# =============================================================================
# Define a tool that uses an API key
# =============================================================================
# IMPORTANT: Import modules INSIDE the function (sandbox requirement)

def get_weather(city: str) -> str:
    """
    Get current weather for a city using the weather API.
    
    Args:
        city: Name of the city (e.g., "San Francisco")
    
    Returns:
        Weather information as JSON string
    """
    import os
    import requests  # Import inside function!
    
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Error: WEATHER_API_KEY not configured"
    
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": api_key,
                "units": "metric"
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return f"Weather in {city}: {data['weather'][0]['description']}, {data['main']['temp']}°C"
    
    except requests.RequestException as e:
        return f"Error fetching weather: {str(e)}"


# =============================================================================
# Create the tool
# =============================================================================

tool = client.tools.create_from_function(
    func=get_weather,
    pip_requirements=[{"name": "requests"}]  # Declare dependencies
)

print(f"Created tool: {tool.id}")


# =============================================================================
# Create agent WITH the secret configured
# =============================================================================
# The 'secrets' parameter sets environment variables in the tool sandbox

agent = client.agents.create(
    name="weather-assistant",
    model="anthropic/claude-sonnet-4-5-20250929",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "persona", "value": "I am a weather assistant."},
        {"label": "human", "value": "User location preferences."}
    ],
    tool_ids=[tool.id],
    secrets={
        "WEATHER_API_KEY": "your-openweathermap-api-key"  # Replace with real key
    }
)

print(f"Created agent: {agent.id}")


# =============================================================================
# Test the tool
# =============================================================================

response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[
        {"role": "user", "content": "What's the weather in Tokyo?"}
    ]
)

for message in response.messages:
    if message.message_type == "tool_call_message":
        print(f"\n[Calling: {message.tool_call.name}({message.tool_call.arguments})]")
    elif message.message_type == "tool_return_message":
        print(f"[Result: {message.tool_return}]")
    elif message.message_type == "assistant_message":
        print(f"\nAgent: {message.content}")


# =============================================================================
# Updating secrets on an existing agent
# =============================================================================

# You can update secrets later using agents.update()
# client.agents.update(
#     agent_id=agent.id,
#     secrets={
#         "WEATHER_API_KEY": "new-api-key"
#     }
# )
