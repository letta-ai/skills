---
name: scraper-health
description: Add freshness monitoring and failure alerting to data scrapers and cron pipelines
triggers:
  - "scraper health"
  - "monitor scraper freshness"
  - "add freshness monitoring"
  - "scraper alerting"
  - "data freshness check"
  - "is my scraper data stale"
tools_required:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - TodoWrite
---

# Scraper Health

Adds freshness monitoring and failure alerting to data scrapers, cron jobs, and any pipeline
that produces timestamped output. Answers three questions: Is the data fresh? Did the last
run succeed? When should we alert?

Many projects have scrapers or scheduled jobs that fail silently — the cron runs, hits an error,
and nobody notices until someone manually checks. This skill adds a `last_updated` timestamp
pattern, defines a freshness window, and wires up alerting when data goes stale.

## What it produces

1. A `last_updated` timestamp column or file for each data source
2. A freshness check script that compares `last_updated` against an expected window
3. A GitHub Actions workflow (or cron equivalent) that runs the check and opens an issue when stale
4. Optional: database migration to add the timestamp column

See `prompts/setup-monitoring.md` for the full setup guide.
See `examples/github-actions-check.yml` for a ready-to-use workflow.
