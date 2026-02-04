#!/usr/bin/env python3
"""Find emails that need a reply.

Identifies emails where:
1. You haven't replied at all
2. Your only "reply" is an unsent draft

Usage:
    python needs_reply.py
    python needs_reply.py --max-results 20
    python needs_reply.py --query "is:important"
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_auth import get_gmail_service

# Generic patterns for automated/notification senders
# These catch common automated email patterns without listing specific services
AUTOMATED_SENDER_PATTERNS = [
    r"noreply@",
    r"no-reply@",
    r"donotreply@",
    r"do-not-reply@",
    r"notifications?@",
    r"alerts?@",
    r"marketing@",
    r"news@",
    r"newsletter@",
    r"updates?@",
    r"digest@",
    r"automated@",
    r"mailer@",
    r"bounce@",
    r"@.*notification",
    r"@.*-alerts",
    r"@mail\.",      # mail.company.com subdomains
    r"@email\.",     # email.company.com subdomains  
    r"@comm\.",      # comm.company.com subdomains
    r"@plans\.",     # plans.company.com subdomains
]

# Compile patterns for efficiency
AUTOMATED_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in AUTOMATED_SENDER_PATTERNS]


def is_automated_sender(from_address: str) -> bool:
    """Check if an email address appears to be from an automated sender."""
    from_lower = from_address.lower()
    for pattern in AUTOMATED_PATTERNS_COMPILED:
        if pattern.search(from_lower):
            return True
    return False


def get_needs_reply(
    credentials_path: str | None = None,
    max_results: int = 50,
    query: str = "",
    include_automated: bool = False,
) -> list[dict]:
    """Find emails that need a reply.
    
    Args:
        credentials_path: Path to credentials.json
        max_results: Maximum number of inbox emails to check
        query: Additional Gmail search query to filter
        include_automated: If True, include automated/notification emails
    
    Returns:
        List of emails needing reply with metadata
    """
    service = get_gmail_service(credentials_path)
    
    # Get user's email address
    profile = service.users().getProfile(userId="me").execute()
    my_email = profile["emailAddress"].lower()
    
    # Use labelIds for more reliable inbox filtering instead of "in:inbox" query
    # The "in:inbox" query can sometimes return 0 results due to Gmail API quirks
    # Also filter out emails from self
    search_query = f"-from:me {query}".strip()
    
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],  # More reliable than "in:inbox" in query
        q=search_query if search_query else None,
        maxResults=max_results
    ).execute()
    
    messages = results.get("messages", [])
    needs_reply = []
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", 
            id=msg["id"], 
            format="metadata",
            metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe"]
        ).execute()
        
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
        from_address = headers.get("From", "")
        labels = msg_data.get("labelIds", [])
        thread_id = msg_data.get("threadId")
        
        # Skip automated senders unless explicitly requested
        if not include_automated:
            # Check if sender matches automated patterns
            if is_automated_sender(from_address):
                continue
            # Emails with List-Unsubscribe header are usually newsletters
            if "List-Unsubscribe" in headers:
                continue
        
        # Get full thread to check for replies
        thread = service.users().threads().get(
            userId="me", 
            id=thread_id, 
            format="metadata"
        ).execute()
        
        # Sort messages by internalDate
        thread_msgs = sorted(
            thread.get("messages", []), 
            key=lambda x: int(x.get("internalDate", 0))
        )
        
        # Find the last non-draft message from someone else
        last_external_msg = None
        last_external_date = 0
        
        for t_msg in thread_msgs:
            t_labels = t_msg.get("labelIds", [])
            t_headers = {h["name"]: h["value"] for h in t_msg["payload"]["headers"]}
            t_from = t_headers.get("From", "").lower()
            
            # Skip drafts
            if "DRAFT" in t_labels:
                continue
            
            # Skip my sent messages
            if my_email in t_from:
                continue
            
            # This is an external message
            msg_date = int(t_msg.get("internalDate", 0))
            if msg_date > last_external_date:
                last_external_date = msg_date
                last_external_msg = t_msg
        
        if not last_external_msg:
            continue
        
        # Check if I've replied AFTER this message (excluding drafts)
        my_reply_after = False
        has_draft_reply = False
        
        for t_msg in thread_msgs:
            t_labels = t_msg.get("labelIds", [])
            t_headers = {h["name"]: h["value"] for h in t_msg["payload"]["headers"]}
            t_from = t_headers.get("From", "").lower()
            msg_date = int(t_msg.get("internalDate", 0))
            
            if my_email in t_from:
                if msg_date > last_external_date:
                    if "DRAFT" in t_labels:
                        has_draft_reply = True
                    else:
                        my_reply_after = True
                        break
        
        # If I haven't sent a reply (only draft or nothing), add to list
        if not my_reply_after:
            last_headers = {h["name"]: h["value"] for h in last_external_msg["payload"]["headers"]}
            
            status = "DRAFT_ONLY" if has_draft_reply else "NO_REPLY"
            
            needs_reply.append({
                "id": last_external_msg["id"],
                "thread_id": thread_id,
                "from": last_headers.get("From", ""),
                "subject": last_headers.get("Subject", "(no subject)"),
                "date": last_headers.get("Date", ""),
                "snippet": last_external_msg.get("snippet", "")[:100],
                "status": status,
                "is_unread": "UNREAD" in labels,
            })
    
    # Sort: unread first, then draft-only, then no-reply
    needs_reply.sort(key=lambda x: (
        not x["is_unread"],
        x["status"] != "DRAFT_ONLY",
    ))
    
    return needs_reply


def main():
    parser = argparse.ArgumentParser(
        description="Find emails that need a reply",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --max-results 30
  %(prog)s --query "is:important"
  %(prog)s --query "from:@company.com"
  %(prog)s --include-automated  # Include newsletters/notifications
        """,
    )
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=50,
        help="Maximum inbox emails to check (default: 50)",
    )
    parser.add_argument(
        "--query", "-q",
        default="",
        help="Additional Gmail search query",
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
    parser.add_argument(
        "--include-automated",
        action="store_true",
        help="Include automated/notification emails (normally filtered out)",
    )
    
    args = parser.parse_args()
    
    emails = get_needs_reply(
        credentials_path=args.credentials,
        max_results=args.max_results,
        query=args.query,
        include_automated=args.include_automated,
    )
    
    if args.json:
        print(json.dumps(emails, indent=2))
    else:
        if not emails:
            print("✅ No emails need a reply!")
            return
        
        print(f"Found {len(emails)} email(s) needing a reply:\n")
        print("=" * 70)
        
        for i, email in enumerate(emails, 1):
            if email["status"] == "DRAFT_ONLY":
                status_icon = "📝 DRAFT UNSENT"
            elif email["is_unread"]:
                status_icon = "🔴 UNREAD"
            else:
                status_icon = "⏳ NEEDS REPLY"
            
            print(f"[{i}] {status_icon}")
            print(f"    From: {email['from'][:60]}")
            print(f"    Subject: {email['subject'][:55]}")
            print(f"    Date: {email['date'][:30]}")
            print(f"    Preview: {email['snippet']}...")
            print()


if __name__ == "__main__":
    main()
