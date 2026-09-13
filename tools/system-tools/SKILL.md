---
name: system-tools
description: Shell execution, file operations, and directory listing tools for Letta agents. Provides capabilities not available in Letta's built-in tools.
---

# System Tools for Letta Agents

Provides four essential system interaction tools that extend Letta's built-in capabilities:

- **execute_shell_command** - Run shell commands (not available in Letta built-ins)
- **read_file_contents** - Read files without character limits (Letta's built-in has 500 char limit)
- **write_file_contents** - Overwrite files (Letta's built-in only appends)
- **list_directory_contents** - List directory contents (not available in Letta built-ins)
- **smart_read_file** - LLM-powered extraction of relevant snippets (prevents context blowup)
- **smart_grep_file** - Regex search with context (no LLM required)

## When to Use

- Agents that need to execute shell commands (git, npm, docker, etc.)
- Agents that need to read full file contents without truncation
- Agents that need to write/overwrite files (not just append)
- Agents that need to explore directory structures

## Why These Tools?

Letta's built-in file tools have limitations:

| Capability | Letta Built-in | These Tools |
|------------|----------------|-------------|
| Shell execution | Not available | `execute_shell_command` |
| Read files | 500 char limit | No limit |
| Write files | Append only | Full overwrite |
| List directories | Not available | `list_directory_contents` |

## Installation

### Option 1: Register via REST API

```bash
python scripts/register_system_tools.py --server http://localhost:8283
```

### Option 2: Register via Letta SDK

```python
from letta import create_client
from system_tools import TOOLS

client = create_client(base_url="http://localhost:8283")

for tool_name, tool_def in TOOLS.items():
    client.create_tool(
        source_code=tool_def["source_code"],
        tags=tool_def.get("tags", [])
    )
```

### Option 3: Copy source code directly

Each tool is self-contained. Copy the function from `scripts/system_tools.py` and register it:

```python
client.create_tool(func=execute_shell_command, name="execute_shell_command")
```

## Tool Reference

### execute_shell_command

Execute shell commands with timeout protection.

```python
execute_shell_command(command: str, timeout: int = 30) -> str
```

**Parameters:**
- `command` - The shell command to execute
- `timeout` - Maximum execution time in seconds (default: 30)

**Returns:** Exit code, stdout, and stderr

**Example:**
```
Agent: execute_shell_command("git status")
Result: Exit code: 0
STDOUT:
On branch main
nothing to commit, working tree clean
```

### read_file_contents

Read file contents without character limits.

```python
read_file_contents(file_path: str) -> str
```

**Parameters:**
- `file_path` - Path to the file (relative or absolute)

**Returns:** File path, length, and full contents

**Example:**
```
Agent: read_file_contents("package.json")
Result: File: /workspace/project/package.json
Length: 1847 characters

{
  "name": "my-project",
  ...
}
```

### write_file_contents

Write content to a file (creates parent directories if needed).

```python
write_file_contents(file_path: str, content: str) -> str
```

**Parameters:**
- `file_path` - Path to the file (relative or absolute)
- `content` - Content to write

**Returns:** Success message with bytes written

**Example:**
```
Agent: write_file_contents("config.json", '{"debug": true}')
Result: Successfully wrote 15 characters to /workspace/project/config.json
```

### list_directory_contents

List directory contents with file sizes.

```python
list_directory_contents(path: str = ".") -> str
```

**Parameters:**
- `path` - Directory path (default: current directory)

**Returns:** Formatted listing of directories and files with sizes

**Example:**
```
Agent: list_directory_contents("src")
Result: Directory: /workspace/project/src

Directories (3):
  components/
  utils/
  hooks/

Files (2):
  index.ts (245 bytes)
  App.tsx (1,847 bytes)
```

### smart_read_file

Read a file and return only snippets relevant to your query. Uses LLM-powered extraction to prevent context window blowup.

```python
smart_read_file(file_path: str, query: str, max_chars: int = 500) -> str
```

**Parameters:**
- `file_path` - Path to the file
- `query` - What you're looking for (e.g., "authentication logic", "error handling")
- `max_chars` - Maximum characters to return (default: 500)

**Returns:** Relevant snippets with line numbers

**Example:**
```
Agent: smart_read_file("src/auth.py", "password validation")
Result: File: src/auth.py (5847 chars)
Query: password validation

Lines 45-52:
def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    return True
```

**Note:** Requires `ANTHROPIC_API_KEY` environment variable. Falls back to truncation if unavailable.

### smart_grep_file

Search a file for a pattern and return matching lines with context. No LLM required.

```python
smart_grep_file(file_path: str, pattern: str, context_lines: int = 2, max_matches: int = 5) -> str
```

**Parameters:**
- `file_path` - Path to the file
- `pattern` - Regex pattern to search for
- `context_lines` - Lines of context before/after each match (default: 2)
- `max_matches` - Maximum matches to return (default: 5)

**Returns:** Matching snippets with line numbers and context

**Example:**
```
Agent: smart_grep_file("src/api.py", "def.*endpoint", context_lines=1)
Result: File: src/api.py
Pattern: def.*endpoint
Matches: 3/7

    44: @app.route("/users")
>>> 45: def users_endpoint():
    46:     return get_users()
---
    78: @app.route("/posts")
>>> 79: def posts_endpoint():
    80:     return get_posts()
```

## Security Considerations

These tools execute operations on the host system. Consider:

1. **Sandboxing** - Run Letta in a container or VM for isolation
2. **Path restrictions** - Tools can be modified to restrict paths to a workspace
3. **Command filtering** - `execute_shell_command` can be extended to block dangerous commands
4. **Timeouts** - All tools have timeout protection to prevent hanging

## Comparison with Letta Built-ins

| Tool | vs Letta Built-in |
|------|-------------------|
| `execute_shell_command` | Letta has no shell execution (by design for security) |
| `read_file_contents` | `read_from_text_file` limited to 500 chars |
| `write_file_contents` | `append_to_text_file` only appends, doesn't overwrite |
| `list_directory_contents` | No equivalent in Letta |

For Python code execution, use Letta's built-in `run_code` tool instead - it provides sandboxed execution via E2B.

## References

- [Letta Tool Documentation](https://docs.letta.com/tools)
- [Letta Built-in Tool Execution](https://docs.letta.com/guides/agents/tool-execution-builtin/)
- [scripts/system_tools.py](scripts/system_tools.py) - Tool implementations
- [scripts/register_system_tools.py](scripts/register_system_tools.py) - Registration script
