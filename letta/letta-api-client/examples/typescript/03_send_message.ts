/**
 * Send messages to an agent and handle different response types.
 *
 * Run: npx ts-node 03_send_message.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

async function main() {
  // ==========================================================================
  // Create an agent
  // ==========================================================================

  const agent = await client.agents.create({
    name: "chat-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am a helpful assistant." },
      { label: "human", value: "User info." },
    ],
    tools: ["web_search"],
  });

  console.log(`Agent: ${agent.id}`);

  // ==========================================================================
  // Send a simple message
  // ==========================================================================

  const response = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "Hello! How are you today?" }],
  });

  console.log("\n--- Simple Message ---");
  for (const message of response.messages) {
    console.log(`[${message.message_type}]`);
    if (message.message_type === "assistant_message") {
      console.log(`  Content: ${message.content}`);
    } else if (message.message_type === "reasoning_message") {
      console.log(`  Reasoning: ${message.reasoning.slice(0, 200)}...`);
    }
  }

  // ==========================================================================
  // Send a message that triggers tool use
  // ==========================================================================

  const response2 = await client.agents.messages.create(agent.id, {
    messages: [
      {
        role: "user",
        content: "Search the web for the latest news about AI agents.",
      },
    ],
  });

  console.log("\n--- Message with Tool Use ---");
  for (const message of response2.messages) {
    switch (message.message_type) {
      case "reasoning_message":
        console.log(`[Reasoning] ${message.reasoning.slice(0, 100)}...`);
        break;
      case "tool_call_message":
        console.log(`[Tool Call] ${message.tool_call.name}`);
        console.log(`  Args: ${JSON.stringify(message.tool_call.arguments)}`);
        break;
      case "tool_return_message":
        console.log(`[Tool Return] ${message.tool_return.slice(0, 200)}...`);
        break;
      case "assistant_message":
        console.log(`[Response] ${message.content}`);
        break;
    }
  }

  // ==========================================================================
  // Helper function to extract assistant message
  // ==========================================================================

  function getAssistantResponse(response: any): string {
    for (const message of response.messages) {
      if (message.message_type === "assistant_message") {
        return message.content;
      }
    }
    return "";
  }

  const response3 = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "What's 2 + 2?" }],
  });

  console.log("\n--- Extracted Response ---");
  console.log(getAssistantResponse(response3));

  // ==========================================================================
  // List message history
  // ==========================================================================

  console.log("\n--- Message History ---");
  const messages = client.agents.messages.list(agent.id, { limit: 10 });

  for await (const msg of messages) {
    if (msg.message_type === "user_message") {
      console.log(`User: ${msg.content.slice(0, 50)}...`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`Agent: ${msg.content.slice(0, 50)}...`);
    }
  }
}

main().catch(console.error);
