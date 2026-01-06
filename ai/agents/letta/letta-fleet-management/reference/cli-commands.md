# CLI Commands Reference

Complete command reference for lettactl.

## Global Options

```bash
--verbose, -v          # Verbose output
--no-spinner           # Disable spinner (for CI/CD)
--help, -h             # Show help
```

## apply

Apply fleet configuration to create or update agents.

```bash
lettactl apply -f <file>
```

### Options

| Option | Description |
|--------|-------------|
| `-f, --file <path>` | Path to fleet YAML file (required) |
| `--dry-run` | Preview changes without applying |
| `--agent <pattern>` | Filter agents by name pattern |
| `--match <pattern>` | Template mode: apply to existing agents matching pattern |
| `--root <path>` | Root path for resolving relative file paths |

### Examples

```bash
# Apply all agents
lettactl apply -f fleet.yaml

# Preview changes
lettactl apply -f fleet.yaml --dry-run

# Apply specific agent
lettactl apply -f fleet.yaml --agent support-agent

# Template mode: update existing agents
lettactl apply -f template.yaml --match "*-draper"
```

## get

List resources.

```bash
lettactl get <resource>
```

### Resources

- `agents` - List agents
- `blocks` - List memory blocks
- `tools` - List tools
- `folders` - List folders
- `mcp-servers` - List MCP servers

### Options

| Option | Description |
|--------|-------------|
| `-o, --output <format>` | Output format: `json`, `yaml`, `wide` |
| `--agent <name>` | Filter by agent (for blocks, tools, folders) |
| `--shared` | Show only shared resources (2+ agents) |
| `--orphaned` | Show only orphaned resources (0 agents) |

### Examples

```bash
# List agents
lettactl get agents
lettactl get agents -o wide
lettactl get agents -o json

# List blocks for specific agent
lettactl get blocks --agent my-agent

# Find orphaned tools
lettactl get tools --orphaned

# Find shared blocks
lettactl get blocks --shared
```

## describe

Show detailed information about a resource.

```bash
lettactl describe <resource> <name>
```

### Resources

- `agent` - Agent details
- `block` - Block details
- `tool` - Tool details

### Examples

```bash
lettactl describe agent support-agent
lettactl describe block company-context
lettactl describe tool send_email
```

## send

Send a message to an agent.

```bash
lettactl send <agent> <message>
```

### Options

| Option | Description |
|--------|-------------|
| `--stream` | Stream the response |
| `--async` | Send asynchronously (returns run ID) |
| `--max-steps <n>` | Maximum agent steps |
| `--enable-thinking` | Enable thinking mode |

### Examples

```bash
# Simple message
lettactl send my-agent "Hello, how are you?"

# Stream response
lettactl send my-agent "Explain quantum computing" --stream

# Async (returns immediately)
lettactl send my-agent "Process this data" --async
```

## messages

Manage agent message history.

### list

```bash
lettactl messages list <agent>
```

| Option | Description |
|--------|-------------|
| `--limit <n>` | Number of messages |
| `--order <asc\|desc>` | Sort order |
| `--before <id>` | Messages before ID |
| `--after <id>` | Messages after ID |
| `-o json` | JSON output |

### reset

Clear agent message history.

```bash
lettactl messages reset <agent>
lettactl messages reset <agent> --add-default  # Keep default messages
```

### compact

Compact/summarize message history.

```bash
lettactl messages compact <agent>
```

### cancel

Cancel running async messages.

```bash
lettactl messages cancel <agent>
lettactl messages cancel <agent> --run-ids id1,id2
```

## delete

Delete resources.

```bash
lettactl delete <resource> <name>
```

### Resources

- `agent` - Delete agent
- `block` - Delete block
- `tool` - Delete tool

### Examples

```bash
lettactl delete agent old-agent
lettactl delete block unused-block
lettactl delete tool deprecated-tool
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LETTA_BASE_URL` | Letta server URL (required) |
| `LETTA_API_KEY` | API key for Letta Cloud |
| `SUPABASE_URL` | Supabase URL for bucket storage |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
