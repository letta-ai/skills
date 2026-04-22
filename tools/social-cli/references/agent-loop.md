# Agent loop patterns

## Minimal cron loop

Runs every 10 minutes, exits quietly when there's nothing to do.

```bash
#!/usr/bin/env bash
set -euo pipefail
cd ~/my-agent

social-cli sync
social-cli check || exit 0

# Your agent logic here — read inbox, write outbox
node generate-outbox.js

social-cli dispatch
```

Crontab:

```
*/10 * * * * /usr/local/bin/my-agent-run.sh >> /var/log/my-agent.log 2>&1
```

## Per-platform isolation

Run each platform in its own working directory to isolate state:

```bash
cd ~/agents/bsky-only
social-cli sync -p bsky
# ...

cd ~/agents/x-only
social-cli sync -p x
# ...
```

Each directory has its own `.env`, `inbox-*.yaml`, `outbox-*.yaml`, and `sent_ledger-*.yaml`.

## LLM-driven outbox generation

A common pattern: sync the inbox, feed it to an LLM, parse the response into an outbox.

```bash
social-cli sync -p bsky

# Convert inbox to a prompt the LLM can reason about
INBOX=$(cat inbox-bsky.yaml)

# Generate outbox via your LLM provider of choice
# (example pseudo-script)
my-llm-cli --system-prompt reply-decider.md --input "$INBOX" > outbox-bsky.yaml

social-cli dispatch
```

## Handling partial thread failures

When `dispatch_result-{platform}.yaml` shows `status: partial`, the `resumeFrom` index tells you where to restart:

```bash
social-cli dispatch

# If the exit code was 2 and the result shows a partial thread
if grep -q "status: partial" dispatch_result-bsky.yaml; then
  # Regenerate outbox with only the remaining posts
  jq '.remaining' dispatch_result-bsky.yaml > next-outbox.yaml
  # Retry on next run
fi
```

## Rate limit awareness

`social-cli rate-limits` reports remaining quota per platform. Gate dispatches when low:

```bash
REMAINING=$(social-cli rate-limits -p x --field remaining)
if [ "$REMAINING" -lt 10 ]; then
  echo "Low X rate limit, skipping" >&2
  exit 0
fi
```

## Replay protection

Every successful action is appended to `sent_ledger-{platform}.yaml`. Subsequent `sync` runs filter the inbox against this ledger, so the same notification never produces two actions.

Do not manually edit the ledger unless you know what you're doing. Deleting it causes every past notification to re-appear in the next inbox.
