---
name: fix-git
description: This skill provides guidance for recovering lost Git commits, resolving detached HEAD states, and fixing common Git repository issues. Use this skill when encountering lost commits, accidental checkouts, orphaned branches, merge conflicts during recovery, or needing to restore repository state from reflog history.
---

# Git Recovery and Repair

This skill provides systematic approaches for diagnosing and recovering from common Git repository issues, particularly lost commits, detached HEAD states, and merge conflicts during recovery operations.

## When to Use This Skill

- Recovering lost commits after accidental operations (reset, checkout, rebase)
- Fixing detached HEAD states where commits were made outside any branch
- Restoring work after improper branch operations
- Resolving merge conflicts during recovery merges
- Diagnosing repository state to understand what went wrong

## Diagnostic Approach

### Initial Assessment

Before attempting any recovery, gather comprehensive repository state information:

1. **Check current state**: Run `git status`, `git branch -a`, and `git log --oneline -10` to understand the current position
2. **Examine reflog**: Run `git reflog` to see the complete history of HEAD movements, including operations that don't appear in normal git log
3. **Identify the problem**: Determine whether dealing with a detached HEAD, lost commits, or branch confusion

### Understanding Reflog Output

The reflog shows every HEAD position change with commit hashes and operation descriptions. Key patterns to identify:

- `checkout: moving from X to HEAD~N` indicates entering a detached HEAD state
- `commit:` entries in detached HEAD state represent orphaned commits at risk of garbage collection
- `checkout: moving from <hash> to <branch>` indicates leaving detached HEAD state (potentially abandoning commits)

## Recovery Strategies

### Lost Commits from Detached HEAD

When commits were made in a detached HEAD state and then lost:

1. Use `git reflog` to find the commit hash containing the lost work
2. Verify the commit contents with `git show <hash>` or `git log -1 -p <hash>`
3. Decide on recovery method:
   - **Merge**: Preserves full history, appropriate when commits should be part of branch history
   - **Cherry-pick**: Applies changes without merge commit, appropriate for selective recovery
   - **Create branch**: Run `git branch recovery-branch <hash>` to preserve commits for later decision

### Merge-Based Recovery

When merging recovered commits back into a branch:

```
git checkout <target-branch>
git merge <recovered-commit-hash> -m "Recover lost changes from <description>"
```

### Handling Merge Conflicts During Recovery

Merge conflicts during recovery require careful resolution:

1. **Identify all conflicting files**: Check `git status` for the complete list of unmerged files
2. **Understand both versions**: Before resolving, read the conflict markers to understand what each version contains
3. **Resolve with intention**: Determine which version should prevail based on the recovery goal
4. **Remove all conflict markers**: Ensure no `<<<<<<<`, `=======`, or `>>>>>>>` markers remain
5. **Verify resolution**: After editing, read the resolved file to confirm correctness

## Verification Protocol

### Post-Recovery Verification (Critical)

After any recovery operation, perform these verification steps:

1. **Check merge/operation status**: Run `git status` to confirm no unfinished operations
2. **Verify file contents**: Read recovered files to ensure no conflict markers remain and content is correct
3. **Review commit history**: Run `git log --oneline -5` to confirm the recovery commit appears correctly
4. **Check all affected files**: If multiple files were involved, verify each one merged cleanly
5. **Test functionality**: If applicable, run tests or manually verify the recovered code works

### Conflict Marker Detection

After resolving conflicts, search for residual markers:

```
grep -r "<<<<<<" <file>
grep -r "======" <file>
grep -r ">>>>>>" <file>
```

## Common Pitfalls

### Mistakes to Avoid

1. **Incomplete conflict resolution**: Leaving partial conflict markers (e.g., only removing `<<<<<<<` but not `>>>>>>>`)
2. **Ignoring secondary files**: When a commit touches multiple files, focusing only on the conflicting file and ignoring others
3. **No pre-recovery backup**: Not creating a safety branch before attempting recovery merges
4. **Assuming success without verification**: Not reading the final file content after conflict resolution
5. **Skipping reflog analysis**: Attempting recovery without fully understanding the sequence of operations that caused the issue

### User Communication

When helping users recover from Git issues:

1. **Explain the root cause**: Help users understand what operation caused the problem (e.g., "Checking out HEAD~1 put you in a detached HEAD state")
2. **Confirm conflict resolution choices**: When resolving conflicts with significant content differences, verify which version the user wants
3. **Educate on prevention**: Briefly explain how to avoid the issue in the future

## Safety Measures

### Before Recovery Operations

1. **Create a backup branch**: `git branch backup-before-recovery` preserves the current state
2. **Note current commit**: Record the current HEAD hash in case rollback is needed
3. **Check for uncommitted changes**: Ensure working directory is clean before recovery operations

### Recovery Rollback

If a recovery operation produces incorrect results:

```
git reset --hard <backup-commit-hash>
```

Or if a backup branch was created:

```
git reset --hard backup-before-recovery
```

## Reference

For detailed recovery scenarios and advanced techniques, see `references/git_recovery_guide.md`.
