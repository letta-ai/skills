---
name: merge-to-main
description: Push current branch and merge to the default branch (with optional deletion of feature branch)
triggers:
  - "merge to main"
  - "push and merge"
  - "ship it"
  - "land this"
tools_required:
  - Bash
---

# Merge to Main

This skill handles the complete workflow of pushing the current branch and merging it to the default branch (main/master).

## When to Use

Use this skill when you want to:
- Push your current feature branch and merge it into the default branch
- Complete a feature and land it on main/master
- Ship changes that are ready for production

## Pre-flight Checks

Before merging, verify:
1. All changes are committed (no uncommitted changes)
2. Tests pass (if applicable)
3. The branch is up to date with the default branch

## Workflow

### Step 1: Detect Default Branch
```bash
DEFAULT_BRANCH=$(git remote show origin | grep "HEAD branch" | sed 's/.*: //')
echo "Default branch: $DEFAULT_BRANCH"
```
This auto-detects whether the repo uses `main`, `master`, or another default branch.

### Step 2: Verify Clean State
```bash
git status
```
Ensure there are no uncommitted changes.

### Step 3: Get Current Branch Name
```bash
FEATURE_BRANCH=$(git branch --show-current)
echo "Feature branch: $FEATURE_BRANCH"
```
Store this for later reference.

### Step 4: Push Current Branch
```bash
git push -u origin $(git branch --show-current)
```

### Step 5: Fetch and Update Default Branch
```bash
git fetch origin $DEFAULT_BRANCH
git checkout $DEFAULT_BRANCH
git pull origin $DEFAULT_BRANCH
```

### Step 6: Merge Feature Branch
```bash
git merge $FEATURE_BRANCH --no-ff -m "Merge $FEATURE_BRANCH into $DEFAULT_BRANCH"
```
Use `--no-ff` to preserve branch history.

### Step 7: Push Default Branch
```bash
git push origin $DEFAULT_BRANCH
```

### Step 8: Cleanup (Optional)
Ask user if they want to delete the feature branch:
```bash
git branch -d $FEATURE_BRANCH
git push origin --delete $FEATURE_BRANCH
```

## Error Handling

- **Merge conflicts**: Stop and inform the user. Do not force merge.
- **Push rejected**: Fetch latest and try rebase, or inform user of diverged history.
- **Protected branch**: Inform user that the default branch may require a PR instead.

## Notes

- This skill auto-detects the default branch (main, master, etc.) from the remote.
- For repositories requiring PRs, this skill should not be used - use the standard PR workflow instead.
- Always confirm with the user before deleting branches.
