# Process Management for QEMU in Limited Environments

This document provides strategies for managing QEMU processes, especially in environments where standard tools may be unavailable.

## Understanding Process Hierarchy

### Backgrounded Processes

When a process is started with `&`:

```bash
qemu-system-x86_64 ... &
```

The process becomes a child of the shell initially, but if the shell exits, the process is reparented to PID 1 (init/systemd).

**Key Insight**: Using a tool to kill a shell session does NOT automatically kill backgrounded children. The QEMU process continues running independently.

### Process Groups

Processes started in the same shell share a process group ID (PGID). This can be used for group termination if tools are available:

```bash
kill -- -PGID  # Kill entire process group
```

## Process Discovery Methods

### Method 1: Standard Tools (When Available)

```bash
# Using ps
ps aux | grep qemu

# Using pgrep
pgrep -a qemu

# Find process using specific port
lsof -i :6665
ss -tlnp | grep 6665
netstat -tlnp | grep 6665
```

### Method 2: /proc Filesystem (Always Available on Linux)

When `ps`, `pgrep`, etc. are unavailable, use `/proc` directly:

#### Find All QEMU Processes

```bash
for pid in /proc/[0-9]*; do
  cmdline="$pid/cmdline"
  if [ -f "$cmdline" ] && grep -q qemu "$cmdline" 2>/dev/null; then
    echo "PID: $(basename $pid)"
    cat "$cmdline" | tr '\0' ' '
    echo
  fi
done
```

#### Find Process by Port

```bash
# Check /proc/net/tcp for port bindings
# Port 6665 in hex is 0x1A09
grep -i "1A09" /proc/net/tcp
```

#### Get Process Information

```bash
PID=12345

# Command line
cat /proc/$PID/cmdline | tr '\0' ' '

# Working directory
readlink /proc/$PID/cwd

# Executable path
readlink /proc/$PID/exe

# File descriptors (including sockets)
ls -la /proc/$PID/fd/
```

### Method 3: Using /proc/*/comm

The `comm` file contains the process name (first 15 characters):

```bash
for pid in /proc/[0-9]*; do
  if grep -q "qemu" "$pid/comm" 2>/dev/null; then
    echo "Found: $(basename $pid) - $(cat $pid/comm)"
  fi
done
```

## Process Termination Methods

### Method 1: kill Command

```bash
kill PID         # SIGTERM (graceful)
kill -9 PID      # SIGKILL (force)
kill -TERM PID   # Explicit SIGTERM
```

### Method 2: pkill/killall (When Available)

```bash
pkill qemu
pkill -f "qemu.*6665"  # Match command line pattern
killall qemu-system-x86_64
```

### Method 3: QEMU Monitor

If QEMU monitor is accessible:

```bash
# Via telnet to monitor port
echo "quit" | nc localhost MONITOR_PORT

# Or interactively
telnet localhost MONITOR_PORT
# Then type: quit
```

### Method 4: Process Signal via /proc

On some systems, writing to `/proc/PID/` is restricted, but reading allows discovery. Use `kill` command with discovered PID.

## Port Conflict Resolution

### Identifying Port Usage

```bash
# Multiple approaches - use what's available:

# netstat
netstat -tuln | grep PORT

# ss
ss -tuln | grep PORT

# lsof
lsof -i :PORT

# nc (netcat) probe
nc -z 127.0.0.1 PORT && echo "In use" || echo "Free"

# /proc/net/tcp (PORT must be converted to hex)
# Example: Port 6665 = 0x1A09
cat /proc/net/tcp | grep -i "1A09"
```

### Releasing a Port

1. Identify the process holding the port
2. Terminate that process
3. Wait briefly (1-2 seconds) for kernel to release the port
4. Verify port is free before restarting

```bash
# Example sequence
PID=$(lsof -t -i :6665)  # Get PID
kill $PID                 # Terminate
sleep 2                   # Wait for release
nc -z 127.0.0.1 6665 || echo "Port now free"
```

## Verification Strategies

### Verify Process is Running

```bash
# Check if PID exists
[ -d /proc/$PID ] && echo "Running" || echo "Not running"

# Check if process is still qemu
grep -q qemu /proc/$PID/cmdline 2>/dev/null && echo "QEMU running"
```

### Verify Correct Process Owns Port

```bash
# Get PID from port
PORT_PID=$(lsof -t -i :6665)

# Verify it's QEMU
cat /proc/$PORT_PID/cmdline | grep -q qemu && echo "QEMU owns port"
```

### Verify Process Responds

```bash
# Test telnet connection
timeout 3 bash -c "echo '' | nc 127.0.0.1 6665" && echo "Responding"
```

## Common Pitfalls

### Pitfall 1: Assuming Shell Kill Stops QEMU

**Wrong assumption**: Killing a shell/terminal session stops all processes started from it.

**Reality**: Backgrounded processes (`&`) continue running after shell death.

**Solution**: Explicitly track and terminate QEMU processes by PID.

### Pitfall 2: Not Waiting for Port Release

**Problem**: Starting new QEMU immediately after killing old one causes "Address in use" error.

**Solution**: Wait 1-2 seconds and verify port is free before restart.

### Pitfall 3: Multiple QEMU Instances

**Problem**: Multiple QEMU processes from failed attempts, unclear which is serving.

**Solution**: Before starting, enumerate all existing QEMU processes and terminate them cleanly.

### Pitfall 4: Relying on Unavailable Tools

**Problem**: Scripting with `ps`, `pkill`, etc. that aren't installed.

**Solution**: Check tool availability first; have `/proc` fallback ready.

## Best Practices

1. **Record PIDs**: When starting QEMU, capture and record its PID
   ```bash
   qemu-system-x86_64 ... &
   QEMU_PID=$!
   echo "QEMU started with PID: $QEMU_PID"
   ```

2. **Clean State Before Start**: Always check for and terminate existing instances before starting new ones

3. **Verify After Actions**: After starting or stopping, verify the expected state

4. **Document Running Processes**: Keep track of what's running for later management
