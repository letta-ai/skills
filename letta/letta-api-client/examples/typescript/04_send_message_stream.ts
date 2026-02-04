/**
 * Stream agent responses in real-time.
 *
 * Run: npx ts-node 04_send_message_stream.ts
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
    name: "streaming-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am a storytelling assistant." },
      { label: "human", value: "User preferences." },
    ],
  });

  console.log(`Agent: ${agent.id}\n`);

  // ==========================================================================
  // Basic streaming
  // ==========================================================================

  console.log("--- Basic Streaming ---");
  const stream = await client.agents.messages.stream(agent.id, {
    messages: [
      { role: "user", content: "Tell me a very short story about a robot." },
    ],
  });

  for await (const chunk of stream) {
    if (chunk.message_type === "reasoning_message") {
      console.log("\n[Thinking...]\n");
    } else if (chunk.message_type === "assistant_message") {
      const content = typeof chunk.content === "string" 
        ? chunk.content 
        : JSON.stringify(chunk.content);
      process.stdout.write(content);
    }
  }

  console.log("\n");

  // ==========================================================================
  // Streaming with include_pings (for long operations)
  // ==========================================================================

  console.log("--- Streaming with Pings ---");
  const stream2 = await client.agents.messages.stream(agent.id, {
    messages: [
      { role: "user", content: "Write a haiku about programming." },
    ],
    include_pings: true,
  });

  for await (const chunk of stream2) {
    if (chunk.message_type === "ping") {
      process.stdout.write("[ping] ");
      continue;
    }

    if (chunk.message_type === "assistant_message") {
      const content = typeof chunk.content === "string" 
        ? chunk.content 
        : JSON.stringify(chunk.content);
      process.stdout.write(content);
    }
  }

  console.log("\n");

  // ==========================================================================
  // Handle all message types while streaming
  // ==========================================================================

  console.log("--- Full Message Type Handling ---");
  const stream3 = await client.agents.messages.stream(agent.id, {
    messages: [
      { role: "user", content: "What do you remember about me?" },
    ],
  });

  for await (const chunk of stream3) {
    switch (chunk.message_type) {
      case "reasoning_message":
        console.log(`🧠 Thinking: ${chunk.reasoning.slice(0, 80)}...`);
        break;
      case "tool_call_message":
        console.log(
          `🔧 Tool: ${chunk.tool_call.name}(${JSON.stringify(chunk.tool_call.arguments)})`
        );
        break;
      case "tool_return_message":
        console.log(`📤 Result: ${chunk.tool_return.slice(0, 100)}...`);
        break;
      case "assistant_message":
        const content = typeof chunk.content === "string" 
          ? chunk.content 
          : JSON.stringify(chunk.content);
        console.log(`💬 ${content}`);
        break;
      case "ping":
        // Ignore pings
        break;
    }
  }

  // ==========================================================================
  // Background execution with resumable streams
  // ==========================================================================

  // Note: Background execution creates a run that continues server-side.
  // This is useful for long operations where you don't want to hold a connection.
  console.log("\n--- Non-Streaming Example ---");
  const response = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "Count to 5." }],
  });

  for (const msg of response.messages) {
    if (msg.message_type === "assistant_message") {
      const content = typeof msg.content === "string" 
        ? msg.content 
        : JSON.stringify(msg.content);
      console.log(`Content: ${content}`);
    }
  }

  console.log(`\nDone!`);
}

main().catch(console.error);
