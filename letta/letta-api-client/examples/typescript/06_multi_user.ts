/**
 * Multi-user patterns in TypeScript.
 *
 * Run: npx ts-node 06_multi_user.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

// =============================================================================
// Pattern 1: One Agent Per User
// =============================================================================

async function oneAgentPerUser() {
  console.log("--- Pattern 1: One Agent Per User ---");

  // Create agent for a user
  async function createUserAgent(userId: string, userName: string) {
    const agent = await client.agents.create({
      name: `assistant-${userId}`,
      model: "anthropic/claude-sonnet-4-5-20250929",
      embedding: "openai/text-embedding-3-small",
      memory_blocks: [
        {
          label: "persona",
          value: "I am a personal assistant. I remember your preferences.",
        },
        {
          label: "human",
          value: `Name: ${userName}\nUser ID: ${userId}\nPreferences: (learning...)`,
        },
      ],
      tags: [`user:${userId}`],
    });
    return agent;
  }

  // Find existing agent for user
  async function findUserAgent(userId: string) {
    const agents = client.agents.list({ tags: [`user:${userId}`], limit: 1 });
    for await (const agent of agents) {
      return agent;
    }
    return null;
  }

  // Create agents for two users
  const aliceAgent = await createUserAgent("user-001", "Alice");
  const bobAgent = await createUserAgent("user-002", "Bob");

  console.log(`Created agent for Alice: ${aliceAgent.id}`);
  console.log(`Created agent for Bob: ${bobAgent.id}`);

  // Each user has isolated conversations
  await client.agents.messages.create(aliceAgent.id, {
    messages: [
      { role: "user", content: "I prefer short answers. Remember that." },
    ],
  });

  await client.agents.messages.create(bobAgent.id, {
    messages: [
      { role: "user", content: "I like detailed explanations. Remember that." },
    ],
  });

  console.log("\nAlice's agent learned her preference.");
  console.log("Bob's agent learned his preference (independently).");

  return { aliceAgent, bobAgent };
}

// =============================================================================
// Pattern 2: Shared Agent with Conversations
// =============================================================================

async function sharedAgentWithConversations() {
  console.log("\n--- Pattern 2: Shared Agent with Conversations ---");

  // Create ONE shared support agent
  const supportAgent = await client.agents.create({
    name: "support-bot",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: "I am a customer support agent for TechCorp.",
      },
      {
        label: "knowledge",
        value: "Product info: TechWidget costs $99. Returns within 30 days.",
      },
    ],
  });

  console.log(`Created shared support agent: ${supportAgent.id}`);

  // Create separate conversations for different users
  const convAlice = await client.conversations.create({
    agent_id: supportAgent.id,
  });

  const convBob = await client.conversations.create({
    agent_id: supportAgent.id,
  });

  console.log(`Created conversation for Alice: ${convAlice.id}`);
  console.log(`Created conversation for Bob: ${convBob.id}`);

  // Users chat in isolated conversations
  // conversations.messages.create returns a stream by default
  const streamAlice = await client.conversations.messages.create(convAlice.id, {
    messages: [{ role: "user", content: "What's your return policy?" }],
  });

  const streamBob = await client.conversations.messages.create(convBob.id, {
    messages: [{ role: "user", content: "How much does TechWidget cost?" }],
  });

  // Extract responses from streams
  let aliceResponse = "";
  for await (const chunk of streamAlice as any) {
    if (chunk.message_type === "assistant_message") {
      const content = typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content);
      aliceResponse = content;
    }
  }
  console.log(`\nAlice's response: ${aliceResponse.slice(0, 100)}...`);

  let bobResponse = "";
  for await (const chunk of streamBob as any) {
    if (chunk.message_type === "assistant_message") {
      const content = typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content);
      bobResponse = content;
    }
  }
  console.log(`Bob's response: ${bobResponse.slice(0, 100)}...`);

  return { supportAgent, convAlice, convBob };
}

// =============================================================================
// Concurrent requests (fully parallel)
// =============================================================================

async function concurrentRequests(convIds: string[]) {
  console.log("\n--- Concurrent Requests ---");

  // These run fully parallel - no blocking between conversations
  const streams = await Promise.all([
    client.conversations.messages.create(convIds[0], {
      messages: [{ role: "user", content: "Question from user 1" }],
    }),
    client.conversations.messages.create(convIds[1], {
      messages: [{ role: "user", content: "Question from user 2" }],
    }),
  ]);

  // Consume both streams
  for (const stream of streams) {
    for await (const chunk of stream as any) {
      if (chunk.message_type === "assistant_message") {
        const content = typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content);
        console.log(`Response: ${content.slice(0, 50)}...`);
        break;
      }
    }
  }

  console.log(`Processed ${streams.length} concurrent requests`);
}

// =============================================================================
// User service class example
// =============================================================================

class UserAgentService {
  private client: Letta;
  private agentCache: Map<string, string> = new Map();

  constructor(apiKey: string) {
    this.client = new Letta({ apiKey });
  }

  async getOrCreateAgent(userId: string, userName: string): Promise<string> {
    // Check cache first
    if (this.agentCache.has(userId)) {
      return this.agentCache.get(userId)!;
    }

    // Look for existing agent
    const agents = this.client.agents.list({
      tags: [`user:${userId}`],
      limit: 1,
    });

    for await (const agent of agents) {
      this.agentCache.set(userId, agent.id);
      return agent.id;
    }

    // Create new agent
    const agent = await this.client.agents.create({
      name: `assistant-${userId}`,
      model: "anthropic/claude-sonnet-4-5-20250929",
      embedding: "openai/text-embedding-3-small",
      memory_blocks: [
        { label: "persona", value: "I am a personal assistant." },
        { label: "human", value: `Name: ${userName}` },
      ],
      tags: [`user:${userId}`],
    });

    this.agentCache.set(userId, agent.id);
    return agent.id;
  }

  async chat(userId: string, message: string): Promise<string> {
    const agentId = this.agentCache.get(userId);
    if (!agentId) {
      throw new Error(`No agent found for user ${userId}`);
    }

    const response = await this.client.agents.messages.create(agentId, {
      messages: [{ role: "user", content: message }],
    });

    for (const msg of response.messages) {
      if (msg.message_type === "assistant_message") {
        return typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content);
      }
    }

    return "";
  }
}

// =============================================================================
// Main
// =============================================================================

async function main() {
  await oneAgentPerUser();
  const { convAlice, convBob } =
    await sharedAgentWithConversations();
  await concurrentRequests([convAlice.id, convBob.id]);

  console.log("\n--- User Service Example ---");
  const service = new UserAgentService(process.env.LETTA_API_KEY!);
  const agentId = await service.getOrCreateAgent("user-003", "Charlie");
  console.log(`Got/created agent for Charlie: ${agentId}`);
}

main().catch(console.error);
