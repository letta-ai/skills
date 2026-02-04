#!/usr/bin/env python3
"""Find busy periods in a calendar for a given time range."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from calendar_auth import get_calendar_service


def find_busy(
    start: str,
    end: str,
    calendar_id: str = "primary",
    credentials_path: str = None,
):
    """Find busy periods in the calendar."""
    service = get_calendar_service(credentials_path)
    
    # Ensure proper datetime format
    if not start.endswith("Z") and "+" not in start:
        start = start + ":00" if start.count(":") == 1 else start
    if not end.endswith("Z") and "+" not in end:
        end = end + ":00" if end.count(":") == 1 else end
    
    body = {
        "timeMin": start,
        "timeMax": end,
        "items": [{"id": calendar_id}],
    }
    
    freebusy_result = service.freebusy().query(body=body).execute()
    
    calendars = freebusy_result.get("calendars", {})
    busy_periods = calendars.get(calendar_id, {}).get("busy", [])
    
    print(f"Checking availability from {start} to {end}\n")
    
    if not busy_periods:
        print("No busy periods found - you're completely free!")
        return []
    
    print(f"Found {len(busy_periods)} busy period(s):\n")
    for period in busy_periods:
        start_dt = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
        
        start_str = start_dt.strftime("%I:%M %p")
        end_str = end_dt.strftime("%I:%M %p")
        
        print(f"  Busy: {start_str} - {end_str}")
    
    return busy_periods


def main():
    parser = argparse.ArgumentParser(description="Find busy periods in Google Calendar")
    parser.add_argument("--start", required=True, help="Start time (e.g., 2026-01-10T09:00:00)")
    parser.add_argument("--end", required=True, help="End time (e.g., 2026-01-10T18:00:00)")
    parser.add_argument("--calendar", default="primary", help="Calendar ID")
    parser.add_argument("--credentials", help="Path to credentials.json")
    args = parser.parse_args()
    
    find_busy(
        start=args.start,
        end=args.end,
        calendar_id=args.calendar,
        credentials_path=args.credentials,
    )


if __name__ == "__main__":
    main()
