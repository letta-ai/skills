# Template Mode Reference

Apply configurations to existing agents using kubectl-style three-way merge.

## Overview

Template mode updates existing agents while preserving user-added resources. Uses the `--match` flag to target agents by name pattern.

```bash
lettactl apply -f template.yaml --match "*-draper"
```

## How It Works

### Three-Way Merge

Compares three states to determine changes:

1. **Last Applied** - Previous configuration applied by lettactl
2. **Current State** - Agent's current state on server
3. **Desired State** - New configuration being applied

### Merge Semantics

| Last Applied | Current | Desired | Result |
|--------------|---------|---------|--------|
| Has tool A | Has tool A | Has tool A | Keep A |
| Has tool A | Has tool A | No tool A | Remove A |
| No tool A | Has tool A | No tool A | Keep A (user-added) |
| No tool A | No tool A | Has tool A | Add A |

**Key principle**: Resources added by users (not in last-applied) are preserved.

## First Apply Behavior

On first template apply to an agent:
- Uses MERGE semantics (no removals)
- Adds new resources from template
- Preserves all existing resources
- Stores configuration as baseline for future applies

## Conflict Detection

Content changes are tracked via SHA-256 hashes:

- **Tool source code** - Hash of tool implementation
- **Memory block content** - Hash of block value
- **File content** - Hash of files in folders

If server content differs from last-applied hash, lettactl detects potential conflicts.

## Template YAML Structure

Template files are standard fleet configs. The agent name in the template is ignored; configuration is applied to matched agents.

```yaml
agents:
  - name: template          # Name ignored in template mode
    system_prompt:
      from_file: ./prompts/standard.md
    llm_config:
      model: gpt-4o
    memory_blocks:
      - name: guidelines
        description: Standard guidelines
        limit: 3000
        from_file: ./blocks/guidelines.md
    tools:
      - standard_search
      - standard_reply
```

## Pattern Matching

The `--match` flag uses glob patterns:

```bash
--match "*-draper"        # Ends with -draper
--match "support-*"       # Starts with support-
--match "*-prod-*"        # Contains -prod-
--match "agent-001"       # Exact match
```

## Examples

### Update All Production Agents

```bash
# Template with production config
cat > prod-template.yaml << EOF
agents:
  - name: template
    llm_config:
      model: gpt-4o
      context_window: 128000
    tools:
      - production_logger
      - error_reporter
EOF

lettactl apply -f prod-template.yaml --match "*-prod"
```

### Add Shared Block to Existing Agents

```yaml
shared_blocks:
  - name: new-policy
    description: Updated company policy
    limit: 5000
    from_file: ./policy-2024.md

agents:
  - name: template
    shared_blocks:
      - new-policy
```

```bash
lettactl apply -f add-policy.yaml --match "*"
```

### SDK Template Mode

```typescript
import { LettaCtl } from 'lettactl';

const ctl = new LettaCtl();

// Apply template to matching agents
await ctl.deployFromYaml('./template.yaml', {
  match: '*-customer-*'
});

// Programmatic template
await ctl.deployFleet({
  agents: [{
    name: 'template',
    tools: ['new_tool'],
    memory_blocks: [{
      name: 'update',
      description: 'New memory block',
      limit: 2000,
      value: 'Updated content'
    }]
  }]
}, {
  match: 'support-*'
});
```

## Metadata Storage

Template mode stores last-applied configuration in agent metadata under `lettactl.lastApplied`. This enables accurate three-way merge on subsequent applies.

```json
{
  "lettactl.lastApplied": {
    "tools": ["tool1", "tool2"],
    "sharedBlocks": ["block1"],
    "toolHashes": {
      "tool1": "abc123..."
    },
    "blockHashes": {
      "block1": "def456..."
    }
  }
}
```

## Limitations

- Pattern must match at least one agent
- Cannot create new agents in template mode
- Shared blocks are updated globally (affect all agents using them)
