#!/bin/bash
# Block dangerous commands - PreToolUse hook
#
# Prevents: rm -rf, git push --force, DROP TABLE, etc.
# Exit 2 = block with feedback to agent
#
# Usage: Configure in .letta/settings.json:
# {
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "Bash",
#       "hooks": [{"type": "command", "command": "./hooks/block-dangerous.sh"}]
#     }]
#   }
# }

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

# Only check Bash commands
if [ "$tool_name" != "Bash" ]; then
  exit 0
fi

command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Dangerous patterns to block
declare -a PATTERNS=(
  'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)'  # rm -rf
  'git\s+push.*--force'                                   # force push
  'git\s+push.*-f\b'                                      # force push shorthand
  'DROP\s+(TABLE|DATABASE)'                               # SQL drops
  'TRUNCATE\s+TABLE'                                      # SQL truncate
  '>\s*/dev/sd[a-z]'                                      # write to disk device
  'mkfs\.'                                                # format filesystem
  'dd\s+if=.*of=/dev'                                     # dd to device
)

for pattern in "${PATTERNS[@]}"; do
  if echo "$command" | grep -qEi "$pattern"; then
    cat >&2 << EOF
BLOCKED: This command matches a dangerous pattern.

Command: ${command:0:100}
Pattern: $pattern

This type of command requires manual execution for safety.
If you're certain, ask the user to run it directly.
EOF
    exit 2
  fi
done

exit 0
