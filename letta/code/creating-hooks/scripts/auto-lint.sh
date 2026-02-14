#!/bin/bash
# Auto-lint on changes - Stop hook
#
# Runs linter when there are uncommitted changes.
# If linting fails, exits 2 so agent can fix the issues.
#
# Usage: Configure in .letta/settings.json:
# {
#   "hooks": {
#     "Stop": [{
#       "hooks": [{"type": "command", "command": "./hooks/auto-lint.sh"}]
#     }]
#   }
# }

set -uo pipefail

# Check if there are any uncommitted changes
if git diff --quiet HEAD 2>/dev/null; then
  echo "No changes detected, skipping lint."
  exit 0
fi

# Detect project type and run appropriate linter
if [ -f "package.json" ]; then
  # Node.js project
  if grep -q '"lint"' package.json 2>/dev/null; then
    echo "Running npm run lint..."
    output=$(npm run lint 2>&1)
    exit_code=$?
  elif [ -f "node_modules/.bin/eslint" ]; then
    echo "Running eslint..."
    output=$(npx eslint . --ext .js,.ts,.jsx,.tsx 2>&1)
    exit_code=$?
  else
    echo "No linter configured."
    exit 0
  fi
elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  # Python project
  if command -v ruff &>/dev/null; then
    echo "Running ruff..."
    output=$(ruff check . 2>&1)
    exit_code=$?
  elif command -v flake8 &>/dev/null; then
    echo "Running flake8..."
    output=$(flake8 . 2>&1)
    exit_code=$?
  else
    echo "No Python linter found."
    exit 0
  fi
else
  echo "Unknown project type, skipping lint."
  exit 0
fi

if [ $exit_code -eq 0 ]; then
  echo "Lint passed."
  exit 0
else
  cat >&2 << EOF
LINT ERRORS FOUND - Please fix before continuing:

$output
EOF
  exit 2
fi
