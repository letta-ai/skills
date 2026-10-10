#!/usr/bin/env bash
# Diagnose and fix issues with bare repo worktree workspaces.
#
# Usage:
#   doctor.sh <workspace-dir>           # diagnose only
#   doctor.sh --fix <workspace-dir>     # diagnose and fix issues
#
# Checks for:
#   - Antigravity compatibility issues (repositoryformatversion, relative paths config)
#   - Relative vs absolute paths in .git files and gitdir files
#   - Missing .git pointer file at workspace root
#   - Orphaned worktree entries
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

usage() {
  cat <<'EOF'
Usage:
  doctor.sh <workspace-dir>           # diagnose only
  doctor.sh --fix <workspace-dir>     # diagnose and fix issues

Examples:
  doctor.sh ~/Code/alliance/ragtime
  doctor.sh --fix ~/Code/alliance/skills
EOF
}

# ── Diagnostic Functions ─────────────────────────────────────────────────────

check_repositoryformatversion() {
  local workspace="$1"
  local config="$workspace/.bare/config"
  local version

  version=$(git -C "$workspace" config --get core.repositoryformatversion 2>/dev/null || echo "0")

  if [[ "$version" == "1" ]]; then
    echo -e "${YELLOW}⚠${NC} repositoryformatversion = 1 (should be 0 for Antigravity compatibility)"
    return 1
  else
    echo -e "${GREEN}✓${NC} repositoryformatversion = 0"
    return 0
  fi
}

check_relative_paths_config() {
  local workspace="$1"
  local issues=0

  if git -C "$workspace" config --get worktree.useRelativePaths 2>/dev/null | grep -q "true"; then
    echo -e "${YELLOW}⚠${NC} worktree.useRelativePaths = true (causes Antigravity issues)"
    issues=$((issues + 1))
  else
    echo -e "${GREEN}✓${NC} worktree.useRelativePaths is not set or false"
  fi

  if git -C "$workspace" config --get extensions.relativeWorktrees 2>/dev/null | grep -q "true"; then
    echo -e "${YELLOW}⚠${NC} extensions.relativeWorktrees = true (causes Antigravity issues)"
    issues=$((issues + 1))
  else
    echo -e "${GREEN}✓${NC} extensions.relativeWorktrees is not set or false"
  fi

  if (( issues > 0 )); then
    return 1
  fi
  return 0
}

check_worktree_git_files() {
  local workspace="$1"
  local issues=0

  while IFS= read -r worktree_git; do
    local worktree_name parent_dir gitdir_path

    parent_dir=$(dirname "$worktree_git")
    worktree_name=$(basename "$parent_dir")
    gitdir_path=$(head -1 "$worktree_git" 2>/dev/null | sed 's/^gitdir: //' || true)

    if [[ -z "$gitdir_path" ]]; then
      echo -e "${RED}✗${NC} $worktree_name/.git has invalid format"
      issues=$((issues + 1))
      continue
    fi

    # Check if path is relative (doesn't start with /)
    if [[ "$gitdir_path" != /* ]]; then
      echo -e "${YELLOW}⚠${NC} $worktree_name/.git uses relative path: $gitdir_path"
      issues=$((issues + 1))
    fi
  done < <(find "$workspace" -mindepth 2 -maxdepth 2 -name ".git" -type f 2>/dev/null | sort)

  if (( issues == 0 )); then
    echo -e "${GREEN}✓${NC} All worktree .git files use absolute paths"
    return 0
  fi
  return 1
}

check_gitdir_files() {
  local workspace="$1"
  local issues=0

  if [[ ! -d "$workspace/.bare/worktrees" ]]; then
    echo -e "${CYAN}ℹ${NC} No worktrees directory found"
    return 0
  fi

  while IFS= read -r gitdir_file; do
    local worktree_name gitdir_path

    worktree_name=$(basename "$(dirname "$gitdir_file")")
    gitdir_path=$(head -1 "$gitdir_file" 2>/dev/null || true)

    if [[ -z "$gitdir_path" ]]; then
      echo -e "${RED}✗${NC} .bare/worktrees/$worktree_name/gitdir is empty"
      issues=$((issues + 1))
      continue
    fi

    # Check if path is relative (doesn't start with /)
    if [[ "$gitdir_path" != /* ]]; then
      echo -e "${YELLOW}⚠${NC} .bare/worktrees/$worktree_name/gitdir uses relative path: $gitdir_path"
      issues=$((issues + 1))
    fi
  done < <(find "$workspace/.bare/worktrees" -mindepth 2 -maxdepth 2 -name "gitdir" -type f 2>/dev/null | sort)

  if (( issues == 0 )); then
    echo -e "${GREEN}✓${NC} All gitdir files use absolute paths"
    return 0
  fi
  return 1
}

check_root_git_pointer() {
  local workspace="$1"
  local git_file="$workspace/.git"
  local gitdir_path

  if [[ ! -f "$git_file" ]]; then
    echo -e "${RED}✗${NC} Missing .git pointer file at workspace root"
    return 1
  fi

  gitdir_path=$(head -1 "$git_file" 2>/dev/null | sed 's/^gitdir: //' || true)

  if [[ -z "$gitdir_path" ]]; then
    echo -e "${RED}✗${NC} .git pointer file has invalid format"
    return 1
  fi

  echo -e "${GREEN}✓${NC} .git pointer file exists: $gitdir_path"
  return 0
}

# ── Fix Functions ────────────────────────────────────────────────────────────

fix_repositoryformatversion() {
  local workspace="$1"
  local config="$workspace/.bare/config"

  # Check if the file has the section with version = 1
  if grep -q "repositoryformatversion = 1" "$config" 2>/dev/null; then
    sed -i '' 's/repositoryformatversion = 1/repositoryformatversion = 0/' "$config"
    echo -e "  ${GREEN}Fixed${NC}: repositoryformatversion set to 0"
  fi
}

fix_relative_paths_config() {
  local workspace="$1"
  local config="$workspace/.bare/config"
  local fixed=0

  # Remove [worktree] section if it exists (version 0 repos shouldn't have it)
  if grep -qE "^\[worktree\]" "$config" 2>/dev/null; then
    # Remove the entire [worktree] section
    sed -i '' '/^\[worktree\]/,/^[^[:space:]]/{
      /^\[worktree\]/d
      /useRelativePaths/d
    }' "$config" 2>/dev/null || true
    echo -e "  ${GREEN}Fixed${NC}: Removed [worktree] section"
    fixed=$((fixed + 1))
  fi

  # Remove [extensions] section if it exists (version 0 repos shouldn't have it)
  if grep -qE "^\[extensions\]" "$config" 2>/dev/null; then
    # Remove the entire [extensions] section
    sed -i '' '/^\[extensions\]/,/^[^[:space:]]/{
      /^\[extensions\]/d
      /relativeWorktrees/d
      /relativeworktrees/d
    }' "$config" 2>/dev/null || true
    echo -e "  ${GREEN}Fixed${NC}: Removed [extensions] section"
    fixed=$((fixed + 1))
  fi

  echo "  Fixed $fixed config section(s)"
}

fix_worktree_git_files() {
  local workspace="$1"
  local fixed=0

  while IFS= read -r worktree_git; do
    local parent_dir worktree_name gitdir_path new_path

    parent_dir=$(dirname "$worktree_git")
    worktree_name=$(basename "$parent_dir")
    gitdir_path=$(head -1 "$worktree_git" 2>/dev/null | sed 's/^gitdir: //' || true)

    if [[ -z "$gitdir_path" ]]; then
      continue
    fi

    # If relative, convert to absolute
    if [[ "$gitdir_path" != /* ]]; then
      new_path="$workspace/.bare/worktrees/$worktree_name"
      echo "gitdir: $new_path" > "$worktree_git"
      echo -e "  ${GREEN}Fixed${NC}: $worktree_name/.git → absolute path"
      fixed=$((fixed + 1))
    fi
  done < <(find "$workspace" -mindepth 2 -maxdepth 2 -name ".git" -type f 2>/dev/null | sort)

  echo "  Fixed $fixed worktree .git file(s)"
}

fix_gitdir_files() {
  local workspace="$1"
  local fixed=0

  if [[ ! -d "$workspace/.bare/worktrees" ]]; then
    return 0
  fi

  while IFS= read -r gitdir_file; do
    local worktree_name gitdir_path new_path

    worktree_name=$(basename "$(dirname "$gitdir_file")")
    gitdir_path=$(head -1 "$gitdir_file" 2>/dev/null || true)

    if [[ -z "$gitdir_path" ]]; then
      continue
    fi

    # If relative, convert to absolute
    if [[ "$gitdir_path" != /* ]]; then
      # Find the worktree directory for this gitdir
      # It should be workspace/<worktree_name>
      new_path="$workspace/$worktree_name/.git"
      echo "$new_path" > "$gitdir_file"
      echo -e "  ${GREEN}Fixed${NC}: .bare/worktrees/$worktree_name/gitdir → absolute path"
      fixed=$((fixed + 1))
    fi
  done < <(find "$workspace/.bare/worktrees" -name "gitdir" -type f 2>/dev/null | sort)

  echo "  Fixed $fixed gitdir file(s)"
}

# ── Main ─────────────────────────────────────────────────────────────────────

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

FIX_MODE=false
WORKSPACE=""

if [[ "$1" == "--fix" ]]; then
  FIX_MODE=true
  WORKSPACE="${2:-}"
  if [[ -z "$WORKSPACE" ]]; then
    echo "Error: --fix requires a workspace path." >&2
    usage
    exit 1
  fi
  shift 2
else
  WORKSPACE="$1"
  shift
fi

if [[ ! -d "$WORKSPACE" ]]; then
  echo "Error: workspace '$WORKSPACE' does not exist." >&2
  exit 1
fi

# Resolve to absolute path
WORKSPACE_ABS=$(cd "$WORKSPACE" && pwd)

# Verify it's a bare repo workspace
if [[ ! -d "$WORKSPACE_ABS/.bare" ]]; then
  echo -e "${RED}Error${NC}: '$WORKSPACE_ABS' does not appear to be a bare repo workspace (.bare/ not found)." >&2
  exit 1
fi

echo ""
echo -e "${CYAN}Bare Repo Worktree Doctor${NC}"
echo "================================"
echo "Workspace: $WORKSPACE_ABS"
echo ""

if [[ "$FIX_MODE" == true ]]; then
  echo -e "${CYAN}Running diagnostics and fixes...${NC}"
  echo ""
else
  echo -e "${CYAN}Running diagnostics...${NC}"
  echo ""
fi

ISSUES=0

# Run diagnostics
check_root_git_pointer "$WORKSPACE_ABS" || ISSUES=$((ISSUES + 1))
check_repositoryformatversion "$WORKSPACE_ABS" || ISSUES=$((ISSUES + 1))
check_relative_paths_config "$WORKSPACE_ABS" || ISSUES=$((ISSUES + 1))
check_worktree_git_files "$WORKSPACE_ABS" || ISSUES=$((ISSUES + 1))
check_gitdir_files "$WORKSPACE_ABS" || ISSUES=$((ISSUES + 1))

echo ""

if [[ "$FIX_MODE" == true ]]; then
  echo -e "${CYAN}Applying fixes...${NC}"
  echo ""

  # IMPORTANT: Fix paths BEFORE config changes
  # Changing repositoryformatversion before fixing relative paths
  # can cause Git to prune worktrees
  fix_worktree_git_files "$WORKSPACE_ABS"
  fix_gitdir_files "$WORKSPACE_ABS"
  fix_repositoryformatversion "$WORKSPACE_ABS"
  fix_relative_paths_config "$WORKSPACE_ABS"

  echo ""

  # Verify git still works
  echo "Verifying git operations..."
  if git -C "$WORKSPACE_ABS" worktree list > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} git worktree list: OK"
  else
    echo -e "${RED}✗${NC} git worktree list: FAILED"
  fi
else
  if (( ISSUES > 0 )); then
    echo -e "${YELLOW}Found $ISSUES issue(s).${NC} Run with --fix to resolve."
  else
    echo -e "${GREEN}All checks passed!${NC}"
  fi
fi

echo ""
