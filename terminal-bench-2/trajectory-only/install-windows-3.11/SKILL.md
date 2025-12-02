---
name: install-windows-3-11
description: Guidance for setting up legacy Windows VMs (like Windows 3.11) in QEMU with web-based remote access via noVNC. This skill should be used when tasks involve running legacy operating systems in virtual machines, configuring QEMU for older OS images, setting up VNC/noVNC web interfaces, or establishing programmatic keyboard control via QMP. Covers VM boot verification strategies, nginx reverse proxy configuration, and websockify setup.
---

# Install Windows 3.11

## Overview

This skill provides guidance for setting up legacy Windows virtual machines (particularly Windows 3.11) using QEMU with web-based remote access. The core challenge is not just launching the VM, but verifying it reaches a usable state and providing reliable remote access.

## Critical Success Criteria

Before marking any VM setup task complete, verify:

1. **The VM actually boots to the expected state** - Screenshots, VNC connection tests, or QMP display queries must confirm the desktop/expected state
2. **Web interface is fully functional** - End-to-end test through the browser, not just service status checks
3. **Keyboard/mouse input works** - Verify input actually affects VM state, not just that commands are accepted

## Approach

### Phase 1: Environment Assessment

Before installing anything:

1. Check QEMU version requirements in task description - note any specific version compatibility statements
2. Audit existing nginx configuration to understand current server blocks
3. Identify required ports and check for conflicts
4. Determine the disk image format and any special QEMU flags needed

### Phase 2: QEMU Configuration

When configuring QEMU for legacy operating systems:

1. **Memory allocation**: Windows 3.11 typically needs 16-64MB RAM. Check image documentation for requirements
2. **VNC setup**: Use `-vnc :1` for display 1 (port 5901). Consider `-vnc :1,share=ignore-disconnects` for stability
3. **QMP socket**: Enable with `-qmp unix:/path/to/qmp.sock,server,nowait` for programmatic control
4. **Display**: Legacy OS may need specific display settings like `-vga std` or `-vga cirrus`

Example QEMU command structure:
```bash
qemu-system-i386 \
  -m 32 \
  -hda /path/to/disk.img \
  -vnc :1 \
  -qmp unix:/tmp/qmp.sock,server,nowait \
  -vga std
```

### Phase 3: Web Access Stack

The typical stack for web-based VNC access:

```
Browser → nginx (port 80) → websockify → VNC server (QEMU)
```

**nginx configuration approach:**

1. First, examine `/etc/nginx/nginx.conf` for existing server blocks
2. Check if `sites-enabled` is included in the main config
3. Create configuration in the appropriate location to avoid conflicts
4. Test configuration with `nginx -t` before reloading

**websockify setup:**

```bash
websockify --web=/usr/share/novnc 6080 localhost:5901
```

Key parameters:
- `--web` serves noVNC static files
- Port 6080 is the WebSocket endpoint
- Target is the VNC port (5901 for display :1)

### Phase 4: Boot Verification

This is the most commonly failed step. Never assume boot succeeded based on process status alone.

**Verification strategies:**

1. **QMP display query**: Send `{"execute": "query-status"}` to check VM state
2. **VNC screenshot**: Use `vncsnapshot` or similar to capture current display
3. **QMP screendump**: `{"execute": "screendump", "arguments": {"filename": "/tmp/screen.ppm"}}`
4. **Connect via VNC client**: Actually view the display, not just test connectivity

**Boot timing considerations:**

- Legacy OS may need user interaction to complete boot (pressing Enter, clicking OK)
- Implement polling rather than fixed sleep delays
- Consider boot sequence: BIOS → DOS → Windows (multiple stages)

### Phase 5: Input Verification

After establishing QMP connection:

1. Send test keystrokes and verify display changes
2. Each QMP connection requires capability negotiation first:
   ```json
   {"execute": "qmp_capabilities"}
   ```
3. Then send keys:
   ```json
   {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "ret"}]}}
   ```

## Common Pitfalls

### QEMU Version Compatibility

If task specifies "compatible with QEMU X.Y.Z" but a different version is installed:
- Document the version mismatch
- Test if the image actually boots with the available version
- Report any compatibility issues observed

### nginx Configuration Conflicts

Symptoms: 502 Bad Gateway, connection refused

Prevention:
- Always audit existing nginx config before adding new server blocks
- Check for conflicting `listen` directives
- Verify upstream (websockify) is running before nginx tries to proxy to it

### Premature Task Completion

Never mark "VM booted successfully" without:
- Visual confirmation (screenshot or VNC connection)
- Or QMP state verification showing expected state

### QMP Socket Issues

- Stale socket files from previous runs cause connection failures
- Always clean up `/tmp/*.sock` or equivalent before starting QEMU
- Use `socat` or `nc` to test socket connectivity

### Boot Detection

Arbitrary `sleep` commands are unreliable. Instead:
- Poll QMP status at intervals
- Check for specific display content changes
- Implement timeout with failure handling

## Verification Checklist

Before declaring task complete:

- [ ] QEMU process is running (check with `pgrep` or `ps`)
- [ ] VNC port is listening (`ss -tlnp | grep 5901`)
- [ ] Websockify is running and connected to VNC
- [ ] nginx is proxying correctly (test with curl to WebSocket endpoint)
- [ ] **Visual confirmation of expected OS state** (screenshot or live view)
- [ ] Keyboard input affects VM display (send test key, verify change)
- [ ] Web interface loads in browser and connects to VM

## Resources

### references/

Refer to `references/qemu_legacy_os.md` for detailed QEMU flags and compatibility notes for legacy operating systems.

Refer to `references/novnc_nginx_config.md` for production-ready nginx configuration templates.
