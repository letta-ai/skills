# Hook Types Reference

Detailed documentation of all hook types and their input fields.

## Tool-Related Hooks

These hooks require matchers and receive tool information.

### PreToolUse

Fires **before** tool execution. Can block.

```json
{
  "event_type": "PreToolUse",
  "working_directory": "/path/to/project",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite"
  }
}
```

**Fields:**
- `event_type`: Always "PreToolUse"
- `working_directory`: Current working directory
- `tool_name`: Name of tool (Bash, Edit, Write, Task, Read, Glob, Grep, etc.)
- `tool_input`: Object with tool-specific parameters

**Tool-specific inputs:**
- **Bash**: `command`, `description`, `timeout`, `run_in_background`
- **Edit**: `file_path`, `old_string`, `new_string`, `replace_all`
- **Write**: `file_path`, `content`
- **Task**: `subagent_type`, `prompt`, `description`, `model`, `agent_id`
- **Read**: `file_path`, `offset`, `limit`

### PostToolUse

Fires **after** tool completes successfully. Cannot block.

```json
{
  "event_type": "PostToolUse",
  "working_directory": "/path/to/project",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite"
  },
  "tool_output": "All tests passed",
  "preceding_reasoning": "I need to run the tests to verify the changes work.",
  "preceding_assistant_message": "Let me run the tests now."
}
```

**Additional fields:**
- `tool_output`: Result/output from the tool
- `preceding_reasoning`: Agent's thinking before the tool call
- `preceding_assistant_message`: Text the agent sent before the tool

### PermissionRequest

Fires when permission dialog appears. Can block (auto-deny).

```json
{
  "event_type": "PermissionRequest",
  "working_directory": "/path/to/project",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules"
  }
}
```

Same fields as PreToolUse. Use to auto-approve or auto-deny specific patterns.

## Session Hooks

These don't use matchers and fire at session lifecycle points.

### Stop

Fires when agent finishes responding. Can block (continue working).

```json
{
  "event_type": "Stop",
  "stop_reason": "end_turn",
  "working_directory": "/path/to/project",
  "preceding_reasoning": "The user asked about the project structure. I should summarize.",
  "assistant_message": "Here's an overview of the project structure...",
  "agent_id": "agent-xxx",
  "conversation_id": "conv-yyy"
}
```

**Fields:**
- `stop_reason`: Why agent stopped ("end_turn", "max_tokens", etc.)
- `preceding_reasoning`: Agent's thinking
- `assistant_message`: Final message to user
- `agent_id`, `conversation_id`: Identifiers

**Blocking Stop hooks**: Exit code 2 sends stderr to agent and it continues working. Useful for automated quality checks.

### SubagentStop

Fires when a subagent (Task) completes. Can block.

```json
{
  "event_type": "SubagentStop",
  "working_directory": "/path/to/project",
  "subagent_type": "comms",
  "subagent_description": "Draft reply",
  "output": "Drafted reply: The approach looks correct...",
  "agent_id": "agent-parent",
  "conversation_id": "conv-parent"
}
```

**Fields:**
- `subagent_type`: Type of subagent (explore, general-purpose, etc.)
- `subagent_description`: Task description
- `output`: Subagent's final output

### UserPromptSubmit

Fires when user submits a prompt. Can block.

```json
{
  "event_type": "UserPromptSubmit",
  "working_directory": "/path/to/project",
  "prompt": "Delete all files in /tmp",
  "agent_id": "agent-xxx",
  "conversation_id": "conv-yyy"
}
```

Use for input validation or transformation.

### Notification

Fires when Letta Code sends a notification. Cannot block.

```json
{
  "event_type": "Notification",
  "message": "Task completed successfully",
  "level": "info"
}
```

**Fields:**
- `message`: Notification text
- `level`: "info", "warning", or "error"

### PreCompact

Fires before context compaction. Cannot block.

```json
{
  "event_type": "PreCompact",
  "working_directory": "/path/to/project",
  "agent_id": "agent-xxx",
  "conversation_id": "conv-yyy"
}
```

Use to save state before context is compressed.

### SessionStart

Fires when session begins or resumes. Cannot block.

```json
{
  "event_type": "SessionStart",
  "working_directory": "/path/to/project",
  "agent_id": "agent-xxx",
  "conversation_id": "conv-yyy",
  "is_new_session": true
}
```

**Fields:**
- `is_new_session`: True if new session, false if resuming

### SessionEnd

Fires when session terminates. Cannot block.

```json
{
  "event_type": "SessionEnd",
  "working_directory": "/path/to/project",
  "agent_id": "agent-xxx",
  "conversation_id": "conv-yyy"
}
```

Use for cleanup, final logging, state persistence.

### Setup

Fires when CLI invoked with `--init`. Cannot block.

```json
{
  "event_type": "Setup",
  "working_directory": "/path/to/project"
}
```

Use for one-time initialization tasks.
