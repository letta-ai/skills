# Fleet Configuration Reference

Complete YAML schema for lettactl fleet configuration.

## Top-Level Structure

```yaml
root_path: ./my-fleet     # Optional: base dir for relative paths
shared_blocks: []          # Optional: blocks shared across agents
shared_folders: []         # Optional: folders shared across agents
mcp_servers: []            # Optional: MCP server configs
agents: []                 # Required: agent definitions
```

## Agent Definition

```yaml
agents:
  - name: agent-name                    # Required: unique name ([a-zA-Z0-9_-]+)
    description: Agent description      # Required

    system_prompt:                      # Required
      value: "Inline prompt"            # Option 1
      from_file: ./prompt.md            # Option 2
      from_bucket:                      # Option 3
        provider: supabase
        bucket: prompts
        path: agent/system.md
      disable_base_prompt: false        # Skip Letta base instructions

    llm_config:                         # Required
      model: google_ai/gemini-2.5-pro   # provider/model-name format
      context_window: 128000            # 1,000 - 200,000
      max_tokens: 4096                  # Optional: max output tokens

    embedding: openai/text-embedding-3-small  # Optional (default)
    embedding_config: {}                      # Optional: additional settings
    reasoning: true                           # Optional: chain-of-thought (default: true)
    first_message: "Boot message"             # Optional: sent on first creation only

    tags: []                            # Optional: key:value strings for filtering
    memory_blocks: []                   # Optional: agent-specific blocks
    archives: []                        # Optional: vector-searchable memory (max 1)
    shared_blocks: []                   # Optional: references to shared_blocks
    shared_folders: []                  # Optional: references to shared_folders
    folders: []                         # Optional: file folders for RAG
    tools: []                           # Optional: tool names, objects, or globs
    mcp_tools: []                       # Optional: tools from MCP servers
```

## Memory Blocks

Agent-specific memory blocks with ownership semantics:

```yaml
memory_blocks:
  # Agent can modify this block — YAML won't overwrite on apply
  - name: user_preferences
    description: "What I know about the user"
    limit: 5000
    value: "No preferences yet."
    agent_owned: true

  # YAML controls this block — syncs on every apply
  - name: brand_guidelines
    description: "Brand voice and identity"
    limit: 3000
    from_file: "brand/guidelines.md"
    agent_owned: false
    version: "2.1.0"
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Required. Unique within agent. |
| `description` | string | Required. Human-readable purpose. |
| `limit` | integer | Required. Max characters. |
| `agent_owned` | boolean | Required. `true`: agent writes, YAML won't overwrite. `false`: YAML syncs on every apply. |
| `value` / `from_file` / `from_bucket` | string | Content source. Exactly one required. |
| `version` | string | Optional. User-defined version tag. |

## Shared Blocks

```yaml
shared_blocks:
  - name: company-knowledge
    description: Company policies and procedures
    limit: 10000
    from_file: ./context/company.md
    version: "2.0.0"
```

Define at root level, attach by name in agents via `shared_blocks: [name]`.

## Shared Folders

```yaml
shared_folders:
  - name: brand_assets
    files:
      - "brand/*.md"
      - from_bucket:
          provider: supabase
          bucket: assets
          path: "brand/*.pdf"
```

Define at root level, attach by name in agents via `shared_folders: [name]`.

## Archives

Vector-searchable long-term memory. Max one per agent.

```yaml
archives:
  - name: knowledge_base
    description: "Long-term knowledge storage"
    embedding: "openai/text-embedding-3-small"
```

## Tools

Reference built-in tools by name, custom tools by path, or auto-discover from a directory:

```yaml
tools:
  # Built-in by name
  - archival_memory_insert
  - archival_memory_search

  # Custom tool from cloud storage
  - name: "web_search"
    from_bucket:
      provider: supabase
      bucket: tools
      path: "web_search.py"

  # Auto-discover all .py files in tools/ directory
  - "tools/*"
```

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

## MCP Servers

```yaml
mcp_servers:
  # SSE server with auth
  - name: firecrawl
    type: sse
    server_url: "https://sse.firecrawl.dev"
    auth_header: "Authorization"
    auth_token: "Bearer ${FIRECRAWL_API_KEY}"

  # Stdio server
  - name: filesystem
    type: stdio
    command: npx
    args: ["-y", "@anthropic/mcp-server-filesystem", "/tmp"]
    env:
      NODE_ENV: production

  # Streamable HTTP
  - name: custom-api
    type: streamable_http
    server_url: "https://api.example.com/mcp"
    custom_headers:
      X-Api-Version: "2"
```

Types: `sse`, `stdio`, `streamable_http`. Auth fields: `auth_header`, `auth_token`, `custom_headers`.

## MCP Tool Selection

Select which tools from an MCP server an agent can use:

```yaml
mcp_tools:
  - server: firecrawl
    tools: ["scrape", "crawl"]    # Specific tools only
  - server: filesystem             # All tools (default)
```

## Tags

Tags enable multi-tenancy and filtering. Format: `key:value`.

```yaml
agents:
  - name: support-agent
    tags:
      - "tenant:acme-corp"
      - "role:support"
      - "env:production"
```

```bash
lettactl get agents --tags "tenant:acme-corp"
lettactl send --tags "role:support,env:production" "Update"
```

Tags use AND logic — all specified tags must match.

## Folders

File collections for RAG. Supports local files, globs, and cloud storage:

```yaml
folders:
  - name: documentation
    files:
      - "docs/guide.md"
      - "docs/*.txt"
      - "knowledge/**/*.md"
      - from_bucket:
          provider: supabase
          bucket: my-bucket
          path: "docs/*.pdf"
```

## FromBucket (Cloud Storage)

```yaml
from_bucket:
  provider: supabase       # Currently only supabase
  bucket: bucket-name
  path: file/path.md       # Supports glob patterns
```

Used by: system prompts, memory blocks, shared blocks, folders, tools.

## File Source Priority

When multiple sources specified: `from_bucket` > `from_file` > `value`.

## Variable Interpolation

Environment variables are expanded:

```yaml
agents:
  - name: ${AGENT_NAME:-default-agent}
    llm_config:
      model: ${MODEL_NAME}
```

## Defaults

| Field | Default |
|-------|---------|
| `model` | `google_ai/gemini-2.5-pro` |
| `context_window` | `28000` |
| `embedding` | `openai/text-embedding-3-small` |
| `reasoning` | `true` |
| `disable_base_prompt` | `false` |

## Validation Rules

- Unique agent names (`[a-zA-Z0-9_-]+`)
- Reserved names: `agents`, `blocks`, `archives`, `tools`, `folders`, `files`, `mcp-servers`, `archival`
- Unique block names within an agent
- Max 1 archive per agent
- Single content source per prompt/block (`value`, `from_file`, or `from_bucket`)
- Context window: 1,000–200,000
- Tags: no commas, non-empty strings
- Strict validation — unknown fields rejected
