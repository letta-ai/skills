#!/usr/bin/env python3
"""Search calendar events by text query and/or date range."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from calendar_auth import get_calendar_service


def parse_datetime(dt_str: str) -> str:
    """Parse datetime string to RFC3339 format."""
    # Handle date-only format
    if "T" not in dt_str:
        dt_str += "T00:00:00"
    
    # Parse and add timezone if missing
    if not dt_str.endswith("Z") and "+" not in dt_str and "-" not in dt_str[-6:]:
        # Assume local timezone, add Z for UTC or use local offset
        dt_str += "Z"
    
    return dt_str


def search_events(
    query: str = None,
    start: str = None,
    end: str = None,
    max_results: int = 20,
    calendar_id: str = "primary",
    credentials_path: str = None,
):
    """Search for calendar events."""
    service = get_calendar_service(credentials_path)
    
    # Default to today if no start date
    if not start:
        start = datetime.utcnow().isoformat() + "Z"
    else:
        start = parse_datetime(start)
    
    # Default to 7 days from start if no end date
    if not end:
        end_dt = datetime.utcnow() + timedelta(days=7)
        end = end_dt.isoformat() + "Z"
    else:
        end = parse_datetime(end)
    
    # Build query parameters
    params = {
        "calendarId": calendar_id,
        "timeMin": start,
        "timeMax": end,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    
    if query:
        params["q"] = query
    
    events_result = service.events().list(**params).execute()
    events = events_result.get("items", [])
    
    if not events:
        print(f"No events found{' matching: ' + query if query else ''}")
        return
    
    print(f"Found {len(events)} event(s):\n")
    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        end_time = event["end"].get("dateTime", event["end"].get("date"))
        
        # Format datetime for display
        if "T" in start_time:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            start_display = start_dt.strftime("%a %b %d, %Y %I:%M %p")
        else:
            start_display = start_time
        
        summary = event.get("summary", "(No title)")
        location = event.get("location", "")
        
        print(f"  [{event['id'][:8]}] {summary}")
        print(f"    When: {start_display}")
        if location:
            print(f"    Where: {location}")
        
        # Show attendees if any
        attendees = event.get("attendees", [])
        if attendees:
            names = [a.get("email", "") for a in attendees[:3]]
            more = f" +{len(attendees)-3} more" if len(attendees) > 3 else ""
            print(f"    With: {', '.join(names)}{more}")
        
        print()


def main():
    parser = argparse.ArgumentParser(description="Search Google Calendar events")
    parser.add_argument("query", nargs="?", help="Text to search for in events")
    parser.add_argument("--start", help="Start date/time (e.g., 2026-01-09 or 2026-01-09T09:00:00)")
    parser.add_argument("--end", help="End date/time")
    parser.add_argument("--max-results", type=int, default=20, help="Maximum results")
    parser.add_argument("--calendar", default="primary", help="Calendar ID")
    parser.add_argument("--credentials", help="Path to credentials.json")
    args = parser.parse_args()
    
    search_events(
        query=args.query,
        start=args.start,
        end=args.end,
        max_results=args.max_results,
        calendar_id=args.calendar,
        credentials_path=args.credentials,
    )


if __name__ == "__main__":
    main()
