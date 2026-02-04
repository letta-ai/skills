/**
 * Basic client initialization for Letta.
 *
 * Run: npx ts-node 01_basic_client.ts
 */
import { Letta } from "@letta-ai/letta-client";

// =============================================================================
// Option 1: Letta Cloud
// =============================================================================

const cloudClient = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

async function cloudExample() {
  // Verify connection by creating a simple agent
  const agent = await cloudClient.agents.create({
    name: "test-connection",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [{ label: "persona", value: "Test agent" }],
  });
  console.log(`Connected to Letta Cloud. Created agent: ${agent.id}`);
  
  // Clean up
  await cloudClient.agents.delete(agent.id);
  console.log("Deleted test agent.");
}

// =============================================================================
// Option 2: Self-Hosted (Docker)
// =============================================================================

const localClient = new Letta({
  baseURL: "http://localhost:8283",
});

async function localExample() {
  try {
    // Try to connect to local server
    const agent = await localClient.agents.create({
      name: "local-test",
      model: "anthropic/claude-sonnet-4-5-20250929",
      embedding: "openai/text-embedding-3-small",
      memory_blocks: [{ label: "persona", value: "Test" }],
    });
    console.log(`Connected to local server. Created: ${agent.id}`);
    await localClient.agents.delete(agent.id);
  } catch (e: any) {
    console.log(`Local server not available: ${e.message || e}`);
  }
}

// =============================================================================
// Run examples
// =============================================================================

async function main() {
  await cloudExample();
  await localExample();
}

main().catch(console.error);
