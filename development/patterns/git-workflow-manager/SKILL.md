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
1. Always create a feature branch for changes unless explicitly told to work on main
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
- `add/api-rate-limiting-feature`
- `update/documentation-clarity`
- `docs/clarify-installation-steps`

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
- NEVER update git config without permission
- NEVER use interactive git commands (`git add -i`, `git rebase -i`)
- If pre-commit hooks modify files, amend the commit to include those changes
- Always check for repository-specific commit conventions first

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

Check the repository for existing PR templates (`.github/PULL_REQUEST_TEMPLATE.md`) or recent PRs to match the style. If no template exists, use a clear structure like:

```markdown
## Summary
<Brief description of changes>

## Changes
- Change 1
- Change 2
- Change 3

## Testing
<How the changes were tested>
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

### Repository Convention Discovery

**Always check repository conventions first:**

1. Look for contribution guidelines:
   - `CONTRIBUTING.md`
   - `DEVELOPERS.md`
   - `README.md` (often has contribution section)

2. Check for commit message conventions:
   - Look at recent commits: `git log --oneline -10`
   - Check for Conventional Commits usage
   - Note any patterns in commit format

3. Check for PR templates:
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - Recent PRs: `gh pr list --limit 5`

4. Look for automated checks:
   - `.github/workflows/` - CI/CD requirements
   - Pre-commit hooks
   - Commit message linters

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

# 2. Add files and commit (use repository's commit format)
git add <relevant-files>
git commit -m "Your commit message following repo conventions"

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

# 2. Check for existing PRs and templates
gh pr list --limit 5
cat .github/PULL_REQUEST_TEMPLATE.md  # if exists

# 3. Push and create PR
git push -u origin <branch-name>
gh pr create --title "Title" --body "Description following repo conventions"
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
Common commit message formatting guidelines including Conventional Commits. Load when working on commits.

### references/pr-templates.md
Common PR description patterns and best practices. Load when creating pull requests.

### scripts/git-check.py
Validation script for checking commit messages and branch names against common conventions. Run before committing if validation is needed.

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

**Adapt to repository:**
- Every repository has its own conventions
- Always check existing patterns before following defaults
- When in doubt, ask the user about preferences
