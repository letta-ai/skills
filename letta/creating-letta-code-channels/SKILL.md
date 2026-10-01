---
name: creating-letta-code-channels
description: Builds and debugs Letta Code channels, including first-party channel adapters and dynamic user channel plugins under ~/.letta/channels. Use when adding Telegram, WhatsApp, Bluesky, Slack, Discord, or custom channel support; testing channel routing, pairing, MessageChannel, runtime dependencies, or channel plugin manifests.
license: MIT
---

# Creating Letta Code channels

Use this when adding or debugging Letta Code channel support.

## First choice

- **User plugin** (`~/.letta/channels/<id>/`) for headless experiments, community plugins, and fast workflow tests.
- **First-party channel** (`src/channels/<id>/`) when the channel needs bespoke Desktop UI, custom account snapshots, Slack/Discord-style auto-routing, rich protocol fields, or migration/compatibility shims.

User plugins cannot shadow first-party ids: `telegram`, `slack`, and `discord` are ignored under `~/.letta/channels/`. Use ids like `telegram-test`, `whatsapp-community`, or `custom-chat`.

## Core workflow

1. Work in `~/letta/letta-code` or a worktree.
2. Read `src/channels/README.md` on branches with dynamic plugins.
3. For a user plugin, create:
   - `~/.letta/channels/<id>/channel.json`
   - `~/.letta/channels/<id>/plugin.mjs`
   - `~/.letta/channels/<id>/accounts.json`
4. Implement `messageActions` for both reply modes: explicit tool replies and automatic relay text use the common outbound adapter path.
5. Start with `dmPolicy: "pairing"` for testing, or `allowlist`/`open` for known headless deployments.
6. Test all four legs:
   - plugin discovery/import
   - inbound `adapter.onMessage(msg)` to route/pairing
   - routed channel notification reaches the agent
   - outbound behavior matches the account's captured reply mode: explicit `MessageChannel` delivery in tool mode, or automatic finalized-text delivery in relay mode
7. Run targeted tests, then `bun run typecheck`, `bun run lint`, `bun run build`.

## References

Read only what is needed:

- `references/user-plugins.md` — dynamic plugin manifest/account/runtime/headless flow and gotchas.
- `references/first-party-channels.md` — first-party channel file cascade and safety checks.
- `references/testing.md` — smoke-test checklist and commands.

## Scaffold helper

Use the bundled scaffold for a minimal user plugin skeleton. Replace `<path-to-this-skill>` with this skill directory path:

```bash
npx tsx <path-to-this-skill>/scripts/scaffold-user-channel-plugin.ts \
  my-channel "My Channel" \
  --runtime-package some-sdk@1.0.0 \
  --runtime-module some-sdk
```

It creates `channel.json`, `plugin.mjs`, and `accounts.example.json`. Replace the TODO inbound/outbound implementation with the real SDK calls.

## Hard lessons

- Accounts default to tool mode when `reply_mode` is unset or invalid. Add `"reply_mode": "relay"` to an existing saved account, preserving its actual ID, root fields, and credentials.
- Relay requires a build containing [PR 4043](https://github.com/letta-ai/letta-code/pull/4043); v0.34.1 predates it. The on-device gateway implements delivery; remote hosts must supply transport and captured per-input policy. This is a host distinction, not an agent-state restriction. Mode changes affect new inputs, not active or queued ones.
- A single-destination relay input sends finalized text without `MessageChannel`; unfinished error/cancel text, reasoning, and subagent output are excluded. Multi-destination inputs require explicit replies, never broadcasts. Queued inputs stay separate. Use tool mode for reactions, files, and proactive sends.
- For public channels, suppress tool approval/control prompts unless there is verified operator routing. Posting approval prompts publicly leaks tool input and invites forged `approve` replies.
- User plugin runtime resolution must not count parent/dev `node_modules`. Runtime modules should resolve from explicit runtime dirs only.
- Headless pairing is CLI-first: `letta channels pair --channel <id> --code <code> --agent <agent-id> --conversation <conversation-id>`.
- Running listeners reload `pairing.yaml` and `routing.yaml` on the next inbound miss; restart only when adapter/account config itself changed.
