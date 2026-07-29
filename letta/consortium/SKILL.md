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
    # model: omit to use agent's default (recommended)
    # If overriding, use full handle (e.g. "openai/gpt-4o") to preserve
    # provider routing. Bare names like "glm" may route to wrong billing path.
    env:
      LETTA_ACP_BACKEND: remote
      LETTA_AGENT_ID: agent-xxxx
    cwd: /home/user

  - id: bob
    name: Bob
    command: claude-agent-acp
    args: []
    max_messages: 3  # optional: per-agent override of global --max-messages
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

The optional `model` field names the model to use. `model_env` specifies which environment variable to inject with that value.

**Recommended:** Omit `model` for Letta Code agents. The agent will use its configured default model, which includes correct provider routing (BYOK, Letta credits, etc.).

**If overriding:** Use the full model handle (e.g. `openai/gpt-4o`, `anthropic/claude-sonnet-4-5-20250929`). Bare names like `glm` may strip the provider prefix and route to a different billing path than intended.

- **letta-acp**: `model_env: LETTA_ACP_MODEL` (or omit entirely)
- **Custom agents**: use whatever env var your agent reads, or pass model via `args` instead

Different agents can use different models in the same consortium.

## How It Works

1. **Spawn**: Each agent is started as a subprocess communicating via ACP (JSON-RPC 2.0 over stdio)
2. **Initialize**: Consortium sends `initialize` + `session/new` via ACP protocol
3. **Event-driven discussion**: Each agent runs as an independent long-running task. Messages flow immediately as they're produced — fast agents speak again without waiting for slow ones
4. **Compose-check-block**: When an agent finishes composing, it checks if new messages arrived from other agents. If yes, it re-composes to incorporate them before broadcasting. This guarantees every agent sees all prior messages before speaking
5. **PASS mechanism**: Agents can PASS if they have nothing to add (PASS doesn't consume quota). After PASSing, they wait and get re-prompted when new messages arrive
6. **Idle timeout**: Conversation ends after N seconds of silence (default 30s)
7. **Reflection**: After the discussion, each agent receives the full transcript to process (update memory, run tools, note action items)
8. **Transcript**: Full conversation saved to `~/consortium-transcripts/`

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--topic` | Discussion topic (required) | — |
| `--config` | Agent config file (YAML or JSON) | — |
| `--agent` | Agent in `name:command` format (repeatable) | — |
| `--max-messages` | Max messages per agent (or per-agent via config) | 5 |
| `--initiator` | Who started the discussion | Human |
| `--interactive` | Human can type messages during discussion | false |
| `--timeout` | Per-agent prompt timeout (seconds) | 300 |
| `--idle-timeout` | Seconds of silence before ending | 30 |
| `--unsafe` | Auto-approve all agent tool permissions | false |
| `--max-cycles` | Safety valve: max compose cycles | 100 |

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
