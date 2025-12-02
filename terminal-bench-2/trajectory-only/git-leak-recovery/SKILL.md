---
name: git-leak-recovery
description: This skill provides guidance for recovering secrets or sensitive data from git repositories (including orphaned commits, reflog, and unreachable objects) and subsequently cleaning up those secrets from git history. It should be used when tasks involve finding leaked credentials, recovering data from git history, or ensuring secrets are completely removed from a repository's object store.
---

# Git Leak Recovery

## Overview

This skill covers two related but distinct operations: (1) recovering secrets or data that may exist in orphaned commits, reflog entries, or unreachable git objects, and (2) thoroughly cleaning repositories to ensure sensitive data cannot be recovered. Both operations require understanding git's internal storage mechanisms beyond standard high-level commands.

## Workflow Decision Tree

```
Is the goal to RECOVER or CLEAN UP a secret?
│
├─► RECOVER secret from git history
│   └─► Follow "Recovery Workflow" section
│
└─► CLEAN UP / ensure secret is removed
    └─► Follow "Cleanup Workflow" section
    └─► CRITICAL: Follow "Verification Workflow" - superficial checks are insufficient
```

## Recovery Workflow

### Step 1: Identify Potential Secret Locations

Search these locations in order of likelihood:

1. **Reflog** - Records all ref updates, even after commits are "deleted"
   ```bash
   git reflog --all
   git reflog show HEAD
   ```

2. **Unreachable/Orphaned commits** - Commits not referenced by any branch
   ```bash
   git fsck --unreachable --no-reflogs
   git fsck --lost-found  # Creates refs in .git/lost-found/
   ```

3. **Dangling objects** - Objects not referenced by anything
   ```bash
   git fsck --dangling
   ```

4. **Stashes** - Often forgotten storage location
   ```bash
   git stash list
   git stash show -p stash@{N}
   ```

5. **Git notes** - Metadata attached to commits
   ```bash
   git notes list
   ```

### Step 2: Examine Suspicious Objects

Once object hashes are identified:

```bash
# View commit content
git show <commit-hash>

# View any object type
git cat-file -p <object-hash>

# Determine object type
git cat-file -t <object-hash>
```

### Step 3: Extract and Save

After locating the secret:
```bash
# Save specific file from a commit
git show <commit>:<path/to/file> > recovered_file.txt

# Or checkout the entire commit temporarily
git checkout <commit> -- <path/to/file>
```

## Cleanup Workflow

### Step 1: Remove References

Remove all references that point to commits containing the secret:

```bash
# Delete reflog entries
git reflog expire --expire=now --all

# Remove backup refs (created by filter-branch, etc.)
rm -rf .git/refs/original/

# Remove stashes if they contain secrets
git stash drop stash@{N}

# Remove notes if applicable
git notes remove <commit>
```

### Step 2: Garbage Collection

Force immediate garbage collection:

```bash
git gc --prune=now --aggressive
```

### Step 3: Handle Pack Files

Pack files may retain objects even after gc:

```bash
# Repack aggressively
git repack -a -d -f --depth=250 --window=250

# Or for thorough cleanup, unpack and repack
mv .git/objects/pack/*.pack .
git unpack-objects < *.pack
rm *.pack
git gc --prune=now
```

## Verification Workflow

**CRITICAL**: Standard verification commands are often insufficient. Follow this thorough approach.

### Common Pitfall: Superficial Verification

These commands are **NOT sufficient** for security-sensitive cleanup:

```bash
# INSUFFICIENT: Only searches working directory, not git objects
grep -r "secret" .

# INSUFFICIENT: Greps fsck output (SHA hashes), not object content
git fsck --unreachable | grep "secret"
```

### Thorough Verification Steps

1. **Search all reachable commit content**:
   ```bash
   git log --all -p -S "secret_pattern" --
   ```

2. **Search unreachable objects content** (see `references/verification_commands.md`):
   ```bash
   # List all objects and search their content
   git rev-list --all --objects | cut -d' ' -f1 | while read obj; do
     git cat-file -p "$obj" 2>/dev/null | grep -l "secret_pattern" && echo "Found in: $obj"
   done
   ```

3. **Search loose objects directly**:
   ```bash
   find .git/objects -type f -name '[0-9a-f]*' | while read f; do
     dir=$(dirname "$f" | xargs basename)
     file=$(basename "$f")
     hash="${dir}${file}"
     git cat-file -p "$hash" 2>/dev/null | grep "secret_pattern" && echo "Found in loose object: $hash"
   done
   ```

4. **Search pack files**:
   ```bash
   for pack in .git/objects/pack/*.idx; do
     git verify-pack -v "$pack" 2>/dev/null | awk '{print $1}' | while read obj; do
       git cat-file -p "$obj" 2>/dev/null | grep "secret_pattern" && echo "Found in pack: $obj"
     done
   done
   ```

5. **Verify no backup refs exist**:
   ```bash
   ls -la .git/refs/original/ 2>/dev/null
   find .git -name "*.orig" -o -name "*_BACKUP_*"
   ```

6. **Check for any remaining refs**:
   ```bash
   git for-each-ref --format='%(refname)'
   ```

## Common Pitfalls

| Pitfall | Why It Happens | Solution |
|---------|----------------|----------|
| Grepping fsck output | `git fsck` outputs hashes, not content | Use `git cat-file -p` on each object |
| Missing pack files | Objects may be packed, not loose | Search both loose objects and pack files |
| Forgetting reflog | Reflog preserves "deleted" commits | `git reflog expire --expire=now --all` |
| Ignoring backup refs | filter-branch creates refs/original/ | Remove `.git/refs/original/` |
| Overlooking stashes | Stashes are separate ref namespace | Check `git stash list` |
| Missing git notes | Notes attach to commits separately | Check `git notes list` |
| Shallow verification | Working directory != git object store | Search object store directly |

## Resources

### references/

- `verification_commands.md` - Comprehensive verification scripts for thorough cleanup verification

These references provide ready-to-use command sequences for the verification workflow, which is the most error-prone part of git leak recovery tasks.
