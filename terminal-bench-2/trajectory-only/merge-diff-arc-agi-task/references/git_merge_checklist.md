# Git Merge Checklist for ARC-AGI Tasks

## Pre-Merge Setup

- [ ] **Configure git identity**:
  ```bash
  git config user.email "agent@example.com"
  git config user.name "Agent"
  ```

- [ ] **Check current status**:
  ```bash
  git status
  git branch -a
  ```

- [ ] **Ensure clean working directory** (stash or commit changes if needed)

---

## Bundle Extraction

### Step 1: Identify Bundle Files

- [ ] List bundle files in the task directory
- [ ] Note the naming convention (often indicates branch names)

### Step 2: Extract Bundles

For each bundle file:

```bash
# Verify bundle is valid
git bundle verify <bundle-file>

# List refs in bundle
git bundle list-heads <bundle-file>

# Unbundle to get refs
git bundle unbundle <bundle-file>
```

### Step 3: Create Local Branches

```bash
# Create branch from extracted ref
git checkout -b <branch-name> <ref-from-bundle>

# Verify branch was created
git branch
```

---

## Pre-Merge Analysis

Before merging, understand what will be merged:

- [ ] **Read implementation on branch 1**:
  ```bash
  git checkout <branch1>
  cat <algorithm-file>
  ```

- [ ] **Read implementation on branch 2**:
  ```bash
  git checkout <branch2>
  cat <algorithm-file>
  ```

- [ ] **Document key differences**:
  - Different algorithms used?
  - Different dependencies?
  - Different edge case handling?
  - Different coding styles?

- [ ] **Identify potential conflicts**:
  ```bash
  git checkout <branch1>
  git diff <branch2> -- <files>
  ```

---

## Merge Execution

### Step 1: Choose Base Branch

- [ ] Decide which branch to merge into (typically the more complete one)
- [ ] Checkout the base branch:
  ```bash
  git checkout <base-branch>
  ```

### Step 2: Perform Merge

```bash
git merge <other-branch>
```

### Step 3: Handle Conflicts

If conflicts occur:

1. **List conflicted files**:
   ```bash
   git status
   ```

2. **For each conflict**:
   - [ ] Read both versions carefully
   - [ ] Understand what each version does
   - [ ] Decide on resolution strategy:
     - Keep one side
     - Combine both approaches
     - Write new implementation
   - [ ] Edit the file to resolve
   - [ ] Remove conflict markers

3. **Stage resolved files**:
   ```bash
   git add <resolved-file>
   ```

4. **Complete merge**:
   ```bash
   git commit -m "Merge <branch> with <base>: <resolution-description>"
   ```

---

## Post-Merge Verification

- [ ] **Verify merge completed**:
  ```bash
  git status
  git log --oneline -5
  ```

- [ ] **Test the merged code**:
  - Run any test scripts
  - Verify algorithm works on all examples

- [ ] **Check for untracked files** that should be committed

---

## Troubleshooting

### Merge Fails with "Please tell me who you are"

**Cause**: Git identity not configured

**Fix**:
```bash
git config user.email "agent@example.com"
git config user.name "Agent"
```

### Merge Aborted Due to Uncommitted Changes

**Cause**: Working directory not clean

**Fix**:
```bash
git stash
git merge <branch>
git stash pop  # if needed after merge
```

### Wrong Branch Merged

**Fix** (if not pushed):
```bash
git reset --hard HEAD~1  # Undo the merge commit
```

### Need to Redo Merge with Different Resolution

**Fix**:
```bash
git merge --abort  # If merge in progress
# or
git reset --hard HEAD~1  # If merge completed
```
