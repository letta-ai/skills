#!/usr/bin/env python3
"""List all calendars accessible to the user."""

import argparse
import sys
from pathlib import Path

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from calendar_auth import get_calendar_service


def list_calendars(credentials_path: str = None):
    """List all calendars."""
    service = get_calendar_service(credentials_path)
    
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get("items", [])
    
    if not calendars:
        print("No calendars found.")
        return
    
    print(f"Found {len(calendars)} calendar(s):\n")
    for cal in calendars:
        primary = " (primary)" if cal.get("primary") else ""
        access = cal.get("accessRole", "unknown")
        print(f"  ID: {cal['id']}")
        print(f"  Name: {cal['summary']}{primary}")
        print(f"  Access: {access}")
        print()


def main():
    parser = argparse.ArgumentParser(description="List Google Calendars")
    parser.add_argument("--credentials", help="Path to credentials.json")
    args = parser.parse_args()
    
    list_calendars(args.credentials)


if __name__ == "__main__":
    main()
