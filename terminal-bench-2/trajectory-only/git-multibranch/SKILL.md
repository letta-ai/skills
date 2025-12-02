---
name: git-multibranch
description: Guidance for setting up Git-based multi-branch deployment systems with web servers. This skill applies when configuring Git repositories with post-receive hooks that deploy different branches to different directories, typically served by Nginx or Apache. Use for tasks involving SSH-accessible Git servers, branch-specific deployments, and web server configuration.
---

# Git Multi-Branch Deployment

## Overview

This skill provides guidance for configuring Git repositories that automatically deploy content from different branches to different web-accessible directories. The typical setup involves a bare Git repository with post-receive hooks that check out branch contents to specific deployment directories served by a web server.

## Core Components

A multi-branch deployment system requires four interconnected components:

1. **SSH Server** - Enables remote Git operations
2. **Bare Git Repository** - Receives pushes and triggers deployment hooks
3. **Post-Receive Hook** - Deploys branch contents to appropriate directories
4. **Web Server** - Serves deployed content from branch-specific directories

## Approach Strategy

### Phase 1: SSH Configuration

Before configuring Git, ensure SSH access is properly configured:

- Verify SSH service is running and accessible
- Check authentication settings: `PasswordAuthentication`, `PermitRootLogin`, and also `UsePAM`, `KbdInteractiveAuthentication`
- Create the Git user account with appropriate shell access
- Test SSH connectivity before proceeding to Git setup

**Critical Check**: After any SSH configuration changes, restart the SSH service and verify connectivity with a test login.

### Phase 2: Git Repository Setup

Create a bare repository that will receive pushes:

```bash
# Create as the git user or with proper ownership
git init --bare /path/to/repo.git
```

Key considerations:
- The repository must be owned by the Git user
- The repository starts empty - handle first-push scenarios in the hook
- Set appropriate permissions on the repository directory

### Phase 3: Deployment Directory Setup

Create and configure deployment directories before writing the hook:

```bash
mkdir -p /var/www/main /var/www/dev
chown git:git /var/www/main /var/www/dev
```

**Permission Verification**: The post-receive hook runs as the Git user. Verify the Git user has write permissions to all deployment directories before testing.

### Phase 4: Post-Receive Hook Implementation

The post-receive hook deploys branch contents on each push. See `references/post_receive_hook.md` for implementation details and edge case handling.

Key hook requirements:
- Parse branch name from stdin (format: `oldrev newrev refname`)
- Handle initial push when branches don't exist yet
- Deploy to correct directory based on branch name
- Handle the `refs/heads/` prefix in refnames

### Phase 5: Web Server Configuration

Configure the web server to serve content from deployment directories. Each branch maps to a specific location path or virtual host.

## Verification Strategy

### Test from Clean State

**Critical**: Always test from the exact state that evaluation will use:

1. Start with a fresh clone of an empty repository
2. Make initial commits locally
3. Push to the server
4. Verify deployment directories contain expected content

### Verification Commands

After each deployment phase, verify:

```bash
# Check SSH connectivity
ssh git@localhost 'echo connected'

# Verify repository permissions
ls -la /path/to/repo.git

# Check hook is executable
ls -la /path/to/repo.git/hooks/post-receive

# Verify deployment directory permissions
ls -la /var/www/

# Test web server response
curl -s http://localhost/main/
curl -s http://localhost/dev/
```

### Clean State Testing Protocol

After initial setup testing, reset to clean state before final verification:

1. Remove all content from deployment directories
2. Delete any test branches in the repository
3. Perform a fresh clone and push sequence
4. This ensures the setup handles first-push scenarios correctly

## Common Pitfalls

### SSH Configuration Incomplete

**Problem**: Changing `PasswordAuthentication` alone may not enable password auth.

**Solution**: Check all related settings: `UsePAM`, `KbdInteractiveAuthentication`, `ChallengeResponseAuthentication`. Restart SSH service after changes.

### Post-Receive Hook Edge Cases

**Problem**: Hook fails on first push when target branch doesn't exist.

**Solution**: The hook must handle both:
- First push to a new branch (branch doesn't exist yet)
- Subsequent pushes to existing branches

See `references/post_receive_hook.md` for handling strategies.

### Testing Pollutes Repository State

**Problem**: Test commits and pushes leave the repository in a non-empty state, making subsequent tests unrepresentative.

**Solution**:
- Test from a clean state matching evaluation conditions
- Avoid force-pushing as a workaround - this masks first-push issues
- Reset deployment directories and repository state between test iterations

### Git User Permission Issues

**Problem**: Post-receive hook runs as Git user but cannot write to deployment directories.

**Solution**:
- Verify ownership: `chown git:git /var/www/main /var/www/dev`
- Check parent directory permissions
- Test hook execution manually as the Git user

### Host Key Verification Overhead

**Problem**: Using both manual host key addition and `StrictHostKeyChecking=no` is redundant.

**Solution**: Choose one approach:
- Add host key to known_hosts once, then rely on it
- OR use `StrictHostKeyChecking=no` consistently (less secure but simpler for local testing)

### Deployment Methods

**Problem**: Unclear which method to use for deploying branch content.

**Options**:
- `git checkout -f` - Simple, overwrites working tree
- `git archive | tar` - Creates clean export, no .git files
- `git worktree` - Maintains multiple checkouts

Choose based on requirements. Document the rationale for the chosen approach.

## Edge Cases to Handle

1. **First push scenario**: When pushing to a branch that doesn't exist on the server yet
2. **Empty repository**: The very first push when no branches exist at all
3. **Branch deletion**: Decide whether to clean up deployment directories when branches are deleted
4. **Non-existent deployment directories**: Handle gracefully if directories don't exist during hook execution
5. **Concurrent pushes**: Consider race conditions if multiple pushes happen simultaneously

## Resources

### references/

- `post_receive_hook.md` - Detailed post-receive hook implementation with edge case handling
