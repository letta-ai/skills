# QEMU Alpine SSH Troubleshooting Guide

## Port Binding Failures

### Symptom
QEMU fails to start with errors like:
- `Could not set up host forwarding rule 'tcp::2222-:22'`
- `Address already in use`
- Silent failure when port forwarding doesn't work

### Diagnosis Steps
1. Check if the port is already in use:
   ```bash
   ss -tlnp | grep :2222
   # or
   netstat -tlnp | grep :2222
   # or check /proc/net/tcp for hex port (08AE = 2222)
   cat /proc/net/tcp | grep 08AE
   ```

2. Find processes using the port:
   ```bash
   lsof -i :2222
   fuser 2222/tcp
   ```

3. Check for orphaned QEMU processes:
   ```bash
   ps aux | grep qemu
   pgrep -la qemu
   ```

### Resolution
1. Kill existing processes using the port:
   ```bash
   fuser -k 2222/tcp
   # or
   pkill -f "qemu-system-x86_64"
   ```

2. Verify port is free before retrying:
   ```bash
   ! ss -tlnp | grep -q :2222 && echo "Port 2222 is free"
   ```

## SSH Connection Failures

### Symptom
- `Connection refused` when connecting via SSH
- `Permission denied` for root login
- Connection times out

### Diagnosis Steps
1. Verify SSH service is running in VM:
   ```
   rc-status | grep sshd
   # or
   ps aux | grep sshd
   ```

2. Check SSH configuration:
   ```
   grep PermitRootLogin /etc/ssh/sshd_config
   ```

3. Verify network interface is up:
   ```
   ip addr show
   ifconfig
   ```

### Resolution
1. Enable root login in sshd_config:
   ```bash
   sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
   # Verify the change took effect:
   grep "^PermitRootLogin" /etc/ssh/sshd_config
   ```

2. Restart SSH service:
   ```bash
   rc-service sshd restart
   ```

3. Ensure network is configured:
   ```bash
   ifconfig eth0 up
   udhcpc -i eth0
   ```

## Network Configuration Issues

### Symptom
- Cannot reach package repositories
- `apk add` fails with network errors
- No IP address assigned

### Diagnosis Steps
1. Check interface status:
   ```bash
   ip link show
   cat /sys/class/net/eth0/operstate
   ```

2. Check for DHCP lease:
   ```bash
   cat /var/lib/dhcp/dhclient.leases
   ```

### Resolution
1. Bring up interface and get DHCP:
   ```bash
   ifconfig eth0 up
   udhcpc -i eth0
   ```

2. Configure DNS if needed:
   ```bash
   echo "nameserver 8.8.8.8" > /etc/resolv.conf
   ```

3. Set up repositories:
   ```bash
   setup-apkrepos -1
   # or manually:
   echo "http://dl-cdn.alpinelinux.org/alpine/latest-stable/main" > /etc/apk/repositories
   ```

## QEMU Process Management

### Checking Running Instances
```bash
# List all QEMU processes
ps aux | grep -E "qemu-system" | grep -v grep

# Check specific port bindings
ss -tlnp | grep qemu
```

### Clean Shutdown
```bash
# Graceful shutdown via QEMU monitor (if accessible)
# Or terminate process
pkill -TERM -f "qemu-system-x86_64"
```

### Force Cleanup
```bash
# Kill all QEMU instances (use with caution)
pkill -9 -f "qemu-system-x86_64"

# Verify cleanup
sleep 1
pgrep qemu && echo "QEMU still running" || echo "All QEMU processes terminated"
```

## Common QEMU Command Issues

### Valid hostfwd Syntax Variations
All of these are valid and functionally equivalent:
```bash
-netdev user,id=net0,hostfwd=tcp::2222-:22
-netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22
-netdev user,id=net0,hostfwd=tcp:0.0.0.0:2222-:22
```

If one syntax fails, the issue is likely NOT the syntax but:
- Port already in use
- Missing dependencies (slirp library)
- Incorrect device configuration

### Memory and CPU Settings
For Alpine Linux, reasonable minimums:
```bash
-m 512M    # 512MB RAM (256MB may work but is tight)
-smp 1     # Single CPU is sufficient
```

## Verification Checklist

Before declaring setup complete, verify:

1. **QEMU is running**: `pgrep -la qemu`
2. **Port forwarding active**: `ss -tlnp | grep :2222`
3. **SSH service running in VM**: `rc-status | grep sshd`
4. **Root login enabled**: `grep "^PermitRootLogin yes" /etc/ssh/sshd_config`
5. **Network configured**: `ip addr show eth0` shows an IP
6. **SSH connection works**: `ssh -o ConnectTimeout=5 -p 2222 root@localhost`
