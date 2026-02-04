/**
 * Creating custom tools in TypeScript.
 *
 * Tools are defined as source code strings (Python) that run server-side.
 *
 * Run: npx ts-node 08_custom_tool.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY! });

async function main() {
  // ===========================================================================
  // Simple tool - no external dependencies
  // ===========================================================================

  const greetTool = await client.tools.create({
    source_code: `
def greet(name: str, enthusiasm: int = 1) -> str:
    """
    Greet someone by name.
    
    Args:
        name: The person's name
        enthusiasm: Number of exclamation marks (1-5)
    
    Returns:
        A greeting message
    """
    exclaim = "!" * min(max(enthusiasm, 1), 5)
    return f"Hello, {name}{exclaim}"
`,
  });

  console.log(`Created tool: ${greetTool.name} (${greetTool.id})`);

  // ===========================================================================
  // Tool with imports (must be inside function)
  // ===========================================================================

  const dateTool = await client.tools.create({
    source_code: `
def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current date and time.
    
    Args:
        timezone: Timezone name (e.g., "UTC", "US/Eastern")
    
    Returns:
        Current datetime string
    """
    from datetime import datetime
    import pytz
    
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")
`,
  });

  console.log(`Created tool: ${dateTool.name} (${dateTool.id})`);

  // ===========================================================================
  // Tool with secrets (environment variables)
  // ===========================================================================

  const apiTool = await client.tools.create({
    source_code: `
def call_external_api(endpoint: str) -> str:
    """
    Call an external API using configured credentials.
    
    Args:
        endpoint: API endpoint path
    
    Returns:
        API response
    """
    import os
    import requests
    
    api_key = os.getenv("EXTERNAL_API_KEY")
    base_url = os.getenv("EXTERNAL_API_URL", "https://api.example.com")
    
    if not api_key:
        return "Error: EXTERNAL_API_KEY not configured"
    
    response = requests.get(
        f"{base_url}/{endpoint}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return response.text
`,
  });

  console.log(`Created tool: ${apiTool.name} (${apiTool.id})`);

  // ===========================================================================
  // Create agent with tools and secrets
  // ===========================================================================

  const agent = await client.agents.create({
    name: "tool-demo-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am a helpful assistant with custom tools." },
      { label: "human", value: "User information." },
    ],
    tool_ids: [greetTool.id, dateTool.id, apiTool.id],
    secrets: {
      EXTERNAL_API_KEY: "your-api-key-here",
      EXTERNAL_API_URL: "https://api.example.com",
    },
  });

  console.log(`\nCreated agent: ${agent.id}`);

  // ===========================================================================
  // Test the tools
  // ===========================================================================

  console.log("\n--- Testing Tools ---");

  const response = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "Greet me enthusiastically!" }],
  });

  for (const msg of response.messages) {
    if (msg.message_type === "tool_call_message") {
      console.log(`Tool called: ${msg.tool_call.name}`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`Agent: ${msg.content}`);
    }
  }
}

main().catch(console.error);
