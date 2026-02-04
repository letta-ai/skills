#!/usr/bin/env python3
"""Gmail API authentication utilities.

Shared authentication logic for all Gmail scripts.
"""

import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Default scopes for reading, composing, and modifying (not sending)
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_credentials_path(custom_path: Optional[str] = None) -> Path:
    """Get path to credentials.json file."""
    if custom_path:
        return Path(custom_path)
    
    # Check environment variable
    env_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
    if env_path:
        return Path(env_path)
    
    # Default to skill root directory (parent of scripts directory)
    return Path(__file__).parent.parent / "credentials.json"


def get_token_path(credentials_path: Path) -> Path:
    """Get path to token.json file (same directory as credentials)."""
    return credentials_path.parent / "token.json"


def authenticate(
    credentials_path: Optional[str] = None,
    scopes: Optional[list[str]] = None,
) -> Credentials:
    """Authenticate with Gmail API and return credentials.
    
    Args:
        credentials_path: Path to credentials.json file
        scopes: OAuth scopes to request (defaults to readonly + compose)
    
    Returns:
        Authenticated credentials object
    """
    scopes = scopes or DEFAULT_SCOPES
    creds_path = get_credentials_path(credentials_path)
    token_path = get_token_path(creds_path)
    
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found at {creds_path}\n"
            "Please download OAuth credentials from Google Cloud Console."
        )
    
    creds = None
    
    # Load existing token if available
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    
    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
            creds = flow.run_local_server(port=0)
        
        # Save token for future use with restricted permissions
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        os.chmod(token_path, 0o600)  # Restrict to owner-only access
        print(f"Token saved to {token_path}")
    
    return creds


def get_gmail_service(credentials_path: Optional[str] = None):
    """Get authenticated Gmail API service.
    
    Args:
        credentials_path: Path to credentials.json file
    
    Returns:
        Gmail API service object
    """
    creds = authenticate(credentials_path)
    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    # Test authentication
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Gmail authentication")
    parser.add_argument("--credentials", help="Path to credentials.json")
    args = parser.parse_args()
    
    service = get_gmail_service(args.credentials)
    profile = service.users().getProfile(userId="me").execute()
    
    print(f"Authenticated as: {profile['emailAddress']}")
    print(f"Total messages: {profile['messagesTotal']}")
    print(f"Total threads: {profile['threadsTotal']}")
