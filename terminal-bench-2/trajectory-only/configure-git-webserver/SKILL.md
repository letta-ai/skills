---
name: configure-git-webserver
description: Guidance for setting up Git-based web deployment systems where pushing to a Git repository automatically deploys content to a web server. This skill should be used when tasks involve configuring bare Git repositories with post-receive hooks for automated web deployment, setting up lightweight web servers to serve deployed content, or creating Git-push-to-deploy workflows. Covers service persistence, permission management, and verification strategies.
---

# Git Web Server Deployment Configuration

This skill provides guidance for configuring Git-based web deployment systems where content is automatically deployed to a web server when pushed to a Git repository.

## Task Pattern Recognition

This skill applies to tasks involving:
- Setting up bare Git repositories for deployment
- Configuring post-receive hooks for automated deployment
- Running web servers to serve deployed content
- Creating push-to-deploy workflows (e.g., `git push` triggers deployment)
- SSH-based remote Git access configuration

## Pre-Implementation Checklist

Before starting implementation, verify the environment:

1. **Check available tools and permissions**
   - Determine if `sudo` is available: `command -v sudo`
   - Check available web servers: `command -v nginx`, `command -v python3`
   - Verify git is installed: `git --version`
   - Check current user context: `whoami`, `id`

2. **Configure Git identity proactively**
   - Set user.name and user.email before any Git operations
   - Prevents errors during testing phase: `git config --global user.name "Deploy" && git config --global user.email "deploy@localhost"`

3. **Identify port availability**
   - Check if intended port is in use: `lsof -i :PORT` or `ss -tlnp | grep PORT`
   - Have fallback ports ready (8080, 8000, 3000)

## Implementation Approach

### Step 1: Create Bare Git Repository

```bash
# Create the bare repository directory
mkdir -p /git/server
cd /git/server
git init --bare
```

A bare repository has no working directory and is designed for remote operations.

### Step 2: Create Web Directory

```bash
# Create web root with appropriate permissions
mkdir -p /var/www/html
chmod 755 /var/www/html
```

Document why this directory was chosen (standard location, permissions, etc.).

### Step 3: Create Post-Receive Hook

The post-receive hook triggers after each push. Critical considerations:

```bash
#!/bin/bash
# /git/server/hooks/post-receive

# Handle multiple branch naming conventions
while read oldrev newrev refname; do
    branch=$(echo $refname | sed 's/refs\/heads\///')

    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        GIT_WORK_TREE=/var/www/html git checkout -f $branch
        echo "Deployed $branch to /var/www/html"
    fi
done
```

Make executable: `chmod +x /git/server/hooks/post-receive`

**Hook considerations:**
- Handle both `main` and `master` branch names
- Use force checkout (`-f`) to overwrite local changes
- Log deployment actions for debugging
- Consider adding error handling and notifications

### Step 4: Web Server Setup

#### Option A: Python Simple Server (Development/Testing)

```bash
cd /var/www/html
python3 -m http.server 8080 &
```

**Limitations:** No auto-restart, no production features, terminates with session.

#### Option B: Production-Ready Setup

For persistent service, create a systemd service or use a process manager. See `references/deployment_checklist.md` for service configuration patterns.

### Step 5: Verification Strategy

**Test the actual use case, not just components:**

1. **Local clone test (basic validation):**
   ```bash
   git clone /git/server /tmp/test-clone
   cd /tmp/test-clone
   echo "test" > index.html
   git add . && git commit -m "test" && git push origin main
   ```

2. **Remote SSH test (full validation):**
   ```bash
   git clone user@server:/git/server /tmp/remote-test
   ```
   This validates the SSH access path that users will actually use.

3. **Web server verification:**
   ```bash
   curl http://localhost:8080/index.html
   ```

4. **Cleanup test artifacts:**
   ```bash
   rm -rf /tmp/test-clone /tmp/remote-test
   ```

## Common Pitfalls and Solutions

### 1. Service Persistence

**Problem:** Background processes (`command &`) terminate when session ends.

**Solution:**
- Use systemd services, supervisord, or similar process managers
- At minimum, document that the server requires manual restart
- Consider using `nohup` for slightly better persistence: `nohup python3 -m http.server 8080 &`

### 2. Permission Issues

**Problem:** Different users pushing may not have write access to web directory.

**Solutions:**
- Ensure web directory is writable by git user
- Consider group permissions: `chgrp -R webgroup /var/www/html && chmod -R g+w /var/www/html`
- Verify SSH user matches repository permissions

### 3. Missing Git Configuration

**Problem:** `git commit` fails during testing without user.name/user.email.

**Solution:** Configure Git identity at the start of implementation, not when errors occur.

### 4. Port Conflicts

**Problem:** Web server fails to start because port is already in use.

**Solution:**
- Check port availability before starting server
- Use alternative ports if needed
- Kill existing processes if appropriate: `fuser -k 8080/tcp`

### 5. Testing Wrong Workflow

**Problem:** Testing with local paths doesn't validate SSH-based remote access.

**Solution:** Test both local (`/git/server`) and remote (`user@server:/git/server`) access patterns when SSH is part of the requirements.

### 6. Hook Not Executing

**Problem:** Post-receive hook doesn't run after push.

**Checklist:**
- Hook is executable: `chmod +x hooks/post-receive`
- Hook has correct shebang: `#!/bin/bash`
- No syntax errors: `bash -n hooks/post-receive`
- Check hook output in push response

### 7. Force Checkout Overwrites

**Problem:** `git checkout -f` overwrites files modified directly in web directory.

**Consideration:** This is usually desired behavior for deployment, but document it for users who may manually edit deployed files.

## Verification Checklist

Before marking task complete, verify:

- [ ] Bare repository initialized and accessible
- [ ] Post-receive hook is executable and tested
- [ ] Web directory exists with correct permissions
- [ ] Web server is running and serving content
- [ ] End-to-end push-to-deploy workflow tested
- [ ] Service persistence documented or configured
- [ ] Test artifacts cleaned up
- [ ] Remote access path validated (if SSH-based)

## Environment-Specific Considerations

- **Container environments:** Services may need different persistence strategies
- **Restricted environments:** `sudo` may not be available; adapt paths accordingly
- **Multi-user systems:** Consider shared access and permission inheritance
