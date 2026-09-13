# Setup Scraper Health Monitoring

You are adding freshness monitoring to a project's data scrapers or cron pipelines. Your job is
to ensure that stale data and silent failures are detected and surfaced automatically. Never
let a scraper fail silently — every data source must have a freshness contract.

## Principles

1. **Freshness is a contract** — Every data source declares how often it should update. Violations are alerts.
2. **Fail loudly** — Silent failures are the default failure mode for scrapers. This skill eliminates them.
3. **Minimal footprint** — Add timestamps and checks to the existing pipeline. Don't rebuild it.
4. **Works offline** — The check script must work with just a database connection or filesystem access — no external dependencies.

---

## INPUTS

Before starting, confirm with the user:

1. **What scrapers/pipelines exist?** — List each data source by name.
2. **Where does data land?** — Database table, JSON file, CSV, API cache, etc.
3. **What's the expected update frequency?** — Hourly, daily, weekly, etc.
4. **How should alerts be delivered?** — GitHub Issue, Slack webhook, email, log, etc.

---

## STEP 1: Discover Existing Scrapers

Search the project for scrapers, cron jobs, and scheduled data pipelines.

```
Glob pattern="**/*scrape*" OR "**/*crawl*" OR "**/*fetch*" OR "**/*ingest*"
Grep pattern="cron|schedule|@hourly|@daily|EventBridge|celery.beat" type="py"
Grep pattern="cron|schedule" glob="*.yml"
```

For each data source found, record:
- **Name**: Human-readable identifier (e.g., "Confidence Index Scraper")
- **Entry point**: File path and function/command
- **Output**: Where the data lands (table name, file path)
- **Schedule**: How often it runs (or "manual")
- **Current health signals**: Does it already log success/failure? Does it update a timestamp?

---

## STEP 2: Add Freshness Timestamps

For each data source, ensure a `last_updated` (or `last_scraped_at`, `fetched_at`) timestamp
is written on every successful run. Choose the approach that matches the storage:

### Database tables

Add a metadata row or column:

```sql
-- Option A: Dedicated metadata table (recommended for multiple scrapers)
CREATE TABLE IF NOT EXISTS scraper_health (
    source_name    TEXT PRIMARY KEY,
    last_updated   TIMESTAMPTZ NOT NULL,
    last_status    TEXT NOT NULL DEFAULT 'success',  -- 'success' | 'failure' | 'partial'
    last_error     TEXT,
    row_count      INTEGER,
    duration_ms    INTEGER,
    freshness_window_minutes INTEGER NOT NULL DEFAULT 1440  -- expected max age
);
```

```sql
-- Option B: Column on existing table (simpler for single-table pipelines)
ALTER TABLE <target_table> ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMPTZ;
```

### File-based pipelines

Write a sidecar JSON file alongside the data output:

```json
{
  "source": "confidence-index",
  "last_updated": "2026-03-06T12:00:00Z",
  "status": "success",
  "row_count": 142,
  "duration_ms": 3200,
  "freshness_window_minutes": 1440
}
```

Convention: name it `<source>.health.json` next to the data file.

### Updating the scraper code

Wrap the scraper's main function to record health on every run:

```python
import datetime
import traceback


def record_scraper_health(source_name, db_conn, func, *args, **kwargs):
    """Run a scraper function and record its health outcome."""
    start = datetime.datetime.now(datetime.timezone.utc)
    try:
        result = func(*args, **kwargs)
        duration_ms = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds() * 1000)
        row_count = result if isinstance(result, int) else None
        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO scraper_health (source_name, last_updated, last_status, row_count, duration_ms, freshness_window_minutes)
            VALUES (%s, NOW(), 'success', %s, %s, %s)
            ON CONFLICT (source_name) DO UPDATE SET
                last_updated = NOW(),
                last_status = 'success',
                last_error = NULL,
                row_count = EXCLUDED.row_count,
                duration_ms = EXCLUDED.duration_ms
            """,
            (source_name, row_count, duration_ms, kwargs.get("freshness_window_minutes", 1440)),
        )
        db_conn.commit()
        return result
    except Exception as e:
        duration_ms = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds() * 1000)
        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO scraper_health (source_name, last_updated, last_status, last_error, duration_ms, freshness_window_minutes)
            VALUES (%s, NOW(), 'failure', %s, %s, %s)
            ON CONFLICT (source_name) DO UPDATE SET
                last_updated = NOW(),
                last_status = 'failure',
                last_error = EXCLUDED.last_error,
                duration_ms = EXCLUDED.duration_ms
            """,
            (source_name, str(e)[:1000], duration_ms, kwargs.get("freshness_window_minutes", 1440)),
        )
        db_conn.commit()
        raise
```

For file-based pipelines, the equivalent writes the `.health.json` sidecar:

```python
import json
import datetime
from pathlib import Path


def record_health_file(source_name, output_dir, func, *args, freshness_window_minutes=1440, **kwargs):
    """Run a pipeline function and write a health sidecar file."""
    health_path = Path(output_dir) / f"{source_name}.health.json"
    start = datetime.datetime.now(datetime.timezone.utc)
    try:
        result = func(*args, **kwargs)
        duration_ms = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds() * 1000)
        health = {
            "source": source_name,
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "success",
            "row_count": result if isinstance(result, int) else None,
            "duration_ms": duration_ms,
            "freshness_window_minutes": freshness_window_minutes,
        }
        health_path.write_text(json.dumps(health, indent=2))
        return result
    except Exception as e:
        duration_ms = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds() * 1000)
        health = {
            "source": source_name,
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "failure",
            "error": str(e)[:1000],
            "duration_ms": duration_ms,
            "freshness_window_minutes": freshness_window_minutes,
        }
        health_path.write_text(json.dumps(health, indent=2))
        raise
```

---

## STEP 3: Create the Freshness Check Script

Create a standalone script that checks all registered data sources and reports which are stale
or failing. This script runs independently of the scrapers themselves.

```python
#!/usr/bin/env python3
"""Check scraper freshness and report stale/failing data sources."""

import argparse
import datetime
import json
import sys
from pathlib import Path


def check_db_freshness(db_conn):
    """Check freshness of all sources in scraper_health table."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT source_name, last_updated, last_status, last_error, freshness_window_minutes FROM scraper_health")
    now = datetime.datetime.now(datetime.timezone.utc)
    issues = []
    for row in cursor.fetchall():
        source, updated, status, error, window = row
        age_minutes = (now - updated).total_seconds() / 60
        if status == "failure":
            issues.append({"source": source, "issue": "last_run_failed", "error": error, "age_minutes": round(age_minutes)})
        elif age_minutes > window:
            issues.append({"source": source, "issue": "stale", "age_minutes": round(age_minutes), "window_minutes": window})
    return issues


def check_file_freshness(health_dir):
    """Check freshness of all .health.json sidecar files."""
    now = datetime.datetime.now(datetime.timezone.utc)
    issues = []
    for health_file in Path(health_dir).glob("*.health.json"):
        data = json.loads(health_file.read_text())
        updated = datetime.datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
        age_minutes = (now - updated).total_seconds() / 60
        window = data.get("freshness_window_minutes", 1440)
        if data.get("status") == "failure":
            issues.append({"source": data["source"], "issue": "last_run_failed", "error": data.get("error"), "age_minutes": round(age_minutes)})
        elif age_minutes > window:
            issues.append({"source": data["source"], "issue": "stale", "age_minutes": round(age_minutes), "window_minutes": window})
    return issues


def main():
    parser = argparse.ArgumentParser(description="Check scraper data freshness")
    parser.add_argument("--db-url", help="Database connection URL")
    parser.add_argument("--health-dir", help="Directory containing .health.json files")
    parser.add_argument("--format", choices=["text", "json", "github"], default="text")
    args = parser.parse_args()

    issues = []

    if args.db_url:
        import psycopg2
        conn = psycopg2.connect(args.db_url)
        issues.extend(check_db_freshness(conn))
        conn.close()

    if args.health_dir:
        issues.extend(check_file_freshness(args.health_dir))

    if not issues:
        print("All data sources are fresh.")
        sys.exit(0)

    if args.format == "json":
        print(json.dumps(issues, indent=2))
    elif args.format == "github":
        # Output for GitHub Actions: set output and format as markdown
        print("## Stale Data Alert")
        print()
        print("| Source | Issue | Age (min) | Window (min) | Error |")
        print("|--------|-------|-----------|-------------|-------|")
        for i in issues:
            print(f"| {i['source']} | {i['issue']} | {i.get('age_minutes', '-')} | {i.get('window_minutes', '-')} | {i.get('error', '-')[:80]} |")
    else:
        for i in issues:
            status = "STALE" if i["issue"] == "stale" else "FAILED"
            age = f"{i.get('age_minutes', '?')}m"
            window = f"(window: {i.get('window_minutes', '?')}m)" if i["issue"] == "stale" else ""
            error = f" — {i.get('error', '')[:80]}" if i.get("error") else ""
            print(f"  [{status}] {i['source']}: age={age} {window}{error}")

    sys.exit(1)


if __name__ == "__main__":
    main()
```

Save this as `scripts/check_scraper_freshness.py` (or wherever scripts live in the target project).

---

## STEP 4: Wire Up Alerting

Choose the delivery mechanism that fits the project:

### GitHub Actions (recommended for open-source / small teams)

Copy `examples/github-actions-check.yml` into `.github/workflows/` and configure:
- The schedule (default: every 6 hours)
- The check command (database URL or health directory)
- Whether to open issues, send Slack, or just log

### Cron + Slack Webhook

```bash
# Add to crontab (check every 6 hours)
0 */6 * * * /path/to/check_scraper_freshness.py --db-url "$DATABASE_URL" --format text | \
  curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\": \"$(cat)\"}" "$SLACK_WEBHOOK_URL"
```

### Database + Algedonic (for scaffold projects)

```python
# Write stale alerts to algedonic_alerts for VSM routing
from common.db_pool import get_connection

issues = check_db_freshness(conn)
if issues:
    with get_connection() as alert_conn:
        cursor = alert_conn.cursor()
        for issue in issues:
            cursor.execute(
                """INSERT INTO algedonic_alerts (source, severity, message, created_at)
                   VALUES (%s, %s, %s, NOW())""",
                (f"scraper:{issue['source']}", "warning", json.dumps(issue)),
            )
        alert_conn.commit()
```

---

## STEP 5: Verify the Setup

After wiring everything up, verify end-to-end:

1. **Timestamp writes**: Run the scraper manually and confirm `last_updated` is set.
2. **Freshness check passes**: Run the check script — it should report "All data sources are fresh."
3. **Simulate staleness**: Backdate `last_updated` by more than the freshness window, then re-run the check — it should report the source as stale.
4. **Simulate failure**: Force an error in the scraper and confirm `last_status = 'failure'` is recorded.
5. **Alert delivery**: Confirm the alert reaches the configured channel (issue opened, Slack message sent, etc.).

---

## Output Checklist

When done, confirm:

- [ ] Every data source has a `last_updated` timestamp written on each run
- [ ] Every data source has a defined `freshness_window_minutes`
- [ ] Failures are recorded with error messages (not swallowed)
- [ ] A freshness check script exists and can be run independently
- [ ] Alerting is wired to a delivery channel (GitHub Issues, Slack, algedonic, etc.)
- [ ] The check is scheduled to run automatically (Actions, cron, EventBridge)

---

## Tips

- **Set freshness windows conservatively at first.** If a scraper runs daily, set the window to
  36 hours (2160 minutes), not 24. This avoids false alerts from timing jitter.
- **Track `row_count`** — a scraper that "succeeds" but returns 0 rows is often a silent failure.
  Consider adding a minimum row count threshold to the freshness check.
- **Duration tracking** catches performance degradation before it becomes a timeout failure.
- **For database pipelines**, the `scraper_health` table approach is cleanest because it
  centralizes health for all sources in one place.
- **For file-based pipelines**, the `.health.json` sidecar keeps health metadata next to the data
  without modifying the data format.
