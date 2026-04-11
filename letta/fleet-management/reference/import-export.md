# Import / Export Reference

Move agents between environments with full fidelity.

## Export Single Agent

```bash
lettactl export agent support-agent              # YAML (default)
lettactl export agent support-agent -f json      # Letta-native JSON
lettactl export agent support-agent -f yaml --skip-first-message
```

## Bulk Export

```bash
lettactl export agents --all                     # Entire fleet
lettactl export agents --match "support-*"       # By pattern
lettactl export agents --tags "tenant:acme"      # By tags
```

## Export Options

| Flag | Description |
|------|-------------|
| `-f, --format <fmt>` | `yaml` (default) or `json` |
| `--legacy-format` | v1 export compatibility |
| `--skip-first-message` | Omit first_message |
| `--max-steps <n>` | Limit exported processing steps |

## Import

```bash
lettactl import agent-export.yaml
lettactl import agent-export.json --name new-agent
lettactl import agent-export.yaml --append-copy
lettactl import agent-export.yaml --strip-messages --embedding openai/text-embedding-3-small
```

## Import Options

| Flag | Description |
|------|-------------|
| `--name <name>` | Override agent name |
| `--append-copy` | Add '_copy' suffix |
| `--embedding <model>` | Override embedding model |
| `--override-tools` | Overwrite existing tool source code |
| `--strip-messages` | Remove message history |
| `--secrets <json>` | Inject secrets as JSON |
| `--env-vars <json>` | Inject environment variables |

## LettaBot Export

Generate ready-to-use lettabot.yaml from agents with channel configs:

```bash
lettactl export lettabot support-agent       # Single agent
lettactl export lettabot --all               # All agents with lettabot configs
lettactl export lettabot --match "*-chat"    # By pattern
lettactl export lettabot --tags "role:chat"  # By tags
```
