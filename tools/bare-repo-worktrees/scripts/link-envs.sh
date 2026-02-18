#!/usr/bin/env bash
# Symlink all env files from <workspace>/.envs/ into a given worktree.
#
# Usage:
#   link-envs.sh <workspace-root> <worktree-path-or-name>
#
# The worktree path can be absolute or relative to the workspace root.
# Absolute paths in .envs are used so symlinks work regardless of nesting depth.

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
    # Already a symlink — update if it points somewhere wrong
    existing="$(readlink "$target")"
    if [[ "$existing" == "$envfile" ]]; then
      echo "  Already linked: $relpath"
      continue
    else
      echo "  Updating link:  $relpath  ($existing → $envfile)"
      ln -sf "$envfile" "$target"
    fi
  elif [[ -f "$target" ]]; then
    # Check if file is tracked by git — if so, don't replace it
    if git -C "$WORKTREE" ls-files --error-unmatch "$relpath" &>/dev/null; then
      echo "  Skipping (tracked by git): $relpath"
      continue
    fi
    echo "  Replacing file with link: $relpath"
    rm "$target"
    ln -sf "$envfile" "$target"
  else
    echo "  Linking: $relpath"
    ln -sf "$envfile" "$target"
  fi
done < <(find "$ENV_DIR" -type f | sort)

echo "Done."
