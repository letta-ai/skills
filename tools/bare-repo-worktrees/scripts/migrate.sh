#!/usr/bin/env bash
# Migrate a Git repository to the bare repo worktree pattern.
#
# main/ is the source of truth for all shared files (.env, .letta, etc.).
# .shared/ contains ONLY symlinks pointing to main/.
# Feature worktrees get symlinks that resolve to main/ files.
#
# Usage:
#   migrate.sh <repo-url> <target-dir> [--copy-from <old-clone>] [--main-branch <branch>]
#
# Example (simple):
#   migrate.sh git@github.com:org/repo.git ~/projects/repo
#
# Example (monorepo with nested .env files):
#   migrate.sh git@github.com:org/repo.git ~/projects/repo --copy-from ~/projects/repo-old --main-branch dev
#
# Backward compatible: --copy-envs-from still works as an alias.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Parse arguments ───────────────────────────────────────────────────────────
REPO_URL="${1:?Usage: migrate.sh <repo-url> <target-dir> [--copy-from <old-clone>] [--main-branch <branch>]}"
TARGET_DIR="${2:?Usage: migrate.sh <repo-url> <target-dir> [--copy-from <old-clone>] [--main-branch <branch>]}"
ENV_SOURCE=""
MAIN_BRANCH="main"

shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy-from|--copy-envs-from|--move-env-from)
      ENV_SOURCE="${2:?$1 requires a path}"
      shift 2
      ;;
    --main-branch)
      MAIN_BRANCH="${2:?--main-branch requires a branch name}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# ── Validate ──────────────────────────────────────────────────────────────────
if [[ -d "$TARGET_DIR" ]]; then
  echo "Error: $TARGET_DIR already exists. Remove it first or choose a different path." >&2
  exit 1
fi

# ── Create bare repo structure ────────────────────────────────────────────────
echo "Creating bare repo at $TARGET_DIR..."
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Clone as bare. --single-branch avoids pulling all remote branches as local branches.
git clone --bare --single-branch "$REPO_URL" .bare

# Create .git pointer file (makes git commands work from the workspace root)
echo "gitdir: ./.bare" > .git

# Configure fetch to see all remote branches
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# Make worktree paths portable (workspace can be moved without breaking)
git config worktree.useRelativePaths true

# Enable commit signing
git config commit.gpgsign true

# Fetch all remote branches
echo "Fetching all remote branches..."
git fetch --all --quiet

# ── Create main worktree with tracking ───────────────────────────────────────
echo "Creating '$MAIN_BRANCH' worktree..."
git worktree add "$MAIN_BRANCH" "$MAIN_BRANCH"

# Set tracking branch (bare clones don't set this automatically)
git -C "$MAIN_BRANCH" branch --set-upstream-to="origin/$MAIN_BRANCH" "$MAIN_BRANCH"

# ── Create scaffold directories ───────────────────────────────────────────────
mkdir -p feat fix hotfix docs

# ── Copy .env files into main/ (source of truth) ─────────────────────────────
WORKSPACE="$(pwd)"
SHARED_DIR="$WORKSPACE/.shared"
MAIN_DIR="$WORKSPACE/$MAIN_BRANCH"

if [[ -n "$ENV_SOURCE" ]]; then
  if [[ ! -d "$ENV_SOURCE" ]]; then
    echo "Warning: source '$ENV_SOURCE' does not exist, skipping env copy." >&2
  else
    echo "Discovering .env files in $ENV_SOURCE..."
    mkdir -p "$SHARED_DIR"

    # Find all .env, .env.*, and .envrc files (skip node_modules, .git, .bare, build dirs)
    # Also skip files tracked by git — those should stay as real files, not symlinks
    while IFS= read -r envfile; do
      relpath="${envfile#$ENV_SOURCE/}"
      # Skip if tracked by git
      if git -C "$ENV_SOURCE" ls-files --error-unmatch "$relpath" &>/dev/null; then
        echo "  Skipping (tracked by git): $relpath"
        continue
      fi

      # Copy into main/ (source of truth)
      destfile="$MAIN_DIR/$relpath"
      mkdir -p "$(dirname "$destfile")"
      cp "$envfile" "$destfile"
      echo "  Copied to $MAIN_BRANCH/: $relpath"

      # Create symlink in .shared/ pointing to main/
      shared_link="$SHARED_DIR/$relpath"
      mkdir -p "$(dirname "$shared_link")"
      ln -sfn "$MAIN_DIR/$relpath" "$shared_link"

    done < <(find "$ENV_SOURCE" \
        -not -path "*/node_modules/*" \
        -not -path "*/.git/*" \
        -not -path "*/.bare/*" \
        -not -path "*/.next/*" \
        -not -path "*/dist/*" \
        -not -path "*/build/*" \
        -not -path "*/.dist/*" \
        -not -path "*/__pycache__/*" \
        -not -path "*/.venv/*" \
        \( -name ".env" -o -name ".env.*" -o -name ".envrc" \) \
        | sort)
  fi
fi

# ── .letta handling ───────────────────────────────────────────────────────────
# .letta/ lives in main/ (source of truth). If it exists at workspace root
# (from an old setup), move it into main/. Then create a symlink in .shared/.
if [[ -d "$WORKSPACE/.letta" && ! -L "$WORKSPACE/.letta" ]]; then
  # Old-style: .letta at workspace root → move into main/
  if [[ -L "$MAIN_DIR/.letta" ]]; then
    rm "$MAIN_DIR/.letta"
  fi
  mv "$WORKSPACE/.letta" "$MAIN_DIR/.letta"
  echo "Moved .letta/ into $MAIN_BRANCH/"
  mkdir -p "$SHARED_DIR"
  ln -sfn "$MAIN_DIR/.letta" "$SHARED_DIR/.letta"
  echo "Added .letta symlink to .shared/"
elif [[ -d "$MAIN_DIR/.letta" ]]; then
  # .letta already in main/ (e.g., from old clone copy)
  mkdir -p "$SHARED_DIR"
  ln -sfn "$MAIN_DIR/.letta" "$SHARED_DIR/.letta"
  echo "Added .letta symlink to .shared/"
fi
# If .letta doesn't exist anywhere, that's fine — Letta Code creates it on first use.

# ── Detect ecosystem for next-steps hint ──────────────────────────────────────
INSTALL_CMD=""
if [[ -f "$MAIN_DIR/pnpm-lock.yaml" ]]; then
  INSTALL_CMD="pnpm install"
elif [[ -f "$MAIN_DIR/bun.lockb" || -f "$MAIN_DIR/bun.lock" ]]; then
  INSTALL_CMD="bun install"
elif [[ -f "$MAIN_DIR/yarn.lock" ]]; then
  INSTALL_CMD="yarn install"
elif [[ -f "$MAIN_DIR/package.json" ]]; then
  INSTALL_CMD="npm install"
elif [[ -f "$MAIN_DIR/pyproject.toml" ]]; then
  INSTALL_CMD="uv sync"
elif [[ -f "$MAIN_DIR/requirements.txt" ]]; then
  INSTALL_CMD="pip install -r requirements.txt"
elif [[ -f "$MAIN_DIR/Cargo.toml" ]]; then
  INSTALL_CMD="cargo build"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Bare repo worktree setup complete!"
echo ""
echo "  Workspace root:  $TARGET_DIR"
echo "  Main worktree:   $TARGET_DIR/$MAIN_BRANCH (source of truth)"
echo "  Git data:        $TARGET_DIR/.bare"
if [[ -d "$SHARED_DIR" ]]; then
  echo "  Shared manifest: $TARGET_DIR/.shared (symlinks → $MAIN_BRANCH/)"
fi
echo ""
echo "Next steps:"
if [[ -n "$INSTALL_CMD" ]]; then
  echo "  cd $TARGET_DIR/$MAIN_BRANCH && $INSTALL_CMD"
else
  echo "  cd $TARGET_DIR/$MAIN_BRANCH"
fi
echo ""
echo "To share additional files/directories across worktrees:"
echo "  ln -s \"\$(pwd)/$MAIN_BRANCH/.workflow-data\" .shared/.workflow-data"
echo "  ln -s \"\$(pwd)/$MAIN_BRANCH/.letta\" .shared/.letta"
echo ""
echo "To create a feature worktree:"
echo "  bash ~/.letta/skills/bare-repo-worktrees/scripts/new-worktree.sh feat/my-feature $MAIN_BRANCH"
