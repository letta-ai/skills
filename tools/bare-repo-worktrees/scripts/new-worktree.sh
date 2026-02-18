#!/usr/bin/env bash
# Create a new git worktree and automatically symlink all shared files:
#   - All .env / .envrc / .env.* files from .envs/
#   - .letta/ directory (from workspace root)
#
# Usage:
#   new-worktree.sh <branch-name> [base-branch]
#   new-worktree.sh --link-only <existing-worktree-path>
#
# Must be run from the workspace root (the directory containing .bare/ and .git pointer file).
#
# Examples:
#   new-worktree.sh feat/my-feature main
#   new-worktree.sh fix/urgent-bug dev
#   new-worktree.sh --link-only feat/existing-worktree   # just re-add symlinks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Helpers ───────────────────────────────────────────────────────────────────
link_shared_files() {
  local workspace="$1"
  local worktree="$2"

  # Symlink all env files
  if [[ -d "$workspace/.envs" ]]; then
    bash "$SCRIPT_DIR/link-envs.sh" "$workspace" "$worktree"
  else
    echo "(No .envs/ at workspace root — skipping env symlinking)"
    echo "Tip: create $workspace/.envs/ and populate it to enable auto-symlinking."
  fi

  # Symlink .letta
  if [[ -d "$workspace/.letta" ]]; then
    if [[ ! -e "$worktree/.letta" ]]; then
      ln -sf "$workspace/.letta" "$worktree/.letta"
      echo "Linked .letta -> $workspace/.letta"
    else
      echo "  .letta already present in worktree"
    fi
  fi
}

# ── Parse arguments ───────────────────────────────────────────────────────────
if [[ "${1:-}" == "--link-only" ]]; then
  WORKTREE_ARG="${2:?--link-only requires a worktree path or name}"
  WORKSPACE="$(pwd)"
  if [[ "$WORKTREE_ARG" = /* ]]; then
    WORKTREE="$WORKTREE_ARG"
  else
    WORKTREE="$WORKSPACE/$WORKTREE_ARG"
  fi
  link_shared_files "$WORKSPACE" "$WORKTREE"
  exit 0
fi

BRANCH="${1:?Usage: new-worktree.sh <branch-name> [base-branch]}"
BASE_BRANCH="${2:-}"

WORKSPACE="$(pwd)"

# ── Verify we're in a workspace root ─────────────────────────────────────────
if [[ ! -f "$WORKSPACE/.git" ]] || ! grep -q "gitdir" "$WORKSPACE/.git" 2>/dev/null; then
  echo "Error: must be run from the bare-repo workspace root (the dir containing .git pointer file)." >&2
  exit 1
fi

# ── Create worktree ───────────────────────────────────────────────────────────
WORKTREE="$WORKSPACE/$BRANCH"

if [[ -d "$WORKTREE" ]]; then
  echo "Directory already exists: $WORKTREE"
  echo "To re-link shared files: new-worktree.sh --link-only $BRANCH"
  exit 1
fi

# Create parent directory for slash-named branches (e.g. feat/my-feature)
mkdir -p "$(dirname "$WORKTREE")"

if git show-ref --quiet "refs/remotes/origin/$BRANCH" 2>/dev/null; then
  # Branch exists on remote — check it out with tracking
  echo "Checking out existing remote branch: $BRANCH"
  git worktree add "$WORKTREE" --track -b "$BRANCH" "origin/$BRANCH"
elif [[ -n "$BASE_BRANCH" ]]; then
  # New branch from specified base
  echo "Creating new branch '$BRANCH' from '$BASE_BRANCH'..."
  git worktree add "$WORKTREE" -b "$BRANCH" "$BASE_BRANCH"
else
  # New branch from HEAD
  echo "Creating new branch '$BRANCH' from HEAD..."
  git worktree add "$WORKTREE" -b "$BRANCH"
fi

# ── Symlink shared files ──────────────────────────────────────────────────────
link_shared_files "$WORKSPACE" "$WORKTREE"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Worktree ready: $WORKTREE"
echo ""
echo "Next:"
echo "  cd $WORKTREE && <package-manager> install"
