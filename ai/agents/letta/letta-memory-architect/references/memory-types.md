# Memory Types in Letta

## Core Memory (In-Context)

**What it is:**
- Structured sections of agent's context window
- Always visible to agent
- Persists across all interactions

**When to use:**
- Current state and active context
- Frequently referenced information
- User preferences and agent identity
- Information that should be immediately accessible

**Structure:**
- Label: unique identifier
- Description: guides agent usage
- Value: the actual data
- Limit: character limit per block

**Access:**
- Always in context (no tool call needed)
- Agent can edit via memory_insert, memory_replace, memory_rethink

**Best for:**
- User profile information
- Agent personality and guidelines
- Current project/task context
- Active conversation metadata

## Archival Memory (Out-of-Context)

**What it is:**
- Vector database storing embedded content
- Semantic search over historical data
- Not automatically included in context

**When to use:**
- Large knowledge bases
- Historical interaction records
- Past project notes
- Reference documentation

**Access:**
- Agent must explicitly call archival_memory_search
- Results brought into context on demand
- Agent can add via archival_memory_insert

**Important notes:**
- NOT auto-populated from context overflow
- Must be explicitly added by agent
- Separate from memory blocks (not connected)

**Best for:**
- Past conversation summaries
- Historical customer interactions
- Large documentation sets
- Long-term knowledge accumulation

## Conversation History

**What it is:**
- Past messages from current conversation
- Moves out of context window as conversation grows
- Stored in database, searchable

**When to use:**
- Referencing earlier discussion
- Tracking conversation flow
- Finding specific past exchanges

**Access:**
- Agent calls conversation_search tool
- Can filter by date range, role, query

**Automatic behavior:**
- Messages automatically move to history when context full
- Agent can trigger summarization when needed

**Best for:**
- Multi-turn conversation context
- Tracking what was already discussed
- Finding specific user requests

## Memory Type Selection Guide

| Use Case | Core Memory | Archival Memory | Conversation History |
|----------|-------------|-----------------|----------------------|
| User name and preferences | ✓ | | |
| Agent personality | ✓ | | |
| Current task status | ✓ | | |
| Last 10 messages | (in context) | | |
| Messages 50+ turns ago | | | ✓ |
| Past project notes | | ✓ | |
| Large documentation | | ✓ | |
| Company policies | ✓ | | |
| Historical customer data | | ✓ | |

## Common Misconceptions

**Myth:** "Archival memory is automatically populated when context overflows"
**Reality:** Archival memory must be explicitly added via archival_memory_insert tool

**Myth:** "Memory blocks and archival memory are connected"
**Reality:** They are completely separate systems

**Myth:** "Conversation history is lost when context fills"
**Reality:** It's stored in database and accessible via conversation_search
