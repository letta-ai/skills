---
name: qemu-alpine-ssh
description: This skill provides guidance for setting up Alpine Linux virtual machines in QEMU with SSH access via port forwarding. It should be used when tasks involve running Alpine Linux in QEMU, configuring SSH access to VMs, setting up port forwarding for VM network access, or troubleshooting QEMU networking issues.
---

# QEMU Alpine SSH Setup

## Overview

This skill guides the setup of Alpine Linux virtual machines in QEMU with SSH access configured through port forwarding. The typical goal is to have a running Alpine VM accessible via SSH on a forwarded host port.

## Critical Pre-Flight Checks

Before starting QEMU, always perform these checks to avoid common failures:

### 1. Check for Port Conflicts

The most common cause of QEMU startup failures is a port already in use. Always check before starting:

```bash
# Check if target port is in use
ss -tlnp | grep :<port>
# or
lsof -i :<port>
```

If the port is in use, either:
- Kill the process using it: `fuser -k <port>/tcp`
- Choose a different port

### 2. Check for Orphaned QEMU Processes

Previous QEMU instances may still be running from failed attempts:

```bash
ps aux | grep qemu-system
pgrep -la qemu
```

Clean up any orphaned processes before starting a new instance:

```bash
pkill -f "qemu-system-x86_64" || true
sleep 1
# Verify cleanup
pgrep qemu && echo "WARNING: QEMU still running" || echo "Clean"
```

### 3. Verify Required Files

Ensure ISO/disk images exist and are accessible before attempting to boot.

## Recommended Approach

### Phase 1: Start QEMU with Port Forwarding

Start QEMU with user-mode networking and port forwarding:

```bash
qemu-system-x86_64 \
  -m 512M \
  -cdrom alpine.iso \
  -boot d \
  -netdev user,id=net0,hostfwd=tcp::<host_port>-:22 \
  -device virtio-net-pci,netdev=net0 \
  -nographic
```

Key parameters:
- `-m 512M`: Allocate sufficient memory (256MB minimum, 512MB recommended)
- `-netdev user,id=net0,hostfwd=tcp::<port>-:22`: User-mode networking with port forwarding
- `-nographic`: Console-only mode for scripted interaction

### Phase 2: Configure the VM

After VM boots, perform configuration in this order:

1. **Set root password**:
   ```
   passwd
   ```

2. **Configure networking inside VM**:
   ```bash
   ifconfig eth0 up
   udhcpc -i eth0
   ```

3. **Set up package repositories**:
   ```bash
   setup-apkrepos -1
   # or manually configure /etc/apk/repositories
   ```

4. **Install SSH server**:
   ```bash
   apk update
   apk add openssh
   ```

5. **Configure SSH for root login**:
   ```bash
   sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
   # IMPORTANT: Verify the change
   grep "^PermitRootLogin" /etc/ssh/sshd_config
   ```

6. **Start SSH service**:
   ```bash
   rc-update add sshd
   rc-service sshd start
   ```

### Phase 3: Verify Setup

After configuration, verify each component:

1. **SSH service running**: `rc-status | grep sshd`
2. **Port forwarding working**: From host, `ss -tlnp | grep :<host_port>`
3. **SSH connection**: `ssh -o ConnectTimeout=5 -p <host_port> root@localhost`

## Common Pitfalls

### Port Binding Failures

**Symptom**: QEMU fails to start or port forwarding doesn't work.

**Common mistake**: Trying different hostfwd syntax variations when the syntax is correct but the port is in use.

**Correct approach**: Always check port availability first. All of these syntaxes are valid:
- `hostfwd=tcp::<port>-:22`
- `hostfwd=tcp:127.0.0.1:<port>-:22`
- `hostfwd=tcp:0.0.0.0:<port>-:22`

If one fails, the issue is usually NOT the syntax.

### SSH Connection Refused

**Symptom**: Cannot connect via SSH even though VM appears to be running.

**Check in order**:
1. Is sshd running in VM?
2. Is `PermitRootLogin yes` set in sshd_config?
3. Was sshd restarted after config change?
4. Is the network interface up with an IP?

### Network Not Working in VM

**Symptom**: Cannot install packages, DNS fails.

**Resolution**:
1. Bring up interface: `ifconfig eth0 up`
2. Get DHCP lease: `udhcpc -i eth0`
3. If DNS fails: `echo "nameserver 8.8.8.8" > /etc/resolv.conf`

## Verification Strategies

### Incremental Verification

Verify each step before proceeding to the next. Do not assume success.

After running commands that modify configuration:
- Use `grep` or `cat` to verify changes took effect
- Check service status after starting services
- Test connectivity at each stage

### Final Verification Checklist

Before declaring the task complete, verify ALL of:

- [ ] QEMU process is running: `pgrep -la qemu`
- [ ] Host port is listening: `ss -tlnp | grep :<port>`
- [ ] SSH service running in VM: `rc-status | grep sshd`
- [ ] Root login enabled: config shows `PermitRootLogin yes`
- [ ] VM has network: `ip addr` shows IP on eth0
- [ ] SSH connection succeeds from host

## Debugging Failed States

When things fail, diagnose systematically rather than trying random variations:

1. **Identify the failure point**: Which specific step failed?
2. **Check prerequisites**: Are all prerequisites for that step satisfied?
3. **Examine error messages**: What exactly does the error say?
4. **Check resource conflicts**: Ports, processes, file locks
5. **Verify intermediate state**: Did previous steps actually succeed?

For detailed troubleshooting steps, consult `references/troubleshooting.md`.

## Resources

### references/

- `troubleshooting.md`: Detailed diagnosis and resolution steps for common issues including port conflicts, SSH failures, and network configuration problems.
