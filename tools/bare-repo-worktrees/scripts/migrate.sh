#!/usr/bin/env bash
# Migrate a Git repository to the bare repo worktree pattern.
#
# Usage:
#   migrate.sh <repo-url> <target-dir> [--copy-envs-from <old-clone>] [--main-branch <branch>]
#
# Examples:
#   migrate.sh git@github.com:org/repo.git ~/projects/repo
#   migrate.sh git@github.com:org/repo.git ~/projects/repo --copy-envs-from ~/projects/repo-old
#   migrate.sh git@github.com:org/repo.git ~/projects/repo --main-branch dev

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Parse arguments ───────────────────────────────────────────────────────────
REPO_URL="${1:?Usage: migrate.sh <repo-url> <target-dir> [--copy-envs-from <old-clone>] [--main-branch <branch>]}"
TARGET_DIR="${2:?Usage: migrate.sh <repo-url> <target-dir> [--copy-envs-from <old-clone>] [--main-branch <branch>]}"
ENV_SOURCE=""
MAIN_BRANCH="main"

shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy-envs-from)
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

# ── Create primary worktree with tracking ────────────────────────────────────
echo "Creating '$MAIN_BRANCH' worktree..."
git worktree add "$MAIN_BRANCH" "$MAIN_BRANCH"

# Set tracking branch (bare clones don't set this automatically)
git -C "$MAIN_BRANCH" branch --set-upstream-to="origin/$MAIN_BRANCH" "$MAIN_BRANCH"

# ── Create scaffold directories ───────────────────────────────────────────────
mkdir -p feat fix hotfix docs

# ── Copy & symlink .env files ─────────────────────────────────────────────────
WORKSPACE="$(pwd)"

if [[ -n "$ENV_SOURCE" ]]; then
  if [[ ! -d "$ENV_SOURCE" ]]; then
    echo "Warning: ENV_SOURCE '$ENV_SOURCE' does not exist, skipping env copy." >&2
  else
    echo "Discovering .env files in $ENV_SOURCE..."
    ENV_DIR="$WORKSPACE/.envs"
    mkdir -p "$ENV_DIR"

    # Find all .env, .env.*, and .envrc files; skip generated/dependency directories
    while IFS= read -r envfile; do
      relpath="${envfile#$ENV_SOURCE/}"
      destfile="$ENV_DIR/$relpath"
      mkdir -p "$(dirname "$destfile")"
      cp "$envfile" "$destfile"
      echo "  Copied: $relpath"
    done < <(find "$ENV_SOURCE" \
        -not -path "*/node_modules/*" \
        -not -path "*/.git/*" \
        -not -path "*/.bare/*" \
        -not -path "*/.next/*" \
        -not -path "*/dist/*" \
        -not -path "*/build/*" \
        -not -path "*/__pycache__/*" \
        -not -path "*/.venv/*" \
        \( -name ".env" -o -name ".env.*" -o -name ".envrc" \) \
        | sort)

    echo "Symlinking env files into $MAIN_BRANCH/..."
    bash "$SCRIPT_DIR/link-envs.sh" "$WORKSPACE" "$MAIN_BRANCH"
  fi
fi

# ── Symlink .letta into primary worktree ──────────────────────────────────────
# .letta lives at workspace root and is symlinked into each worktree so
# agent settings are shared and visible in every checkout.
if [[ -d "$WORKSPACE/.letta" ]]; then
  ln -sf "$WORKSPACE/.letta" "$WORKSPACE/$MAIN_BRANCH/.letta"
  echo "Linked .letta into $MAIN_BRANCH/"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Bare repo worktree setup complete!"
echo ""
echo "  Workspace root:  $TARGET_DIR"
echo "  Primary worktree: $TARGET_DIR/$MAIN_BRANCH"
echo "  Git data:         $TARGET_DIR/.bare"
[[ -d "$TARGET_DIR/.envs" ]] && echo "  Env files:        $TARGET_DIR/.envs (symlinked into $MAIN_BRANCH/)"
echo ""
echo "Next steps:"
echo "  cd $TARGET_DIR/$MAIN_BRANCH && <package-manager> install"
echo ""
echo "To create a feature worktree:"
echo "  cd $TARGET_DIR"
echo "  bash ~/.letta/skills/bare-repo-worktrees/scripts/new-worktree.sh feat/my-feature $MAIN_BRANCH"
