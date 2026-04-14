---
name: discord
description: Discord automation CLI — send/read/search messages, manage channels and servers, react, create threads, pin messages, and look up users.
---

# Discord automation with `discord_cli.py`

A bundled Python script that wraps the Discord REST API v10. Zero external dependencies — uses only Python stdlib (`urllib`, `json`, `argparse`).

Invoke as: `python3 <path-to-skill>/scripts/discord_cli.py <command> <subcommand> [args]`

## Setup

### 1. Create a Discord bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. Click **Bot** on the sidebar → click **Reset Token** → copy the token
3. **Critical**: Scroll down to **Privileged Gateway Intents** and enable **Message Content Intent** — without this, message content will be empty in API responses
4. Optionally enable **Server Members Intent** (needed for `user list`)

### 2. Add the bot to your server

1. Click **OAuth2** on the sidebar → scroll to **OAuth2 URL Generator**
2. Check scopes: `bot` + `applications.commands`
3. Under **Bot Permissions**, check: View Channels, Send Messages, Read Message History, Add Reactions, Attach Files
4. Copy the generated URL → open in browser → select your server → **Authorize**

Shortcut if you know the client ID:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot+applications.commands&permissions=274877975552
```

### 3. Set your bot token

```bash
export DISCORD_BOT_TOKEN="your_token_here"
```

### 4. Verify

```bash
python3 <path-to-skill>/scripts/discord_cli.py auth test
```

Expected output:
```json
{"ok": true, "user": "your-bot-name", "id": "...", "discriminator": "..."}
```

## Commands

### Auth

```bash
python3 <path-to-skill>/scripts/discord_cli.py auth test
```

### Servers

```bash
python3 <path-to-skill>/scripts/discord_cli.py server list
python3 <path-to-skill>/scripts/discord_cli.py server info <server-id>
```

### Channels

```bash
python3 <path-to-skill>/scripts/discord_cli.py channel list <server-id>
```

Returns text, announcement, and forum channels sorted by category and position. Each channel has `id`, `name`, `type`, `category`, and `topic`.

### Messages

```bash
# List recent messages (default 25, chronological order)
python3 <path-to-skill>/scripts/discord_cli.py message list <channel-id>
python3 <path-to-skill>/scripts/discord_cli.py message list <channel-id> --limit 50

# Get a single message
python3 <path-to-skill>/scripts/discord_cli.py message get <channel-id> <message-id>

# Send a message
python3 <path-to-skill>/scripts/discord_cli.py message send <channel-id> "Hello from the agent!"

# Edit a message (bot can only edit its own messages)
python3 <path-to-skill>/scripts/discord_cli.py message edit <channel-id> <message-id> "Updated text"

# Delete a message
python3 <path-to-skill>/scripts/discord_cli.py message delete <channel-id> <message-id>

# Search messages in a server
python3 <path-to-skill>/scripts/discord_cli.py message search <server-id> "query"
python3 <path-to-skill>/scripts/discord_cli.py message search <server-id> "query" --channel-id <id> --author-id <id> --limit 10
```

### Reactions

```bash
python3 <path-to-skill>/scripts/discord_cli.py reaction add <channel-id> <message-id> 👍
python3 <path-to-skill>/scripts/discord_cli.py reaction remove <channel-id> <message-id> 👍
python3 <path-to-skill>/scripts/discord_cli.py reaction list <channel-id> <message-id>
```

### Threads

```bash
# Create a new thread in a channel
python3 <path-to-skill>/scripts/discord_cli.py thread create <channel-id> "Discussion Topic"

# Create a thread from a specific message
python3 <path-to-skill>/scripts/discord_cli.py thread create <channel-id> "Bug Triage" --message-id <id>
```

### Pins

```bash
python3 <path-to-skill>/scripts/discord_cli.py pin list <channel-id>
python3 <path-to-skill>/scripts/discord_cli.py pin add <channel-id> <message-id>
python3 <path-to-skill>/scripts/discord_cli.py pin remove <channel-id> <message-id>
```

### Users

```bash
python3 <path-to-skill>/scripts/discord_cli.py user list <server-id>
python3 <path-to-skill>/scripts/discord_cli.py user list <server-id> --limit 200
python3 <path-to-skill>/scripts/discord_cli.py user info <user-id>
```

Mention users in messages as `<@USER_ID>`.

## Output format

All commands output JSON to stdout. Errors go to stderr with an `error` field and HTTP `status` code.

Message objects include: `id`, `author`, `author_id`, `content`, `timestamp`, plus optional `thread_id`, `attachments` (with `filename` and `url`), and `reactions` (with `emoji` and `count`). Null and empty fields are pruned.

## Troubleshooting

### Message content is empty

**Message Content Intent** is not enabled. Go to Developer Portal → Bot → Privileged Gateway Intents → toggle on Message Content Intent.

### `user list` returns empty or partial results

**Server Members Intent** is not enabled. Toggle it on in the same intents section.

### 403 / missing access errors

The bot doesn't have permission for that channel. Check bot role permissions in Discord server settings, or re-authorize with the correct permissions.

### Token errors

If the bot token was rotated, update `DISCORD_BOT_TOKEN` with the new value.

## Notes

- Discord uses **Snowflake IDs** (large numbers like `1161736244074659893`) for all identifiers. You cannot use channel names directly — use `channel list <server-id>` to find IDs first.
- The bot can only access servers it has been invited to and channels it has permissions for.
- Bot token auth uses the official Discord API — no user token extraction, no ToS risk.
- Messages are returned in chronological order (oldest first).
