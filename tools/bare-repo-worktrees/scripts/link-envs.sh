#!/usr/bin/env bash
# Symlink all env files from <workspace>/.envs/ into a given worktree.
#
# Usage:
#   link-envs.sh <workspace-root> <worktree-path-or-name>
#
# The worktree path can be absolute or relative to the workspace root.
# Absolute symlink paths are used so links work regardless of nesting depth
# (e.g., feat/my-feature won't break with relative paths).

set -euo pipefail

WORKSPACE="${1:?Usage: link-envs.sh <workspace-root> <worktree-path-or-name>}"
WORKTREE_ARG="${2:?Usage: link-envs.sh <workspace-root> <worktree-path-or-name>}"

# Resolve workspace to absolute path
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
ENV_DIR="$WORKSPACE/.envs"

# Resolve worktree to absolute path
if [[ "$WORKTREE_ARG" = /* ]]; then
  WORKTREE="$WORKTREE_ARG"
else
  WORKTREE="$WORKSPACE/$WORKTREE_ARG"
fi

if [[ ! -d "$ENV_DIR" ]]; then
  echo "No .envs/ directory found at $ENV_DIR — nothing to symlink." >&2
  exit 0
fi

if [[ ! -d "$WORKTREE" ]]; then
  echo "Error: worktree directory '$WORKTREE' does not exist." >&2
  exit 1
fi

echo "Linking env files into $(basename "$WORKTREE")..."

while IFS= read -r envfile; do
  relpath="${envfile#$ENV_DIR/}"
  target="$WORKTREE/$relpath"
  targetdir="$(dirname "$target")"

  mkdir -p "$targetdir"

  if [[ -L "$target" ]]; then
    existing="$(readlink "$target")"
    if [[ "$existing" == "$envfile" ]]; then
      echo "  Already linked: $relpath"
      continue
    else
      echo "  Updating link:  $relpath  ($existing → $envfile)"
      ln -sf "$envfile" "$target"
    fi
  elif [[ -f "$target" ]]; then
    echo "  Replacing file with link: $relpath"
    rm "$target"
    ln -sf "$envfile" "$target"
  else
    echo "  Linking: $relpath"
    ln -sf "$envfile" "$target"
  fi
done < <(find "$ENV_DIR" -type f | sort)

echo "Done."
