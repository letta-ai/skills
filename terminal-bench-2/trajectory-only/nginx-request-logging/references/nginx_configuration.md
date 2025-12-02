# Nginx Configuration Reference

## Log Format Variables

Common variables for custom log formats:

| Variable | Description |
|----------|-------------|
| `$time_local` | Local time in Common Log Format |
| `$time_iso8601` | Local time in ISO 8601 format |
| `$request_method` | HTTP method (GET, POST, etc.) |
| `$request_uri` | Full original request URI with arguments |
| `$uri` | Current URI (may differ from request_uri after rewrites) |
| `$status` | Response status code |
| `$body_bytes_sent` | Number of bytes sent to client (excluding headers) |
| `$bytes_sent` | Total bytes sent to client |
| `$http_user_agent` | User-Agent header value |
| `$http_referer` | Referer header value |
| `$remote_addr` | Client IP address |
| `$remote_user` | Username from basic auth |
| `$request_time` | Request processing time in seconds |
| `$upstream_response_time` | Time spent receiving response from upstream |

## Rate Limiting Directives

### limit_req_zone

Defines a shared memory zone for rate limiting.

```nginx
limit_req_zone $key zone=name:size rate=rate;
```

Parameters:
- `$key`: Variable to use as key (typically `$binary_remote_addr`)
- `zone=name:size`: Zone name and size (e.g., `myzone:10m` for 10 megabytes)
- `rate=rate`: Request rate (e.g., `10r/s` for 10 requests per second, `60r/m` for 60 per minute)

### limit_req

Applies rate limiting to a location.

```nginx
limit_req zone=name [burst=number] [nodelay | delay=number];
```

Parameters:
- `zone=name`: Reference to a defined zone
- `burst=number`: Maximum burst size (optional)
- `nodelay`: Process burst requests immediately (optional)
- `delay=number`: Number of requests to process without delay before queuing (optional)

## Server Block Directives

### listen

```nginx
listen address[:port] [options];
listen port [options];
```

Common options:
- `default_server`: Make this the default server for the port
- `ssl`: Enable SSL/TLS
- `http2`: Enable HTTP/2

### root

Sets the document root directory:

```nginx
root /var/www/html;
```

### index

Sets default index file(s):

```nginx
index index.html index.htm;
```

### access_log

Configures access logging:

```nginx
access_log path [format [buffer=size] [gzip[=level]] [flush=time] [if=condition]];
access_log off;
```

### error_log

Configures error logging:

```nginx
error_log path [level];
```

Levels: `debug`, `info`, `notice`, `warn`, `error`, `crit`, `alert`, `emerg`

### try_files

Checks files in order and serves the first found:

```nginx
try_files file ... uri;
try_files file ... =code;
```

Example:
```nginx
try_files $uri $uri/ /index.html;
try_files $uri $uri/ =404;
```

## Configuration File Locations

| Distribution | Main Config | Additional Configs |
|--------------|-------------|-------------------|
| Debian/Ubuntu | `/etc/nginx/nginx.conf` | `/etc/nginx/conf.d/*.conf`, `/etc/nginx/sites-enabled/*` |
| RHEL/CentOS | `/etc/nginx/nginx.conf` | `/etc/nginx/conf.d/*.conf` |
| Alpine | `/etc/nginx/nginx.conf` | `/etc/nginx/conf.d/*.conf` |

## Common HTTP Status Codes from Nginx

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 200 | OK | Request successful |
| 301 | Moved Permanently | Redirect configured |
| 302 | Found | Temporary redirect |
| 400 | Bad Request | Malformed request |
| 403 | Forbidden | Permission denied or directory listing disabled |
| 404 | Not Found | File doesn't exist |
| 500 | Internal Server Error | Configuration error or upstream failure |
| 502 | Bad Gateway | Upstream server error |
| 503 | Service Unavailable | Rate limit exceeded or server overloaded |
| 504 | Gateway Timeout | Upstream timeout |

## Process Management Commands

### Using systemctl (systemd)

```bash
systemctl start nginx      # Start Nginx
systemctl stop nginx       # Stop Nginx
systemctl restart nginx    # Stop then start
systemctl reload nginx     # Reload config without stopping
systemctl status nginx     # Check status
systemctl enable nginx     # Enable on boot
```

### Using nginx directly

```bash
nginx                      # Start Nginx
nginx -s stop              # Fast shutdown
nginx -s quit              # Graceful shutdown
nginx -s reload            # Reload configuration
nginx -s reopen            # Reopen log files
nginx -t                   # Test configuration
nginx -T                   # Test and dump configuration
```

## Configuration Validation Checklist

Before applying any configuration:

1. **Syntax check**: `nginx -t`
2. **Full config dump**: `nginx -T` (shows included files)
3. **Check for duplicate `listen` directives on same port**
4. **Verify all referenced files exist** (SSL certs, root directories, include files)
5. **Check log directory permissions**
6. **Verify upstream servers are reachable** (if using proxy)
