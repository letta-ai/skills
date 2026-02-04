#!/usr/bin/env npx ts-node
/**
 * Basic Model Configuration Example (TypeScript)
 *
 * Demonstrates how to create a Letta agent with custom model settings.
 *
 * Usage:
 *     export LETTA_API_KEY="your-api-key"
 *     npx ts-node basic_config.ts
 */

import Letta from "@letta-ai/letta-client";

async function main() {
  // Initialize client
  const client = new Letta({ apiKey: process.env.LETTA_API_KEY });

  // Create agent with model configuration
  const agent = await client.agents.create({
    name: "configured-agent-ts",
    // Model handle format: provider/model-name
    model: "openai/gpt-4o",
    // Model behavior settings (provider_type required!)
    model_settings: {
      provider_type: "openai", // Must match model provider
      temperature: 0.7, // 0.0-2.0, lower = more deterministic
      max_output_tokens: 4096, // Maximum response length
    },
    // Context window (set at agent level, not in model_settings)
    context_window_limit: 128000,
    // Memory blocks
    memory_blocks: [
      { label: "persona", value: "You are a helpful assistant." },
      { label: "human", value: "The user hasn't shared any information yet." },
    ],
  });

  console.log(`Created agent: ${agent.id}`);
  console.log(`Model: ${agent.model}`);

  // Send a test message
  const response = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "Hello! What model are you running on?" }],
  });

  // Print response
  for (const message of response.messages) {
    if ("content" in message && message.content) {
      console.log(`Agent: ${message.content}`);
    }
  }
}

main().catch(console.error);
