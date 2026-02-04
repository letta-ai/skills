/**
 * Client injection for custom memory tools.
 *
 * On Letta Cloud, tools have access to:
 * - `client` - Pre-configured Letta client
 * - `os.getenv("LETTA_AGENT_ID")` - Current agent's ID
 *
 * This enables tools that modify the agent's own memory.
 *
 * Run: npx ts-node 11_client_injection.ts
 */
import { Letta } from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY! });

async function main() {
  // ===========================================================================
  // Custom memory tool using injected client
  // ===========================================================================

  const rememberTool = await client.tools.create({
    source_code: `
def remember_with_category(content: str, category: str) -> str:
    """
    Store information in the notes memory block with a category tag.
    
    Args:
        content: The information to remember
        category: Category for organization (e.g., "preference", "fact", "task")
    
    Returns:
        Confirmation message
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    # Get current notes block
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="notes"
    )
    
    # Append with category tag
    entry = f"[{category}] {content}"
    updated_value = f"{block.value}\\n{entry}" if block.value else entry
    
    # Update the block
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="notes",
        value=updated_value
    )
    
    return f"Remembered ({category}): {content}"
`,
  });

  // ===========================================================================
  // Tool to search and summarize notes
  // ===========================================================================

  const searchNotesTool = await client.tools.create({
    source_code: `
def search_notes(category: str = "") -> str:
    """
    Search notes, optionally filtered by category.
    
    Args:
        category: Optional category to filter by
    
    Returns:
        Matching notes
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="notes"
    )
    
    if not block.value:
        return "No notes found"
    
    lines = block.value.split("\\n")
    
    if category:
        lines = [l for l in lines if f"[{category}]" in l]
    
    if not lines:
        return f"No notes found for category: {category}"
    
    return "\\n".join(lines)
`,
  });

  // ===========================================================================
  // Tool to clear a category
  // ===========================================================================

  const clearCategoryTool = await client.tools.create({
    source_code: `
def clear_category(category: str) -> str:
    """
    Remove all notes in a specific category.
    
    Args:
        category: Category to clear
    
    Returns:
        Confirmation message
    """
    import os
    
    agent_id = os.getenv("LETTA_AGENT_ID")
    
    block = client.agents.blocks.retrieve(
        agent_id=agent_id,
        block_label="notes"
    )
    
    if not block.value:
        return "No notes to clear"
    
    lines = block.value.split("\\n")
    remaining = [l for l in lines if f"[{category}]" not in l]
    
    client.agents.blocks.update(
        agent_id=agent_id,
        block_label="notes",
        value="\\n".join(remaining)
    )
    
    removed_count = len(lines) - len(remaining)
    return f"Cleared {removed_count} notes from category: {category}"
`,
  });

  console.log("Created custom memory tools");

  // ===========================================================================
  // Create agent with custom memory tools
  // ===========================================================================

  const agent = await client.agents.create({
    name: "self-modifying-agent",
    model: "anthropic/claude-sonnet-4-5-20250929",
    embedding: "openai/text-embedding-3-small",
    memory_blocks: [
      {
        label: "persona",
        value: "I manage my own memory using custom tools.",
      },
      { label: "human", value: "User information." },
      { label: "notes", value: "Categorized notes:" },
    ],
    tool_ids: [rememberTool.id, searchNotesTool.id, clearCategoryTool.id],
  });

  console.log(`Created agent: ${agent.id}`);

  // ===========================================================================
  // Test the custom memory tools
  // ===========================================================================

  console.log("\n--- Testing Custom Memory Tools ---");

  // Store some categorized information
  const response1 = await client.agents.messages.create(agent.id, {
    messages: [
      {
        role: "user",
        content:
          "Remember these things: I like dark mode (preference), my meeting is at 3pm (task), and the API uses REST (fact).",
      },
    ],
  });

  for (const msg of response1.messages) {
    if (msg.message_type === "tool_call_message") {
      console.log(`Called: ${msg.tool_call.name}`);
    } else if (msg.message_type === "assistant_message") {
      console.log(`Agent: ${msg.content}`);
    }
  }

  // Check the notes block
  const notesBlock = await client.agents.blocks.retrieve("notes", {
    agent_id: agent.id,
  });
  console.log(`\nNotes block:\n${notesBlock.value}`);

  // Search by category
  console.log("\n--- Searching by Category ---");

  const response2 = await client.agents.messages.create(agent.id, {
    messages: [{ role: "user", content: "What tasks do I have?" }],
  });

  for (const msg of response2.messages) {
    if (msg.message_type === "assistant_message") {
      console.log(`Agent: ${msg.content}`);
    }
  }
}

main().catch(console.error);
