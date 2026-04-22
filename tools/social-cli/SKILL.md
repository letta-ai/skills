---
name: social-cli
description: Agent-optimized CLI for Bluesky (ATProto) and X (Twitter). YAML in, YAML out, exit codes for automation. Use when the task involves posting, replying, reading feeds, searching, annotating URLs, or running a sync/check/dispatch agent loop across social platforms.
---

# social-cli

Agent-optimized social CLI. Bluesky + X. YAML in, YAML out, exit codes for automation.

Repo: https://github.com/letta-ai/social-cli

## Setup

### 1. Install

```bash
git clone https://github.com/letta-ai/social-cli.git
cd social-cli
pnpm install
pnpm build
```

Link the binary globally or invoke via `node dist/cli.js` / `pnpm start` from the repo directory.

### 2. Credentials

Create a `.env` in the working directory where you run `social-cli`:

```bash
# Bluesky / ATProto
ATPROTO_HANDLE=you.bsky.social
ATPROTO_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ATPROTO_PDS=https://bsky.social          # optional, defaults to bsky.social

# X / Twitter (OAuth 1.0a)
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
X_BEARER_TOKEN=...                       # optional, for app-only endpoints
```

Only credentials for platforms you actually use are required.

### 3. Verify

```bash
social-cli whoami
social-cli rate-limits
```

## Agent loop (sync → check → dispatch)

The canonical automation workflow. Each phase reads/writes YAML files in the working directory.

```bash
social-cli sync                    # pull notifications → inbox-{platform}.yaml
social-cli check || exit 0         # anything actionable? exit 1 = nothing to do
# read inbox, decide, write outbox-{platform}.yaml
social-cli dispatch                # execute outbox, archive results
```

- `sync`: deduplicates against `sent_ledger-{platform}.yaml` and caps inbox size.
- `check`: exits 0 if inbox has actionable items, 1 otherwise. Wrap with `|| exit 0` in cron loops.
- `dispatch`: executes the outbox atomically. Writes `dispatch_result-{platform}.yaml` and appends to `sent_ledger-{platform}.yaml` for replay protection.

## Quick commands

```bash
# Post / reply / thread
social-cli post "Hello world" -p bsky
social-cli reply "Thanks" --id "at://did:plc:.../app.bsky.feed.post/abc" -p bsky
social-cli thread "p1" "p2" "p3" -p bsky

# Engagement
social-cli like "at://..." -p bsky
social-cli delete "at://..." -p bsky
social-cli follow "handle.bsky.social" -p bsky

# Reading
social-cli search "query" -p bsky -n 10              # → stdout YAML
social-cli feed -p bsky -n 20                        # → feed.yaml (or -o - for stdout)
social-cli feed --feed "at://did:.../app.bsky.feed.generator/name" -n 10  # custom feed
social-cli profile "handle.bsky.social" -p bsky
social-cli whoami
social-cli rate-limits
```

## Annotations (Bluesky only)

Uses the `at.margin.note` lexicon (W3C Web Annotation model). Annotations work on any URL, not just ATProto posts. They appear in margin.at and Semble.

```bash
# Annotate a web page
social-cli annotate "Note about this article" --target https://example.com

# Anchor to an exact passage
social-cli annotate "Key insight" --target https://example.com \
  --quote "exact passage from the page" --motivation highlighting
```

Motivations: `commenting`, `highlighting`, `questioning`, `describing`, `linking`.

## Inbox format (`inbox-{platform}.yaml`)

```yaml
notifications:
  - id: "at://did:plc:xxx/app.bsky.feed.post/abc"
    platform: bsky
    type: mention          # mention, reply, like, follow, repost, quote
    author: someone.bsky.social
    authorId: "did:plc:xxx"
    postId: "at://..."
    text: "Hey, what do you think?"
    timestamp: "2026-03-25T12:00:00Z"
    parentPostId: "at://..."     # for replies
    parentPostText: "..."        # context
    rootPostId: "at://..."       # thread root
    rootPostText: "..."
```

## Outbox format (`outbox-{platform}.yaml`)

Write decisions as a `dispatch` list. Each entry is a single action.

```yaml
dispatch:
  - reply:
      platform: bsky
      id: "at://did:plc:xxx/app.bsky.feed.post/abc"
      text: "Thanks for the mention"

  - post:
      text: "Hello from my agent"
      platforms: [bsky, x]          # post to both

  - thread:
      platform: bsky
      posts:
        - "Thread post 1"
        - "Thread post 2"

  - like:
      platform: bsky
      id: "at://..."

  - annotate:
      platform: bsky
      id: "https://example.com/article"
      text: "Key observation"
      motivation: commenting
      quote: "exact text to anchor to"

  - ignore:
      id: "notif_003"
      reason: "spam"
```

## Dispatch results and exit codes

`dispatch_result-{platform}.yaml` is written after every dispatch. Exit codes:

| Code | Meaning |
|------|---------|
| 0 | All actions succeeded |
| 1 | Invalid outbox (schema error, missing creds) |
| 2 | Partial failure (some succeeded, some failed) |

Thread failures include a `resumeFrom` field with the index and remaining posts so you can retry just the tail.

## Character limits

| Platform | Limit |
|----------|-------|
| Bluesky | 300 chars |
| X | 280 chars |

The CLI rejects over-limit posts before hitting the API.

## Platform differences

| Feature | Bluesky | X |
|---------|---------|---|
| Annotations (`at.margin.note`) | Yes | No |
| Search | Yes | Yes |
| Feed | Yes (custom feeds) | Yes (home/user) |
| Threads | Yes | Yes |
| Notifications | mention, reply, like, follow, repost, quote | mentions only |
| Quote post context | Yes | Yes |

## Resilience

- Retries 3x with exponential backoff on 429s, 5xx, and network errors. Respects `Retry-After`.
- Bluesky session auto-refreshes on token expiry.
- Atomic file writes (tmp + rename) — no partial inbox/outbox corruption.
- Thread resume on partial failure via `resumeFrom`.
- `sent_ledger-{platform}.yaml` prevents duplicate dispatch across runs.

## Working directory layout

Everything is scoped to your current working directory, so you can run multiple agents with isolated state:

```
./
├── .env
├── inbox-bsky.yaml          # sync output
├── inbox-x.yaml
├── outbox-bsky.yaml         # your decisions
├── outbox-x.yaml
├── dispatch_result-bsky.yaml  # last dispatch outcome
├── dispatch_result-x.yaml
├── sent_ledger-bsky.yaml      # replay protection
├── sent_ledger-x.yaml
└── feed.yaml                  # optional feed snapshots
```

## References

- `references/commands.md`: full command map with all flags
- `references/outbox-schema.md`: complete outbox YAML schema
- `references/agent-loop.md`: patterns for cron/systemd automation loops
