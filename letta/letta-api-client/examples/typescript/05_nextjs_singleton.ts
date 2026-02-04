/**
 * Next.js singleton pattern for Letta client.
 *
 * This pattern ensures a single client instance is reused across all API routes.
 */

// =============================================================================
// lib/letta.ts - Singleton client module
// =============================================================================

import { Letta } from "@letta-ai/letta-client";

// Singleton pattern - reuse client across requests
let lettaClient: Letta | null = null;

export function getLettaClient(): Letta {
  if (!lettaClient) {
    lettaClient = new Letta({
      apiKey: process.env.LETTA_API_KEY!,
    });
  }
  return lettaClient;
}

// Direct export for simple imports
export const letta = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

// =============================================================================
// app/api/chat/route.ts - API route example
// =============================================================================

/*
import { letta } from "@/lib/letta";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const { agentId, message } = await req.json();

    // Validate input
    if (!agentId || !message) {
      return NextResponse.json(
        { error: "agentId and message are required" },
        { status: 400 }
      );
    }

    // Send message to agent
    const response = await letta.agents.messages.create(agentId, {
      messages: [{ role: "user", content: message }],
    });

    // Extract assistant response
    const assistantMessage = response.messages.find(
      (m) => m.message_type === "assistant_message"
    );

    return NextResponse.json({
      response: assistantMessage?.content || "",
      messages: response.messages,
    });
  } catch (error) {
    console.error("Letta API error:", error);
    return NextResponse.json(
      { error: "Failed to process message" },
      { status: 500 }
    );
  }
}
*/

// =============================================================================
// app/api/chat/stream/route.ts - Streaming API route
// =============================================================================

/*
import { letta } from "@/lib/letta";
import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  const { agentId, message } = await req.json();

  const stream = await letta.agents.messages.stream(agentId, {
    messages: [{ role: "user", content: message }],
    include_pings: true, // Prevent timeout on long operations
  });

  // Create a readable stream for the response
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          if (chunk.message_type === "ping") {
            continue; // Skip keepalive pings
          }

          if (chunk.message_type === "assistant_message") {
            controller.enqueue(encoder.encode(chunk.content));
          }
        }
      } catch (error) {
        console.error("Stream error:", error);
      } finally {
        controller.close();
      }
    },
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
    },
  });
}
*/

// =============================================================================
// app/api/agents/route.ts - Agent management
// =============================================================================

/*
import { letta } from "@/lib/letta";
import { NextRequest, NextResponse } from "next/server";

// GET /api/agents - List agents
export async function GET(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const tag = searchParams.get("tag");

  const agents = letta.agents.list({
    tags: tag ? [tag] : undefined,
    limit: 20,
  });

  const agentList = [];
  for await (const agent of agents) {
    agentList.push({
      id: agent.id,
      name: agent.name,
      model: agent.model,
      tags: agent.tags,
    });
  }

  return NextResponse.json({ agents: agentList });
}

// POST /api/agents - Create agent
export async function POST(req: NextRequest) {
  const { name, userId } = await req.json();

  const agent = await letta.agents.create({
    name: name || `agent-${Date.now()}`,
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      { label: "persona", value: "I am a helpful assistant." },
      { label: "human", value: "User info." },
    ],
    tags: userId ? [`user:${userId}`] : [],
  });

  return NextResponse.json({ agent: { id: agent.id, name: agent.name } });
}
*/

// =============================================================================
// components/Chat.tsx - React component example
// =============================================================================

/*
"use client";

import { useState } from "react";

export function Chat({ agentId }: { agentId: string }) {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  // Non-streaming request
  async function sendMessage() {
    setLoading(true);
    setResponse("");

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agentId, message }),
    });

    const data = await res.json();
    setResponse(data.response);
    setMessage("");
    setLoading(false);
  }

  // Streaming request
  async function sendMessageStream() {
    setLoading(true);
    setResponse("");

    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agentId, message }),
    });

    const reader = res.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      setResponse((prev) => prev + text);
    }

    setMessage("");
    setLoading(false);
  }

  return (
    <div>
      <div>{response}</div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
      />
      <button onClick={sendMessageStream} disabled={loading}>
        {loading ? "Sending..." : "Send"}
      </button>
    </div>
  );
}
*/

console.log("See comments in this file for Next.js integration patterns.");
