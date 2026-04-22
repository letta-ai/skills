# Outbox YAML schema

`outbox-{platform}.yaml` describes actions to execute via `social-cli dispatch`.

```yaml
dispatch:
  - <action-type>:
      <fields>
  - <action-type>:
      <fields>
```

## Action types

### `post`

Create a new post.

```yaml
- post:
    text: "Hello world"
    platforms: [bsky, x]         # post to one or more platforms
    images:                       # optional, up to 4
      - path: "./photo.jpg"
        alt: "description of image"
```

### `reply`

Reply to an existing post.

```yaml
- reply:
    platform: bsky
    id: "at://did:plc:xxx/app.bsky.feed.post/abc"   # or tweet ID for X
    text: "Thanks for the mention"
```

### `thread`

Post a thread (each entry becomes a reply to the previous).

```yaml
- thread:
    platform: bsky
    posts:
      - "Post 1 of thread"
      - "Post 2 of thread"
      - "Post 3 of thread"
```

On partial failure, `dispatch_result` includes `resumeFrom` with the next index to retry.

### `like`

Like a post.

```yaml
- like:
    platform: bsky
    id: "at://..."
```

### `follow`

Follow a user.

```yaml
- follow:
    platform: bsky
    handle: "handle.bsky.social"   # or DID
```

### `annotate` (Bluesky only)

Create an annotation on any URL using the `at.margin.note` lexicon.

```yaml
- annotate:
    platform: bsky
    id: "https://example.com/article"
    text: "My note"
    motivation: commenting               # commenting | highlighting | questioning | describing | linking
    quote: "exact text to anchor to"     # optional
```

### `delete`

Delete one of your posts.

```yaml
- delete:
    platform: bsky
    id: "at://..."
```

### `ignore`

Mark an inbox item as handled without taking action. Prevents re-processing on next sync.

```yaml
- ignore:
    id: "notif_003"
    reason: "spam"
```

## Validation

- Over-limit text is rejected before any API call (300 chars bsky, 280 chars X).
- Missing credentials for the target platform cause dispatch to exit 1 with an error.
- Unknown action types cause exit 1.

## Dispatch result format

`dispatch_result-{platform}.yaml` after run:

```yaml
results:
  - action: reply
    status: success              # success | failed
    postId: "at://..."           # populated on success
    error: "..."                 # populated on failure
  - action: thread
    status: partial
    completed: 2
    resumeFrom: 2                # retry from index 2
    remaining: ["Post 3", "Post 4"]
```
