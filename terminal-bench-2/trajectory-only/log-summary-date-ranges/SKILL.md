---
name: log-summary-date-ranges
description: This skill provides guidance for analyzing log files across date ranges and producing summary statistics. Use when tasks involve parsing log files, counting log entries by severity (ERROR, WARNING, INFO), aggregating by date ranges (today, last N days, month-to-date), or producing CSV reports from log data.
---

# Log Summary Date Ranges

## Overview

This skill guides log file analysis tasks that require aggregating entries across different date ranges and producing summary reports. Common scenarios include counting log entries by severity level (ERROR, WARNING, INFO) for various time periods and outputting results in structured formats like CSV.

## Workflow

### Step 1: Understand the Data Structure

Before writing any analysis code:

1. **Examine the log directory structure** - Identify how log files are organized (by date, by service, flat structure)
2. **Identify the naming pattern** - Log files often follow patterns like `app-YYYY-MM-DD.log` or `service.log.YYYY-MM-DD`
3. **Parse sample log entries** - Understand the exact format of log lines:
   - Timestamp format (ISO 8601, Unix timestamp, custom)
   - Severity level position and format (uppercase, lowercase, bracketed)
   - Delimiter between fields

Example log entry formats:
```
2025-08-12 10:30:45 ERROR Database connection failed
[2025-08-12T10:30:45.123Z] [ERROR] Database connection failed
ERROR 2025-08-12 10:30:45 - Database connection failed
```

### Step 2: Calculate Date Ranges Correctly

Given a reference date, calculate inclusive date ranges:

| Range | Calculation | Example (ref: 2025-08-12) |
|-------|-------------|---------------------------|
| Today | reference date only | 2025-08-12 |
| Last 7 days | reference - 6 days to reference | 2025-08-06 to 2025-08-12 |
| Last 30 days | reference - 29 days to reference | 2025-07-14 to 2025-08-12 |
| Month to date | first of month to reference | 2025-08-01 to 2025-08-12 |

**Critical consideration**: Clarify whether ranges are inclusive or exclusive at boundaries. "Last 7 days" typically means today plus the 6 preceding days (7 total days).

### Step 3: Implement the Analysis

When writing the analysis script:

1. **File selection** - Filter log files by date extracted from filename or file metadata
2. **Entry parsing** - Extract timestamp and severity from each log line
3. **Date matching** - Determine which date range(s) each entry belongs to
4. **Aggregation** - Count entries by severity for each date range
5. **Output formatting** - Produce output in the required format (CSV, JSON, etc.)

### Step 4: Verify Results Independently

**Always verify results using independent methods:**

1. **Spot-check individual counts** - Use grep/awk to count specific severities for specific dates
2. **Verify boundary dates** - Test entries at range boundaries (first/last day of each range)
3. **Check totals** - Sum of individual day counts should equal range totals
4. **Validate all ranges** - Do not verify only "today" and "total"; verify intermediate ranges too

Example verification commands:
```bash
# Count ERROR entries for a specific date
grep "2025-08-12" logs/*.log | grep -c "ERROR"

# Count all ERROR entries
grep -r "ERROR" logs/ | wc -l

# Verify a specific file's contribution
grep -c "ERROR" logs/app-2025-08-12.log
```

## Common Pitfalls

### Date Range Calculation Errors

- **Off-by-one errors** - "Last 7 days" should include 7 days, not 6 or 8
- **Timezone issues** - Log timestamps may be in different timezone than reference date
- **Inclusive vs exclusive** - Clarify whether end dates are included in ranges

### Output Format Issues

- **Line endings** - Use Unix-style `\n` unless Windows format is explicitly required. Configure CSV writers properly:
  ```python
  # Python: Prevent Windows line endings
  with open('output.csv', 'w', newline='') as f:
      writer = csv.writer(f)
  ```
- **Quoting** - Ensure CSV fields with commas or quotes are properly escaped
- **Column order** - Match the exact column order specified in requirements

### Parsing Issues

- **Case sensitivity** - Severity levels may appear as "ERROR", "error", or "Error"
- **Multiple matches per line** - A log line mentioning "ERROR in error handler" should count once
- **Malformed entries** - Gracefully handle log lines that don't match expected format
- **Empty files** - Log files may exist but be empty; handle this case

### Verification Gaps

- **Partial verification** - Verifying only endpoints (today, total) may miss bugs in intermediate ranges
- **Incomplete code review** - Ensure the full analysis script is visible and reviewable
- **No independent validation** - Always cross-check results with simple grep/awk commands

## Verification Checklist

Before declaring the task complete:

- [ ] All date range boundaries calculated correctly
- [ ] Sample entries from each range verified manually
- [ ] Output format matches specification exactly (columns, line endings, quoting)
- [ ] Edge cases handled (empty files, malformed entries, missing dates)
- [ ] Independent verification performed for each severity level
- [ ] Intermediate ranges verified (not just endpoints)
- [ ] Temporary files cleaned up (scripts, intermediate outputs)

## Resources

### references/

See `references/date_range_patterns.md` for common date range calculation patterns and edge cases.

### scripts/

No scripts are bundled. Analysis scripts should be written based on the specific log format and requirements of each task.

### assets/

No assets are bundled with this skill.
