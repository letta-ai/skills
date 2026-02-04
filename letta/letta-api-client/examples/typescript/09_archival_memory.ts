/**
 * Archival memory for long-term storage.
 *
 * Archival memory stores information outside the context window,
 * retrievable via semantic search.
 *
 * Run: npx ts-node 09_archival_memory.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY! });

async function main() {
  // ===========================================================================
  // Create agent with archival memory tools
  // ===========================================================================

  const agent = await client.agents.create({
    name: "archival-memory-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: "I store and retrieve information from my long-term memory.",
      },
      { label: "human", value: "User information." },
    ],
    include_base_tools: true, // Adds archival_memory_insert and archival_memory_search
  });

  console.log(`Created agent: ${agent.id}`);

  // ===========================================================================
  // Store information via agent
  // ===========================================================================

  console.log("\n--- Storing Information ---");

  const storeResponse = await client.agents.messages.create(agent.id, {
    messages: [
      {
        role: "user",
        content:
          "Remember these facts: 1) My favorite color is blue. 2) I work as a software engineer. 3) I prefer morning meetings.",
      },
    ],
  });

  for (const msg of storeResponse.messages) {
    if (msg.message_type === "tool_call_message") {
      console.log(`Stored via: ${msg.tool_call.name}`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`Agent: ${msg.content}`);
    }
  }

  // ===========================================================================
  // Retrieve information via agent
  // ===========================================================================

  console.log("\n--- Retrieving Information ---");

  const searchResponse = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "What's my favorite color?" }],
  });

  for (const msg of searchResponse.messages) {
    if (msg.message_type === "tool_call_message") {
      console.log(`Searched via: ${msg.tool_call.name}`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`Agent: ${msg.content}`);
    }
  }

  // ===========================================================================
  // Direct API access to passages
  // ===========================================================================

  console.log("\n--- Direct Passage Access ---");

  // Insert a passage directly
  const passages = await client.agents.passages.create(agent.id, {
    text: "The user mentioned they enjoy hiking on weekends.",
  });

  // Note: create returns an array of passages
  const passage = passages[0];
  console.log(`Created passage: ${passage?.id || "unknown"}`);

  // List all passages
  const allPassages = await client.agents.passages.list(agent.id);

  console.log(`\nListing passages:`);
  for await (const p of allPassages) {
    console.log(`  - ${p.text.slice(0, 50)}...`);
  }

  // Search passages
  const searchResults = await client.agents.passages.list(agent.id, {
    search: "work job career",
    limit: 3,
  });

  console.log("\nSearch results for 'work job career':");
  for await (const result of searchResults) {
    console.log(`  - ${result.text}`);
  }
}

main().catch(console.error);
