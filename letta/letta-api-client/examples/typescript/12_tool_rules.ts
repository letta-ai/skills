/**
 * Tool rules for constraining tool execution order.
 *
 * Tool rules let you:
 * - Force tools to run in a specific order
 * - Create approval workflows
 * - Build sequential pipelines
 *
 * Run: npx ts-node 12_tool_rules.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY! });

async function main() {
  // ===========================================================================
  // Create tools for a data processing pipeline
  // ===========================================================================

  const fetchTool = await client.tools.create({
    source_code: `
def fetch_data(query: str) -> str:
    """
    Fetch data based on a query. Must be called first.
    
    Args:
        query: The search query
    
    Returns:
        Fetched data string
    """
    return f"Fetched data for: {query}"
`,
  });

  const processTool = await client.tools.create({
    source_code: `
def process_data(data: str) -> str:
    """
    Process the fetched data. Can only be called after fetch_data.
    
    Args:
        data: The data to process
    
    Returns:
        Processed data string
    """
    return f"Processed: {data}"
`,
  });

  const formatTool = await client.tools.create({
    source_code: `
def format_output(processed: str) -> str:
    """
    Format the final output. Ends the agent's turn.
    
    Args:
        processed: The processed data to format
    
    Returns:
        Formatted output string
    """
    return f"Final output: {processed}"
`,
  });

  console.log("Created pipeline tools");

  // ===========================================================================
  // Create agent with sequential pipeline rules
  // ===========================================================================

  console.log("\n--- Creating Agent with Tool Rules ---");

  const agent = await client.agents.create({
    name: "pipeline-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: "I process data in a strict pipeline: fetch -> process -> format.",
      },
      { label: "human", value: "User requesting data processing." },
    ],
    tool_ids: [fetchTool.id, processTool.id, formatTool.id],
    tool_rules: [
      // fetch_data must be called first
      { type: "run_first", tool_name: "fetch_data" },

      // After fetch_data, only process_data can be called
      { type: "constrain_child_tools", tool_name: "fetch_data", children: ["process_data"] },

      // After process_data, only format_output can be called
      { type: "constrain_child_tools", tool_name: "process_data", children: ["format_output"] },

      // format_output ends the turn
      { type: "exit_loop", tool_name: "format_output" },
    ],
  });

  console.log(`Created agent: ${agent.id}`);

  // ===========================================================================
  // Test the pipeline
  // ===========================================================================

  console.log("\n--- Testing Pipeline ---");

  const response = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "Process data about 'AI agents'" }],
  });

  console.log("Tool execution order:");
  for (const msg of response.messages) {
    if (msg.message_type === "tool_call_message") {
      console.log(`  → ${msg.tool_call.name}`);
    } else if (msg.message_type === "tool_return_message") {
      console.log(`    Result: ${msg.tool_return.slice(0, 50)}...`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`\nFinal response: ${msg.content}`);
    }
  }

  // ===========================================================================
  // Example 2: Approval workflow
  // ===========================================================================

  console.log("\n\n--- Creating Approval Workflow Agent ---");

  const proposeTool = await client.tools.create({
    source_code: `
def propose_action(action: str) -> str:
    """
    Propose an action that needs approval.
    
    Args:
        action: The action to propose
    
    Returns:
        Proposal message
    """
    return f"Proposed action: {action}. Awaiting confirmation."
`,
  });

  const confirmTool = await client.tools.create({
    source_code: `
def confirm_action(approved: bool, reason: str = "") -> str:
    """
    Confirm or reject the proposed action.
    
    Args:
        approved: Whether to approve the action
        reason: Optional reason for the decision
    
    Returns:
        Confirmation message
    """
    if approved:
        return f"Action approved. {reason}"
    return f"Action rejected. {reason}"
`,
  });

  const executeTool = await client.tools.create({
    source_code: `
def execute_action() -> str:
    """
    Execute the approved action. Only callable after confirmation.
    
    Returns:
        Execution result message
    """
    return "Action executed successfully!"
`,
  });

  const approvalAgent = await client.agents.create({
    name: "approval-workflow-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: "I follow a strict approval workflow: propose -> confirm -> execute.",
      },
      { label: "human", value: "User." },
    ],
    tool_ids: [proposeTool.id, confirmTool.id, executeTool.id],
    tool_rules: [
      // Must propose first
      { type: "run_first", tool_name: "propose_action" },

      // After proposing, must confirm
      { type: "constrain_child_tools", tool_name: "propose_action", children: ["confirm_action"] },

      // After confirming, can execute
      { type: "constrain_child_tools", tool_name: "confirm_action", children: ["execute_action"] },

      // Execute ends the turn
      { type: "exit_loop", tool_name: "execute_action" },
    ],
  });

  console.log(`Created approval agent: ${approvalAgent.id}`);

  // Test approval workflow
  const approvalResponse = await client.agents.messages.create(approvalAgent.id, {
    messages: [
      { role: "user", content: "Send an email to the team about the project update" },
    ],
  });

  console.log("\nApproval workflow execution:");
  for (const msg of approvalResponse.messages) {
    if (msg.message_type === "tool_call_message") {
      console.log(`  → ${msg.tool_call.name}(${JSON.stringify(msg.tool_call.arguments)})`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`\nAgent: ${msg.content}`);
    }
  }
}

main().catch(console.error);
