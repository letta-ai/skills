#!/usr/bin/env python3
"""Create a new calendar event."""

import argparse
import sys
from pathlib import Path

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from calendar_auth import get_calendar_service


def create_event(
    summary: str,
    start: str,
    end: str,
    description: str = None,
    location: str = None,
    attendees: list = None,
    timezone: str = None,
    calendar_id: str = "primary",
    credentials_path: str = None,
):
    """Create a new calendar event."""
    service = get_calendar_service(credentials_path)
    
    # Build event body
    event = {
        "summary": summary,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    
    # Add timezone if specified
    if timezone:
        event["start"]["timeZone"] = timezone
        event["end"]["timeZone"] = timezone
    
    if description:
        event["description"] = description
    
    if location:
        event["location"] = location
    
    if attendees:
        event["attendees"] = [{"email": email.strip()} for email in attendees]
    
    # Create the event
    created_event = service.events().insert(
        calendarId=calendar_id,
        body=event,
        sendUpdates="all" if attendees else "none",
    ).execute()
    
    print(f"Event created successfully!")
    print(f"  Summary: {created_event['summary']}")
    print(f"  Start: {created_event['start']['dateTime']}")
    print(f"  End: {created_event['end']['dateTime']}")
    print(f"  Link: {created_event.get('htmlLink', 'N/A')}")
    
    return created_event


def main():
    parser = argparse.ArgumentParser(description="Create a Google Calendar event")
    parser.add_argument("--summary", required=True, help="Event title")
    parser.add_argument("--start", required=True, help="Start time (e.g., 2024-01-10T10:00:00)")
    parser.add_argument("--end", required=True, help="End time (e.g., 2024-01-10T11:00:00)")
    parser.add_argument("--description", help="Event description")
    parser.add_argument("--location", help="Event location")
    parser.add_argument("--attendees", help="Comma-separated list of attendee emails")
    parser.add_argument("--timezone", help="Timezone (e.g., America/Los_Angeles, America/New_York)")
    parser.add_argument("--calendar", default="primary", help="Calendar ID")
    parser.add_argument("--credentials", help="Path to credentials.json")
    args = parser.parse_args()
    
    attendees = args.attendees.split(",") if args.attendees else None
    
    create_event(
        summary=args.summary,
        start=args.start,
        end=args.end,
        description=args.description,
        location=args.location,
        attendees=attendees,
        timezone=args.timezone,
        calendar_id=args.calendar,
        credentials_path=args.credentials,
    )


if __name__ == "__main__":
    main()
