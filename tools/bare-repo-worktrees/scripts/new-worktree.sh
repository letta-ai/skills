#!/usr/bin/env bash
# Create a new git worktree and automatically symlink shared files from .shared/
#
# Usage:
#   new-worktree.sh <branch-name> [base-branch]
#   new-worktree.sh --link-only <existing-worktree-path>
#
# Must be run from the workspace root (the directory containing .bare/ and .git).
#
# Examples:
#   new-worktree.sh feat/my-feature dev
#   new-worktree.sh fix/urgent-bug main
#   new-worktree.sh --link-only /path/to/existing/worktree   # just add symlinks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Parse arguments ───────────────────────────────────────────────────────────
if [[ "${1:-}" == "--link-only" ]]; then
  WORKTREE_PATH="${2:?--link-only requires a worktree path}"
  WORKSPACE="$(pwd)"
  bash "$SCRIPT_DIR/link-shared.sh" "$WORKSPACE" "$WORKTREE_PATH"
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
  echo "If this is an existing worktree, run:  new-worktree.sh --link-only $WORKTREE"
  exit 1
fi

# Create parent directory if branch contains a slash (e.g. feat/my-feature)
mkdir -p "$(dirname "$WORKTREE")"

if git show-ref --quiet "refs/remotes/origin/$BRANCH" 2>/dev/null; then
  # Branch exists on remote — check it out and track it
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

# ── Add to zoxide for quick navigation ─────────────────────────────────────────
if command -v zoxide &>/dev/null; then
  zoxide add "$WORKTREE"
  echo "Added to zoxide: $WORKTREE"
fi

# ── Symlink shared files ─────────────────────────────────────────────────────
# link-shared.sh handles .shared/ (preferred) and .envs/ (fallback) automatically
bash "$SCRIPT_DIR/link-shared.sh" "$WORKSPACE" "$WORKTREE"

# ── Detect package managers ───────────────────────────────────────────────────
HAS_PYTHON=false
HAS_NODE=false
HAS_CARGO=false

[[ -f "$WORKTREE/pyproject.toml" || -f "$WORKTREE/requirements.txt" || -f "$WORKTREE/setup.py" ]] && HAS_PYTHON=true
[[ -f "$WORKTREE/package.json" ]] && HAS_NODE=true
[[ -f "$WORKTREE/Cargo.toml" ]] && HAS_CARGO=true

# Detect Node package manager preference
NODE_PM="npm install"
if [[ -f "$WORKTREE/pnpm-lock.yaml" ]]; then
  NODE_PM="pnpm install"
elif [[ -f "$WORKTREE/bun.lockb" || -f "$WORKTREE/bun.lock" ]]; then
  NODE_PM="bun install"
elif [[ -f "$WORKTREE/yarn.lock" ]]; then
  NODE_PM="yarn install"
fi

# ── Install dependencies ─────────────────────────────────────────────────────
if $HAS_PYTHON || $HAS_NODE || $HAS_CARGO; then
  echo ""
  echo "Installing dependencies..."
  (
    cd "$WORKTREE"
    if $HAS_PYTHON; then
      echo "  Running: uv sync"
      uv sync
    fi
    if $HAS_NODE; then
      echo "  Running: $NODE_PM"
      $NODE_PM
    fi
    if $HAS_CARGO; then
      echo "  Running: cargo build"
      cargo build
    fi
  )
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "✅ Worktree ready: $WORKTREE"
echo "  cd $WORKTREE"

if $HAS_PYTHON; then
  echo ""
  echo "  Tip: always run tests via 'uv run python -m pytest'"
  echo "  (bare 'python -m pytest' may use the wrong .venv)"
fi
