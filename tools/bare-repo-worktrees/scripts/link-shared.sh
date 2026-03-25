#!/usr/bin/env bash
# Symlink all shared files from <workspace>/.shared/ into a given worktree.
# .shared/ contains ONLY symlinks pointing to main/ (the source of truth).
# This script resolves each symlink and creates a corresponding symlink in
# the target worktree. If the resolved target is inside the target worktree
# (i.e., we're linking into main/ itself), the entry is skipped.
#
# Usage:
#   link-shared.sh <workspace-root> <worktree-path-or-name>
#
# The worktree path can be absolute or relative to the workspace root.
# Absolute paths are used so symlinks work regardless of nesting depth.
#
# Backward compatible: auto-renames .envs/ → .shared/ if found.

set -euo pipefail

WORKSPACE="${1:?Usage: link-shared.sh <workspace-root> <worktree-path-or-name>}"
WORKTREE_ARG="${2:?Usage: link-shared.sh <workspace-root> <worktree-path-or-name>}"

# Resolve workspace to absolute path
WORKSPACE="$(cd "$WORKSPACE" && pwd)"

# Find shared directory (.shared preferred, auto-migrate .envs if found)
SHARED_DIR="$WORKSPACE/.shared"
if [[ ! -d "$SHARED_DIR" ]]; then
  if [[ -d "$WORKSPACE/.envs" ]]; then
    echo "Renaming .envs/ → .shared/..."
    mv "$WORKSPACE/.envs" "$SHARED_DIR"
  else
    echo "No .shared/ directory found at $WORKSPACE — nothing to symlink." >&2
    exit 0
  fi
fi

# Resolve worktree to absolute path
if [[ "$WORKTREE_ARG" = /* ]]; then
  WORKTREE="$WORKTREE_ARG"
else
  WORKTREE="$WORKSPACE/$WORKTREE_ARG"
fi

if [[ ! -d "$WORKTREE" ]]; then
  echo "Error: worktree directory '$WORKTREE' does not exist." >&2
  exit 1
fi

echo "Linking shared files into $(basename "$WORKTREE")..."

link_entry() {
  local shared_file="$1"
  local relpath="${shared_file#$SHARED_DIR/}"
  local target="$WORKTREE/$relpath"
  local targetdir
  targetdir="$(dirname "$target")"

  # For symlinks in .shared/, resolve to the real target so the worktree
  # symlink points to the actual resource (not to .shared/)
  local link_target="$shared_file"
  if [[ -L "$shared_file" ]]; then
    link_target="$(readlink -f "$shared_file" 2>/dev/null || readlink "$shared_file")"
  fi

  # Skip if the resolved target is inside the target worktree.
  # This prevents replacing real files in main/ with self-referencing symlinks.
  if [[ "$link_target" == "$WORKTREE"/* ]]; then
    echo "  Skipping (source lives here): $relpath"
    return
  fi

  mkdir -p "$targetdir"

  if [[ -L "$target" ]]; then
    existing="$(readlink "$target")"
    if [[ "$existing" == "$link_target" ]]; then
      echo "  Already linked: $relpath"
      return
    else
      echo "  Updating link:  $relpath"
      ln -sfn "$link_target" "$target"
    fi
  elif [[ -e "$target" ]]; then
    # Check if tracked by git — if so, don't replace it
    if git -C "$WORKTREE" ls-files --error-unmatch "$relpath" &>/dev/null 2>&1; then
      echo "  Skipping (tracked by git): $relpath"
      return
    fi
    echo "  Replacing with link: $relpath"
    rm -rf "$target"
    ln -sfn "$link_target" "$target"
  else
    echo "  Linking: $relpath"
    ln -sfn "$link_target" "$target"
  fi
}

# Process regular files and symlinks (to files or directories) at top level of .shared/
# Symlinks are not followed (-not -type d excludes real directories to avoid recursing)
while IFS= read -r entry; do
  link_entry "$entry"
done < <(find "$SHARED_DIR" -maxdepth 1 \( -type f -o -type l \) | sort)

# Process nested files (subdirectories contain regular files to symlink individually)
while IFS= read -r entry; do
  link_entry "$entry"
done < <(find "$SHARED_DIR" -mindepth 2 -type f | sort)

echo "Done."
