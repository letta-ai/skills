/**
 * Shared memory blocks between agents.
 *
 * Multiple agents can share the same memory block.
 * When one agent updates it, others see the change.
 *
 * Run: npx ts-node 10_shared_blocks.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY! });

async function main() {
  // ===========================================================================
  // Create a shared memory block
  // ===========================================================================

  console.log("--- Creating Shared Block ---");

  const sharedBlock = await client.blocks.create({
    label: "team_knowledge",
    value: "Team shared knowledge base:\n- Project started: January 2026",
  });

  console.log(`Created shared block: ${sharedBlock.id}`);

  // ===========================================================================
  // Create two agents that share the block
  // ===========================================================================

  console.log("\n--- Creating Agents ---");

  const agent1 = await client.agents.create({
    name: "researcher",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am a researcher. I discover and record findings." },
      { label: "human", value: "Team member." },
    ],
  });

  const agent2 = await client.agents.create({
    name: "analyst",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am an analyst. I analyze shared knowledge." },
      { label: "human", value: "Team member." },
    ],
  });

  console.log(`Created researcher: ${agent1.id}`);
  console.log(`Created analyst: ${agent2.id}`);

  // ===========================================================================
  // Attach shared block to both agents
  // ===========================================================================

  console.log("\n--- Attaching Shared Block ---");

  await client.agents.blocks.attach(sharedBlock.id, { agent_id: agent1.id });
  await client.agents.blocks.attach(sharedBlock.id, { agent_id: agent2.id });

  console.log("Attached team_knowledge block to both agents");

  // ===========================================================================
  // Agent 1 updates the shared block
  // ===========================================================================

  console.log("\n--- Researcher Updates Shared Knowledge ---");

  const response1 = await client.agents.messages.create(agent1.id, {
    messages: [
      {
        role: "user",
        content:
          "Add to the team knowledge: We discovered that the API supports batch processing.",
      },
    ],
  });

  for (const msg of response1.messages) {
    if (msg.message_type === "assistant_message") {
      console.log(`Researcher: ${msg.content}`);
    }
  }

  // Check the block was updated
  const updatedBlock = await client.agents.blocks.retrieve("team_knowledge", {
    agent_id: agent1.id,
  });
  console.log(`\nShared block now contains:\n${updatedBlock.value}`);

  // ===========================================================================
  // Agent 2 sees the update
  // ===========================================================================

  console.log("\n--- Analyst Reads Shared Knowledge ---");

  const response2 = await client.agents.messages.create(agent2.id, {
    messages: [{ role: "user", content: "What do we know about the API?" }],
  });

  for (const msg of response2.messages) {
    if (msg.message_type === "assistant_message") {
      console.log(`Analyst: ${msg.content}`);
    }
  }

  // ===========================================================================
  // Direct block updates (outside of agent)
  // ===========================================================================

  console.log("\n--- Direct Block Update ---");

  await client.blocks.update(sharedBlock.id, {
    value: `${updatedBlock.value}\n- Performance benchmarks completed: 500ms p99`,
  });

  console.log("Updated shared block directly via API");

  // Both agents now see the new content
  const block1 = await client.agents.blocks.retrieve("team_knowledge", {
    agent_id: agent1.id,
  });
  console.log(`\nBlock visible to researcher:\n${block1.value}`);
}

main().catch(console.error);
