# SDK Usage Reference

Programmatic TypeScript API for managing Letta agent fleets.

## Installation

```bash
npm install lettactl
# or
pnpm add lettactl
```

## Quick Start

```typescript
import { LettaCtl } from 'lettactl';

const ctl = new LettaCtl({
  lettaBaseUrl: 'http://localhost:8283'
});

await ctl.deployFromYaml('./fleet.yaml');
```

## LettaCtl Class

### Constructor

```typescript
interface LettaCtlOptions {
  lettaBaseUrl?: string            // Letta server URL
  lettaApiKey?: string             // For Letta Cloud
  supabaseUrl?: string             // For bucket storage
  supabaseAnonKey?: string         // Supabase auth
  supabaseServiceRoleKey?: string  // Supabase service role
  root?: string                    // Root dir (defaults to cwd)
}

const ctl = new LettaCtl(options?: LettaCtlOptions);
```

Environment variables are used as defaults if options not provided.

### deployFleet(config, options?)

Deploy a fleet from a typed config object.

```typescript
const result = await ctl.deployFleet(config, {
  dryRun: true,                // Preview without applying
  agentPattern: "support-*",   // Only deploy matching agents
  match: "tags:team=support",  // Filter by tags
});

interface DeployResult {
  agents: Record<string, string>  // name → letta_agent_id
  created: string[]
  updated: string[]
  unchanged: string[]
}
```

### deployFromYaml(path, options?)

Deploy directly from a YAML file. Same options as deployFleet.

```typescript
const result = await ctl.deployFromYaml(
  './fleet.yaml',
  { dryRun: false, rootPath: './config' }
);

// Also available:
await ctl.deployFromYamlString(yamlContent, options);
```

### sendMessage(agentId, message, options?)

Send a message to an agent and get the run handle back.

```typescript
const run = await ctl.sendMessage(
  'agent-id',
  'Hello, how can you help?',
  {
    onComplete: (run) => console.log('Done:', run.id),
    onError: (err) => console.error('Failed:', err),
    timeout: 30,  // seconds
  }
);

// Poll for completion
const completed = await ctl.waitForRun(run.id, {
  timeout: 300,
});

interface Run {
  id: string
  status: 'created' | 'running' | 'completed' | 'failed'
  agent_id: string
  created_at: string
  completed_at?: string
  stop_reason?: string
}
```

### bulkSendMessage(message, options?)

Send a message to multiple agents by pattern or tags.

```typescript
await ctl.bulkSendMessage('Policy update', {
  pattern: 'support-*',          // Glob pattern
  tags: ['tenant:acme'],         // Tag filter (AND logic)
  messageFn: (agent) =>          // Per-agent message customization
    `Hello ${agent.name}, please review the new policy.`,
  collectResponse: true,         // Capture agent replies
  timeout: 60,
});
```

### deleteAgent(name)

```typescript
await ctl.deleteAgent('support-agent');
```

### validateFleet(config)

Validate configuration without deploying. Throws on invalid.

```typescript
ctl.validateFleet(config);
```

## FleetConfigBuilder

Fluent builder for constructing fleet configs programmatically.

```typescript
const config = ctl.createFleetConfig()
  .addSharedBlock({
    name: 'brand-voice',
    description: 'Brand guidelines',
    limit: 5000,
    from_file: 'memory/brand.md',
  })
  .addSharedFolder({
    name: 'knowledge',
    files: [
      'docs/faq.md',
      'docs/policies.md',
      { from_bucket: {
        provider: 'supabase',
        bucket: 'docs',
        path: 'handbook/',
      }},
    ],
  })
  .addAgent({
    name: 'support-agent',
    description: 'Tier 1 support',
    tags: ['team:support', 'tier:production'],
    system_prompt: { from_file: 'prompts/support.md' },
    llm_config: {
      model: 'google_ai/gemini-2.5-pro',
      context_window: 32000,
    },
    shared_blocks: ['brand-voice'],
    shared_folders: ['knowledge'],
    memory_blocks: [{
      name: 'customer_data',
      description: 'Customer context',
      agent_owned: true,
      limit: 5000,
    }],
    tools: [
      'archival_memory_search',
      'archival_memory_insert',
      'send_email',
    ],
  })
  .build();

ctl.validateFleet(config); // throws on invalid
await ctl.deployFleet(config);
```

## Configuration Types

```typescript
interface FleetConfig {
  shared_blocks?: SharedBlock[]
  shared_folders?: SharedFolderConfig[]
  mcp_servers?: McpServerConfig[]
  agents: AgentConfig[]  // At least 1 required
}

interface AgentConfig {
  name: string              // [a-zA-Z0-9_-]+
  description: string
  system_prompt: PromptConfig
  llm_config: LLMConfig
  tags?: string[]           // For multi-tenancy filtering
  tools?: string[]
  mcp_tools?: McpToolConfig[]
  shared_blocks?: string[]
  shared_folders?: string[]
  memory_blocks?: MemoryBlock[]
  archives?: ArchiveConfig[]  // Max 1 per agent
  folders?: FolderConfig[]
  embedding?: string
  reasoning?: boolean       // Default: true
  first_message?: string    // Sent on first creation
}

interface LLMConfig {
  model: string             // "provider/model-name"
  context_window: number    // 1000-200000
  max_tokens?: number       // Max output tokens per call
}

interface PromptConfig {
  value?: string
  from_file?: string
  from_bucket?: BucketSource
  disable_base_prompt?: boolean
}

interface MemoryBlock {
  name: string
  description: string
  limit: number
  agent_owned: boolean      // true = agent writes
  value?: string
  from_file?: string
  from_bucket?: BucketSource
  version?: string
}

interface McpServerConfig {
  name: string
  type: 'sse' | 'stdio' | 'streamable_http'
  server_url?: string
  command?: string
  args?: string[]
  env?: Record<string, string>
  auth_header?: string
  auth_token?: string
  custom_headers?: Record<string, string>
}
```

## Template Mode

Apply configuration to existing agents:

```typescript
// Update all agents matching pattern
await ctl.deployFromYaml('./template.yaml', {
  match: '*-production'
});

// Programmatic template mode
await ctl.deployFleet(templateConfig, {
  match: 'support-*'
});
```

## Error Handling

```typescript
try {
  await ctl.deployFromYaml('./fleet.yaml');
} catch (error) {
  if (error.message.includes('validation')) {
    console.error('Invalid configuration:', error.message);
  } else if (error.message.includes('LETTA_BASE_URL')) {
    console.error('Missing environment variable');
  } else {
    throw error;
  }
}
```

## Example: Dynamic Multi-Tenant Fleet

```typescript
import { LettaCtl } from 'lettactl';

async function provisionTenant(tenantId: string, agents: string[]) {
  const ctl = new LettaCtl();

  const config = ctl.createFleetConfig()
    .addSharedBlock({
      name: 'product-info',
      description: 'Product documentation',
      limit: 10000,
      from_file: './docs/products.md'
    });

  for (const role of agents) {
    config.addAgent({
      name: `${tenantId}-${role}`,
      description: `${role} agent for ${tenantId}`,
      tags: [`tenant:${tenantId}`, `role:${role}`],
      system_prompt: { from_file: `./prompts/${role}.md` },
      llm_config: {
        model: 'google_ai/gemini-2.5-pro',
        context_window: 32000,
      },
      shared_blocks: ['product-info'],
      tools: ['lookup_order', 'send_email']
    });
  }

  await ctl.deployFleet(config.build());
}
```
