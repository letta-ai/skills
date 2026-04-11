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

| Option | Description |
|--------|-------------|
| `-f, --file <path>` | Path to fleet YAML file (required) |
| `--dry-run` | Preview changes without applying |
| `--agent <pattern>` | Filter agents by name pattern |
| `--match <pattern>` | Template mode: apply to existing agents matching pattern |
| `--root <path>` | Root path for resolving relative file paths |
| `--manifest` | Write JSON manifest with resource IDs |
| `--canary` | Deploy isolated canary copies (CANARY- prefix) |
| `--canary-prefix <str>` | Custom canary prefix (default: CANARY-) |
| `--promote` | Promote canary config to production agents |
| `--cleanup` | Remove canary agents |
| `--recalibrate` | Re-send calibration messages to changed agents |
| `--recalibrate-message <msg>` | Custom calibration message |
| `--recalibrate-tags <tags>` | Scope recalibration by tags (AND logic) |
| `--recalibrate-match <pattern>` | Scope recalibration by glob pattern |
| `--no-wait` | Fire-and-forget recalibration |
| `--skip-first-message` | Skip first_message on creation |

### Examples

```bash
lettactl apply -f fleet.yaml
lettactl apply -f fleet.yaml --dry-run
lettactl apply -f fleet.yaml --agent support-agent
lettactl apply -f fleet.yaml --match "*-draper"
lettactl apply -f fleet.yaml --canary
lettactl apply -f fleet.yaml --promote
lettactl apply -f fleet.yaml --cleanup
lettactl apply -f fleet.yaml --recalibrate --recalibrate-tags "role:support"
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
| `--tags <tags>` | Filter by tags (AND logic) |
| `--canary` | Show only canary agents |
| `--query <text>` | Semantic search in archival memory |

### Examples

```bash
lettactl get agents
lettactl get agents -o wide
lettactl get agents --tags "tenant:acme-corp"
lettactl get agents --tags "role:support,env:production"
lettactl get blocks --agent my-agent
lettactl get tools --orphaned
lettactl get blocks --shared
```

## describe

Show detailed information about a resource.

```bash
lettactl describe <resource> <name>
```

Resources: `agent`, `block`, `tool`.

| Option | Description |
|--------|-------------|
| `--canary` | Describe canary version |

```bash
lettactl describe agent support-agent
lettactl describe block company-context
lettactl describe tool send_email
```

## send

Send a message to an agent or multiple agents.

```bash
lettactl send <agent> <message>
```

### Single Agent Options

| Option | Description |
|--------|-------------|
| `--stream` | Stream the response |
| `--sync` | Synchronous mode (wait for response) |
| `--async` | Send asynchronously (returns run ID) |
| `--max-steps <n>` | Maximum agent steps |
| `--enable-thinking` | Enable thinking mode |
| `--timeout <s>` | Per-agent timeout (default: 60s) |

### Bulk Messaging Options

| Option | Description |
|--------|-------------|
| `--all <pattern>` | Send to agents matching glob pattern |
| `--tags <tags>` | Send to agents matching tags (AND logic) |
| `-f <file>` | Target agents defined in a config file |
| `--confirm` | Skip confirmation prompt |
| `--no-wait` | Fire-and-forget mode |

### Examples

```bash
lettactl send my-agent "Hello, how are you?"
lettactl send my-agent "Explain this" --stream
lettactl send my-agent "Process data" --async
lettactl send --all "support-*" "New policy update"
lettactl send --tags "tenant:acme,role:support" "Policy change"
lettactl send -f fleet.yaml "System check"
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

```bash
lettactl messages reset <agent>
lettactl messages reset <agent> --add-default  # Keep default messages
```

### compact

```bash
lettactl messages compact <agent>
```

### cancel

```bash
lettactl messages cancel <agent>
lettactl messages cancel <agent> --run-ids id1,id2
```

## export

Export agents to YAML or JSON.

### Single Agent

```bash
lettactl export agent <name>
```

| Option | Description |
|--------|-------------|
| `-f, --format <fmt>` | `yaml` (default) or `json` |
| `--legacy-format` | v1 export compatibility |
| `--skip-first-message` | Omit first_message from export |
| `--max-steps <n>` | Limit exported processing steps |

### Bulk Export

```bash
lettactl export agents --all
lettactl export agents --match "support-*"
lettactl export agents --tags "tenant:acme"
```

### LettaBot Export

```bash
lettactl export lettabot <agent>        # Single agent lettabot.yaml
lettactl export lettabot --all          # All agents with lettabot configs
lettactl export lettabot --match "*"    # By pattern
lettactl export lettabot --tags "role:chat"  # By tags
```

## import

Import an agent from an exported file.

```bash
lettactl import <file>
```

| Option | Description |
|--------|-------------|
| `--name <name>` | Override agent name |
| `--append-copy` | Add '_copy' suffix to name |
| `--embedding <model>` | Override embedding model |
| `--override-tools` | Overwrite existing tool source code |
| `--strip-messages` | Remove message history |
| `--secrets <json>` | Inject secrets as JSON |
| `--env-vars <json>` | Inject environment variables |

```bash
lettactl import agent-export.yaml
lettactl import agent-export.json --name new-agent --strip-messages
```

## report

Fleet-wide reporting and analysis.

### memory

```bash
lettactl report memory
```

| Option | Description |
|--------|-------------|
| `--analyze` | LLM-powered deep memory analysis |
| `--confirm` | Skip confirmation for bulk analysis |
| `-o json` | JSON output |

```bash
lettactl report memory                  # Usage stats
lettactl report memory --analyze        # Deep analysis with LLM
```

## delete

Delete resources.

```bash
lettactl delete <resource> <name>
```

Resources: `agent`, `block`, `tool`.

```bash
lettactl delete agent old-agent
lettactl delete block unused-block
lettactl delete tool deprecated-tool
```

## delete-all

Bulk delete with pattern matching.

```bash
lettactl delete-all --pattern "CANARY-.*"
lettactl delete-all --pattern "test-.*" --force  # Actually delete
```

## create / update

Create or update agents from CLI flags.

```bash
lettactl create agent --name my-agent --model openai/gpt-4o
lettactl update agent my-agent --model google_ai/gemini-2.5-pro
```

## Utility Commands

```bash
lettactl health                    # Health check (supports -o json)
lettactl context <agent>           # Show context window token usage
lettactl files <agent>             # Show file attachment state
lettactl runs                      # List async job runs
lettactl run <run-id>              # Get run details
lettactl run-delete <run-id>       # Cancel async run
lettactl cleanup                   # Remove orphaned resources
lettactl validate -f fleet.yaml    # Validate config without applying
lettactl completion <shell>        # Shell completion (bash/zsh/fish)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LETTA_BASE_URL` | Letta server URL (required) |
| `LETTA_API_KEY` | API key for Letta Cloud |
| `SUPABASE_URL` | Supabase URL for bucket storage |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `LETTA_USE_TPUF` | Enable Turbopuffer for semantic conversation search |
| `LETTA_TPUF_API_KEY` | Turbopuffer API key |
| `LETTA_EMBED_ALL_MESSAGES` | Embed all messages for semantic search |
