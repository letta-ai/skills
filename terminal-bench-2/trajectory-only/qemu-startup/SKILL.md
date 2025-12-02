---
name: qemu-startup
description: This skill provides guidance for starting QEMU virtual machines with proper serial console access, process management, and boot verification. It should be used when tasks involve launching QEMU VMs, configuring serial/telnet console access, or managing VM lifecycle. Covers common pitfalls around KVM availability, port conflicts, process hierarchy, and boot readiness detection.
---

# QEMU VM Startup

This skill guides the process of starting QEMU virtual machines with accessible serial consoles, typically via telnet. It addresses process management challenges, console configuration, and boot verification in environments where standard system tools may be limited.

## Pre-Flight Verification

Before attempting to start a QEMU VM, verify the following in order:

### 1. Tool Availability Check

Determine which tools are available in the environment:

```bash
# Check for QEMU
which qemu-system-x86_64 || which qemu-system-i386

# Check for process management tools (may not all be available)
which ps pkill pgrep ss netstat lsof
```

**Important**: Document which tools are NOT available early—this affects process management strategy later.

### 2. KVM Availability Check

Always verify KVM before using `-enable-kvm`:

```bash
# Check if KVM module is loaded
ls /dev/kvm 2>/dev/null && echo "KVM available" || echo "KVM not available"
```

**Decision Point**: If KVM is unavailable, omit `-enable-kvm` flag entirely. Do not attempt KVM first and fail—check proactively.

### 3. Port Availability Check

Before starting QEMU with telnet serial access, verify the target port is free:

```bash
# Try multiple approaches based on available tools
netstat -tuln | grep :PORT_NUMBER
ss -tuln | grep :PORT_NUMBER
nc -z 127.0.0.1 PORT_NUMBER && echo "Port in use" || echo "Port free"
```

### 4. Required Files Check

Verify all required files exist before starting:

```bash
# Check for ISO/disk images
ls -la /path/to/image.iso
ls -la /path/to/disk.qcow2
```

## QEMU Serial Console Configuration

Refer to `references/qemu_serial_console.md` for detailed option explanations.

### Recommended Configuration for Telnet Access

For serial console access via telnet:

```bash
qemu-system-x86_64 \
  -cdrom /path/to/image.iso \
  -m 512 \
  -serial telnet:127.0.0.1:PORT,server,nowait \
  -monitor none \
  -nographic \
  -no-reboot
```

**Critical Options**:
- `-serial telnet:...` — Redirects serial port to telnet server
- `-monitor none` — Disables QEMU monitor (prevents monitor prompt interference)
- `-nographic` — No graphical output, essential for headless operation
- `nowait` — QEMU starts immediately without waiting for telnet connection

### Common Configuration Mistakes

1. **Missing `-monitor none`**: Results in QEMU monitor prompt appearing instead of serial console
2. **Using `-nographic` without `-serial`**: May cause unexpected console behavior
3. **Forgetting `nowait`**: QEMU blocks waiting for connection before booting

## Process Management Strategy

Refer to `references/process_management.md` for detailed strategies.

### Understanding Process Hierarchy

When QEMU is started with `&` (backgrounded), it becomes independent of the parent shell:

```bash
qemu-system-x86_64 ... &
```

**Critical Understanding**: Killing the shell does NOT kill the backgrounded QEMU process. The QEMU process is reparented to init (PID 1).

### Tracking QEMU Processes

When standard tools (`ps`, `pkill`) are unavailable:

```bash
# Inspect /proc filesystem directly
ls /proc/*/cmdline 2>/dev/null | while read f; do
  if grep -l qemu "$f" 2>/dev/null; then
    echo "QEMU PID: $(echo $f | cut -d/ -f3)"
  fi
done

# Alternative: Check /proc for qemu in comm
for pid in /proc/[0-9]*; do
  if grep -q qemu "$pid/comm" 2>/dev/null; then
    echo "Found QEMU: $pid"
    cat "$pid/cmdline" | tr '\0' ' '
    echo
  fi
done
```

### Terminating QEMU Processes

Before starting a new QEMU instance on the same port:

1. Identify running QEMU processes (see above)
2. Terminate using available methods:
   ```bash
   # If kill is available
   kill PID

   # Via /proc if available
   echo "Terminate process: kill PID"
   ```
3. Wait briefly for port release
4. Verify port is free before restarting

## Boot Verification Approach

### Avoid Arbitrary Sleeps

Instead of `sleep 45`, implement polling-based verification:

```bash
# Poll for login prompt availability
for i in $(seq 1 60); do
  if echo "" | nc -w 1 127.0.0.1 PORT 2>/dev/null | grep -q "login"; then
    echo "VM ready after $i seconds"
    break
  fi
  sleep 1
done
```

### Connection Testing

To verify serial console is accessible:

```bash
# Test with timeout
timeout 5 telnet 127.0.0.1 PORT

# Or with nc
echo "" | nc -w 2 127.0.0.1 PORT
```

### Success Indicators

The VM is ready when:
- Telnet connection succeeds
- Login prompt is visible (e.g., "localhost login:")
- No QEMU monitor prompt (`(qemu)`) appears

## Verification Checklist

Before declaring success, verify:

1. **Process Identification**: Know which specific QEMU process is running
2. **Port Binding**: Confirm the correct process owns the port
3. **Console Access**: Successfully connect and see login prompt
4. **No Conflicts**: No "Address already in use" errors in logs

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| "Address already in use" | Previous QEMU still running | Find and terminate existing process |
| QEMU monitor prompt instead of login | Missing `-monitor none` | Add `-monitor none` to command |
| Connection refused | QEMU not started or crashed | Check QEMU process, review startup logs |
| Blank console | Boot not complete | Wait longer, check with polling |
| "KVM not available" | KVM module not loaded | Remove `-enable-kvm` flag |

## Final State Documentation

Always document the final state:
- PID of running QEMU process
- Port being used
- How to connect (e.g., `telnet 127.0.0.1 6665`)
- How to terminate the VM when done
