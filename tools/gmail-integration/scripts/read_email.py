#!/usr/bin/env python3
"""Read a specific Gmail message by ID.

Usage:
    python read_email.py <message_id>
    python read_email.py <message_id> --format full
    python read_email.py <message_id> --json
"""

import argparse
import base64
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_auth import get_gmail_service


def decode_body(data: str) -> str:
    """Decode base64url encoded email body."""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8")
    except Exception:
        return "(Unable to decode body)"


def extract_body(payload: dict) -> str:
    """Extract plain text body from message payload."""
    # Check for direct body
    if payload.get("body", {}).get("data"):
        return decode_body(payload["body"]["data"])
    
    # Check parts (multipart messages)
    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType", "")
        
        # Prefer plain text
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return decode_body(part["body"]["data"])
        
        # Recurse into nested parts
        if part.get("parts"):
            body = extract_body(part)
            if body:
                return body
    
    # Fall back to HTML if no plain text
    for part in parts:
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            return f"(HTML content)\n{decode_body(part['body']['data'])}"
    
    return "(No readable body found)"


def get_attachments_info(payload: dict) -> list[dict]:
    """Extract attachment information from message payload."""
    attachments = []
    
    def scan_parts(parts):
        for part in parts:
            filename = part.get("filename")
            if filename:
                attachments.append({
                    "filename": filename,
                    "mime_type": part.get("mimeType", "unknown"),
                    "size": part.get("body", {}).get("size", 0),
                    "attachment_id": part.get("body", {}).get("attachmentId"),
                })
            if part.get("parts"):
                scan_parts(part["parts"])
    
    if payload.get("parts"):
        scan_parts(payload["parts"])
    
    return attachments


def read_email(
    message_id: str,
    credentials_path: str | None = None,
    include_full: bool = False,
) -> dict:
    """Read a specific email message.
    
    Args:
        message_id: Gmail message ID
        credentials_path: Path to credentials.json
        include_full: Include full details (attachments, labels, etc.)
    
    Returns:
        Email details dictionary
    """
    service = get_gmail_service(credentials_path)
    
    # Fetch the full message
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()
    
    # Extract headers
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    
    # Build result
    result = {
        "id": msg["id"],
        "thread_id": msg["threadId"],
        "message_id": headers.get("Message-ID", ""),  # For threaded replies
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "cc": headers.get("Cc", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date": headers.get("Date", ""),
        "body": extract_body(msg["payload"]),
    }
    
    if include_full:
        result["labels"] = msg.get("labelIds", [])
        result["attachments"] = get_attachments_info(msg["payload"])
        result["size_estimate"] = msg.get("sizeEstimate", 0)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Read a Gmail message by ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 18d5a7b3c4e5f6a7
  %(prog)s 18d5a7b3c4e5f6a7 --format full
  %(prog)s 18d5a7b3c4e5f6a7 --json
        """,
    )
    parser.add_argument("message_id", help="Gmail message ID")
    parser.add_argument(
        "--format", "-f",
        choices=["basic", "full"],
        default="basic",
        help="Output format (default: basic)",
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
    
    email = read_email(
        message_id=args.message_id,
        credentials_path=args.credentials,
        include_full=(args.format == "full"),
    )
    
    if args.json:
        print(json.dumps(email, indent=2))
    else:
        print(f"From: {email['from']}")
        print(f"To: {email['to']}")
        if email.get('cc'):
            print(f"Cc: {email['cc']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        if email.get('message_id'):
            print(f"Message-ID: {email['message_id']}")
        
        if args.format == "full":
            print(f"Labels: {', '.join(email.get('labels', []))}")
            if email.get('attachments'):
                print(f"Attachments:")
                for att in email['attachments']:
                    print(f"  - {att['filename']} ({att['mime_type']}, {att['size']} bytes)")
        
        print("\n" + "=" * 60 + "\n")
        print(email['body'])


if __name__ == "__main__":
    main()
