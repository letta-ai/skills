---
name: datadog
description: Query Datadog observability data (logs, metrics, monitors, dashboards, hosts) via direct API. Use when investigating production issues, checking monitors, searching logs, or accessing Datadog data.
---

# Datadog CLI

Direct API access to Datadog observability data — logs, metrics, monitors, dashboards, hosts, and APM spans.

## Prerequisites

Set these environment variables:

```bash
export DD_API_KEY="your-32-char-hex-api-key"
export DD_APP_KEY="your-application-key"
export DD_SITE="us5.datadoghq.com"  # or datadoghq.com, datadoghq.eu, etc.
```

**Get keys from Datadog:**
- API Key: Organization Settings → API Keys
- App Key: Organization Settings → Application Keys

**Required scopes** (for read-only access):
- `dashboards_read`, `monitors_read`, `metrics_read`, `logs_read_data`, `incidents_read`, `hosts_read`, `apm_read`

## Quick Start

```bash
# Test credentials
npx tsx <skill-path>/scripts/datadog.ts validate

# Search logs
npx tsx <skill-path>/scripts/datadog.ts search-logs "status:error" --from -1h

# Query metrics
npx tsx <skill-path>/scripts/datadog.ts query-metrics "avg:system.cpu.user{*}" --from -4h

# List monitors
npx tsx <skill-path>/scripts/datadog.ts list-monitors
```

## Commands

### Logs

```bash
# Search logs (default: last hour, 50 results)
npx tsx <skill-path>/scripts/datadog.ts search-logs "service:api status:error"
npx tsx <skill-path>/scripts/datadog.ts search-logs "env:prod" --from -30m --limit 100
```

### Metrics

```bash
# Query metric timeseries
npx tsx <skill-path>/scripts/datadog.ts query-metrics "avg:system.cpu.user{*}" --from -4h
npx tsx <skill-path>/scripts/datadog.ts query-metrics "sum:requests.count{service:api}.as_count()" --from -1d
```

### Monitors

```bash
# List all monitors
npx tsx <skill-path>/scripts/datadog.ts list-monitors

# Filter monitors
npx tsx <skill-path>/scripts/datadog.ts list-monitors --query "status:alert"

# Get specific monitor
npx tsx <skill-path>/scripts/datadog.ts get-monitor 12345
```

### Dashboards

```bash
npx tsx <skill-path>/scripts/datadog.ts list-dashboards
```

### Hosts

```bash
npx tsx <skill-path>/scripts/datadog.ts list-hosts
npx tsx <skill-path>/scripts/datadog.ts list-hosts --filter "env:production"
```

### Incidents

```bash
npx tsx <skill-path>/scripts/datadog.ts list-incidents
```

### APM (Spans & Services)

```bash
# Search spans
npx tsx <skill-path>/scripts/datadog.ts search-spans "service:api @http.status_code:500" --from -1h

# List services
npx tsx <skill-path>/scripts/datadog.ts list-services
```

## Time Formats

The `--from` and `--to` flags accept:
- Relative: `-1h`, `-30m`, `-1d`, `-4h`
- ISO 8601: `2026-03-20T00:00:00Z`

## Datadog Sites

| Region | DD_SITE value |
|--------|---------------|
| US1 | `datadoghq.com` |
| US3 | `us3.datadoghq.com` |
| US5 | `us5.datadoghq.com` |
| EU | `datadoghq.eu` |
| AP1 | `ap1.datadoghq.com` |

## Troubleshooting

**403 Forbidden:**
- Check DD_SITE matches your Datadog region
- Verify app key has required scopes
- Confirm API key is active

**Credentials not found:**
- Ensure DD_API_KEY and DD_APP_KEY are exported
- Check for typos in env var names
