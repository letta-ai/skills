---
name: google-calendar
description: Connect Letta Code to Google Calendar via OAuth 2.0 and perform calendar operations. Use when a user wants to search events, check availability, or create/schedule meetings. Triggers on queries about calendar, schedule, meetings, availability, or booking time.
---

# Google Calendar Integration

This skill provides Google Calendar access using the same OAuth credentials as Gmail.

## Prerequisites

- OAuth credentials already set up (shared with Gmail skill)
- Calendar API enabled in Google Cloud Console
- Token includes calendar scopes (calendar.readonly, calendar.events)

## Available Scripts

All scripts are in `.skills/google-calendar/scripts/` and require `--credentials ./credentials.json`.

### List Calendars

```bash
uv run python .skills/google-calendar/scripts/list_calendars.py --credentials ./credentials.json
```

### Search Events

Search for events by text query or time range:

```bash
# Search by text
uv run python .skills/google-calendar/scripts/search_events.py "meeting" --credentials ./credentials.json

# Search by date range (use YYYY-MM-DD format)
uv run python .skills/google-calendar/scripts/search_events.py --start "YYYY-MM-DD" --end "YYYY-MM-DD" --credentials ./credentials.json

# Combine text and date
uv run python .skills/google-calendar/scripts/search_events.py "standup" --start "YYYY-MM-DD" --credentials ./credentials.json
```

### Check Availability (Free/Busy)

Find busy periods in a time range:

```bash
uv run python .skills/google-calendar/scripts/find_busy.py --start "YYYY-MM-DDTHH:MM:00" --end "YYYY-MM-DDTHH:MM:00" --credentials ./credentials.json
```

**Note:** This script may have issues with datetime formatting. Use `search_events.py` as a more reliable way to check what's on the calendar.

### Create Event

Create a new calendar event:

```bash
uv run python .skills/google-calendar/scripts/create_event.py \
  --summary "Team Standup" \
  --start "YYYY-MM-DDTHH:MM:00" \
  --end "YYYY-MM-DDTHH:MM:00" \
  --credentials ./credentials.json

# With optional fields
uv run python .skills/google-calendar/scripts/create_event.py \
  --summary "Product Demo" \
  --start "YYYY-MM-DDTHH:MM:00" \
  --end "YYYY-MM-DDTHH:MM:00" \
  --description "Demo of new features" \
  --location "Zoom" \
  --attendees "alice@example.com,bob@example.com" \
  --timezone "America/Los_Angeles" \
  --credentials ./credentials.json
```

**Options:**
- `--summary` (required): Event title
- `--start` (required): Start datetime in ISO format
- `--end` (required): End datetime in ISO format
- `--description`: Event description
- `--location`: Event location (e.g., "Zoom", "Conference Room A")
- `--attendees`: Comma-separated email addresses (sends invites automatically)
- `--timezone`: Timezone for the event (e.g., America/Los_Angeles, America/New_York, Europe/London)
- `--calendar`: Calendar ID (default: "primary")

## Common Patterns

### Check availability for a day
Use `search_events.py` with start and end dates to see all events:
```bash
uv run python .skills/google-calendar/scripts/search_events.py --start "YYYY-MM-DD" --end "YYYY-MM-DD" --credentials ./credentials.json
```

### Schedule a meeting
1. Check calendar with `search_events.py` to find free slots
2. Create event with `create_event.py`

### Review upcoming week
```bash
uv run python .skills/google-calendar/scripts/search_events.py --start "TODAY" --end "NEXT_WEEK" --credentials ./credentials.json
```
(Replace TODAY/NEXT_WEEK with actual dates)
