# Gmail Search Operators

Quick reference for Gmail search query syntax. Use these with `search_emails.py`.

## Common Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `from:` | `from:john@example.com` | Messages from a sender |
| `to:` | `to:jane@example.com` | Messages to a recipient |
| `cc:` | `cc:team@example.com` | Messages with CC recipient |
| `subject:` | `subject:meeting` | Words in subject line |
| `label:` | `label:work` | Messages with a label |
| `is:` | `is:unread`, `is:starred` | Message state |
| `has:` | `has:attachment` | Messages with attachments |
| `in:` | `in:inbox`, `in:sent` | Messages in a folder |

## Date Filters

| Operator | Example | Description |
|----------|---------|-------------|
| `after:` | `after:2024/01/01` | Sent after date |
| `before:` | `before:2024/12/31` | Sent before date |
| `older_than:` | `older_than:7d` | Older than period (d/m/y) |
| `newer_than:` | `newer_than:2d` | Newer than period |

## Attachment Filters

| Operator | Example | Description |
|----------|---------|-------------|
| `has:attachment` | | Any attachment |
| `filename:` | `filename:report.pdf` | Specific filename |
| `filename:pdf` | | Files with extension |
| `larger:` | `larger:5M` | Larger than size |
| `smaller:` | `smaller:1M` | Smaller than size |

## Message State

| Query | Description |
|-------|-------------|
| `is:unread` | Unread messages |
| `is:read` | Read messages |
| `is:starred` | Starred messages |
| `is:important` | Important messages |
| `is:snoozed` | Snoozed messages |

## Combining Operators

- **AND** (implicit): `from:john subject:meeting` - both conditions
- **OR**: `from:john OR from:jane` - either condition
- **NOT** / `-`: `-from:newsletter` - exclude condition
- **Grouping**: `(from:john OR from:jane) subject:urgent`
- **Exact phrase**: `"project update"` - exact match

## Examples

```bash
# Unread emails from a specific person
search_emails.py "is:unread from:boss@company.com"

# Emails with PDF attachments from last month
search_emails.py "has:attachment filename:pdf newer_than:30d"

# Important emails not from newsletters
search_emails.py "is:important -label:newsletters"

# Emails about meetings this week
search_emails.py "subject:meeting newer_than:7d"

# Large attachments
search_emails.py "has:attachment larger:10M"
```
