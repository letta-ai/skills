# Memory Block Size Management

## Character Limits

**Typical limits per block:**
- 2000-5000 characters depending on configuration
- Total core memory should stay under 80% of context window

**Monitor size:**
- Via ADE: shows character count per block
- Via API: check block `value` length

## Growth Strategies

### 1. Split by Topic

When a block covers multiple independent topics, split into focused blocks.

**Before:**
```yaml
customer_profile:
  value: |
    Business: Tech startup, 50 employees, B2B SaaS
    Contact: Jane Doe, CTO, jane@company.com
    Preferences: Prefers technical detail, async communication
    History: Signed up 2023, upgraded to Enterprise in 2024
```

**After:**
```yaml
customer_business:
  value: |
    Industry: Tech startup, 50 employees
    Product: B2B SaaS platform
    Stage: Series A, growing rapidly

customer_contact:
  value: |
    Primary: Jane Doe, CTO
    Email: jane@company.com
    Preferences: Technical detail, async communication

customer_history:
  value: |
    Signed up: 2023
    Milestones: Upgraded to Enterprise (2024)
```

### 2. Split by Time

For temporal data, split into recent and historical.

**Before:**
```yaml
interaction_history:
  value: |
    [6 months of interaction notes...]
```

**After:**
```yaml
recent_interactions:
  value: |
    [Last 2 weeks of interactions]

# Archive older interactions to archival memory via archival_memory_insert
```

### 3. Archive to Archival Memory

Move historical or infrequently accessed data to archival memory.

**Process:**
1. Identify data that's rarely needed immediately
2. Use `archival_memory_insert` to store it
3. Remove from core memory block
4. Agent can retrieve via `archival_memory_search` when needed

**Good candidates for archival:**
- Past conversation summaries
- Historical project notes
- Completed task records
- Old customer interactions

### 4. Consolidate with memory_rethink

Summarize and rewrite block content to be more concise.

**Before:**
```yaml
project_context:
  value: |
    Project Name: Customer Portal
    Started: January 2024
    Stack: React, Node.js, PostgreSQL
    Architecture: Microservices with API gateway
    Current Phase: User authentication completed
    Next Phase: Dashboard development
    Team: 3 engineers, 1 designer
    Notes: Using JWT for auth, Redis for sessions
```

**After (condensed):**
```yaml
project_context:
  value: |
    Customer Portal (Jan 2024)
    Stack: React/Node.js/PostgreSQL microservices
    Status: Auth complete, starting dashboard
    Team: 3 eng, 1 design
```

## Proactive Strategies

### Monitor Growth Patterns

**High-growth blocks:**
- Interaction histories
- Task lists
- Conversation summaries

**Strategies:**
- Set up archival thresholds (e.g., archive when >1500 chars)
- Regular consolidation cycles
- Time-based splits (current vs. historical)

### Design for Bounded Growth

**Append-limited blocks:**
```yaml
recent_activity:
  description: "Last 10 user actions. Archive older actions when adding new ones."
```

**Rotating logs:**
```yaml
daily_summary:
  description: "Today's key events. Reset daily, archive yesterday to archival memory."
```

## Warning Signs

**Block is too large when:**
- Approaching character limit
- Agent frequently struggles to find information within it
- Contains multiple unrelated topics
- Includes rarely-referenced historical data

**Action needed:**
- Split by topic or time
- Archive historical content
- Consolidate with memory_rethink
- Redesign block structure

## Context Window Management

**Total core memory guideline:**
- Keep under 80% of context window
- Leave room for conversation, tool outputs, reasoning

**Example for 32k context:**
- ~25k tokens available
- Core memory should be <20k tokens
- ~5k tokens for conversation and tools

**When approaching limit:**
1. Identify least-used blocks
2. Archive or consolidate content
3. Consider splitting large blocks
4. Review if all blocks are still needed
