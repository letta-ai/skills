#!/usr/bin/env python3
"""Create a Gmail draft message.

Usage:
    python create_draft.py --to "recipient@example.com" --subject "Hello" --body "Message"
    python create_draft.py --to "a@example.com" --cc "b@example.com" --subject "Update" --body-file message.txt
    python create_draft.py --to "recipient@example.com" --subject "Re: Topic" --body "Reply" --reply-to <message_id>
"""

import argparse
import base64
import json
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_auth import get_gmail_service


def create_message(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    reply_to_message_id: str | None = None,
    thread_id: str | None = None,
    html: bool = False,
) -> dict:
    """Create a message for the Gmail API.
    
    Args:
        to: Recipient email address(es), comma-separated
        subject: Email subject
        body: Email body (plain text or HTML)
        cc: CC recipients, comma-separated
        bcc: BCC recipients, comma-separated
        reply_to_message_id: Message ID to reply to (for threading)
        thread_id: Thread ID to add message to
        html: If True, body is treated as HTML
    
    Returns:
        Message object for Gmail API
    """
    if html:
        message = MIMEMultipart("alternative")
    else:
        message = MIMEMultipart()
    
    message["to"] = to
    message["subject"] = subject
    
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc
    if reply_to_message_id:
        message["In-Reply-To"] = reply_to_message_id
        message["References"] = reply_to_message_id
    
    if html:
        # For HTML emails, include both plain text and HTML versions
        # Strip HTML tags for plain text version (basic)
        import re
        plain_text = re.sub(r'<[^>]+>', '', body)
        plain_text = plain_text.replace('&nbsp;', ' ')
        message.attach(MIMEText(plain_text, "plain"))
        message.attach(MIMEText(body, "html"))
    else:
        message.attach(MIMEText(body, "plain"))
    
    # Encode the message
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    
    result = {"raw": raw}
    if thread_id:
        result["threadId"] = thread_id
    
    return result


def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    reply_to_message_id: str | None = None,
    thread_id: str | None = None,
    credentials_path: str | None = None,
    html: bool = False,
) -> dict:
    """Create a draft email in Gmail.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        body: Email body (plain text or HTML)
        cc: CC recipients
        bcc: BCC recipients
        reply_to_message_id: Message ID to reply to
        thread_id: Thread ID to add to
        credentials_path: Path to credentials.json
        html: If True, body is treated as HTML
    
    Returns:
        Created draft details
    """
    service = get_gmail_service(credentials_path)
    
    message = create_message(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        reply_to_message_id=reply_to_message_id,
        thread_id=thread_id,
        html=html,
    )
    
    draft = service.users().drafts().create(
        userId="me",
        body={"message": message},
    ).execute()
    
    return {
        "draft_id": draft["id"],
        "message_id": draft["message"]["id"],
        "thread_id": draft["message"].get("threadId"),
        "to": to,
        "subject": subject,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create a Gmail draft",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --to "user@example.com" --subject "Hello" --body "Hi there!"
  %(prog)s --to "a@example.com" --cc "b@example.com" --subject "Meeting" --body "Let's meet tomorrow"
  %(prog)s --to "user@example.com" --subject "Report" --body-file report.txt
  %(prog)s --to "user@example.com" --subject "Re: Question" --body "Here's my answer" --reply-to 18d5a7b3c4e5f6a7
        """,
    )
    parser.add_argument(
        "--to", "-t",
        required=True,
        help="Recipient email address(es), comma-separated",
    )
    parser.add_argument(
        "--subject", "-s",
        required=True,
        help="Email subject",
    )
    parser.add_argument(
        "--body", "-b",
        help="Email body text",
    )
    parser.add_argument(
        "--body-file",
        help="Read body from file",
    )
    parser.add_argument(
        "--cc",
        help="CC recipients, comma-separated",
    )
    parser.add_argument(
        "--bcc",
        help="BCC recipients, comma-separated",
    )
    parser.add_argument(
        "--reply-to",
        help="Message ID to reply to (for threading)",
    )
    parser.add_argument(
        "--thread-id",
        help="Thread ID to add message to",
    )
    parser.add_argument(
        "--credentials",
        help="Path to credentials.json file",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Treat body as HTML (supports links, formatting)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    
    args = parser.parse_args()
    
    # Get body from argument or file
    if args.body_file:
        body = Path(args.body_file).read_text()
    elif args.body:
        body = args.body
    else:
        parser.error("Either --body or --body-file is required")
    
    draft = create_draft(
        to=args.to,
        subject=args.subject,
        body=body,
        cc=args.cc,
        bcc=args.bcc,
        reply_to_message_id=args.reply_to,
        thread_id=args.thread_id,
        credentials_path=args.credentials,
        html=args.html,
    )
    
    if args.json:
        print(json.dumps(draft, indent=2))
    else:
        print("Draft created successfully!")
        print(f"  Draft ID: {draft['draft_id']}")
        print(f"  To: {draft['to']}")
        print(f"  Subject: {draft['subject']}")
        print(f"\nView in Gmail: https://mail.google.com/mail/u/0/#drafts")


if __name__ == "__main__":
    main()
