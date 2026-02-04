/**
 * Create an agent with memory blocks.
 *
 * Run: npx ts-node 02_create_agent.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

async function main() {
  // ==========================================================================
  // Create a basic agent with memory blocks
  // ==========================================================================

  const agent = await client.agents.create({
    name: "my-assistant",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: `I am a helpful assistant named Alex.
I am friendly, concise, and always try to provide accurate information.
I remember user preferences and adapt my communication style accordingly.`,
      },
      {
        label: "human",
        value: `User information will be stored here as I learn about them.
Currently unknown - will update as we interact.`,
      },
      {
        label: "notes",
        value: `Important notes and reminders:
- (empty)`,
      },
    ],
    tools: ["web_search"],
    tags: ["example", "assistant"],
  });

  console.log(`Created agent: ${agent.id}`);
  console.log(`Name: ${agent.name}`);
  console.log(`Model: ${agent.model}`);

  // ==========================================================================
  // Send a message to the agent
  // ==========================================================================

  const response = await client.agents.messages.create(agent.id, {
    messages: [
      {
        role: "user",
        content: "Hi! My name is Sarah and I prefer concise responses.",
      },
    ],
  });

  // Extract and print the assistant's response
  for (const message of response.messages) {
    if (message.message_type === "assistant_message") {
      console.log(`\nAgent: ${message.content}`);
    } else if (message.message_type === "reasoning_message") {
      console.log(`[Reasoning: ${message.reasoning.slice(0, 100)}...]`);
    }
  }

  // ==========================================================================
  // Check if the agent updated its memory
  // ==========================================================================

  const humanBlock = await client.agents.blocks.retrieve("human", {
    agent_id: agent.id,
  });

  console.log(`\n--- Human memory block ---`);
  console.log(humanBlock.value);

  // ==========================================================================
  // Clean up (optional)
  // ==========================================================================
  // await client.agents.delete(agent.id);
  // console.log(`\nDeleted agent: ${agent.id}`);
}

main().catch(console.error);
