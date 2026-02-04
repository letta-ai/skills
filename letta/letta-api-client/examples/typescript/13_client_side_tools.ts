/**
 * Client-side tool execution - run tools locally while agent runs on Letta API.
 *
 * This is how Letta Code executes Bash, Read, Write tools on your machine.
 *
 * Run: npx ts-node 13_client_side_tools.ts
 */
import { execSync } from "child_process";
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({
  apiKey: process.env.LETTA_API_KEY!,
});

async function main() {
  // ===========================================================================
  // Create a client-side tool
  // ===========================================================================

  const tool = await client.tools.upsert({
    name: "run_local_command",
    defaultRequiresApproval: true, // Key: requires approval = client-side
    jsonSchema: {
      type: "function",
      function: {
        name: "run_local_command",
        description: "Run a shell command on the local machine",
        parameters: {
          type: "object",
          properties: {
            command: {
              type: "string",
              description: "The shell command to execute",
            },
          },
          required: ["command"],
        },
      },
    },
    // Stub implementation - never executed server-side
    sourceCode: `def run_local_command(command: str) -> str:
    """
    Run a shell command on the local machine.
    
    Args:
        command: The shell command to execute
    
    Returns:
        Command output
    """
    raise Exception("This tool executes client-side only")`,
  });

  console.log(`Created client-side tool: ${tool.name}`);

  // ===========================================================================
  // Create agent with the tool
  // ===========================================================================

  const agent = await client.agents.create({
    name: "local-executor-ts",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    tools: [tool.name],
    memory_blocks: [
      {
        label: "persona",
        value: "I help users run commands on their local machine.",
      },
      { label: "human", value: "User wants to execute local commands." },
    ],
  });

  console.log(`Created agent: ${agent.id}`);

  // ===========================================================================
  // Send message - agent will request tool approval
  // ===========================================================================

  console.log("\n--- Sending message to agent ---");

  let response = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "List files in current directory" }],
  });

  // ===========================================================================
  // Handle approval request - execute tool locally
  // ===========================================================================

  for (const msg of response.messages) {
    if (msg.message_type === "reasoning_message") {
      console.log(`[Reasoning] ${msg.reasoning.slice(0, 80)}...`);
    } else if (msg.message_type === "approval_request_message") {
      const toolCall = msg.tool_call;
      console.log(`\n[Approval Request] Tool: ${toolCall.name}`);
      console.log(`  Arguments: ${toolCall.arguments}`);

      // Parse arguments
      const args = JSON.parse(toolCall.arguments);
      const command = args.command;

      console.log(`\n--- Executing locally: ${command} ---`);

      // Execute tool on local machine
      let toolReturn: string;
      let status: "success" | "error";
      let stdoutLines: string[] = [];
      let stderrLines: string[] = [];

      try {
        toolReturn = execSync(command, { encoding: "utf-8", timeout: 30000 });
        status = "success";
        stdoutLines = toolReturn.split("\n").filter((l) => l);
      } catch (error: any) {
        toolReturn = `Error: ${error.message}`;
        status = "error";
        stderrLines = [error.message];
      }

      console.log(`[Local Result] Status: ${status}`);
      console.log(`  Output: ${toolReturn.slice(0, 200)}...`);

      // ===========================================================================
      // Send result back to agent
      // ===========================================================================

      console.log("\n--- Sending result back to agent ---");

      response = await client.agents.messages.create(agent.id, {
        messages: [
          {
            type: "approval",
            approvals: [
              {
                type: "tool", // "tool" not "approval" - key difference!
                tool_call_id: toolCall.tool_call_id,
                tool_return: toolReturn,
                status: status,
                stdout: stdoutLines,
                stderr: stderrLines,
              },
            ],
          },
        ],
      });

      // Agent continues with the result
      for (const msg of response.messages) {
        if (msg.message_type === "assistant_message") {
          const content =
            typeof msg.content === "string"
              ? msg.content
              : JSON.stringify(msg.content);
          console.log(`\n[Agent Response] ${content}`);
        }
      }
    } else if (msg.message_type === "assistant_message") {
      const content =
        typeof msg.content === "string"
          ? msg.content
          : JSON.stringify(msg.content);
      console.log(`[Agent] ${content}`);
    }
  }
}

main().catch(console.error);
