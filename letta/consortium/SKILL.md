---description: Consortium — ACP-native multi-agent living group chat. Agents talk to each other autonomously via raw ACP (JSON-RPC over stdio). Agent-agnostic — works with any ACP-compatible agent (Letta, Claude Code, Copilot CLI).
---

# Consortium

Run a structured multi-agent consortium conversation among your agents. Agents see each other's messages, decide whether to respond, and participate in a living discussion with configurable message quotas.

## When to Use

- When you want agents to discuss a topic together
- When you need multiple perspectives on a problem
- When agents need to coordinate or reach consensus
- When you hear "consortium", "group conversation", "multi-agent discussion", "agent roundtable", or "agent council"

## Prerequisites

1. **ACP-compatible agents** running and accessible
2. **Agent config file** (`agents.yaml` or `agents.json`) defining each agent's command, env, and connection details
3. **PyYAML** (optional, for YAML configs): `pip install pyyaml`

## Quick Start

```bash
# 1. Copy the example config and customize
cp agents.example.yaml agents.yaml
# Edit agents.yaml with your agent details

# 2. Run a consortium
python3 consortium.py \
    --topic "How should we architecture the new API?" \
    --config agents.yaml \
    --max-messages 5

# 3. Interactive mode (you participate)
python3 consortium.py \
    --topic "Review the deployment plan" \
    --config agents.yaml \
    --interactive
```

## Agent Config Format

**YAML** (`agents.yaml`):
```yaml
agents:
  - id: alice
    name: Alice
    command: letta-acp
    args: ["--yolo"]
    model: glm          # optional: model override (passed as LETTA_ACP_MODEL)
    env:
      LETTA_ACP_BACKEND: remote
      LETTA_AGENT_ID: agent-xxxx
      LETTA_APP_SERVER_URL: ws://127.0.0.1:14601
    cwd: /home/user

  - id: bob
    name: Bob
    command: claude
    args: []
    model: gpt-4o       # different model per agent
    env: {}
    cwd: /home/user
```

**JSON** (`agents.json`): Same structure as above.

**Inline** (no config file):
```bash
# name:command or name:model:command
python3 consortium.py \
    --topic "..." \
    --agent "alice:glm:letta-acp --yolo" \
    --agent "bob:claude"
```

## How It Works

1. **Spawn**: Each agent is started as a subprocess communicating via ACP (JSON-RPC 2.0 over stdio)
2. **Initialize**: Consortium sends `initialize` + `session/new` via ACP protocol
3. **Discussion**: Agents take turns responding to the topic and each other's messages
4. **PASS mechanism**: Agents can PASS if they have nothing to add (PASS doesn't consume quota)
5. **Re-prompt**: If new messages arrive while an agent is composing, they get a chance to revise
6. **Reflection**: After the discussion, each agent receives the full transcript to process (update memory, run tools, note action items)
7. **Transcript**: Full conversation saved to `~/consortium-transcripts/`

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--topic` | Discussion topic (required) | — |
| `--config` | Agent config file (YAML/JSON) | — |
| `--agent` | Agent in `name:command` or `name:model:command` format (repeatable) | — |
| `--max-messages` | Max messages per agent | 5 |
| `--initiator` | Who started the discussion | Human |
| `--interactive` | Human can type messages during discussion | false |
| `--timeout` | Per-agent prompt timeout (seconds) | 180 |

## Agent-Agnostic

Consortium works with ANY agent that implements the [Agent Client Protocol](https://github.com/AcpProtocol/acp-spec):
- Letta Code agents (via `letta-acp`)
- Claude Code
- GitHub Copilot CLI
- Any custom ACP implementation

No Letta-specific dependencies. Pure ACP protocol.

## Full Tool Access

Agents have full Bash/Read/Write tool access during consortium. They can:
- Edit their own memory files
- Run shell commands
- Read and write files
- Make real changes during the discussion

Permission requests are auto-approved (unrestricted mode).
