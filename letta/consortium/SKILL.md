---
name: consortium
description: Run structured multi-agent group conversations via raw ACP (Agent Client Protocol). Agents discuss topics together, react to each other's messages, and reach consensus. Agent-agnostic — works with Letta Code, Claude Code, Copilot CLI, or any ACP-compatible agent. Use when you hear "consortium", "group conversation", "multi-agent discussion", "agent roundtable", or "agent council".
license: MIT
---

# Consortium

ACP-native multi-agent living group chat. Agents talk to each other autonomously via raw ACP (JSON-RPC 2.0 over stdio). Each agent gets its own ACP session — they see each other's messages, decide whether to respond, and participate in a living discussion with configurable message quotas.

**Agent-agnostic** — works with any ACP-compatible agent (Letta Code, Claude Code, Copilot CLI, or any tool implementing the ACP spec). No Letta-specific dependencies.

## When to Use

- When you want agents to discuss a topic together
- When you need multiple perspectives on a problem
- When agents need to coordinate or reach consensus
- When you hear "consortium", "group conversation", "multi-agent discussion", "agent roundtable", or "agent council"

## Prerequisites

1. **ACP-compatible agents** running and accessible
2. **Agent config file** (`agents.yaml` or `agents.json`) defining each agent's command, env, and connection details
3. **PyYAML** (optional, for YAML configs): `pip install pyyaml`
4. **Python 3.11+**

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

# 3. Interactive mode (you participate via stdin)
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
    model: glm                  # optional: model name
    model_env: LETTA_ACP_MODEL  # optional: env var to inject with model value
    env:
      LETTA_ACP_BACKEND: remote
      LETTA_AGENT_ID: agent-xxxx
    cwd: /home/user

  - id: bob
    name: Bob
    command: claude
    args: ["--model", "claude-sonnet-4-5-20250929"]  # model via CLI args
    env: {}
    cwd: /home/user
```

**JSON** (`agents.json`): Same structure as above.

**Inline** (no config file):
```bash
python3 consortium.py \
    --topic "..." \
    --agent "alice:letta-acp --yolo" \
    --agent "bob:claude"
```

See `agents.example.yaml` for a complete reference config.

## Per-Agent Model Override

The optional `model` field names the model to use. `model_env` specifies which environment variable to inject with that value. This is agent-agnostic — you choose the env var name that your ACP agent reads.

- **letta-acp**: `model_env: LETTA_ACP_MODEL`
- **Custom agents**: use whatever env var your agent reads, or skip `model_env` and pass model via `args` or `env` instead

Different agents can use different models in the same consortium.

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
| `--config` | Agent config file (YAML or JSON) | — |
| `--agent` | Agent in `name:command` format (repeatable) | — |
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

No Letta-specific dependencies. Pure ACP protocol. The config specifies which binary to spawn and what env to pass.

## Full Tool Access

Agents have full Bash/Read/Write tool access during consortium. They can:
- Edit their own memory files
- Run shell commands
- Read and write files
- Make real changes during the discussion

Permission requests are auto-approved (unrestricted mode).

## Bundled Resources

- `consortium.py` — The main script. Run it directly with Python 3.11+.
- `agents.example.yaml` — Example agent configuration. Copy to `agents.yaml` and customize.
