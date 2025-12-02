# Common Regex Patterns for Log Parsing

This reference provides well-tested regex patterns for common log extraction tasks.

## IPv4 Address Patterns

### Basic IPv4 (allows leading zeros)
```regex
\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
```
**Warning**: Matches invalid IPs like `999.999.999.999` and leading zeros like `01.02.03.04`

### Strict IPv4 (no leading zeros, valid ranges)
```regex
\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b
```

**Breakdown of octet pattern:**
- `25[0-5]` — matches 250-255
- `2[0-4][0-9]` — matches 200-249
- `1[0-9]{2}` — matches 100-199
- `[1-9]?[0-9]` — matches 0-99 (single digit 0-9 or two digits 10-99, no leading zeros)

## Date Patterns

### ISO Date (YYYY-MM-DD) - Basic
```regex
\d{4}-\d{2}-\d{2}
```
**Warning**: Matches invalid dates like `2024-99-99`

### ISO Date with Month Validation
```regex
\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])
```
**Warning**: Allows invalid combinations like February 31

### ISO Date with Full Validation (non-leap year)
```regex
\d{4}-(?:(?:0[13578]|1[02])-(?:0[1-9]|[12][0-9]|3[01])|(?:0[469]|11)-(?:0[1-9]|[12][0-9]|30)|02-(?:0[1-9]|1[0-9]|2[0-8]))
```

**Breakdown:**
- `(?:0[13578]|1[02])-(?:0[1-9]|[12][0-9]|3[01])` — 31-day months (Jan, Mar, May, Jul, Aug, Oct, Dec)
- `(?:0[469]|11)-(?:0[1-9]|[12][0-9]|30)` — 30-day months (Apr, Jun, Sep, Nov)
- `02-(?:0[1-9]|1[0-9]|2[0-8])` — February 01-28

### ISO Date allowing Feb 29 (simplified leap year)
```regex
\d{4}-(?:(?:0[13578]|1[02])-(?:0[1-9]|[12][0-9]|3[01])|(?:0[469]|11)-(?:0[1-9]|[12][0-9]|30)|02-(?:0[1-9]|[12][0-9]))
```
Note: Allows Feb 29 for all years. For strict leap year validation, use programmatic checking.

## Timestamp Patterns

### 24-hour Time (HH:MM:SS)
```regex
(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]
```

### 24-hour Time with Milliseconds
```regex
(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.\d{3}
```

### ISO 8601 DateTime
```regex
\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.\d+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])?
```

## Log Level Patterns

### Common Log Levels
```regex
\b(?:DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b
```

### Case-insensitive
```regex
(?i)\b(?:debug|info|warn(?:ing)?|error|fatal|critical)\b
```

## Combining Patterns

### Finding Last Occurrence on a Line

To find the **last** occurrence of PATTERN on lines matching CONDITION:
```regex
^(?=.*CONDITION).*\b(PATTERN)\b(?!.*\bPATTERN\b)
```

**How it works:**
1. `^` — Anchor to line start (use `re.MULTILINE` for multi-line strings)
2. `(?=.*CONDITION)` — Positive lookahead ensures CONDITION exists on line
3. `.*` — Greedy match consumes as much as possible
4. `\b(PATTERN)\b` — Capture the target pattern with word boundaries
5. `(?!.*\bPATTERN\b)` — Negative lookahead ensures no more PATTERNs follow

### Finding First Occurrence on a Line

To find the **first** occurrence of PATTERN on lines matching CONDITION:
```regex
^(?=.*CONDITION).*?\b(PATTERN)\b
```

**How it works:**
1. `^` — Anchor to line start
2. `(?=.*CONDITION)` — Positive lookahead ensures CONDITION exists
3. `.*?` — Lazy match consumes as little as possible
4. `\b(PATTERN)\b` — Capture first matching pattern

## Python Pattern Construction

For complex patterns, build them programmatically for maintainability:

```python
import re

# Define components
IPV4_OCTET = r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])'
IPV4 = rf'\b(?:{IPV4_OCTET}\.){{3}}{IPV4_OCTET}\b'

MONTH_31 = r'(?:0[13578]|1[02])'
MONTH_30 = r'(?:0[469]|11)'
DAY_31 = r'(?:0[1-9]|[12][0-9]|3[01])'
DAY_30 = r'(?:0[1-9]|[12][0-9]|30)'
DAY_FEB = r'(?:0[1-9]|[12][0-9])'

ISO_DATE = rf'\b\d{{4}}-(?:{MONTH_31}-{DAY_31}|{MONTH_30}-{DAY_30}|02-{DAY_FEB})\b'

# Combine for "last date on lines with IP"
PATTERN = rf'^(?=.*{IPV4}).*({ISO_DATE})(?!.*{ISO_DATE})'

regex = re.compile(PATTERN, re.MULTILINE)
```

## Testing Recommendations

Always test patterns against these categories:

1. **Valid matches** — Expected positive cases
2. **Invalid rejections** — Format violations that should NOT match
3. **Edge positions** — Pattern at start, middle, end of line
4. **Multiple occurrences** — Verify first/last logic
5. **Adjacent patterns** — No space between patterns (word boundary test)
6. **Partial matches** — Patterns embedded in larger strings
