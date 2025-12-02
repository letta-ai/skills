# noVNC and nginx Configuration Reference

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│    nginx    │────▶│ websockify  │────▶│  QEMU VNC   │
│  (port 80)  │     │  (reverse   │     │ (port 6080) │     │ (port 5901) │
│             │     │   proxy)    │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   noVNC     │
                    │  (static    │
                    │   files)    │
                    └─────────────┘
```

## Pre-Configuration Checklist

Before configuring nginx:

1. **Audit existing configuration:**
   ```bash
   # Check main config for server blocks
   grep -n "server {" /etc/nginx/nginx.conf

   # Check if sites-enabled is included
   grep -n "include.*sites-enabled" /etc/nginx/nginx.conf

   # List existing site configs
   ls -la /etc/nginx/sites-enabled/
   ```

2. **Check for port conflicts:**
   ```bash
   ss -tlnp | grep -E ':80|:6080|:5901'
   ```

3. **Locate noVNC files:**
   ```bash
   # Common locations
   ls /usr/share/novnc/
   ls /usr/share/noVNC/
   dpkg -L novnc 2>/dev/null | head -20
   ```

## websockify Setup

### Basic Command

```bash
websockify --web=/usr/share/novnc 6080 localhost:5901
```

### With Logging

```bash
websockify --web=/usr/share/novnc 6080 localhost:5901 \
  --log-file=/var/log/websockify.log \
  -v
```

### As Background Process

```bash
nohup websockify --web=/usr/share/novnc 6080 localhost:5901 > /var/log/websockify.log 2>&1 &
```

### Common Issues

**"Target not found" error:**
- VNC server not running on target port
- Check with: `ss -tlnp | grep 5901`

**"Address already in use":**
- Previous websockify instance still running
- Kill with: `pkill -f websockify`

## nginx Configuration

### Option 1: Standalone Server (if no existing sites)

Create `/etc/nginx/sites-available/novnc`:

```nginx
server {
    listen 80 default_server;
    server_name _;

    # Serve noVNC static files
    location / {
        root /usr/share/novnc;
        index vnc.html;
        try_files $uri $uri/ /vnc.html;
    }

    # WebSocket proxy to websockify
    location /websockify {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

Enable the site:
```bash
ln -sf /etc/nginx/sites-available/novnc /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default if exists
nginx -t && systemctl reload nginx
```

### Option 2: Add to Existing nginx.conf

If nginx.conf has its own server block and doesn't use sites-enabled:

```nginx
# Add inside the http {} block in nginx.conf
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/novnc;
        index vnc.html;
    }

    location /websockify {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

### Option 3: Direct websockify (no nginx)

If nginx complexity is unnecessary:

```bash
# websockify can serve noVNC files directly
websockify --web=/usr/share/novnc 80 localhost:5901
```

Note: Requires root privileges for port 80, or use port 8080 instead.

## Troubleshooting

### 502 Bad Gateway

**Cause:** nginx cannot reach websockify

**Diagnosis:**
```bash
# Check if websockify is running
pgrep -a websockify

# Check if port 6080 is listening
ss -tlnp | grep 6080

# Test websockify directly
curl -v http://localhost:6080/
```

**Solutions:**
1. Start websockify before nginx tries to proxy
2. Verify websockify port matches nginx upstream

### WebSocket Connection Failed

**Cause:** WebSocket upgrade not properly proxied

**Diagnosis:**
```bash
# Check nginx error log
tail -f /var/log/nginx/error.log

# Test WebSocket endpoint
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost/websockify
```

**Solutions:**
1. Ensure `proxy_http_version 1.1` is set
2. Ensure `Upgrade` and `Connection` headers are passed

### noVNC Page Loads but Won't Connect

**Cause:** WebSocket path mismatch

**Diagnosis:**
1. Open browser developer tools (F12)
2. Check Network tab for WebSocket connection attempts
3. Look for 404 or connection refused errors

**Solutions:**
1. noVNC typically expects WebSocket at `/websockify` path
2. Verify nginx location matches noVNC expectations
3. Check `vnc.html` or `vnc_lite.html` for WebSocket URL configuration

### Configuration Validation

Always test before applying:

```bash
# Test nginx configuration syntax
nginx -t

# If using systemd
systemctl reload nginx

# Check nginx status
systemctl status nginx

# View recent errors
journalctl -u nginx --since "5 minutes ago"
```

## Security Considerations

### Binding websockify

```bash
# Bind only to localhost (recommended)
websockify --web=/usr/share/novnc 127.0.0.1:6080 localhost:5901

# Bind to all interfaces (use with caution)
websockify --web=/usr/share/novnc 0.0.0.0:6080 localhost:5901
```

### Adding Basic Authentication

In nginx configuration:

```nginx
location / {
    auth_basic "VNC Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    root /usr/share/novnc;
    index vnc.html;
}
```

Create password file:
```bash
htpasswd -c /etc/nginx/.htpasswd username
```

### VNC Password

QEMU VNC can require password:

```bash
qemu-system-i386 ... -vnc :1,password=on ...
```

Then set password via QMP:
```json
{"execute": "change-vnc-password", "arguments": {"password": "secret"}}
```
