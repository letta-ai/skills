# scraper-health

Reusable pattern for monitoring data scraper freshness and alerting on silent failures.

## Problem

Scrapers and cron-based data pipelines fail silently. The job runs, hits an error (or returns
empty data), and nobody notices until someone manually checks. Projects accumulate stale data
without any signal that something is wrong.

## What it does

Guides you through adding three things to any scraper or pipeline:

1. **Freshness timestamps** — A `last_updated` timestamp written on every scraper run (success or failure)
2. **Freshness check script** — A standalone script that compares timestamps against expected windows and reports stale/failing sources
3. **Automated alerting** — A GitHub Actions workflow (or cron job) that runs the check and opens an issue when data is stale

## Usage

```
/scraper-health
```

Or ask:
- "Add freshness monitoring to my scrapers"
- "How do I know if my data pipeline is stale?"
- "Set up scraper alerting"

## Supported patterns

| Storage | Timestamp approach | Check method |
|---------|-------------------|--------------|
| PostgreSQL / SQLite | `scraper_health` table | SQL query against `last_updated` |
| File-based (JSON, CSV) | `.health.json` sidecar file | Glob + parse sidecar files |
| Mixed | Both | Combined check script |

## Time to set up

~30 minutes for a typical project with 1-3 scrapers.

## File structure

```
skills/data-pipeline/scraper-health/
  SKILL.md                              # Skill trigger definition
  README.md                             # This file
  prompts/
    setup-monitoring.md                 # Step-by-step setup guide
  examples/
    github-actions-check.yml            # Ready-to-use Actions workflow
```
