# Troubleshooting Hooks

Common issues and solutions.

## Hook Not Firing

### Problem: Hook doesn't run at all

**Causes and solutions:**

1. **Hooks load at session start**
   - Hooks are loaded when the session starts, not when settings change
   - Solution: Use `/restart` or start a new session after changing settings

2. **Wrong settings file**
   - Local settings override project settings
   - Check: `cat .letta/settings.local.json` and `cat .letta/settings.json`
   - Solution: Ensure hooks are in the right file

3. **Script not executable**
   - Bash/shell scripts must be executable
   - Solution: `chmod +x hooks/*.sh`

4. **Wrong path**
   - Paths are relative to working directory
   - Solution: Use `./hooks/script.sh` or absolute paths

5. **Matcher doesn't match**
   - Regex matchers are case-sensitive
   - Solution: Check your matcher pattern, use `"*"` to match all tools

### Debugging steps:

```bash
# Test hook manually
echo '{"event_type":"PreToolUse","tool_name":"Bash","tool_input":{"command":"test"}}' | ./hooks/my-hook.sh
echo $?  # Check exit code

# Check settings
cat .letta/settings.json | jq '.hooks'

# Check script is executable
ls -la hooks/
```

## Hook Fires But Doesn't Block

### Problem: Exit code 2 doesn't stop the action

**Causes:**

1. **Wrong event type** - Only these hooks can block:
   - `PreToolUse`
   - `PermissionRequest`
   - `Stop`
   - `SubagentStop`
   - `UserPromptSubmit`

2. **Message on stdout, not stderr**
   - Blocking message must go to stderr
   - Solution: Use `echo "message" >&2` (bash) or `print("message", file=sys.stderr)` (Python)

3. **Exit code not 2**
   - Only exit code 2 blocks
   - Solution: Ensure `exit 2` (bash) or `sys.exit(2)` (Python)

### Example correct blocking:

```bash
#!/bin/bash
echo "BLOCKED: Reason here" >&2  # stderr, not stdout
exit 2  # must be 2, not 1
```

```python
print("BLOCKED: Reason here", file=sys.stderr)
sys.exit(2)
```

## Environment Variables Not Available

### Problem: LETTA_AGENT_ID or LETTA_API_KEY empty in hook

**Known issue:** `LETTA_AGENT_ID` may not be passed to hooks in all versions. See [letta-code #729](https://github.com/letta-ai/letta-code/issues/729).

**Workarounds:**

1. **Hardcode agent ID for now:**
   ```python
   AGENT_ID = os.environ.get("LETTA_AGENT_ID", "agent-xxx-fallback")
   ```

2. **Use a config file:**
   ```python
   from pathlib import Path
   config = json.loads(Path(".letta/agent-config.json").read_text())
   agent_id = config["agent_id"]
   ```

3. **Fail closed (block by default):**
   ```python
   if not agent_id:
       print("Unknown agent, blocking for safety", file=sys.stderr)
       sys.exit(2)
   ```

## Hook Timeout

### Problem: Hook times out before completing

**Default timeout:** 60 seconds

**Solutions:**

1. **Increase timeout:**
   ```json
   {
     "type": "command",
     "command": "./hooks/slow-check.sh",
     "timeout": 120000
   }
   ```

2. **Make hook faster:**
   - Avoid network calls if possible
   - Cache results
   - Use async patterns for external APIs

3. **Move slow operations to background:**
   - Have hook trigger a background job
   - Return immediately with exit 0

## Python Import Errors

### Problem: Module not found in Python hook

**Cause:** Hook runs in different environment than your shell

**Solutions:**

1. **Use shebang with explicit interpreter:**
   ```python
   #!/usr/bin/env python3
   ```

2. **Use uv for dependencies:**
   ```json
   {
     "type": "command",
     "command": "uv run python hooks/my-hook.py"
   }
   ```

3. **Add path to project:**
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```

## JSON Parsing Errors

### Problem: Hook fails to parse stdin

**Causes:**

1. **Empty input** - Some events may have minimal data
2. **Invalid JSON** - Rarely, but possible

**Solution: Defensive parsing:**

```python
try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)  # Allow on parse failure
```

```bash
input=$(cat)
if [ -z "$input" ]; then
  exit 0
fi
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
```

## Hooks Running Multiple Times

### Problem: Hook runs more than expected

**Causes:**

1. **Multiple matchers match** - Check your settings for overlapping matchers
2. **Hook registered multiple times** - Check all settings files

**Debug:**
```bash
# Check all hook configs
cat .letta/settings.json | jq '.hooks'
cat .letta/settings.local.json | jq '.hooks' 2>/dev/null
cat ~/.letta/settings.json | jq '.hooks' 2>/dev/null
```

## Performance Issues

### Problem: Hooks slow down the agent

**Solutions:**

1. **Skip unnecessary work:**
   ```python
   # Early exit for irrelevant events
   if input_data.get("tool_name") not in ["Bash", "Edit"]:
       sys.exit(0)
   ```

2. **Use matchers to filter:**
   ```json
   {
     "matcher": "Bash|Edit",  // Only these tools
     "hooks": [...]
   }
   ```

3. **Avoid network calls in PreToolUse:**
   - Move logging to PostToolUse or Stop
   - Cache authentication tokens

4. **Profile your hooks:**
   ```bash
   time echo '{"event_type":"PreToolUse"...}' | ./hooks/my-hook.sh
   ```

## Real-World Gotcha: Naming Conflicts

**Problem:** Hook file named `signal.py` or `inspect.py` shadows Python stdlib

**Solution:** Use unique names like `coordination.py` or `record_inspector.py`

```python
# Bad: hooks/signal.py (shadows stdlib)
# Good: hooks/coordination.py
```
