---
name: letta-fleet-management
description: Manage Letta AI agent fleets declaratively with kubectl-style CLI. Use when creating, updating, or managing multiple Letta agents with shared configurations, memory blocks, tools, folders, canary deployments, multi-tenancy, and bulk operations.
license: MIT
---

# lettactl

kubectl-style CLI for managing Letta AI agent fleets declaratively.

## When to Use

- Deploying multiple agents with shared configurations
- Managing agent memory blocks, tools, and folders
- Applying templates to existing agents
- Running canary deployments before promoting to production
- Multi-tenant agent management (B2B / B2B2C)
- Bulk messaging across agent fleets
- Importing/exporting agents between environments
- Analyzing agent memory health (self-diagnosis)
- Calibrating agents with first-message boot sequences
- Programmatic fleet management via SDK

## Core Workflow

1. Define agents in `fleet.yaml`
2. Apply with `lettactl apply -f fleet.yaml`
3. Verify with `lettactl get agents` and `lettactl describe agent <name>`

## Fleet YAML Structure

```yaml
shared_blocks:
  - name: company-context
    description: Shared company knowledge
    limit: 5000
    from_file: ./context/company.md

shared_folders:
  - name: brand_docs
    files:
      - "docs/*.md"

mcp_servers:
  - name: firecrawl
    type: sse
    server_url: "https://sse.firecrawl.dev"
    auth_header: "Authorization"
    auth_token: "Bearer ${FIRECRAWL_API_KEY}"

agents:
  - name: support-agent
    description: Customer support assistant
    tags:
      - "tenant:acme-corp"
      - "role:support"
    system_prompt:
      from_file: ./prompts/support.md
    llm_config:
      model: google_ai/gemini-2.5-pro
      context_window: 128000
    reasoning: true
    first_message: "Initialize and confirm readiness."
    memory_blocks:
      - name: persona
        description: Agent personality
        limit: 2000
        value: "You are a helpful support agent."
        agent_owned: true
    archives:
      - name: knowledge_base
        description: Long-term knowledge storage
    shared_blocks:
      - company-context
    shared_folders:
      - brand_docs
    tools:
      - send_email
      - search_docs
      - "tools/*"
    mcp_tools:
      - server: firecrawl
        tools: ["scrape", "crawl"]
```

See `reference/fleet-config.md` for full schema.

## CLI Commands

### Apply Configuration
```bash
lettactl apply -f fleet.yaml                    # Create/update agents
lettactl apply -f fleet.yaml --dry-run          # Preview changes
lettactl apply -f fleet.yaml --match "*-prod"   # Template mode
lettactl apply -f fleet.yaml --canary           # Deploy canary copies
lettactl apply -f fleet.yaml --promote          # Promote canary to production
lettactl apply -f fleet.yaml --recalibrate      # Re-send calibration messages
```

### Inspect Resources
```bash
lettactl get agents                        # List all agents
lettactl get agents -o wide                # With details
lettactl get agents --tags "tenant:acme"   # Filter by tags
lettactl get blocks --shared               # Shared blocks only
lettactl get tools --orphaned              # Unused tools
lettactl describe agent <name>             # Full agent details
```

### Messaging
```bash
lettactl send <agent> "Hello"              # Send message
lettactl send <agent> "Hi" --stream        # Stream response
lettactl send --all "support-*" "Update"   # Bulk send by pattern
lettactl send --tags "role:support" "Hi"   # Bulk send by tags
lettactl messages list <agent>             # View history
lettactl messages reset <agent>            # Clear history
lettactl messages compact <agent>          # Summarize history
```

### Import / Export
```bash
lettactl export agent <name> -f yaml       # Export single agent
lettactl export agents --all               # Export entire fleet
lettactl import agent-export.yaml          # Import agent
```

### Fleet Reporting
```bash
lettactl report memory                     # Memory usage report
lettactl report memory --analyze           # LLM-powered deep analysis
```

See `reference/cli-commands.md` for all options.

## Canary Deployments

Test changes on isolated copies before promoting to production:

```bash
lettactl apply -f fleet.yaml --canary           # Create CANARY-* copies
lettactl send CANARY-support-agent "test msg"   # Test the canary
lettactl apply -f fleet.yaml --promote          # Promote to production
lettactl apply -f fleet.yaml --cleanup          # Remove canary agents
```

See `reference/canary-deployments.md`.

## Multi-Tenancy

Tag agents for B2B and B2B2C filtering:

```yaml
agents:
  - name: acme-support
    tags:
      - "tenant:acme-corp"
      - "role:support"
      - "env:production"
```

```bash
lettactl get agents --tags "tenant:acme-corp"
lettactl send --tags "tenant:acme-corp,role:support" "Policy update"
```

See `reference/multi-tenancy.md`.

## Self-Diagnosis

Analyze agent memory health fleet-wide:

```bash
lettactl report memory                  # Usage stats for all agents
lettactl report memory --analyze        # LLM-powered analysis per agent
```

Reports fill percentages, stale data, redundancy, missing knowledge, and split recommendations. See `reference/self-diagnosis.md`.

## Agent Calibration

Prime agents on creation with a boot message:

```yaml
agents:
  - name: support-agent
    first_message: "Review your persona and confirm you understand your role."
```

Recalibrate existing agents after updates:

```bash
lettactl apply -f fleet.yaml --recalibrate
lettactl apply -f fleet.yaml --recalibrate --recalibrate-tags "role:support"
```

See `reference/agent-calibration.md`.

## Template Mode

Apply configuration to existing agents matching a pattern:

```bash
lettactl apply -f template.yaml --match "*-draper"
```

Uses three-way merge: preserves user-added resources while updating managed ones. See `reference/template-mode.md`.

## SDK Usage

```typescript
import { LettaCtl } from 'lettactl';

const ctl = new LettaCtl({ lettaBaseUrl: 'http://localhost:8283' });

// Deploy from YAML
await ctl.deployFromYaml('./fleet.yaml');

// Programmatic fleet config
const config = ctl.createFleetConfig()
  .addSharedBlock({ name: 'kb', description: 'Knowledge', limit: 5000, from_file: 'kb.md' })
  .addAgent({
    name: 'support-agent',
    description: 'Support AI',
    system_prompt: { from_file: 'prompts/support.md' },
    llm_config: { model: 'google_ai/gemini-2.5-pro', context_window: 32000 },
    shared_blocks: ['kb'],
    tags: ['team:support'],
  })
  .build();

await ctl.deployFleet(config);

// Send message with callbacks
await ctl.sendMessage('agent-id', 'Hello', {
  onComplete: (run) => console.log('Done:', run.id),
});

// Template mode
await ctl.deployFromYaml('./template.yaml', { match: '*-prod' });
```

See `reference/sdk-usage.md` for full API.
