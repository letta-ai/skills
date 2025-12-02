# QEMU Legacy OS Configuration Reference

## Windows 3.11 Specific Settings

### Recommended QEMU Command

```bash
qemu-system-i386 \
  -m 32 \
  -hda /path/to/win311.img \
  -vnc :1,share=ignore-disconnects \
  -qmp unix:/tmp/qmp.sock,server,nowait \
  -vga std \
  -cpu 486 \
  -no-acpi \
  -no-hpet
```

### Parameter Explanations

| Parameter | Value | Reason |
|-----------|-------|--------|
| `-m` | 16-64 | Windows 3.11 max addressable memory; 32MB is safe default |
| `-cpu` | 486 | Emulate 486 processor for compatibility |
| `-vga` | std or cirrus | Standard VGA for legacy OS display |
| `-no-acpi` | - | ACPI not supported by Windows 3.11 |
| `-no-hpet` | - | High Precision Event Timer causes issues |

### Boot Sequence

Windows 3.11 typically boots in stages:

1. **BIOS POST** (1-3 seconds)
2. **DOS boot** (2-5 seconds) - May display "Starting MS-DOS..."
3. **WIN.COM execution** (3-10 seconds) - Windows logo appears
4. **Program Manager** (5-15 seconds) - Desktop is ready

Total boot time: 10-30 seconds depending on image and host performance.

### Known Issues

**Black screen after boot**: Try `-vga cirrus` instead of `-vga std`

**Keyboard not working**: Ensure `-enable-kvm` is NOT used (KVM can cause input issues with legacy OS)

**Mouse not detected**: Windows 3.11 may need mouse driver; keyboard navigation is more reliable

## QMP (QEMU Machine Protocol) Reference

### Connection Setup

```bash
# Using socat
socat - UNIX-CONNECT:/tmp/qmp.sock

# Using nc (netcat)
nc -U /tmp/qmp.sock
```

### Capability Negotiation

Every new connection must negotiate capabilities first:

```json
{"execute": "qmp_capabilities"}
```

Expected response:
```json
{"return": {}}
```

### Useful Commands

**Query VM status:**
```json
{"execute": "query-status"}
```

Response when running:
```json
{"return": {"status": "running", "singlestep": false, "running": true}}
```

**Take screenshot:**
```json
{"execute": "screendump", "arguments": {"filename": "/tmp/screen.ppm"}}
```

**Send keystrokes:**
```json
{"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "ret"}]}}
```

Common qcodes:
- `ret` - Enter key
- `esc` - Escape key
- `tab` - Tab key
- `spc` - Spacebar
- `a` through `z` - Letter keys
- `f1` through `f12` - Function keys

**Send key combination (e.g., Alt+F4):**
```json
{"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "alt"}, {"type": "qcode", "data": "f4"}]}}
```

### QMP Helper Script Pattern

For repeated key sending, create a helper script:

```bash
#!/bin/bash
# send-key.sh - Send a key to QEMU via QMP
SOCKET="/tmp/qmp.sock"
KEY="${1:-ret}"

{
  echo '{"execute": "qmp_capabilities"}'
  sleep 0.1
  echo "{\"execute\": \"send-key\", \"arguments\": {\"keys\": [{\"type\": \"qcode\", \"data\": \"$KEY\"}]}}"
  sleep 0.1
} | socat - UNIX-CONNECT:$SOCKET
```

Note: Each invocation creates a new connection, so capability negotiation is required each time.

## Version Compatibility Notes

### QEMU 5.x vs 8.x Differences

If an image is documented for QEMU 5.2.0 but QEMU 8.x is installed:

**Usually compatible:**
- Basic CPU emulation
- Standard VGA
- IDE disk emulation

**May differ:**
- Default machine type (`-M pc` may behave differently)
- Audio device defaults
- Network device defaults

**Mitigation:**
- Explicitly specify machine type: `-M pc-i440fx-5.2` (if available)
- Avoid relying on defaults; specify all devices explicitly

### Checking Available Machine Types

```bash
qemu-system-i386 -M help | grep pc
```

## Disk Image Formats

### Common Formats for Legacy OS

| Format | Command Flag | Notes |
|--------|--------------|-------|
| Raw | `-hda image.img` | Direct disk image, fastest |
| QCOW2 | `-hda image.qcow2` | Supports snapshots, compression |
| VDI | Convert first | VirtualBox format, convert with `qemu-img` |
| VMDK | `-hda image.vmdk` | VMware format, usually works directly |

### Converting Images

```bash
qemu-img convert -f vmdk -O qcow2 source.vmdk dest.qcow2
qemu-img convert -f vdi -O raw source.vdi dest.img
```
