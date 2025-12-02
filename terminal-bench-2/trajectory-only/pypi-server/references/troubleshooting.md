# PyPI Server Troubleshooting Guide

## Diagnostic Commands

### Check Python Environment

```bash
# Full environment check
python3 --version
python3 -c "import sys; print(sys.executable)"
pip3 --version
pip3 list | grep -E "(build|setuptools|wheel)"
```

### Check Network/Port Status

```bash
# Test if port is listening
python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
result = s.connect_ex(('localhost', 8080))
if result == 0:
    print('Port 8080 is OPEN (something is listening)')
else:
    print('Port 8080 is CLOSED (nothing listening)')
s.close()
"

# Alternative using curl
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ || echo "Connection failed"
```

### Find Processes Using Port

```bash
# Using lsof (if available)
lsof -i :8080 2>/dev/null

# Using fuser (if available)
fuser 8080/tcp 2>/dev/null

# Using /proc filesystem (always available on Linux)
for pid in /proc/[0-9]*/; do
    if [ -f "$pid/cmdline" ]; then
        cmdline=$(tr '\0' ' ' < "$pid/cmdline" 2>/dev/null)
        if echo "$cmdline" | grep -q "http.server.*8080"; then
            echo "PID $(basename $pid): $cmdline"
        fi
    fi
done
```

## Common Error Messages and Solutions

### "Address already in use"

**Full error**: `OSError: [Errno 98] Address already in use`

**Cause**: Another process is bound to the port.

**Solutions**:
1. Kill the existing process (see process management commands above)
2. Use a different port: `python3 -m http.server 8081`
3. Wait a moment if you just killed a server (socket may be in TIME_WAIT state)

### "No matching distribution found"

**Full error**: `ERROR: No matching distribution found for packagename==0.1.0`

**Diagnostic steps**:
```bash
# 1. Verify server is running
curl http://localhost:8080/

# 2. Check /simple/ endpoint exists
curl http://localhost:8080/simple/

# 3. Check package directory exists
curl http://localhost:8080/simple/packagename/

# 4. Verify package files are present
ls -la pypi-server/simple/packagename/
```

**Common causes**:
- Server started from wrong directory
- Package files not copied to correct location
- Directory structure incorrect (missing `/simple/` level)
- Package name case mismatch

### "ModuleNotFoundError: No module named 'cgi'"

**Full error**: `ModuleNotFoundError: No module named 'cgi'`

**Cause**: Running pypiserver on Python 3.13+ where `cgi` module was removed (PEP 594).

**Solution**: Use built-in `http.server` instead of pypiserver.

### "404 Not Found" for /simple/

**Diagnostic**:
```bash
# Check what the server's root directory contains
curl http://localhost:8080/

# If you see files but not 'simple/', server is running from wrong directory
```

**Solution**: Kill server and restart from correct directory that contains the `simple/` folder.

## Package Building Issues

### "No module named 'build'"

```bash
pip install build
```

### Build Succeeds but No Files in dist/

Check that you're running `python -m build` from the directory containing `pyproject.toml`.

### "Invalid version" Error

Ensure version string in `pyproject.toml` follows PEP 440:
- Valid: `0.1.0`, `1.0.0`, `2.0.0a1`
- Invalid: `v0.1.0`, `0.1`, `1.0.0.0.0`

## Directory Structure Reference

### Correct Server Structure

```
pypi-server/              <- Server should start HERE
├── simple/               <- This MUST exist
│   └── mypackage/        <- Package name (lowercase, hyphens ok)
│       ├── mypackage-0.1.0.tar.gz
│       └── mypackage-0.1.0-py3-none-any.whl
```

### Correct Package Source Structure (Flat Layout)

```
mypackage-source/
├── pyproject.toml
└── mypackage/
    ├── __init__.py
    └── other_module.py
```

### Correct Package Source Structure (Src Layout)

```
mypackage-source/
├── pyproject.toml
└── src/
    └── mypackage/
        ├── __init__.py
        └── other_module.py
```

## Verification Script

Run this script to verify your setup:

```bash
#!/bin/bash
PORT=8080
PACKAGE=mypackage
VERSION=0.1.0

echo "=== PyPI Server Verification ==="

# Check server
echo -n "Server on port $PORT: "
if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "RUNNING"
else
    echo "NOT RUNNING"
    exit 1
fi

# Check /simple/
echo -n "/simple/ endpoint: "
if curl -s http://localhost:$PORT/simple/ | grep -q "$PACKAGE"; then
    echo "OK (package listed)"
else
    echo "MISSING or package not listed"
fi

# Check package files
echo -n "Package files: "
FILES=$(curl -s http://localhost:$PORT/simple/$PACKAGE/)
if echo "$FILES" | grep -q ".tar.gz\|.whl"; then
    echo "FOUND"
else
    echo "NOT FOUND"
fi

# Test pip install (dry run)
echo -n "pip install test: "
pip install --dry-run --index-url http://localhost:$PORT/simple $PACKAGE==$VERSION 2>&1 | head -3
```

## Process Cleanup Script

When you need to ensure a clean state:

```bash
#!/bin/bash
PORT=8080

echo "Cleaning up processes on port $PORT..."

# Method 1: pkill
pkill -f "http.server $PORT" 2>/dev/null && echo "Killed via pkill"

# Method 2: /proc filesystem
for pid in /proc/[0-9]*/; do
    if [ -f "$pid/cmdline" ]; then
        cmdline=$(tr '\0' ' ' < "$pid/cmdline" 2>/dev/null)
        if echo "$cmdline" | grep -q "http.server.*$PORT"; then
            kill "$(basename $pid)" 2>/dev/null && echo "Killed PID $(basename $pid)"
        fi
    fi
done

# Verify
sleep 1
if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "WARNING: Port still in use"
else
    echo "Port $PORT is now free"
fi
```
