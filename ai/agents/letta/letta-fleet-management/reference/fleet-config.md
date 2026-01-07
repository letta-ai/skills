# Fleet Configuration Reference

Complete YAML schema for lettactl fleet configuration.

## Top-Level Structure

```yaml
shared_blocks: []      # Optional: blocks shared across agents
tools: []              # Optional: tool definitions
mcp_servers: []        # Optional: MCP server configs
agents: []             # Required: agent definitions
```

## Shared Blocks

```yaml
shared_blocks:
  - name: block-name           # Required: unique identifier
    description: Description   # Required: block purpose
    limit: 5000                # Required: max characters
    value: "Inline content"    # Option 1: inline value
    from_file: ./path.md       # Option 2: local file
    from_bucket:               # Option 3: Supabase storage
      bucket: bucket-name
      path: file/path.md
```

## Agent Definition

```yaml
agents:
  - name: agent-name                    # Required: unique name
    description: Agent description      # Optional

    system_prompt:                      # Required
      value: "Inline prompt"            # Option 1
      from_file: ./prompt.md            # Option 2
      from_bucket:                      # Option 3
        bucket: prompts
        path: agent/system.md

    llm_config:                         # Optional
      model: gpt-4o                     # Model name
      context_window: 128000            # Context size

    embedding: text-embedding-3-small   # Required for self-hosted, optional for Cloud

    memory_blocks: []                   # Optional: agent-specific blocks
    shared_blocks: []                   # Optional: references to shared_blocks
    tools: []                           # Optional: tool names
    folders: []                         # Optional: file folders
```

## Memory Blocks

Agent-specific memory blocks:

```yaml
memory_blocks:
  - name: persona                 # Required
    description: Agent persona    # Required
    limit: 2000                   # Required
    value: "Content here"         # Option 1: inline
    from_file: ./persona.md       # Option 2: file
    from_bucket:                  # Option 3: bucket
      bucket: memory
      path: personas/support.md
```

## Tools

### Inline Tool Definition

```yaml
tools:
  - name: search_docs
    description: Search documentation
    source_code: |
      def search_docs(query: str) -> str:
          """Search the documentation."""
          return f"Results for: {query}"
```

### File-Based Tool

```yaml
tools:
  - name: send_email
    from_file: ./tools/send_email.py
```

### Referencing Tools in Agents

```yaml
agents:
  - name: my-agent
    tools:
      - search_docs      # Reference by name
      - send_email
```

## MCP Servers

```yaml
mcp_servers:
  - name: github-server
    type: sse
    url: http://localhost:3000/sse

  - name: local-tools
    type: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

## Folders

Attach file folders to agents for RAG:

```yaml
agents:
  - name: docs-agent
    folders:
      - name: documentation
        files:
          - ./docs/guide.md
          - ./docs/api.md
          - ./docs/**/*.md    # Glob patterns supported
```

## File Source Priority

When multiple sources specified, priority is:
1. `from_bucket` (Supabase storage)
2. `from_file` (local filesystem)
3. `value` (inline content)

## Variable Interpolation

Environment variables can be used:

```yaml
agents:
  - name: ${AGENT_NAME:-default-agent}
    llm_config:
      model: ${MODEL_NAME}
```

## Complete Example

```yaml
shared_blocks:
  - name: company-knowledge
    description: Company policies and procedures
    limit: 10000
    from_file: ./context/company.md

tools:
  - name: lookup_customer
    from_file: ./tools/lookup_customer.py

mcp_servers:
  - name: slack-server
    type: sse
    url: http://localhost:3001/sse

agents:
  - name: support-agent
    description: Customer support assistant
    system_prompt:
      from_file: ./prompts/support.md
    llm_config:
      model: gpt-4o
      context_window: 128000
    memory_blocks:
      - name: persona
        description: Agent personality traits
        limit: 2000
        value: |
          You are a friendly, professional support agent.
          Always be helpful and concise.
    shared_blocks:
      - company-knowledge
    tools:
      - lookup_customer
    folders:
      - name: faq
        files:
          - ./faq/*.md
```
