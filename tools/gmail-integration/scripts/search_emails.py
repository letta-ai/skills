#!/usr/bin/env python3
"""Search Gmail messages by query.

Usage:
    python search_emails.py "from:someone@example.com"
    python search_emails.py "subject:meeting" --max-results 20
    python search_emails.py "is:unread after:2024/01/01" --credentials /path/to/credentials.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_auth import get_gmail_service


def search_emails(
    query: str,
    max_results: int = 10,
    credentials_path: str | None = None,
    output_format: str = "text",
) -> list[dict]:
    """Search emails matching the query.
    
    Args:
        query: Gmail search query (same syntax as Gmail search box)
        max_results: Maximum number of results to return
        credentials_path: Path to credentials.json
        output_format: Output format ("text" or "json")
    
    Returns:
        List of message summaries
    """
    service = get_gmail_service(credentials_path)
    
    # Search for messages
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()
    
    messages = results.get("messages", [])
    
    if not messages:
        return []
    
    # Fetch metadata for each message
    email_summaries = []
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
        
        summary = {
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "snippet": msg_data.get("snippet", ""),
        }
        email_summaries.append(summary)
    
    return email_summaries


def main():
    parser = argparse.ArgumentParser(
        description="Search Gmail messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "from:boss@company.com"
  %(prog)s "subject:urgent is:unread"
  %(prog)s "after:2024/01/01 before:2024/02/01"
  %(prog)s "has:attachment filename:pdf"
        """,
    )
    parser.add_argument("query", help="Gmail search query")
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=10,
        help="Maximum results to return (default: 10)",
    )
    parser.add_argument(
        "--credentials",
        help="Path to credentials.json file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    
    args = parser.parse_args()
    
    emails = search_emails(
        query=args.query,
        max_results=args.max_results,
        credentials_path=args.credentials,
    )
    
    if args.json:
        print(json.dumps(emails, indent=2))
    else:
        if not emails:
            print(f"No messages found matching: {args.query}")
            return
        
        print(f"Found {len(emails)} message(s) matching: {args.query}\n")
        
        for i, email in enumerate(emails, 1):
            print(f"[{i}] ID: {email['id']}")
            print(f"    From: {email['from']}")
            print(f"    Subject: {email['subject']}")
            print(f"    Date: {email['date']}")
            print(f"    Preview: {email['snippet'][:100]}...")
            print()


if __name__ == "__main__":
    main()
