# Date Range Calculation Patterns

## Overview

This reference provides patterns for calculating common date ranges used in log analysis and reporting tasks.

## Python Date Range Calculations

```python
from datetime import datetime, timedelta

def calculate_date_ranges(reference_date: datetime):
    """
    Calculate common date ranges relative to a reference date.
    All ranges are INCLUSIVE of both start and end dates.
    """

    # Today - single day
    today_start = reference_date
    today_end = reference_date

    # Last 7 days - reference date plus 6 preceding days (7 total)
    last_7_start = reference_date - timedelta(days=6)
    last_7_end = reference_date

    # Last 30 days - reference date plus 29 preceding days (30 total)
    last_30_start = reference_date - timedelta(days=29)
    last_30_end = reference_date

    # Month to date - first of current month to reference date
    month_to_date_start = reference_date.replace(day=1)
    month_to_date_end = reference_date

    # Total/All time - no date filtering
    # Handle separately by not filtering on date

    return {
        'today': (today_start, today_end),
        'last_7_days': (last_7_start, last_7_end),
        'last_30_days': (last_30_start, last_30_end),
        'month_to_date': (month_to_date_start, month_to_date_end),
    }


def is_date_in_range(check_date: datetime, start: datetime, end: datetime) -> bool:
    """Check if a date falls within an inclusive range."""
    return start <= check_date <= end
```

## Date Extraction from Log Filenames

```python
import re
from datetime import datetime

# Common filename patterns
patterns = [
    # app-2025-08-12.log
    (r'(\d{4}-\d{2}-\d{2})\.log$', '%Y-%m-%d'),
    # service.log.2025-08-12
    (r'\.log\.(\d{4}-\d{2}-\d{2})$', '%Y-%m-%d'),
    # app_20250812.log
    (r'_(\d{8})\.log$', '%Y%m%d'),
    # 2025/08/12/app.log (from path)
    (r'(\d{4}/\d{2}/\d{2})/', '%Y/%m/%d'),
]

def extract_date_from_filename(filename: str) -> datetime | None:
    """Extract date from log filename using common patterns."""
    for pattern, date_format in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                return datetime.strptime(match.group(1), date_format)
            except ValueError:
                continue
    return None
```

## Date Extraction from Log Lines

```python
import re
from datetime import datetime

def extract_date_from_log_line(line: str) -> datetime | None:
    """
    Extract date from log line. Returns date only (no time).
    Supports common log formats.
    """
    patterns = [
        # ISO format: 2025-08-12T10:30:45
        (r'(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}', '%Y-%m-%d'),
        # Standard: 2025-08-12 10:30:45
        (r'(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2}', '%Y-%m-%d'),
        # American: 08/12/2025 10:30:45
        (r'(\d{2}/\d{2}/\d{4}) \d{2}:\d{2}:\d{2}', '%m/%d/%Y'),
        # Compact: 20250812 103045
        (r'(\d{8}) \d{6}', '%Y%m%d'),
    ]

    for pattern, date_format in patterns:
        match = re.search(pattern, line)
        if match:
            try:
                return datetime.strptime(match.group(1), date_format)
            except ValueError:
                continue
    return None
```

## Edge Cases to Handle

### Timezone Considerations

```python
from datetime import datetime, timezone

# If logs use UTC timestamps but reference date is local
def normalize_to_date(timestamp: datetime, target_tz=None) -> datetime:
    """Convert timestamp to date in target timezone."""
    if target_tz and timestamp.tzinfo:
        timestamp = timestamp.astimezone(target_tz)
    return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
```

### Month Boundaries

```python
from datetime import datetime
import calendar

def month_boundaries(reference_date: datetime):
    """Get first and last day of the reference month."""
    first_day = reference_date.replace(day=1)
    last_day_num = calendar.monthrange(reference_date.year, reference_date.month)[1]
    last_day = reference_date.replace(day=last_day_num)
    return first_day, last_day
```

### Year Boundaries for "Year to Date"

```python
def year_to_date(reference_date: datetime):
    """Get range from Jan 1 to reference date."""
    start = reference_date.replace(month=1, day=1)
    return start, reference_date
```

## Common Mistakes to Avoid

1. **Off-by-one with timedelta**: `timedelta(days=7)` gives 8 days if you include both endpoints
2. **Month rollover**: Using `replace(day=1)` on March 31 works, but going backwards doesn't
3. **Leap years**: February 29 handling when calculating "last year" ranges
4. **DST transitions**: 24-hour periods may have 23 or 25 hours during DST changes

## Verification Patterns

```python
def verify_date_range(start: datetime, end: datetime, expected_days: int) -> bool:
    """Verify a date range contains the expected number of days."""
    actual_days = (end - start).days + 1  # +1 for inclusive
    return actual_days == expected_days

# Example verifications
assert verify_date_range(
    datetime(2025, 8, 6),
    datetime(2025, 8, 12),
    expected_days=7
)  # Last 7 days

assert verify_date_range(
    datetime(2025, 7, 14),
    datetime(2025, 8, 12),
    expected_days=30
)  # Last 30 days
```
