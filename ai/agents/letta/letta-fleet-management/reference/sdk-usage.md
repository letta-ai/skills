# SDK Usage Reference

Programmatic API for managing Letta agent fleets.

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
const ctl = new LettaCtl({
  lettaBaseUrl?: string,           // Letta server URL
  lettaApiKey?: string,            // For Letta Cloud
  supabaseUrl?: string,            // For bucket storage
  supabaseAnonKey?: string,        // Supabase auth
  supabaseServiceRoleKey?: string  // Supabase service role
});
```

Environment variables are used as defaults if options not provided.

### deployFromYaml

Deploy agents from a YAML file.

```typescript
await ctl.deployFromYaml(
  yamlPath: string,
  options?: {
    dryRun?: boolean,        // Preview only
    agentPattern?: string,   // Filter agents
    match?: string,          // Template mode pattern
    rootPath?: string        // Root for relative paths
  }
);
```

### deployFromYamlString

Deploy from YAML string content.

```typescript
const yaml = `
agents:
  - name: my-agent
    system_prompt:
      value: You are helpful.
`;

await ctl.deployFromYamlString(yaml, {
  dryRun: false
});
```

### deployFleet

Deploy from a FleetConfig object.

```typescript
await ctl.deployFleet(
  config: FleetConfig,
  options?: {
    dryRun?: boolean,
    agentPattern?: string,
    match?: string
  }
);
```

### validateFleet

Validate configuration without deploying.

```typescript
const isValid = ctl.validateFleet(config);
```

### createFleetConfig

Builder for creating fleet configs programmatically.

```typescript
const config = ctl.createFleetConfig()
  .addSharedBlock({
    name: 'context',
    description: 'Shared context',
    limit: 5000,
    value: 'Company info here'
  })
  .addAgent({
    name: 'support-agent',
    system_prompt: { value: 'You are helpful.' },
    shared_blocks: ['context'],
    tools: ['search']
  })
  .build();

await ctl.deployFleet(config);
```

## FleetConfig Type

```typescript
interface FleetConfig {
  shared_blocks?: SharedBlock[];
  tools?: ToolConfig[];
  mcp_servers?: McpServerConfig[];
  agents: AgentConfig[];
}

interface AgentConfig {
  name: string;
  description?: string;
  system_prompt: ContentSource;
  llm_config?: {
    model?: string;
    context_window?: number;
  };
  embedding?: string;
  memory_blocks?: MemoryBlock[];
  shared_blocks?: string[];
  tools?: string[];
  folders?: FolderConfig[];
}

interface ContentSource {
  value?: string;
  from_file?: string;
  from_bucket?: {
    bucket: string;
    path: string;
  };
}

interface MemoryBlock {
  name: string;
  description: string;
  limit: number;
  value?: string;
  from_file?: string;
  from_bucket?: BucketSource;
}

interface SharedBlock extends MemoryBlock {}
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

## Example: Dynamic Fleet Creation

```typescript
import { LettaCtl } from 'lettactl';

async function createAgentFleet(customers: string[]) {
  const ctl = new LettaCtl();

  const config = ctl.createFleetConfig()
    .addSharedBlock({
      name: 'product-info',
      description: 'Product documentation',
      limit: 10000,
      from_file: './docs/products.md'
    });

  for (const customer of customers) {
    config.addAgent({
      name: `${customer}-support`,
      description: `Support agent for ${customer}`,
      system_prompt: {
        value: `You are a support agent for ${customer}.`
      },
      shared_blocks: ['product-info'],
      tools: ['lookup_order', 'send_email']
    });
  }

  await ctl.deployFleet(config.build());
}
```
