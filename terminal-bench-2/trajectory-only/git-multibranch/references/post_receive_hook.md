# Post-Receive Hook Implementation

## Overview

The post-receive hook is executed on the server after a push completes. It receives information about what was pushed via stdin and can trigger deployment actions based on the branches updated.

## Input Format

The hook receives lines via stdin in the format:
```
<old-rev> <new-rev> <ref-name>
```

Example:
```
0000000000000000000000000000000000000000 abc123... refs/heads/main
```

- `old-rev`: Previous commit SHA (all zeros for new branch)
- `new-rev`: New commit SHA (all zeros for branch deletion)
- `ref-name`: Full reference name (e.g., `refs/heads/main`)

## Basic Hook Structure

```bash
#!/bin/bash

while read oldrev newrev refname; do
    branch=$(echo "$refname" | sed 's|refs/heads/||')

    case "$branch" in
        main)
            deploy_dir="/var/www/main"
            ;;
        dev)
            deploy_dir="/var/www/dev"
            ;;
        *)
            continue
            ;;
    esac

    # Deploy the branch content
    git --work-tree="$deploy_dir" checkout -f "$branch"
done
```

## Edge Case Handling

### First Push to Empty Repository

When the repository is completely empty (no branches exist), the first push creates the initial branch. The hook should handle this case where no prior commits exist.

**Detection**: `oldrev` is all zeros (40 zeros).

### Branch Deletion

When a branch is deleted, `newrev` is all zeros. Decide whether to:
- Leave deployed content in place
- Remove deployed content
- Log the deletion for manual handling

**Detection**: `newrev` is all zeros.

```bash
# Check for branch deletion
if [ "$newrev" = "0000000000000000000000000000000000000000" ]; then
    echo "Branch $branch was deleted"
    # Optionally: rm -rf "$deploy_dir"/*
    continue
fi
```

### Non-Existent Deployment Directory

If the deployment directory doesn't exist, `git checkout -f` will fail. Ensure directories exist:

```bash
if [ ! -d "$deploy_dir" ]; then
    mkdir -p "$deploy_dir"
fi
```

### Working Tree Already in Use

Using `git --work-tree` with the same directory for different branches can cause issues. Each branch should have its own dedicated deployment directory.

## Deployment Methods Comparison

### Method 1: git checkout -f

```bash
git --work-tree="$deploy_dir" checkout -f "$branch"
```

**Pros**: Simple, one command
**Cons**: Leaves .git references, may have issues with deleted files

### Method 2: git archive

```bash
git archive "$branch" | tar -x -C "$deploy_dir"
```

**Pros**: Clean export without .git files
**Cons**: Doesn't remove old files, need to clear directory first

### Method 3: Clean export with directory wipe

```bash
rm -rf "$deploy_dir"/*
git archive "$branch" | tar -x -C "$deploy_dir"
```

**Pros**: Ensures clean state
**Cons**: Brief period where directory is empty

## Debugging Tips

### Test Hook Manually

Run the hook manually to debug:

```bash
echo "oldrev newrev refs/heads/main" | sudo -u git /path/to/repo.git/hooks/post-receive
```

### Add Logging

Add logging to understand hook execution:

```bash
#!/bin/bash
exec >> /tmp/post-receive.log 2>&1
echo "=== $(date) ==="
echo "Running as user: $(whoami)"

while read oldrev newrev refname; do
    echo "Received: $oldrev $newrev $refname"
    # ... rest of hook
done
```

### Check Permissions

Verify the hook runs with correct permissions:

```bash
# Check hook is executable
ls -la /path/to/repo.git/hooks/post-receive

# Check ownership
stat /path/to/repo.git/hooks/post-receive

# Check deployment directory permissions
ls -la /var/www/
```

## Complete Example with Error Handling

```bash
#!/bin/bash

# Exit on any error
set -e

GIT_DIR="/path/to/repo.git"

while read oldrev newrev refname; do
    # Extract branch name
    branch="${refname#refs/heads/}"

    # Skip if not a branch (tags, etc.)
    if [ "$refname" = "$branch" ]; then
        continue
    fi

    # Skip branch deletions
    if [ "$newrev" = "0000000000000000000000000000000000000000" ]; then
        echo "Branch $branch deleted, skipping deployment"
        continue
    fi

    # Determine deployment directory
    case "$branch" in
        main)
            deploy_dir="/var/www/main"
            ;;
        dev)
            deploy_dir="/var/www/dev"
            ;;
        *)
            echo "Unknown branch $branch, skipping"
            continue
            ;;
    esac

    # Ensure deployment directory exists
    mkdir -p "$deploy_dir"

    # Deploy
    echo "Deploying $branch to $deploy_dir"
    git --work-tree="$deploy_dir" --git-dir="$GIT_DIR" checkout -f "$branch"

    echo "Deployment of $branch complete"
done
```

## Hook Installation

1. Create the hook file at `/path/to/repo.git/hooks/post-receive`
2. Make it executable: `chmod +x /path/to/repo.git/hooks/post-receive`
3. Ensure correct ownership: `chown git:git /path/to/repo.git/hooks/post-receive`
