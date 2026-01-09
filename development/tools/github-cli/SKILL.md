---
name: github-cli
description: GitHub CLI (gh) commands for PR workflows - checking CI status, viewing failed test logs, creating and updating pull requests. Use when working with GitHub PRs, checking why CI failed, or managing PR metadata.
---

# GitHub CLI for PR Workflows

Quick reference for `gh` commands focused on pull request workflows.

## Checking PR Status

```bash
# Check CI status for current branch's PR
gh pr checks

# Check specific PR
gh pr checks 123

# Watch until checks finish
gh pr checks --watch

# Only show required checks
gh pr checks --required

# JSON output for scripting
gh pr checks --json name,state,conclusion
```

Exit codes: `0` = passed, `1` = failed, `8` = pending

## Viewing Failed Test Logs

```bash
# View run summary (interactive picker if no ID)
gh run view

# View specific run with job details
gh run view <run-id> -v

# View logs for failed steps only (most useful)
gh run view <run-id> --log-failed

# View full log for a specific job
gh run view --job <job-id> --log

# Open in browser
gh run view <run-id> --web
```

To get job ID from a URL like `.../runs/123/job/456`, job ID is `456`.

## Creating PRs

```bash
# Interactive (prompts for title/body)
gh pr create

# With title and body
gh pr create --title "Fix bug" --body "Details here"

# Auto-fill from commit messages
gh pr create --fill

# Draft PR
gh pr create --draft

# With reviewers and labels
gh pr create -r reviewer1,reviewer2 -l bug,urgent

# Specify base branch
gh pr create --base develop
```

## Updating PRs

```bash
# Edit title/body
gh pr edit 123 --title "New title" --body "New body"

# Add/remove labels
gh pr edit 123 --add-label "bug" --remove-label "wip"

# Add/remove reviewers
gh pr edit 123 --add-reviewer alice --remove-reviewer bob

# Self-assign
gh pr edit 123 --add-assignee "@me"

# Change base branch
gh pr edit 123 --base main
```

## Other Useful Commands

```bash
# View PR details
gh pr view 123

# View PR in browser
gh pr view 123 --web

# List open PRs
gh pr list

# Checkout PR locally
gh pr checkout 123

# View PR comments
gh api repos/OWNER/REPO/pulls/123/comments

# Re-run failed jobs
gh run rerun <run-id> --failed
```

## Scripts

- `scripts/check-pr.sh` - Check PR status with optional watch mode
- `scripts/view-failed-logs.sh` - View failed logs for a run or job
