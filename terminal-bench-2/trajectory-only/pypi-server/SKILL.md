---
name: pypi-server
description: Guidance for creating Python packages and serving them via a local PyPI server. This skill applies when tasks involve building Python packages (with pyproject.toml or setup.py), setting up local package repositories, or serving packages via HTTP for pip installation. Use when the goal is to create installable Python packages and make them available through a local index URL.
---

# PyPI Server Skill

This skill provides guidance for creating Python packages and serving them through a local PyPI server for installation via pip.

## When to Use This Skill

This skill applies to tasks that involve:
- Creating Python packages with custom modules
- Building distributable packages (.tar.gz, .whl files)
- Setting up a local PyPI-compatible server
- Making packages installable via `pip install --index-url`

## Environment Assessment (Critical First Step)

Before starting any work, assess the execution environment to avoid compatibility issues:

```bash
# Check Python version - critical for tool compatibility
python3 --version

# Check available package tools
which pip3 && pip3 --version
which uv 2>/dev/null  # Fast package manager alternative

# Check for process management tools
which pkill lsof fuser 2>/dev/null || echo "Limited process tools"
```

**Key compatibility consideration**: Python 3.13+ removed the `cgi` module, which breaks `pypiserver`. Plan for fallback approaches if using Python 3.13+.

## Approach Selection

### Option 1: Built-in HTTP Server (Recommended for Python 3.13+)

Use Python's built-in `http.server` module - no external dependencies, works across all Python versions.

**Directory structure required:**
```
server-root/
└── simple/
    └── packagename/
        ├── packagename-0.1.0.tar.gz
        └── packagename-0.1.0-py3-none-any.whl
```

**Server command:**
```bash
cd server-root && python3 -m http.server 8080
```

### Option 2: pypiserver (Python < 3.13 only)

More feature-rich but has Python version constraints.

```bash
pip install pypiserver
pypi-server run -p 8080 ./packages/
```

**Note**: The command is `pypi-server` (with hyphen), not `pypiserver`.

## Package Creation Workflow

### Step 1: Create Package Structure

```
packagename/
├── pyproject.toml
├── src/
│   └── packagename/
│       └── __init__.py
```

Or flat layout:
```
packagename/
├── pyproject.toml
└── packagename/
    └── __init__.py
```

### Step 2: Configure pyproject.toml

Minimal configuration:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "packagename"
version = "0.1.0"
description = "Package description"
requires-python = ">=3.8"
```

### Step 3: Build the Package

```bash
cd packagename
pip install build
python -m build
```

This creates `dist/packagename-0.1.0.tar.gz` and `dist/packagename-0.1.0-py3-none-any.whl`.

## Server Setup Workflow

### Step 1: Create Server Directory Structure

```bash
mkdir -p pypi-server/simple/packagename
cp packagename/dist/* pypi-server/simple/packagename/
```

### Step 2: Start the Server

**Important**: Track the working directory from which the server starts. The server will only serve files relative to its starting directory.

```bash
cd pypi-server && python3 -m http.server 8080 &
```

Record the PID for later cleanup:
```bash
echo $! > server.pid
```

### Step 3: Verify Server Accessibility

```bash
# Check root endpoint
curl -s http://localhost:8080/

# Check simple index (this is what pip uses)
curl -s http://localhost:8080/simple/

# Check package listing
curl -s http://localhost:8080/simple/packagename/
```

## Verification Strategy

### Test Package Installation

```bash
pip install --index-url http://localhost:8080/simple packagename==0.1.0
```

### Test Package Functionality

```python
import packagename
# Test the actual functionality
```

### Full Verification Checklist

1. Server responds on root endpoint (`/`)
2. Server responds on `/simple/` endpoint
3. Package files are listed at `/simple/packagename/`
4. `pip install` succeeds with explicit index URL
5. Installed package imports correctly
6. Package functionality works as expected

## Process Management

### Starting Background Servers

```bash
# Start with explicit working directory tracking
cd /path/to/server-root
python3 -m http.server 8080 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
```

### Checking Server Status

```bash
# Check if port is in use
python3 -c "import socket; s=socket.socket(); s.settimeout(1); result=s.connect_ex(('localhost', 8080)); print('Port in use' if result==0 else 'Port free'); s.close()"

# List processes on port (if tools available)
lsof -i :8080 2>/dev/null || fuser 8080/tcp 2>/dev/null
```

### Stopping Servers

```bash
# If PID is known
kill $SERVER_PID

# If PID unknown, find and kill
pkill -f "http.server 8080" 2>/dev/null

# Fallback: use /proc filesystem
for pid in /proc/[0-9]*; do
    if grep -q "http.server" "$pid/cmdline" 2>/dev/null; then
        kill "$(basename $pid)" 2>/dev/null
    fi
done
```

## Common Pitfalls and Solutions

### Pitfall 1: Server Running from Wrong Directory

**Symptom**: Server running but `/simple/` returns 404.

**Cause**: A previous server instance started from a different directory is still running.

**Solution**: Kill all HTTP server processes, verify port is free, then restart from the correct directory.

### Pitfall 2: Port Already in Use

**Symptom**: "Address already in use" error when starting server.

**Solution**: Find and kill the process using the port, or use a different port.

### Pitfall 3: pypiserver Fails on Python 3.13+

**Symptom**: Import error about missing `cgi` module.

**Solution**: Use the built-in `http.server` approach instead.

### Pitfall 4: pip Can't Find Package

**Symptom**: `pip install` fails with "No matching distribution found."

**Possible causes**:
- Incorrect directory structure (must be `/simple/packagename/`)
- Server not running or wrong port
- Package files not copied to server directory
- Version mismatch in install command

**Debug approach**:
```bash
# Verify server response includes package files
curl http://localhost:8080/simple/packagename/
```

### Pitfall 5: Package Installs but Import Fails

**Symptom**: `pip install` succeeds but `import packagename` fails.

**Cause**: Package structure issue - the importable name may differ from the package name.

**Solution**: Verify `__init__.py` exists and the package structure matches pyproject.toml configuration.

## Clean State Management

Before starting server operations, ensure a clean state:

1. Kill any existing servers on the target port
2. Verify port is free
3. Remove stale server directories if recreating
4. Start fresh server with explicit directory

This prevents confusion from orphaned processes or stale state.
