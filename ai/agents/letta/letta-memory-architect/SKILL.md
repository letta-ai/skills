---
name: letta-memory-architect
description: Guide for designing effective memory architectures in Letta agents. Use when users need help structuring memory blocks, choosing between memory types, or optimizing memory management patterns.
license: MIT
---

# Letta Memory Architect

This skill guides the design of effective memory architectures for Letta agents, including memory block structure, memory type selection, and concurrency patterns.

## When to Use This Skill

Use this skill when users are:
- Designing memory block structure for a new agent
- Choosing between core memory, archival memory, and conversation history
- Optimizing memory block organization for performance
- Implementing shared memory between agents
- Debugging memory-related issues (size limits, concurrency)

## Memory Architecture Process

### 1. Memory Type Selection

Consult `references/memory-types.md` for detailed comparison. Quick guidance:

**Core Memory (in-context):**
- Always accessible in agent's context window
- Use for: current state, active context, frequently referenced information
- Limit: Keep total core memory under 80% of context window

**Archival Memory (out-of-context):**
- Semantic search over vector database
- Use for: historical records, large knowledge bases, past interactions
- Access: Agent must explicitly call archival_memory_search
- Note: NOT automatically populated from context overflow

**Conversation History:**
- Past messages from current conversation
- Retrieved via conversation_search tool
- Use for: referencing earlier discussion, tracking conversation flow

### 2. Memory Block Design

**Core principle:** One block per distinct functional unit.

**Essential blocks:**
- `persona`: Agent identity, behavioral guidelines, capabilities
- `human`: User information, preferences, context

**Add domain-specific blocks based on use case:**

For customer support:
```yaml
company_policies:
  description: "Company policies and procedures. Reference when handling customer requests."
  read_only: true

product_knowledge:
  description: "Product features and common issues. Update when learning new solutions."
  read_only: false

customer:
  description: "Current customer's context and history. Update as you learn more about them."
  read_only: false
```

For coding assistants:
```yaml
project_context:
  description: "Current project architecture and active tasks. Update as project evolves."
  
coding_standards:
  description: "Team's coding standards and review checklist. Reference before code suggestions."
  read_only: true

current_task:
  description: "Active task and implementation progress. Update as work progresses."
```

See `references/memory-patterns.md` for more domain examples.

### 3. Label and Description Best Practices

**Labels:**
- Use underscores, not spaces: `brand_guidelines` not `brand guidelines`
- Keep short and descriptive: `customer_profile`, `project_context`
- Think like variable names

**Descriptions:**
Use instructional style for blocks the agent actively manages:

**Good:**
```
"Brand tone and style guidelines. Reference this when generating content to ensure consistency with brand identity."
```

**Poor:**
```
"Contains brand information"
```

**Template for active blocks:**
```
[What this block contains]. [When to reference it]. [When/how to update it].
```

Consult `references/description-patterns.md` for examples.

### 4. Size Management

**Character limits per block:**
- Typical limit: 2000-5000 characters
- Monitor via block size in ADE or API

**When approaching limits:**
1. **Split by topic:** `customer_profile` → `customer_business`, `customer_preferences`
2. **Split by time:** `interaction_history` → `recent_interactions`, archive older to archival memory
3. **Archive historical data:** Move old information to archival memory
4. **Consolidate with memory_rethink:** Summarize and rewrite block

See `references/size-management.md` for strategies.

### 5. Concurrency Patterns

When multiple agents share memory blocks or agent processes concurrent requests:

**Safest operations:**
- `memory_insert`: Append-only, minimal race conditions
- Database uses PostgreSQL row-level locking

**Risk of race conditions:**
- `memory_replace`: Target string may change before write
- `memory_rethink`: Last-writer-wins, no merge

**Best practices:**
- Design for append operations when possible
- Use memory_insert for concurrent writes
- Reserve memory_rethink for single-agent exclusive access

Consult `references/concurrency.md` for patterns.

## Validation Questions

Before finalizing memory architecture:

1. Is core memory total under 80% of context window?
2. Is each block focused on one functional area?
3. Are descriptions clear about when to read/write?
4. Have you planned for size growth and overflow?
5. If multi-agent, are concurrency patterns considered?

## Common Antipatterns to Avoid

**Too few blocks:**
```yaml
# Bad: Everything in one block
agent_memory: "Agent is helpful. User is John..."
```
Split into focused blocks instead.

**Too many blocks:**
Creating 10+ blocks when 3-4 would suffice. Start minimal, expand as needed.

**Poor descriptions:**
```yaml
# Bad
data: "Contains data"
```
Provide actionable guidance instead.

**Ignoring size limits:**
Letting blocks grow indefinitely until they hit limits. Monitor and manage proactively.

## Next Steps

After architecture design:
1. Create memory blocks via ADE or API
2. Test agent behavior with representative queries
3. Monitor memory tool usage patterns
4. Iterate on structure based on actual usage
