---
name: git-workflow-manager
description: Guide for managing git workflows including branching strategies, commit conventions, PR creation, and merge workflows. Use when working with git operations like creating commits, branches, pull requests, or when needing to follow repository workflow standards.
---

# Git Workflow Manager

## Overview

Provides standardized workflows for git operations including branching, committing, creating pull requests, and merging. Ensures consistent git practices across repositories and captures best practices for common git tasks.

## Core Workflows

### Branch Management

**Creating feature branches:**
1. Always create a feature branch for changes unless explicitly told to push to main
2. Use descriptive branch names that indicate the work being done
3. Common prefixes:
   - `fix/` - Bug fixes
   - `feature/` or `add/` - New features
   - `update/` - Updates to existing features
   - `refactor/` - Code refactoring
   - `docs/` - Documentation changes
   - `chore/` - Maintenance tasks

**Examples:**
- `fix/memory-concurrency-warning`
- `add/api-rate-limiting-skill`
- `update/pr-description-template`
- `docs/clarify-model-selection`

### Committing Changes

**Before committing:**
1. Run `git status` to see all untracked and modified files
2. Run `git diff` to see both staged and unstaged changes
3. Run `git log` (or `git log --oneline -5`) to see recent commit message style
4. Analyze changes to ensure no sensitive information is present

**Commit workflow:**
1. Add relevant files to staging: `git add <files>`
2. Create commit with proper formatting (see `references/commit-conventions.md`)
3. Verify commit succeeded: `git status`

**Important rules:**
- NEVER commit unless user explicitly asks
- NEVER update git config
- NEVER use interactive git commands (`git add -i`, `git rebase -i`)
- If pre-commit hooks modify files, amend the commit to include those changes

**Commit message format:**
```bash
git commit -m "$(cat <<'EOF'
<summary line describing the change>

🐾 Generated with [Letta Code](https://letta.com)

Co-Authored-By: Letta <noreply@letta.com>
EOF
)"
```

Use HEREDOC syntax as shown above to ensure proper multi-line formatting.

### Pull Request Creation

**Before creating PR:**
1. Check git status: `git status`
2. Check if branch tracks remote and is up to date
3. Review full commit history: `git log` and `git diff [base-branch]...HEAD`
4. Analyze ALL commits that will be included in the PR (not just the latest)

**PR creation workflow:**
1. Create branch if needed
2. Push to remote with `-u` flag if needed: `git push -u origin <branch-name>`
3. Create PR using GitHub CLI: `gh pr create`

**PR description format:**
```bash
gh pr create --title "PR title" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points>

## Test plan
[Checklist of TODOs for testing the pull request...]

<fun/memorable quote from the session>

Written by Cameron ◯ Letta Code
EOF
)"
```

See `references/pr-templates.md` for detailed PR description guidelines.

### Merging to Main

**Critical rule:** NEVER push directly to main unless explicitly told to.

**When to merge:**
- User explicitly says "merge to main", "push to main", or similar
- PR is approved and user requests merge

**When NOT to merge:**
- After creating a PR (wait for review)
- Unless specifically requested
- When user says "open a PR" (this means review is expected)

### Handling Git Hooks

If git hooks block a command:
1. Review the hook output to understand the issue
2. Determine if you can adjust your action to satisfy the hook
3. If not, ask the user to check their hooks configuration

Never try to bypass or disable hooks without permission.

## Common Scenarios

### Scenario: User asks to commit changes

```bash
# 1. Parallel: Review current state
git status
git diff
git log --oneline -5

# 2. Add files and commit
git add <relevant-files>
git commit -m "$(cat <<'EOF'
<commit message>

🐾 Generated with [Letta Code](https://letta.com)

Co-Authored-By: Letta <noreply@letta.com>
EOF
)"

# 3. Verify
git status
```

### Scenario: User asks to create a PR

```bash
# 1. Parallel: Review state and history
git status
git diff
git log
git diff main...HEAD

# 2. Push and create PR
git push -u origin <branch-name>
gh pr create --title "Title" --body "$(cat <<'EOF'
## Summary
- Change 1
- Change 2

## Test plan
- [ ] Test item 1
- [ ] Test item 2

"Quote from session"

Written by Cameron ◯ Letta Code
EOF
)"
```

### Scenario: User asks to merge to main

```bash
# Only after explicit permission
git checkout main
git merge <branch-name>
git push origin main
```

## Resources

### references/commit-conventions.md
Detailed commit message formatting guidelines and examples. Load when working on commits.

### references/pr-templates.md
PR description templates and best practices. Load when creating pull requests.

### scripts/git-check.py
Validation script for checking commit messages and branch names. Run before committing if validation is needed.

## Best Practices

**Always run in parallel:**
- When reviewing repository state, batch `git status`, `git diff`, and `git log` together
- Use multiple Bash tool calls in a single response for efficiency

**Communication:**
- Be explicit about what git operations you're performing
- Explain the purpose of commands that make changes
- Ask for permission when the workflow is ambiguous

**Error handling:**
- If a git command fails, read the error message carefully
- Common issues: merge conflicts, authentication, hooks
- Provide clear next steps or ask for guidance
