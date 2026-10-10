#!/usr/bin/env bash
# Set up a bare repo worktree workspace.
#
# Modes:
#   1) Fresh setup from remote URL
#      setup-workspace.sh <repo-url> <target-dir> [--copy-from <old-clone>] [--main-branch <branch>]
#
#   2) Upgrade existing local checkout/workspace
#      setup-workspace.sh --upgrade <workspace-dir> [--main-branch <branch>]
#
# `--upgrade` supports:
#   - Standard checkout (.git directory) -> bare workspace format
#   - Existing bare workspace using worktrees/ layout -> root-level layout
#
# Backward compatible aliases:
#   --copy-envs-from, --move-env-from (same as --copy-from)

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  setup-workspace.sh <repo-url> <target-dir> [--copy-from <old-clone>] [--main-branch <branch>]
  setup-workspace.sh --upgrade <workspace-dir> [--main-branch <branch>]

Examples:
  setup-workspace.sh git@github.com:org/repo.git ~/projects/repo --main-branch dev
  setup-workspace.sh --upgrade ~/projects/repo --main-branch dev
EOF
}

is_git_pointer_file() {
  local workspace="$1"
  [[ -f "$workspace/.git" ]] && grep -q "^gitdir: " "$workspace/.git" 2>/dev/null
}

require_outside_workspace() {
  local workspace="$1"
  case "$PWD" in
    "$workspace"|"$workspace"/*)
      echo "Error: run this command from outside '$workspace' to avoid invalid CWD during migration." >&2
      exit 1
      ;;
  esac
}

detect_default_main_branch() {
  local workspace="$1"

  if [[ -d "$workspace/worktrees/dev" || -d "$workspace/dev" ]]; then
    echo "dev"
    return
  fi

  if [[ -d "$workspace/worktrees/main" || -d "$workspace/main" ]]; then
    echo "main"
    return
  fi

  local head_branch
  head_branch="$(git -C "$workspace" symbolic-ref --short HEAD 2>/dev/null || true)"
  if [[ -n "$head_branch" && "$head_branch" != "__bare_placeholder__" ]]; then
    echo "$head_branch"
    return
  fi

  local remote_head
  remote_head="$(git -C "$workspace" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  remote_head="${remote_head#origin/}"
  if [[ -n "$remote_head" ]]; then
    echo "$remote_head"
    return
  fi

  echo "main"
}

configure_bare_workspace() {
  local workspace="$1"

  git -C "$workspace" config core.bare false

  if git -C "$workspace" remote get-url origin >/dev/null 2>&1; then
    git -C "$workspace" config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
  fi

  # Note: Do NOT set worktree.useRelativePaths = true
  # It breaks compatibility with Antigravity and other Git parsers
  git -C "$workspace" config commit.gpgsign true
}

set_branch_tracking_if_remote_exists() {
  local workspace="$1"
  local main_branch="$2"
  local main_dir="$workspace/$main_branch"

  if git -C "$workspace" show-ref --verify --quiet "refs/remotes/origin/$main_branch"; then
    git -C "$main_dir" branch --set-upstream-to="origin/$main_branch" "$main_branch" >/dev/null 2>&1 || true
  fi
}

move_workspace_contents_to_backup() {
  local workspace="$1"
  local backup_dir="$2"

  shopt -s dotglob nullglob
  local entry
  for entry in "$workspace"/*; do
    local base
    base="$(basename "$entry")"
    [[ "$base" == ".git" ]] && continue
    mv "$entry" "$backup_dir/"
  done
  shopt -u dotglob nullglob
}

restore_backup_into_main() {
  local backup_dir="$1"
  local main_dir="$2"

  shopt -s dotglob nullglob
  local entry
  for entry in "$backup_dir"/*; do
    local base target
    base="$(basename "$entry")"
    target="$main_dir/$base"
    if [[ -e "$target" || -L "$target" ]]; then
      rm -rf "$target"
    fi
    mv "$entry" "$main_dir/"
  done
  shopt -u dotglob nullglob

  rmdir "$backup_dir"
}

rewrite_root_symlinks_from_worktrees_prefix() {
  local workspace="$1"
  local rewritten=0

  while IFS= read -r link_path; do
    local target new_target
    target="$(readlink "$link_path")"
    new_target=""

    case "$target" in
      worktrees/*)
        new_target="${target#worktrees/}"
        ;;
      ./worktrees/*)
        new_target="./${target#./worktrees/}"
        ;;
      "$workspace"/worktrees/*)
        new_target="$workspace/${target#$workspace/worktrees/}"
        ;;
    esac

    if [[ -n "$new_target" && "$new_target" != "$target" ]]; then
      ln -sfn "$new_target" "$link_path"
      echo "  Rewrote symlink: $(basename "$link_path") -> $new_target"
      rewritten=$((rewritten + 1))
    fi
  done < <(find "$workspace" -mindepth 1 -maxdepth 1 -type l | sort)

  if (( rewritten > 0 )); then
    echo "Updated $rewritten top-level symlink(s) that referenced worktrees/."
  fi
}

upgrade_standard_checkout_in_place() {
  local workspace="$1"
  local main_branch="$2"

  if [[ ! -d "$workspace/.git" ]]; then
    echo "Error: '$workspace' does not look like a standard checkout (.git directory not found)." >&2
    exit 1
  fi

  if [[ -d "$workspace/.bare" ]]; then
    echo "Error: '$workspace' already has .bare/. Use '--upgrade' on that workspace layout instead." >&2
    exit 1
  fi

  if ! git -C "$workspace" rev-parse --verify --quiet "$main_branch" >/dev/null; then
    if ! git -C "$workspace" show-ref --verify --quiet "refs/remotes/origin/$main_branch"; then
      echo "Error: main branch '$main_branch' was not found locally or on origin." >&2
      exit 1
    fi
  fi

  local backup_dir
  backup_dir="$(mktemp -d "${TMPDIR:-/tmp}/bare-repo-upgrade.XXXXXX")"

  echo "Temporarily moving current checkout files to: $backup_dir"
  move_workspace_contents_to_backup "$workspace" "$backup_dir"

  echo "Converting .git directory -> .bare..."
  mv "$workspace/.git" "$workspace/.bare"
  echo "gitdir: ./.bare" > "$workspace/.git"

  configure_bare_workspace "$workspace"

  if git -C "$workspace" remote get-url origin >/dev/null 2>&1; then
    echo "Fetching remote branches..."
    git -C "$workspace" fetch --all --quiet || echo "Warning: fetch failed; continuing with local refs."
  fi

  if ! git -C "$workspace" show-ref --verify --quiet "refs/heads/$main_branch"; then
    git -C "$workspace" branch "$main_branch" "origin/$main_branch"
  fi

  git -C "$workspace" symbolic-ref HEAD refs/heads/__bare_placeholder__

  echo "Creating primary worktree at '$workspace/$main_branch'..."
  git -C "$workspace" worktree add "$workspace/$main_branch" "$main_branch"

  set_branch_tracking_if_remote_exists "$workspace" "$main_branch"

  echo "Restoring previous checkout contents into '$main_branch/'..."
  restore_backup_into_main "$backup_dir" "$workspace/$main_branch"

  echo "Standard checkout upgraded to bare workspace format."
}

upgrade_worktrees_layout_to_root() {
  local workspace="$1"

  if [[ ! -d "$workspace/.bare" ]] || ! is_git_pointer_file "$workspace"; then
    echo "Error: '$workspace' is not a bare workspace (.bare + .git pointer file required)." >&2
    exit 1
  fi

  if [[ ! -d "$workspace/worktrees" ]]; then
    echo "Workspace already appears to use root-level worktrees (no worktrees/ directory found)."
    rewrite_root_symlinks_from_worktrees_prefix "$workspace"
    return
  fi

  shopt -s dotglob nullglob
  local entries=("$workspace/worktrees"/*)
  shopt -u dotglob nullglob

  if (( ${#entries[@]} == 0 )); then
    rmdir "$workspace/worktrees" 2>/dev/null || true
    echo "Found empty worktrees/ directory; removed."
    rewrite_root_symlinks_from_worktrees_prefix "$workspace"
    return
  fi

  echo "Moving worktrees/* entries to workspace root..."
  local moved=0
  local src
  for src in "${entries[@]}"; do
    local name dest
    name="$(basename "$src")"
    dest="$workspace/$name"

    if [[ -e "$dest" || -L "$dest" ]]; then
      echo "Error: destination already exists: $dest" >&2
      echo "Resolve conflicts, then rerun --upgrade." >&2
      exit 1
    fi

    mv "$src" "$dest"
    echo "  moved: worktrees/$name -> $name"
    moved=$((moved + 1))
  done

  rmdir "$workspace/worktrees" 2>/dev/null || true
  rewrite_root_symlinks_from_worktrees_prefix "$workspace"

  echo "Moved $moved worktree directory(ies) to workspace root."
}

run_upgrade_mode() {
  local workspace="$1"
  local main_branch="$2"

  if [[ ! -d "$workspace" ]]; then
    echo "Error: workspace '$workspace' does not exist." >&2
    exit 1
  fi

  require_outside_workspace "$workspace"

  if [[ -d "$workspace/.git" ]]; then
    upgrade_standard_checkout_in_place "$workspace" "$main_branch"
  else
    upgrade_worktrees_layout_to_root "$workspace"
  fi

  echo ""
  echo "Upgrade complete."
  echo ""
  echo "Recommended Worktrunk setting:"
  echo "  worktree-path = \"{{ branch | sanitize }}\""
}

run_fresh_setup_mode() {
  local repo_url="$1"
  local target_dir="$2"
  local env_source="$3"
  local main_branch="$4"

  if [[ -d "$target_dir" ]]; then
    echo "Error: $target_dir already exists. Remove it first or choose a different path." >&2
    exit 1
  fi

  echo "Creating bare repo at $target_dir..."
  mkdir -p "$target_dir"
  cd "$target_dir"

  git clone --bare --single-branch "$repo_url" .bare
  echo "gitdir: ./.bare" > .git

  configure_bare_workspace "$target_dir"

  echo "Fetching all remote branches..."
  git fetch --all --quiet

  # Detach HEAD so worktree creation doesn't fail with "already used"
  git symbolic-ref HEAD refs/heads/__bare_placeholder__

  echo "Creating '$main_branch' worktree..."
  git worktree add "$main_branch" "$main_branch"
  set_branch_tracking_if_remote_exists "$target_dir" "$main_branch"

  local workspace main_dir
  workspace="$(pwd)"
  main_dir="$workspace/$main_branch"

  if [[ -n "$env_source" ]]; then
    if [[ ! -d "$env_source" ]]; then
      echo "Warning: source '$env_source' does not exist, skipping env copy." >&2
    else
      echo "Discovering .env files in $env_source..."

      while IFS= read -r envfile; do
        relpath="${envfile#$env_source/}"
        if git -C "$env_source" ls-files --error-unmatch "$relpath" &>/dev/null; then
          echo "  Skipping (tracked by git): $relpath"
          continue
        fi

        destfile="$main_dir/$relpath"
        mkdir -p "$(dirname "$destfile")"
        cp "$envfile" "$destfile"
        echo "  Copied to $main_branch/: $relpath"

      done < <(find "$env_source" \
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

  if [[ -d "$workspace/.letta" && ! -L "$workspace/.letta" ]]; then
    if [[ -L "$main_dir/.letta" ]]; then
      rm "$main_dir/.letta"
    fi
    mv "$workspace/.letta" "$main_dir/.letta"
    echo "Moved .letta/ into $main_branch/"
  fi

  local install_cmd=""
  if [[ -f "$main_dir/pnpm-lock.yaml" ]]; then
    install_cmd="pnpm install"
  elif [[ -f "$main_dir/bun.lockb" || -f "$main_dir/bun.lock" ]]; then
    install_cmd="bun install"
  elif [[ -f "$main_dir/yarn.lock" ]]; then
    install_cmd="yarn install"
  elif [[ -f "$main_dir/package.json" ]]; then
    install_cmd="npm install"
  elif [[ -f "$main_dir/pyproject.toml" ]]; then
    install_cmd="uv sync"
  elif [[ -f "$main_dir/requirements.txt" ]]; then
    install_cmd="pip install -r requirements.txt"
  elif [[ -f "$main_dir/Cargo.toml" ]]; then
    install_cmd="cargo build"
  fi

  echo ""
  echo "Bare repo worktree setup complete!"
  echo ""
  echo "  Workspace root:  $target_dir"
  echo "  Main worktree:   $target_dir/$main_branch (source of truth)"
  echo "  Git data:        $target_dir/.bare"
  echo ""
  echo "Next steps:"
  if [[ -n "$install_cmd" ]]; then
    echo "  cd $target_dir/$main_branch && $install_cmd"
  else
    echo "  cd $target_dir/$main_branch"
  fi
  echo ""
  echo "To share .env files across worktrees:"
  echo "  1. Add files to main/.worktreeinclude (e.g., .env, .envrc)"
  echo "  2. Run 'wt step copy-ignored' after creating a new worktree"
  echo ""
  echo "To create a feature worktree:"
  echo "  cd $target_dir/$main_branch && wt switch --create feat/my-feature"
}

# ── Parse arguments ───────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

MODE="fresh"
REPO_URL=""
TARGET_DIR=""
UPGRADE_DIR=""
ENV_SOURCE=""
MAIN_BRANCH=""
MAIN_BRANCH_SET=false

if [[ "$1" == "--upgrade" ]]; then
  MODE="upgrade"
  UPGRADE_DIR="${2:-}"
  if [[ -z "$UPGRADE_DIR" ]]; then
    echo "Error: --upgrade requires a workspace path." >&2
    usage
    exit 1
  fi
  shift 2
else
  REPO_URL="${1:-}"
  TARGET_DIR="${2:-}"
  if [[ -z "$REPO_URL" || -z "$TARGET_DIR" ]]; then
    usage
    exit 1
  fi
  shift 2
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy-from|--copy-envs-from|--move-env-from)
      if [[ "$MODE" != "fresh" ]]; then
        echo "Error: $1 is only supported in fresh setup mode." >&2
        exit 1
      fi
      ENV_SOURCE="${2:?$1 requires a path}"
      shift 2
      ;;
    --main-branch)
      MAIN_BRANCH="${2:?--main-branch requires a branch name}"
      MAIN_BRANCH_SET=true
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$MODE" == "upgrade" ]]; then
  if [[ ! -d "$UPGRADE_DIR" ]]; then
    echo "Error: workspace '$UPGRADE_DIR' does not exist." >&2
    exit 1
  fi

  WORKSPACE_ABS="$(cd "$UPGRADE_DIR" && pwd)"
  if [[ "$MAIN_BRANCH_SET" == false ]]; then
    MAIN_BRANCH="$(detect_default_main_branch "$WORKSPACE_ABS")"
  fi

  run_upgrade_mode "$WORKSPACE_ABS" "$MAIN_BRANCH"
else
  if [[ "$MAIN_BRANCH_SET" == false ]]; then
    MAIN_BRANCH="main"
  fi

  run_fresh_setup_mode "$REPO_URL" "$TARGET_DIR" "$ENV_SOURCE" "$MAIN_BRANCH"
fi