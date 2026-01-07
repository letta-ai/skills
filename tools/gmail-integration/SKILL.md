---
name: gmail-integration
description: Connect Letta Code to Gmail via OAuth 2.0 and perform email operations. Use when a user wants to set up Gmail access, search their inbox, read emails, create draft messages, or manage their inbox. Triggers on queries about email, Gmail, inbox, drafting messages, or searching mail.
license: Complete terms in LICENSE.txt
---

# Gmail Integration

This skill enables Gmail integration via the Google Gmail API with OAuth 2.0 authentication. It provides scripts for searching emails, reading content, creating drafts, finding emails needing replies, and archiving messages.

## Prerequisites

Before using this skill, ensure:
1. Python 3.10+ is available
2. A Google Cloud project with Gmail API enabled
3. OAuth 2.0 credentials (`credentials.json`) downloaded
4. Required packages installed: `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`

## OAuth Setup Walkthrough

If the user hasn't set up Gmail API access yet, guide them through these steps:

### Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Library**
4. Search for "Gmail API" and click **Enable**

### Step 2: Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Fill in app name and support email
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/gmail.modify` (for archiving/labeling)
5. Add user's email as a test user
6. Save and continue

### Step 3: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as application type
4. Download JSON and rename to `credentials.json`
5. Place in project directory

### Step 4: Install Dependencies
```bash
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib
# or
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Step 5: First Authentication
Run any script (e.g., `search_emails.py`) - it will open a browser for OAuth consent. After authorization, a `token.json` is saved for future use.

## Email Operations

All scripts are in the `scripts/` directory. They share authentication logic and expect `credentials.json` in the same directory (or path specified via `--credentials`).

### Search Emails
```bash
python scripts/search_emails.py "from:someone@example.com" --max-results 10
python scripts/search_emails.py "subject:meeting after:2024/01/01"
python scripts/search_emails.py "is:unread"
python scripts/search_emails.py "in:inbox" --json  # Output as JSON
```

### Read Email
```bash
python scripts/read_email.py <message_id>
python scripts/read_email.py <message_id> --format full  # includes attachments info
```

### Create Draft
```bash
# New email
python scripts/create_draft.py --to "recipient@example.com" --subject "Hello" --body "Message content"
python scripts/create_draft.py --to "a@example.com" --cc "b@example.com" --subject "Update" --body-file message.txt

# HTML email with links
python scripts/create_draft.py --to "recipient@example.com" --subject "Hello" --body "<a href='https://example.com'>link</a>" --html

# IMPORTANT: Reply in same thread (required for proper threading!)
python scripts/create_draft.py --to "person@email.com" --subject "Re: Original Subject" \
  --reply-to "<message-id-header@mail.gmail.com>" \
  --thread-id "thread_id_here" \
  --body "Your reply"
```

⚠️ **Threading replies**: To reply in the same email thread (not create a new conversation), you MUST include:
- `--reply-to`: The `Message-ID` header from the email you're replying to
- `--thread-id`: The Gmail thread ID

To get these values, read the email with `read_email.py` and check the message metadata, or use this Python snippet:
```python
msg_data = service.users().messages().get(userId="me", id=msg_id, format="metadata", metadataHeaders=["Message-ID"]).execute()
thread_id = msg_data.get("threadId")
message_id_header = next(h["value"] for h in msg_data["payload"]["headers"] if h["name"] == "Message-ID")
```

### Find Emails Needing Reply
Identifies emails where you haven't replied, or your only reply is an unsent draft:
```bash
python scripts/needs_reply.py                          # Check inbox for emails needing reply
python scripts/needs_reply.py --max-results 30         # Check more emails
python scripts/needs_reply.py --query "is:important"   # Filter to important emails
python scripts/needs_reply.py --json                   # Output as JSON
```

Status indicators:
- 🔴 UNREAD - New email you haven't read
- 📝 DRAFT UNSENT - You started a reply but never sent it
- ⏳ NEEDS REPLY - Read but not replied to

### Archive Emails
Archive emails by removing the INBOX label (requires `gmail.modify` scope):
```python
service.users().messages().modify(
    userId="me",
    id=msg_id,
    body={"removeLabelIds": ["INBOX"]}
).execute()
```

For bulk archiving, use batch requests (max 100 per batch):
```python
batch = service.new_batch_http_request()
for msg in messages[:50]:  # Keep under 100 limit
    batch.add(service.users().messages().modify(
        userId="me", id=msg["id"], body={"removeLabelIds": ["INBOX"]}
    ))
batch.execute()
```

## Common Workflows

### Find and reply to an email (properly threaded)
1. Search for the email: `search_emails.py "from:person subject:topic" --json`
2. Get the message ID from results, then read it: `read_email.py <message_id>`
3. Get threading info (thread_id and Message-ID header) from the email metadata
4. Create a threaded draft reply:
   ```bash
   create_draft.py --to "person@email.com" --subject "Re: topic" \
     --reply-to "<Message-ID-header>" --thread-id "<thread_id>" \
     --body "Your reply"
   ```

### Find emails needing reply
1. Run: `needs_reply.py --max-results 30`
2. Review emails marked as 🔴 UNREAD, 📝 DRAFT UNSENT, or ⏳ NEEDS REPLY
3. For each email needing reply, get its thread_id and Message-ID, then draft a threaded response

### Inbox triage (complete workflow)
1. Run `needs_reply.py --max-results 50` to get all emails needing attention
2. **Filter out noise** - Identify and archive:
   - Newsletters (from: noreply, notifications, news@, etc.)
   - Receipts and invoices (from: receipts@, invoice@)
   - Automated alerts (from: alerts@, alert@)
   - Marketing emails (promotions, etc.)
   - Transaction notifications (banking, expense tools)
3. **Categorize real emails**:
   - 📝 DRAFT UNSENT - You started but didn't send (finish or delete draft)
   - 🔴 UNREAD from real people - Read and respond
   - ⏳ NEEDS REPLY - Prioritize by importance
4. Draft threaded responses (always use --reply-to and --thread-id)
5. Archive remaining notifications in bulk

### Identifying newsletters vs real emails
Common newsletter/notification patterns to archive:
- `from:noreply` or `from:no-reply`
- `from:notifications@` or `from:alerts@`
- `from:news@` or `from:newsletter@`
- `from:*@substack.com` (newsletters)
- `from:receipts@` or `from:invoice@`
- `from:*@stripe.com` (payment receipts)
- Monitoring: Datadog, PlanetScale, Better Stack, etc.

## Drafting Emails Best Practices

When drafting emails:
- Always use HTML format (`--html`) when including links
- Hyperlink text like "here" rather than showing raw URLs
- Include proper threading with `--reply-to` and `--thread-id` for replies
- Consider creating a memory block to store the user's email style preferences (greeting, signature, tone)

## Search Query Syntax

For complex searches, see [reference/search_operators.md](reference/search_operators.md) for Gmail search operators.

Common operators:
- `from:` / `to:` - Filter by sender/recipient
- `subject:` - Search in subject line
- `is:unread` / `is:read` - Filter by read status
- `in:inbox` / `in:sent` / `in:drafts` - Filter by location
- `after:` / `before:` - Date filters (YYYY/MM/DD format)
- `has:attachment` - Emails with attachments
- `larger:` / `smaller:` - Filter by size

## API Limits & Gotchas

- **Batch request limit**: Max 100 requests per batch (use 50 to be safe)
- **Rate limits**: Gmail API has daily quotas; batch operations help stay under limits
- **Threading gotcha**: Drafts without `--reply-to` and `--thread-id` create NEW threads, not replies
- **Draft detection**: Unsent drafts don't count as replies - `needs_reply.py` handles this correctly
- **Token expiry**: Tokens auto-refresh, but if authentication fails, delete `token.json` and re-auth

## Security Notes

- `credentials.json` contains OAuth client secrets - do not commit to version control
- `token.json` contains access tokens - do not share or commit
- Add both to `.gitignore`
- Tokens can be revoked at https://myaccount.google.com/permissions
