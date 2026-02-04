/**
 * Working with conversations for parallel sessions with shared memory.
 *
 * Conversations allow:
 * - Multiple parallel sessions with the same agent
 * - Shared memory blocks across all conversations
 * - Separate context windows per conversation
 * - Thread-safe concurrent messaging
 *
 * Run: npx ts-node 07_conversations.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

// Helper to extract string content from message
function getContent(content: string | any[]): string {
  return typeof content === "string" ? content : JSON.stringify(content);
}

async function main() {
  // ==========================================================================
  // Create an agent
  // ==========================================================================

  const agent = await client.agents.create({
    name: "multi-session-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: "I am a helpful coding assistant. I remember context across sessions.",
      },
      {
        label: "human",
        value: "User working on multiple tasks.",
      },
      {
        label: "project",
        value: "Project notes shared across all conversations.",
      },
    ],
  });

  console.log(`Created agent: ${agent.id}`);

  // ==========================================================================
  // Create multiple conversations
  // ==========================================================================

  console.log("\n--- Creating Conversations ---");

  const convApi = await client.conversations.create({
    agent_id: agent.id,
  });

  const convTests = await client.conversations.create({
    agent_id: agent.id,
  });

  const convDocs = await client.conversations.create({
    agent_id: agent.id,
  });

  console.log(`Created conversation for API work: ${convApi.id}`);
  console.log(`Created conversation for tests: ${convTests.id}`);
  console.log(`Created conversation for docs: ${convDocs.id}`);

  // ==========================================================================
  // Send messages to different conversations
  // ==========================================================================

  console.log("\n--- Sending Messages to Different Conversations ---");

  // Note: conversations.messages.create returns a stream
  const stream1 = await client.conversations.messages.create(convApi.id, {
    messages: [
      {
        role: "user",
        content: "I'm working on refactoring the user API. The main file is user_api.py.",
      },
    ],
  });

  console.log("API conversation:");
  for await (const chunk of stream1) {
    if (chunk.message_type === "assistant_message") {
      console.log(`  Agent: ${getContent(chunk.content).slice(0, 100)}...`);
      break;
    }
  }

  const stream2 = await client.conversations.messages.create(convTests.id, {
    messages: [
      {
        role: "user",
        content: "I need to write tests for the authentication module.",
      },
    ],
  });

  console.log("\nTests conversation:");
  for await (const chunk of stream2) {
    if (chunk.message_type === "assistant_message") {
      console.log(`  Agent: ${getContent(chunk.content).slice(0, 100)}...`);
      break;
    }
  }

  // ==========================================================================
  // Conversations share memory - updates visible to all
  // ==========================================================================

  console.log("\n--- Memory Sharing Demo ---");

  // Update memory in API conversation
  const stream3 = await client.conversations.messages.create(convApi.id, {
    messages: [
      {
        role: "user",
        content: "Remember: the API uses REST with JSON responses. Update your project notes.",
      },
    ],
  });

  for await (const chunk of stream3) {
    if (chunk.message_type === "assistant_message") {
      console.log(`API conv learned: ${getContent(chunk.content).slice(0, 80)}...`);
      break;
    }
  }

  // Now the tests conversation can see the same memory
  const stream4 = await client.conversations.messages.create(convTests.id, {
    messages: [
      { role: "user", content: "What do you know about our API format?" },
    ],
  });

  console.log("\nTests conv can access shared knowledge:");
  for await (const chunk of stream4) {
    if (chunk.message_type === "assistant_message") {
      console.log(`  ${getContent(chunk.content).slice(0, 150)}...`);
      break;
    }
  }

  // ==========================================================================
  // Stream with token-level output
  // ==========================================================================

  console.log("\n--- Token Streaming in Conversations ---");

  const stream5 = await client.conversations.messages.create(convDocs.id, {
    messages: [
      { role: "user", content: "Write a one-sentence summary of REST APIs." },
    ],
    stream_tokens: true,
  });

  process.stdout.write("Streaming response: ");
  for await (const chunk of stream5) {
    if (chunk.message_type === "assistant_message") {
      const content = typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content);
      process.stdout.write(content);
    }
  }
  console.log();

  // ==========================================================================
  // List all conversations for an agent
  // ==========================================================================

  console.log("\n--- List Conversations ---");

  const conversations = await client.conversations.list({
    agent_id: agent.id,
  });

  for await (const conv of conversations) {
    console.log(`  - ${conv.id}`);
  }

  // ==========================================================================
  // List messages in a conversation
  // ==========================================================================

  console.log("\n--- Message History for API Conversation ---");

  const messages = await client.conversations.messages.list(convApi.id);

  for await (const msg of messages) {
    if (msg.message_type === "user_message") {
      console.log(`  User: ${getContent((msg as any).content).slice(0, 50)}...`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`  Agent: ${getContent((msg as any).content).slice(0, 50)}...`);
    }
  }

  // ==========================================================================
  // Concurrent messaging (thread-safe with conversations)
  // ==========================================================================

  console.log("\n--- Concurrent Messaging ---");

  async function sendToConv(convId: string, message: string): Promise<string> {
    const stream = await client.conversations.messages.create(convId, {
      messages: [{ role: "user", content: message }],
    });

    for await (const chunk of stream) {
      if (chunk.message_type === "assistant_message") {
        return getContent(chunk.content).slice(0, 50);
      }
    }
    return "";
  }

  // These run in parallel - each conversation has its own stream
  const results = await Promise.all([
    sendToConv(convApi.id, "Quick question about REST"),
    sendToConv(convTests.id, "Quick question about testing"),
    sendToConv(convDocs.id, "Quick question about documentation"),
  ]);

  console.log(`Got ${results.length} concurrent responses`);
  results.forEach((result, i) => {
    console.log(`  Response ${i + 1}: ${result}...`);
  });
}

main().catch(console.error);

/*
WHEN TO USE CONVERSATIONS vs SEPARATE AGENTS:

USE CONVERSATIONS when:
- Same user, multiple parallel tasks (coding + testing + docs)
- Need thread-safe concurrent messaging
- Want shared memory across sessions
- Different "threads" of the same overall project

USE SEPARATE AGENTS when:
- Different users (need full isolation)
- Completely unrelated contexts
- Different personas/capabilities needed
- Privacy/data separation required
*/
