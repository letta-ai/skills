# QEMU Serial Console Configuration Reference

This document provides detailed explanations of QEMU options for serial console configuration.

## Serial Port Options

### `-serial` Option

The `-serial` option redirects the virtual machine's serial port. Common configurations:

#### Telnet Server Mode

```bash
-serial telnet:HOST:PORT,server,nowait
```

- `HOST:PORT` — Address and port for telnet server (e.g., `127.0.0.1:6665`)
- `server` — QEMU acts as telnet server, waiting for connections
- `nowait` — Start VM immediately without waiting for client connection

**Without `nowait`**: QEMU blocks at startup until a telnet client connects. This is rarely desired for automated workflows.

#### Other Serial Options

```bash
-serial stdio        # Serial to standard I/O (foreground mode)
-serial pty          # Create a pseudo-terminal
-serial /dev/ttyS0   # Physical serial port
-serial none         # Disable serial port
```

## Display and Monitor Options

### `-nographic` Option

Disables all graphical output. Essential for headless/server operation.

**Behavior**: When used alone, `-nographic` redirects both the serial port AND the QEMU monitor to stdio. This can cause confusion when both appear interleaved.

### `-monitor` Option

Controls the QEMU monitor console:

```bash
-monitor none        # Disable monitor entirely
-monitor stdio       # Monitor on standard I/O
-monitor telnet:...  # Monitor via telnet
```

**Critical for telnet serial**: Use `-monitor none` when redirecting serial to telnet. Otherwise, the QEMU monitor prompt `(qemu)` may appear instead of or mixed with the serial console.

### `-display` Option

```bash
-display none        # No display (alternative to -nographic)
-display curses      # Text-mode display
-display vnc=:0      # VNC display
```

## Recommended Combinations

### Headless with Telnet Serial (Most Common)

```bash
qemu-system-x86_64 \
  -nographic \
  -serial telnet:127.0.0.1:6665,server,nowait \
  -monitor none
```

### Foreground Serial (For Testing)

```bash
qemu-system-x86_64 \
  -nographic \
  -serial stdio \
  -monitor none
```

Use foreground mode to test QEMU parameters before backgrounding.

### Separate Monitor and Serial

```bash
qemu-system-x86_64 \
  -serial telnet:127.0.0.1:6665,server,nowait \
  -monitor telnet:127.0.0.1:6666,server,nowait \
  -display none
```

## Memory and CPU Options

### `-m` Option

Specifies RAM size:

```bash
-m 512      # 512 MB
-m 1G       # 1 GB
-m 2048     # 2048 MB
```

### `-smp` Option

Specifies CPU count:

```bash
-smp 2      # 2 CPUs
-smp 4      # 4 CPUs
```

### `-enable-kvm` Option

Enables KVM hardware virtualization. Requires:
- Linux host
- KVM kernel module loaded (`/dev/kvm` exists)
- Appropriate permissions

**Always check availability before using**:
```bash
[ -e /dev/kvm ] && echo "KVM available"
```

## Boot Options

### `-cdrom` Option

Attach ISO image as CD-ROM:

```bash
-cdrom /path/to/image.iso
```

### `-boot` Option

Control boot order:

```bash
-boot d         # Boot from CD-ROM
-boot c         # Boot from hard disk
-boot order=dc  # Try CD-ROM, then hard disk
```

### `-no-reboot` Option

Exit QEMU instead of rebooting when guest requests reboot. Useful for installation scenarios.

## Networking Options

### User-Mode Networking (Default)

```bash
-net user       # Enable user-mode networking
-net nic        # Create network interface
```

### Port Forwarding

```bash
-net user,hostfwd=tcp::2222-:22  # Forward host 2222 to guest 22
```

## Common Option Combinations

### Alpine Linux Live Boot via Telnet

```bash
qemu-system-x86_64 \
  -cdrom alpine.iso \
  -m 512 \
  -nographic \
  -serial telnet:127.0.0.1:6665,server,nowait \
  -monitor none \
  -no-reboot
```

### Installation to Disk Image

```bash
qemu-system-x86_64 \
  -cdrom installer.iso \
  -hda disk.qcow2 \
  -m 1024 \
  -nographic \
  -serial telnet:127.0.0.1:6665,server,nowait \
  -monitor none \
  -boot d
```
