# Asana Setup Guide

This guide explains how to set up authentication for the Asana skill.

## Getting a Personal Access Token

1. Log in to Asana at https://app.asana.com
2. Click your profile picture in the top right
3. Select **My Settings**
4. Go to the **Apps** tab
5. Click **Manage Developer Apps**
6. Click **Create new token** under "Personal access tokens"
7. Give it a name (e.g., "Claude Code")
8. Copy the token immediately - you won't be able to see it again

## Setting the Environment Variable

### macOS / Linux

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export ASANA_ACCESS_TOKEN="your_token_here"
```

Then reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Per-session

Set it just for the current terminal session:
```bash
export ASANA_ACCESS_TOKEN="your_token_here"
```

### In a .env file

If your project uses dotenv, add to `.env`:
```
ASANA_ACCESS_TOKEN=your_token_here
```

## Optional: Default Workspace

If you work with multiple Asana workspaces, you can set a default:

```bash
export ASANA_WORKSPACE="your_workspace_gid"
```

To find your workspace GID:
```bash
python3 scripts/asana_client.py workspaces
```

## Verifying Setup

Test that your token works:

```bash
python3 scripts/asana_client.py workspaces
```

You should see a list of your Asana workspaces.

## Security Notes

- **Never commit your token** to version control
- Add `.env` to your `.gitignore`
- Personal Access Tokens have full access to your Asana account
- You can revoke tokens anytime from the Asana Developer Console

## Troubleshooting

### "No Asana token provided"

The `ASANA_ACCESS_TOKEN` environment variable is not set. Check:
- The variable is exported (not just assigned)
- You've reloaded your shell after editing the profile
- The variable is available in your current terminal: `echo $ASANA_ACCESS_TOKEN`

### "Authentication failed"

Your token may be invalid or expired. Generate a new one from the Asana Developer Console.

### "No workspaces found"

Your token is valid but doesn't have access to any workspaces. This can happen if:
- You're a guest in workspaces (guests have limited API access)
- The token was created with limited scopes

### Rate Limiting

Asana has API rate limits. If you see "Rate limited" errors:
- Wait the specified time before retrying
- Avoid running many operations in quick succession
- The client automatically handles reasonable rate limiting
