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
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_auth import get_gmail_service


def get_needs_reply(
    credentials_path: str | None = None,
    max_results: int = 50,
    query: str = "",
    user_email: str = "me",
) -> list[dict]:
    """Find emails that need a reply.
    
    Args:
        credentials_path: Path to credentials.json
        max_results: Maximum number of inbox emails to check
        query: Additional Gmail search query to filter
        user_email: Your email address (used to identify your messages)
    
    Returns:
        List of emails needing reply with metadata
    """
    service = get_gmail_service(credentials_path)
    
    # Get user's email address
    profile = service.users().getProfile(userId="me").execute()
    my_email = profile["emailAddress"].lower()
    
    # Base query: in inbox, not from me, not automated
    base_query = "in:inbox -from:me -from:noreply -from:no-reply -from:notifications -from:alerts -from:marketing"
    full_query = f"{base_query} {query}".strip()
    
    results = service.users().messages().list(
        userId="me", 
        q=full_query, 
        maxResults=max_results
    ).execute()
    
    messages = results.get("messages", [])
    needs_reply = []
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", 
            id=msg["id"], 
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
        labels = msg_data.get("labelIds", [])
        thread_id = msg_data.get("threadId")
        
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
    
    args = parser.parse_args()
    
    emails = get_needs_reply(
        credentials_path=args.credentials,
        max_results=args.max_results,
        query=args.query,
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
