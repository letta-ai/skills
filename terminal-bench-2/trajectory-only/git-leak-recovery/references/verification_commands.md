# Git Secret Cleanup Verification Commands

This reference provides comprehensive verification commands to ensure secrets are fully removed from a git repository's object store.

## Why Thorough Verification Matters

Git stores objects in multiple locations:
- **Loose objects**: Individual files in `.git/objects/XX/YYYY...`
- **Pack files**: Compressed archives in `.git/objects/pack/`
- **Refs**: References in `.git/refs/`, including backups in `.git/refs/original/`

Standard commands like `grep -r "pattern" .` only search the working directory, missing the git object store entirely.

## Complete Verification Script

Replace `SECRET_PATTERN` with the actual pattern to search for:

```bash
#!/bin/bash
SECRET_PATTERN="your_secret_pattern_here"
FOUND=0

echo "=== Verifying secret removal from git repository ==="
echo "Searching for: $SECRET_PATTERN"
echo ""

# 1. Search working directory (baseline check)
echo "--- Checking working directory ---"
if grep -r "$SECRET_PATTERN" . --exclude-dir=.git 2>/dev/null; then
    echo "WARNING: Pattern found in working directory"
    FOUND=1
fi

# 2. Search all reachable commit history
echo "--- Checking reachable commit history ---"
if git log --all -p -S "$SECRET_PATTERN" -- 2>/dev/null | head -20; then
    if [ -n "$(git log --all -p -S "$SECRET_PATTERN" -- 2>/dev/null)" ]; then
        echo "WARNING: Pattern found in reachable commits"
        FOUND=1
    fi
fi

# 3. Search reflog
echo "--- Checking reflog ---"
for ref in $(git reflog --all --format='%H' 2>/dev/null); do
    if git show "$ref" 2>/dev/null | grep -q "$SECRET_PATTERN"; then
        echo "WARNING: Pattern found in reflog entry: $ref"
        FOUND=1
    fi
done

# 4. Search unreachable objects
echo "--- Checking unreachable objects ---"
for obj in $(git fsck --unreachable --no-reflogs 2>/dev/null | awk '{print $3}'); do
    if git cat-file -p "$obj" 2>/dev/null | grep -q "$SECRET_PATTERN"; then
        echo "WARNING: Pattern found in unreachable object: $obj"
        FOUND=1
    fi
done

# 5. Search ALL loose objects (comprehensive)
echo "--- Checking all loose objects ---"
find .git/objects -type f -name '[0-9a-f]*' 2>/dev/null | while read f; do
    dir=$(dirname "$f" | xargs basename)
    file=$(basename "$f")
    hash="${dir}${file}"
    if git cat-file -p "$hash" 2>/dev/null | grep -q "$SECRET_PATTERN"; then
        echo "WARNING: Pattern found in loose object: $hash"
        FOUND=1
    fi
done

# 6. Search pack files
echo "--- Checking pack files ---"
for pack in .git/objects/pack/*.idx 2>/dev/null; do
    if [ -f "$pack" ]; then
        for obj in $(git verify-pack -v "$pack" 2>/dev/null | grep -E '^[0-9a-f]{40}' | awk '{print $1}'); do
            if git cat-file -p "$obj" 2>/dev/null | grep -q "$SECRET_PATTERN"; then
                echo "WARNING: Pattern found in packed object: $obj (pack: $pack)"
                FOUND=1
            fi
        done
    fi
done

# 7. Check for backup refs
echo "--- Checking for backup refs ---"
if [ -d ".git/refs/original" ]; then
    echo "WARNING: Backup refs directory exists: .git/refs/original/"
    ls -la .git/refs/original/
    FOUND=1
fi

# 8. Check for stashes
echo "--- Checking stashes ---"
if git stash list 2>/dev/null | grep -q .; then
    echo "WARNING: Stashes exist - verify they don't contain secrets"
    git stash list
    for i in $(seq 0 $(git stash list 2>/dev/null | wc -l)); do
        if git stash show -p "stash@{$i}" 2>/dev/null | grep -q "$SECRET_PATTERN"; then
            echo "WARNING: Pattern found in stash@{$i}"
            FOUND=1
        fi
    done
fi

# 9. Check git notes
echo "--- Checking git notes ---"
if git notes list 2>/dev/null | grep -q .; then
    echo "Git notes exist - checking content"
    for note in $(git notes list 2>/dev/null | awk '{print $1}'); do
        if git notes show "$note" 2>/dev/null | grep -q "$SECRET_PATTERN"; then
            echo "WARNING: Pattern found in git note: $note"
            FOUND=1
        fi
    done
fi

# 10. List all refs for manual review
echo "--- All refs in repository ---"
git for-each-ref --format='%(refname)'

echo ""
echo "=== Verification Complete ==="
if [ $FOUND -eq 0 ]; then
    echo "SUCCESS: Pattern not found in any git storage location"
else
    echo "FAILURE: Pattern still exists in repository - cleanup incomplete"
fi
```

## Quick Verification Commands

For rapid checks (not comprehensive but useful for iteration):

```bash
# Check if any reachable commits contain the pattern
git log --all -p -S "pattern" --

# Check unreachable objects (most common hiding spot after gc)
git fsck --unreachable --no-reflogs 2>/dev/null | awk '{print $3}' | xargs -I {} sh -c 'git cat-file -p {} 2>/dev/null | grep -l "pattern" && echo "Found in {}"'

# Count objects before and after cleanup (should decrease)
find .git/objects -type f | wc -l
```

## Understanding git fsck Output

The `git fsck` command outputs lines like:
```
unreachable commit abc123def456...
unreachable blob def789abc012...
dangling tree 456789012abc...
```

This output contains **object hashes**, not content. To search content:

```bash
# WRONG - searches fsck output format, not object content
git fsck --unreachable | grep "secret"

# RIGHT - searches actual object content
for obj in $(git fsck --unreachable 2>/dev/null | awk '{print $3}'); do
    git cat-file -p "$obj" 2>/dev/null | grep "secret"
done
```

## Object Types and How to Inspect Them

| Type | Description | Inspection Command |
|------|-------------|-------------------|
| blob | File content | `git cat-file -p <hash>` |
| tree | Directory listing | `git cat-file -p <hash>` |
| commit | Commit metadata + message | `git show <hash>` or `git cat-file -p <hash>` |
| tag | Annotated tag | `git cat-file -p <hash>` |

Secrets typically appear in **blobs** (file content) or **commit messages**.
