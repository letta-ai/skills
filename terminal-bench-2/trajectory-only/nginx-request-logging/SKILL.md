---
name: nginx-request-logging
description: Guidance for configuring Nginx web servers with custom logging, rate limiting, and static content serving. This skill should be used when tasks involve setting up Nginx server blocks, configuring custom log formats, implementing rate limiting, or serving static files on specific ports.
---

# Nginx Request Logging

## Overview

This skill provides guidance for configuring Nginx web servers with custom access logging, rate limiting zones, and static content serving. It covers common configuration patterns, verification strategies, and pitfalls to avoid when setting up production-ready Nginx configurations.

## Pre-Configuration Checks

Before making any configuration changes, perform these essential checks:

1. **Check for existing Nginx processes**: Run `pgrep nginx` or `ps aux | grep nginx` to determine if Nginx is already running
2. **Verify port availability**: Use `ss -tlnp | grep <port>` or `netstat -tlnp | grep <port>` to check if the target port is in use
3. **Confirm directory structure**: Verify that `/etc/nginx/conf.d/` exists before writing configuration files
4. **Check log directory permissions**: Ensure `/var/log/nginx/` is writable for custom log files
5. **Back up existing configuration**: Copy current nginx.conf before modifications

## Configuration Workflow

### Step 1: Define Custom Log Format

Add custom log formats in the `http` block of `/etc/nginx/nginx.conf`:

```nginx
log_format custom_format '$time_local $request_method $status "$http_user_agent"';
```

Key considerations:
- Log format must be defined in the `http` block, not within a `server` block
- Variable names are case-sensitive (e.g., `$http_user_agent` not `$HTTP_USER_AGENT`)
- Quoted fields in the format require escaped quotes or single quotes around the entire format

### Step 2: Configure Rate Limiting

Rate limiting requires two components:

1. **Zone definition** (in `http` block):
```nginx
limit_req_zone $binary_remote_addr zone=myzone:10m rate=10r/s;
```

2. **Zone application** (in `server` or `location` block):
```nginx
limit_req zone=myzone burst=10 nodelay;
```

Rate limiting behavior options:
- Without `nodelay`: Burst requests are queued and processed at the defined rate
- With `nodelay`: Burst requests are processed immediately; excess requests rejected
- Without `burst`: Only the base rate is allowed; no bursting permitted

### Step 3: Server Block Configuration

Create a server block in `/etc/nginx/conf.d/` with:

```nginx
server {
    listen <port>;
    server_name localhost;

    root /var/www/<site>;
    index index.html;

    access_log /var/log/nginx/<logfile>.log custom_format;

    location / {
        limit_req zone=myzone burst=10 nodelay;
        try_files $uri $uri/ =404;
    }
}
```

### Step 4: Validate and Apply Configuration

1. **Test configuration syntax**: `nginx -t`
2. **Reload or start Nginx**:
   - If running with systemd: `systemctl reload nginx`
   - If systemd unavailable: `nginx -s reload` (for reload) or `nginx` (for start)
3. **Verify the process is running**: `pgrep nginx` or `ps aux | grep nginx`

## Verification Strategies

### Basic Connectivity Test

```bash
curl -s http://localhost:<port>/
```

### Log Format Verification

After making requests, inspect the log file:

```bash
tail -5 /var/log/nginx/<logfile>.log
```

Verify each expected field is present and correctly formatted.

### Rate Limiting Verification

Test rate limiting with concurrent requests:

```bash
for i in $(seq 1 25); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:<port>/; done
```

Expected behavior:
- Initial requests (up to rate + burst) return 200
- Excess requests return 503 (Service Temporarily Unavailable)

With `burst=10` and `rate=10r/s`:
- First ~11-20 requests typically succeed (depends on timing)
- Remaining requests return 503

## Common Pitfalls

### Configuration Errors

1. **Log format in wrong block**: Custom log formats must be in the `http` block, not `server`
2. **Missing semicolons**: Every Nginx directive must end with a semicolon
3. **Incorrect variable names**: Use `$binary_remote_addr` for rate limiting (more efficient than `$remote_addr`)
4. **Forgetting to test config**: Always run `nginx -t` before reload/restart

### Process Management Errors

1. **Starting when already running**: Check for existing processes before starting
2. **Using wrong reload method**: If systemctl fails, use `nginx -s reload`
3. **Permission issues**: Log directories and HTML root must be accessible by the nginx worker user (typically `www-data` or `nginx`)

### Testing Errors

1. **Echo compatibility**: Use `printf` instead of `echo -e` for portable newline handling
2. **Interpreting rate limit results**: Results vary based on request timing; don't expect exact counts
3. **Not checking actual log output**: Always verify logs contain expected format, not just that requests succeed

## Rollback Strategy

If configuration changes cause issues:

1. **Restore backup**: `cp /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf`
2. **Remove problematic conf.d files**: `rm /etc/nginx/conf.d/<problematic>.conf`
3. **Test and reload**: `nginx -t && nginx -s reload`

## References

For detailed configuration syntax and directives, refer to `references/nginx_configuration.md`.
