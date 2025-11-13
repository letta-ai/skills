# Memory Concurrency Patterns

## Concurrency Scenarios

### 1. Multiple Agents Sharing Memory Blocks
Multiple agents with access to the same memory blocks (e.g., team of agents collaborating)

### 2. Single Agent, Concurrent Requests
One agent processing multiple user requests simultaneously

### 3. Agent + External Updates
Agent and external system (via API) updating same blocks

## Memory Tool Safety

### memory_insert (Safest)

**How it works:**
- Appends content to end of block
- Minimal race condition risk
- PostgreSQL row-level locking prevents conflicts

**Best for:**
- Concurrent writes
- Log-style data
- Accumulating information

**Example:**
```python
# Multiple agents can safely append
memory_insert("interaction_history", "User reported issue X")
```

**Potential issue:**
- Block can grow large if many agents append simultaneously
- Monitor size and archive periodically

### memory_replace (Moderate Risk)

**How it works:**
- Finds exact string match
- Replaces with new content
- Race condition if target string changes between read and write

**Risk scenario:**
```
Agent A reads: "Status: pending"
Agent B reads: "Status: pending"
Agent A writes: "Status: pending" → "Status: in-progress"
Agent B writes: "Status: pending" → "Status: completed"
# Agent B's write fails - string no longer matches
```

**Best for:**
- Single-agent scenarios
- Precise edits when you control timing
- Updating specific facts

**Mitigation:**
- Use for infrequently updated blocks
- Implement retry logic
- Consider memory_insert for concurrent scenarios

### memory_rethink (Highest Risk)

**How it works:**
- Completely rewrites block content
- Last-writer-wins, no merge logic
- Highest risk of data loss in concurrent scenarios

**Risk scenario:**
```
Agent A reads block (version 1)
Agent B reads block (version 1)
Agent A rewrites → block is now version 2
Agent B rewrites → block is now version 3 (overwrites A's changes)
# Agent A's changes are lost
```

**Best for:**
- Single-agent exclusive access
- Consolidation operations
- Intentional full rewrites

**Avoid when:**
- Multiple agents share the block
- Concurrent requests possible
- Changes need to be preserved

## Database-Level Protection

**PostgreSQL row-level locking:**
- Prevents simultaneous writes to same block
- Ensures write consistency
- Does NOT merge changes - last write wins

**What this means:**
- Writes won't corrupt data
- But later write can overwrite earlier write
- Design patterns to minimize conflicts

## Concurrency Patterns

### Pattern 1: Append-Only Blocks

Design blocks for append-only updates using memory_insert.

**Example - Agent Activity Log:**
```yaml
agent_activity:
  description: "Log of agent actions. Append new actions using memory_insert only."
  value: |
    [timestamp] Agent A: Processed request
    [timestamp] Agent B: Updated customer record
```

**Benefits:**
- Safe for concurrent writes
- No data loss
- Clear audit trail

**Manage growth:**
- Archive old entries periodically
- Rotate logs (daily/weekly)

### Pattern 2: Agent-Owned Blocks

Give each agent its own memory blocks.

**Example - Multi-Agent Team:**
```yaml
# Agent A's blocks
agent_a_tasks:
  description: "Tasks owned by Agent A"

agent_a_notes:
  description: "Agent A's working notes"

# Agent B's blocks
agent_b_tasks:
  description: "Tasks owned by Agent B"

agent_b_notes:
  description: "Agent B's working notes"

# Shared read-only
team_guidelines:
  description: "Shared team guidelines (read-only)"
  read_only: true
```

**Benefits:**
- No concurrent writes to same block
- Clear ownership
- Easy to track responsibility

### Pattern 3: Coordinator Pattern

One "coordinator" agent manages shared state, workers report via append-only logs.

**Architecture:**
```yaml
# Coordinator writes
team_state:
  description: "Current team state (coordinator-owned)"

# Workers append
worker_reports:
  description: "Worker status reports (append-only)"
  value: |
    [timestamp] Worker 1: Completed task X
    [timestamp] Worker 2: Started task Y
```

**Workflow:**
1. Workers append reports using memory_insert
2. Coordinator reads reports
3. Coordinator updates team_state using memory_rethink
4. Workers read team_state for coordination

### Pattern 4: Timestamp-Based Merging

Include timestamps to track and merge concurrent updates.

**Example:**
```yaml
customer_updates:
  value: |
    [2024-01-15 10:00] Agent A: Customer requested feature X
    [2024-01-15 10:05] Agent B: Customer upgraded to Enterprise
    [2024-01-15 10:10] Agent A: Follow-up scheduled for next week
```

**Benefits:**
- Track who updated when
- Easier to identify conflicts
- Can implement merge strategies

## Best Practices

### For Shared Memory Blocks

1. **Prefer memory_insert** for concurrent writes
2. **Use clear ownership** - one agent owns write access
3. **Design append-only** when possible
4. **Add timestamps** to track changes
5. **Monitor and archive** to prevent unbounded growth

### For Single-Agent Scenarios

1. **Any tool is safe** when agent has exclusive access
2. **memory_rethink** is fine for consolidation
3. **memory_replace** for precise edits
4. **Still monitor size** and design for growth

### Warning Signs

**Watch for:**
- Blocks growing faster than expected (many agents appending)
- Failed memory_replace operations (race conditions)
- Lost updates (memory_rethink conflicts)
- Confusion about block state

**Action:**
- Redesign for append-only
- Implement agent ownership
- Add coordinator pattern
- Review concurrency patterns

## Testing Concurrent Access

**Validate your design:**
1. Simulate concurrent requests
2. Check for lost updates
3. Monitor block sizes
4. Review conflict rates

**Adjust based on:**
- Conflict frequency
- Update patterns
- Performance requirements
