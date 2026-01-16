---
name: asana
description: Direct Asana REST API client for task management. Reliable 30-second timeouts, automatic retries.
---

# Asana Skill

Direct REST API client for Asana task management. All operations have 30-second timeouts and automatic retries.

## Setup

1. Get a Personal Access Token from https://app.asana.com/0/my-apps
2. Set the environment variable: `export ASANA_ACCESS_TOKEN=your_token_here`
3. Optionally set default workspace: `export ASANA_WORKSPACE=your_workspace_gid`

See [references/SETUP.md](references/SETUP.md) for detailed instructions.

## Usage

```
/asana <command> [args]
```

## Commands

### Read Operations

| Command | Description |
|---------|-------------|
| `task <gid>` | Get task details |
| `tasks --project <gid>` | List tasks in project |
| `subtasks <gid>` | Get subtasks of a task |
| `search <query>` | Search tasks by text |
| `my-tasks` | Tasks assigned to me |
| `projects` | List all projects |
| `workspaces` | List all workspaces |

### Write Operations

| Command | Description |
|---------|-------------|
| `create <name>` | Create a task |
| `update <gid> [options]` | Update a task |
| `comment <gid> <text>` | Add comment to task |

## Examples

### Get task details
```bash
python3 scripts/asana_client.py task 1234567890
```

### Search incomplete tasks
```bash
python3 scripts/asana_client.py search "bug fix" -i
```

### List my incomplete tasks
```bash
python3 scripts/asana_client.py my-tasks -i
```

### Create a task
```bash
python3 scripts/asana_client.py create "Fix login bug" --project 1234567890 --due 2024-12-31
```

### Complete a task
```bash
python3 scripts/asana_client.py update 1234567890 --completed true
```

### Add a comment
```bash
python3 scripts/asana_client.py comment 1234567890 "Fixed in commit abc123"
```

### Get JSON output
```bash
python3 scripts/asana_client.py task 1234567890 --json
```

## Instructions for Claude

When this skill is invoked, run the appropriate command using the script at `scripts/asana_client.py`.

**Important paths:** The script path is relative to this skill's directory. Adjust the path based on where the skill is loaded from.

### Command mapping

| User Command | Script Command |
|--------------|----------------|
| `/asana task <gid>` | `python3 scripts/asana_client.py task <gid>` |
| `/asana tasks -p <project>` | `python3 scripts/asana_client.py tasks --project <project> -i` |
| `/asana subtasks <gid>` | `python3 scripts/asana_client.py subtasks <gid>` |
| `/asana search <query>` | `python3 scripts/asana_client.py search "<query>" -i` |
| `/asana my-tasks` | `python3 scripts/asana_client.py my-tasks -i` |
| `/asana projects` | `python3 scripts/asana_client.py projects` |
| `/asana workspaces` | `python3 scripts/asana_client.py workspaces` |
| `/asana create <name>` | `python3 scripts/asana_client.py create "<name>" [options]` |
| `/asana update <gid> <field=value>` | `python3 scripts/asana_client.py update <gid> --<field> <value>` |
| `/asana comment <gid> <text>` | `python3 scripts/asana_client.py comment <gid> "<text>"` |

### Create options

- `--project <gid>` or `-p <gid>` - Add to project
- `--assignee <gid|me>` or `-a` - Assign to user
- `--due <YYYY-MM-DD>` or `-d` - Set due date
- `--notes <text>` or `-n` - Add description

### Update options

- `--name <text>` - Change task name
- `--completed true|false` or `-c` - Mark complete/incomplete
- `--assignee <gid|me>` or `-a` - Reassign
- `--due <YYYY-MM-DD>` or `-d` - Change due date

### Common flags

- `--json` - Output raw JSON (useful for debugging or piping)
- `-v, --verbose` - Show task GIDs in listings
- `-i, --incomplete` - Filter to incomplete tasks only
- `-l, --limit <n>` - Limit number of results

## Library Usage

The client can also be used as a Python library:

```python
from asana_client import AsanaClient

client = AsanaClient()

# Search tasks
tasks = client.search_tasks(text="bug", completed=False)

# Create task
task = client.create_task(
    name="Fix the thing",
    project="1234567890",
    assignee="me",
    due_on="2024-12-31"
)

# Update task
client.update_task(task["gid"], completed=True)

# Add comment
client.add_comment(task["gid"], "Done!")
```

## Error Handling

The client provides clear error messages:

- **Authentication errors**: Check your `ASANA_ACCESS_TOKEN`
- **Rate limiting**: Wait and retry (the client shows retry-after time)
- **Not found**: Verify the task/project GID exists
- **Permission denied**: Check you have access to the resource

## Why This Exists

MCP-based Asana tools can be unreliable with long timeouts. This skill uses direct REST API calls with:

- 30-second timeouts on all requests
- Automatic retry with exponential backoff
- Clear, actionable error messages
- No external dependencies beyond `requests`
