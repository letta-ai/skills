# Git Recovery Guide

This reference provides detailed scenarios and techniques for Git repository recovery.

## Understanding Git's Safety Net

Git maintains several mechanisms that enable recovery:

### Reflog

The reflog (reference log) records every change to HEAD and branch tips for at least 90 days by default. Even commits that are no longer reachable from any branch remain in the object database and can be found via reflog.

**Key reflog commands:**

```bash
# View HEAD reflog (most common)
git reflog

# View reflog for a specific branch
git reflog show <branch-name>

# View reflog with timestamps
git reflog --date=relative

# View reflog with full commit messages
git reflog --pretty=fuller
```

### Object Database

Git stores all objects (commits, trees, blobs) in `.git/objects/`. Even "deleted" commits persist until garbage collection runs, typically after 2 weeks for unreachable objects.

**Finding dangling commits:**

```bash
# List unreachable commits
git fsck --unreachable --no-reflogs

# Find lost commits
git fsck --lost-found
```

## Detailed Recovery Scenarios

### Scenario 1: Commits Made in Detached HEAD State

**Symptoms:**
- User ran `git checkout <hash>` or `git checkout HEAD~N`
- Made commits while in detached HEAD
- Switched to another branch, losing access to commits

**Diagnosis:**

```bash
# Look for the pattern in reflog
git reflog | grep -A5 "checkout: moving from"
```

Typical reflog pattern:
```
abc1234 HEAD@{0}: checkout: moving from abc1234 to main
def5678 HEAD@{1}: commit: Important changes
abc1234 HEAD@{2}: checkout: moving from main to HEAD~1
```

**Recovery:**

```bash
# Option 1: Create a branch at the lost commit
git branch recovered-work def5678

# Option 2: Merge into current branch
git merge def5678 -m "Recover work from detached HEAD"

# Option 3: Cherry-pick specific commits
git cherry-pick def5678
```

### Scenario 2: Accidental Hard Reset

**Symptoms:**
- User ran `git reset --hard HEAD~N` or `git reset --hard <hash>`
- Commits appear to be gone

**Diagnosis:**

```bash
git reflog | head -20
```

Typical pattern:
```
abc1234 HEAD@{0}: reset: moving to HEAD~3
def5678 HEAD@{1}: commit: Third commit
ghi9012 HEAD@{2}: commit: Second commit
```

**Recovery:**

```bash
# Reset back to before the reset
git reset --hard def5678
```

### Scenario 3: Deleted Branch with Unmerged Work

**Symptoms:**
- Branch was deleted with `git branch -D`
- Work was not merged

**Diagnosis:**

```bash
# Find the branch's last commit in reflog
git reflog | grep "checkout: moving from <branch-name>"
```

**Recovery:**

```bash
# Recreate the branch
git branch <branch-name> <commit-hash>
```

### Scenario 4: Botched Rebase

**Symptoms:**
- Interactive rebase went wrong
- Commits are missing or corrupted

**Diagnosis:**

```bash
# Find pre-rebase state
git reflog | grep "rebase"
```

Look for `rebase (start)` entry - the commit before it is the pre-rebase state.

**Recovery:**

```bash
# If rebase is still in progress
git rebase --abort

# If rebase completed but results are wrong
git reset --hard ORIG_HEAD

# Or find the pre-rebase commit in reflog
git reset --hard <pre-rebase-hash>
```

### Scenario 5: Lost Stash

**Symptoms:**
- Stash was dropped or cleared
- `git stash list` shows nothing

**Diagnosis:**

```bash
# Find dangling commits that might be stashes
git fsck --unreachable | grep commit

# Stashes have a characteristic message pattern
git log --oneline --all $(git fsck --unreachable | grep commit | cut -d' ' -f3) 2>/dev/null | grep -i "WIP on\|On "
```

**Recovery:**

```bash
# Once found, apply it
git stash apply <hash>
```

## Merge Conflict Resolution Patterns

### Understanding Conflict Markers

```
<<<<<<< HEAD
Current branch content
=======
Incoming content (from merge/rebase)
>>>>>>> branch-name-or-hash
```

### Resolution Strategies

**Keep current (ours):**
```bash
git checkout --ours <file>
git add <file>
```

**Keep incoming (theirs):**
```bash
git checkout --theirs <file>
git add <file>
```

**Manual merge:**
Edit the file to combine changes appropriately, then:
```bash
git add <file>
```

### Verifying Complete Resolution

Always verify no markers remain:

```bash
# Check for any remaining conflict markers
grep -rn "^<<<<<<< \|^=======$\|^>>>>>>> " <file>

# Or check all files in repo
git diff --check
```

## Advanced Techniques

### Recovering Specific File Version

To recover a file from a specific commit without checking out the entire commit:

```bash
git show <commit-hash>:<path/to/file> > recovered_file
```

Or restore it directly:

```bash
git checkout <commit-hash> -- <path/to/file>
```

### Finding Commits by Content

When the commit hash is unknown but content is remembered:

```bash
# Search commit messages
git log --all --oneline --grep="keyword"

# Search commit diffs
git log --all -S "code snippet" --oneline

# Search with regex
git log --all -G "pattern" --oneline
```

### Recovering from Corrupted Repository

If the repository itself is corrupted:

```bash
# Check repository integrity
git fsck --full

# If remote exists, re-clone and recover local-only work
git clone <remote-url> fresh-clone
cd fresh-clone
git remote add old ../corrupted-repo
git fetch old  # May recover some objects
```

## Prevention Strategies

### Before Risky Operations

```bash
# Create a backup branch
git branch backup-$(date +%Y%m%d)

# Or tag the current state
git tag backup-before-operation
```

### Configuration for Safety

```bash
# Extend reflog retention (default is 90 days)
git config gc.reflogExpire "180 days"
git config gc.reflogExpireUnreachable "180 days"

# Prevent accidental force pushes to important branches
git config --global receive.denyNonFastForwards true
```

### Aliases for Common Recovery Tasks

```bash
# Add to ~/.gitconfig
[alias]
    # Show recent reflog entries
    recent = reflog -20

    # Find lost commits
    lost = fsck --lost-found

    # Show what would be garbage collected
    dangling = fsck --unreachable
```
