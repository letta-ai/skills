# social-cli command reference

## Agent loop

| Command | Effect |
|---------|--------|
| `social-cli sync` | Pull notifications into `inbox-{platform}.yaml`, deduplicated against the sent ledger |
| `social-cli check` | Exit 0 if inbox has actionable items, exit 1 if nothing to do |
| `social-cli dispatch` | Execute `outbox-{platform}.yaml`, write `dispatch_result-{platform}.yaml`, append to sent ledger |

## Posting

| Command | Flags |
|---------|-------|
| `social-cli post <text>` | `-p <platform>` (required), `--reply-to <id>`, `--quote <id>`, `--image <path>` (repeatable) |
| `social-cli reply <text>` | `--id <at-uri-or-tweet-id>` (required), `-p <platform>` |
| `social-cli thread <post1> <post2> ...` | `-p <platform>`, `--resume-from <index>` |

## Engagement

| Command | Flags |
|---------|-------|
| `social-cli like <id>` | `-p <platform>` |
| `social-cli delete <id>` | `-p <platform>` |
| `social-cli follow <handle-or-id>` | `-p <platform>` |

## Reading

| Command | Flags |
|---------|-------|
| `social-cli search <query>` | `-p <platform>`, `-n <count>`, `-o <path\|->` |
| `social-cli feed` | `-p <platform>`, `-n <count>`, `--feed <at-uri>`, `-o <path\|->` |
| `social-cli profile <handle>` | `-p <platform>` |
| `social-cli posts <handle>` | `-p <platform>`, `-n <count>` |
| `social-cli whoami` | — |
| `social-cli rate-limits` | — |
| `social-cli blog <handle>` | `-p bsky` (ATProto blog reader) |

## Annotations (Bluesky only)

| Command | Flags |
|---------|-------|
| `social-cli annotate <text>` | `--target <url>` (required), `--quote <passage>`, `--motivation <type>` |

Motivations: `commenting`, `highlighting`, `questioning`, `describing`, `linking`.

## Profile management

| Command | Flags |
|---------|-------|
| `social-cli profile-update` | `--display-name <name>`, `--bio <text>`, `--avatar <path>`, `-p <platform>` |

## Output format

- Commands that write files default to `{action}-{platform}.yaml` in cwd.
- Pass `-o -` to write to stdout instead.
- Pass `-o <path>` to write to a specific file.
- All output is YAML.

## Global flags

| Flag | Effect |
|------|--------|
| `-p, --platform <bsky\|x>` | Platform selector (required for most commands) |
| `-n, --limit <count>` | Result count cap |
| `-o, --output <path\|->` | Output destination (`-` for stdout) |
| `--verbose` | Detailed logging |
| `--help` | Per-command help |
