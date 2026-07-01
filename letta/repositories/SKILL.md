---
name: repositories
description: Create, list, attach, detach, and edit Letta-hosted repositories for agents through the Letta Cloud repositories API. Use when an agent needs shared git-backed files outside its memory repo, needs to attach itself to an existing repository, or needs to read/write repository files.
license: MIT
---

# Letta Repositories Skill

Use Letta-hosted repositories to give agents durable, git-backed project files outside their memory repo. A repository can be attached to one or more agents, and an agent can have multiple attached repositories.

Attached repositories appear to the agent in the system prompt under `<repositories>` with paths like:

```text
$MEMORY_DIR/../<repository-name>
```

In hosted sandboxes, attached repositories are cloned next to the agent's memory checkout. In other runtimes, use the API operations below when the files are not present on disk.

## Authentication

Set `LETTA_API_KEY` for a user or service account in the organization that owns the target agent/repositories:

```bash
export LETTA_API_KEY="..."
export LETTA_BASE_URL="https://api.letta.com"  # optional; defaults to Letta Cloud
```

All requests use bearer auth:

```bash
-H "Authorization: Bearer $LETTA_API_KEY"
```

The API key's organization controls visibility and access:

- `GET /v1/repositories` lists repositories in that organization.
- `POST /v1/agents/{agent_id}/repositories` can attach only repositories from the same organization as the agent.
- Cross-organization attaches return `403 Forbidden`.
- Missing/invalid IDs return `404`.
- The `memory` repository is the agent's primary repo and cannot be detached.

If you are an agent attaching yourself, use `$LETTA_AGENT_ID` when available, otherwise ask the user for the agent ID.

## Repository rules

Repository names:

- must be 1-64 characters
- may contain only letters, numbers, dots, underscores, and hyphens
- cannot have leading/trailing whitespace
- cannot be `.` or `..`
- cannot be reserved names: `memory`, `artifacts`

File rules:

- Paths are normalized to remove leading `/`, collapse `.`, and reject `..` and `.git/*`.
- File content is UTF-8 text.
- File content max is 100 KB per create/update call.
- Each repository is limited to 2,000 files.
- `updateFile` supports a `content_sha256` precondition; use it to avoid overwriting concurrent changes.

Permissions for attached repositories:

- `read` — agent should treat repository as read-only.
- `read_write` — agent may modify repository files. This is the default if omitted.

## Quick setup

```bash
BASE_URL="${LETTA_BASE_URL:-https://api.letta.com}"
AUTH=(-H "Authorization: Bearer $LETTA_API_KEY" -H "Content-Type: application/json")
AGENT_ID="${LETTA_AGENT_ID:-agent-...}"
```

## Common operations

### List organization repositories

```bash
curl -sS "${BASE_URL}/v1/repositories?limit=50&offset=0" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

Response:

```json
{
  "repositories": [
    { "id": "repo-api-...", "name": "project-notes", "created_at": "...", "updated_at": "..." }
  ],
  "has_next_page": false
}
```

### Create a repository

```bash
curl -sS -X POST "${BASE_URL}/v1/repositories" \
  "${AUTH[@]}" \
  -d '{"name":"project-notes"}'
```

### Get repository metadata

```bash
REPOSITORY_ID="repo-api-..."

curl -sS "${BASE_URL}/v1/repositories/${REPOSITORY_ID}" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

### Attach a repository to yourself or another agent

```bash
curl -sS -X POST "${BASE_URL}/v1/agents/${AGENT_ID}/repositories" \
  "${AUTH[@]}" \
  -d "{\"repository_id\":\"${REPOSITORY_ID}\",\"permissions\":\"read_write\"}"
```

Response includes the attached repository as the agent will see it:

```json
{
  "success": true,
  "repository": {
    "id": "repo-api-...",
    "name": "project-notes",
    "is_primary": false,
    "permissions": "read_write"
  }
}
```

### List repositories attached to an agent

```bash
curl -sS "${BASE_URL}/v1/agents/${AGENT_ID}/repositories" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

The primary memory repo is returned as `name: "memory", is_primary: true`.

### Detach a repository from an agent

```bash
curl -sS -X DELETE "${BASE_URL}/v1/agents/${AGENT_ID}/repositories/${REPOSITORY_ID}" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

You cannot detach the primary `memory` repository.

## File operations

### List files

```bash
curl -sS "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/files?path_prefix=docs&depth=2" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

Query parameters:

- `path_prefix` optional directory/file prefix
- `depth` optional, 1-10, default 1
- `ref` optional git ref; `HEAD` resolves to `main`

Response:

```json
{
  "files": [
    { "path": "docs/README.md", "type": "file" },
    { "path": "docs/archive", "type": "directory" }
  ],
  "ref": "main"
}
```

### Create a file

```bash
curl -sS -X POST "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/files" \
  "${AUTH[@]}" \
  -d '{"path":"docs/README.md","content":"# Notes\n"}'
```

Returns `path`, `content_sha256`, and `commit_sha`. Existing paths return `409`.

### Read a file

```bash
curl -sS "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/files/content?path=docs/README.md" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

Response includes `content_sha256`. Save it before updating when you want concurrency protection.

### Update, rename, or move a file

Update content:

```bash
SHA="<content_sha256 from read>"

curl -sS -X POST "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/files/content" \
  "${AUTH[@]}" \
  -d "{\"path\":\"docs/README.md\",\"content\":\"# Updated notes\\n\",\"precondition\":{\"type\":\"content_sha256\",\"content_sha256\":\"${SHA}\"}}"
```

Rename/move without changing content:

```bash
curl -sS -X POST "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/files/content" \
  "${AUTH[@]}" \
  -d '{"path":"docs/README.md","new_path":"README.md"}'
```

Update and move in one commit by sending both `content` and `new_path`.

### Delete a file

```bash
curl -sS -X DELETE "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/files/content" \
  "${AUTH[@]}" \
  -d '{"path":"README.md"}'
```

## Versions

List repository history, optionally for one path:

```bash
curl -sS "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/versions?path=README.md&limit=20" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

Read a file at a specific commit:

```bash
COMMIT_SHA="..."

curl -sS "${BASE_URL}/v1/repositories/${REPOSITORY_ID}/versions/${COMMIT_SHA}?path=README.md" \
  -H "Authorization: Bearer $LETTA_API_KEY"
```

## Safer scripting helper

Use this Python helper for repeated operations. It handles bearer auth, JSON bodies, query parameters, error reporting, and common repository actions.

```python
#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("LETTA_BASE_URL", "https://api.letta.com").rstrip("/")
API_KEY = os.environ.get("LETTA_API_KEY")


def request(method, path, body=None, query=None):
    if not API_KEY:
        raise SystemExit("LETTA_API_KEY is required")
    url = BASE_URL + path
    if query:
        params = {k: v for k, v in query.items() if v is not None}
        if params:
            url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"Authorization": f"Bearer {API_KEY}"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8")
        print(f"HTTP {exc.code}: {text}", file=sys.stderr)
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Letta repositories API helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    create_repo = sub.add_parser("create")
    create_repo.add_argument("name")

    attached = sub.add_parser("attached")
    attached.add_argument("agent_id", nargs="?", default=os.environ.get("LETTA_AGENT_ID"))

    attach = sub.add_parser("attach")
    attach.add_argument("repository_id")
    attach.add_argument("agent_id", nargs="?", default=os.environ.get("LETTA_AGENT_ID"))
    attach.add_argument("--permissions", choices=["read", "read_write"], default="read_write")

    detach = sub.add_parser("detach")
    detach.add_argument("repository_id")
    detach.add_argument("agent_id", nargs="?", default=os.environ.get("LETTA_AGENT_ID"))

    files = sub.add_parser("files")
    files.add_argument("repository_id")
    files.add_argument("--path-prefix")
    files.add_argument("--depth", type=int)
    files.add_argument("--ref")

    read = sub.add_parser("read")
    read.add_argument("repository_id")
    read.add_argument("path")
    read.add_argument("--ref")

    write = sub.add_parser("write")
    write.add_argument("repository_id")
    write.add_argument("path")
    write.add_argument("content")
    write.add_argument("--sha", help="Expected current content_sha256")

    args = parser.parse_args()

    if args.cmd == "list":
        result = request("GET", "/v1/repositories", query={"limit": 100})
    elif args.cmd == "create":
        result = request("POST", "/v1/repositories", {"name": args.name})
    elif args.cmd == "attached":
        if not args.agent_id:
            raise SystemExit("agent_id or LETTA_AGENT_ID is required")
        result = request("GET", f"/v1/agents/{args.agent_id}/repositories")
    elif args.cmd == "attach":
        if not args.agent_id:
            raise SystemExit("agent_id or LETTA_AGENT_ID is required")
        result = request(
            "POST",
            f"/v1/agents/{args.agent_id}/repositories",
            {"repository_id": args.repository_id, "permissions": args.permissions},
        )
    elif args.cmd == "detach":
        if not args.agent_id:
            raise SystemExit("agent_id or LETTA_AGENT_ID is required")
        result = request("DELETE", f"/v1/agents/{args.agent_id}/repositories/{args.repository_id}")
    elif args.cmd == "files":
        result = request(
            "GET",
            f"/v1/repositories/{args.repository_id}/files",
            query={"path_prefix": args.path_prefix, "depth": args.depth, "ref": args.ref},
        )
    elif args.cmd == "read":
        result = request(
            "GET",
            f"/v1/repositories/{args.repository_id}/files/content",
            query={"path": args.path, "ref": args.ref},
        )
    elif args.cmd == "write":
        body = {"path": args.path, "content": args.content}
        if args.sha:
            body["precondition"] = {"type": "content_sha256", "content_sha256": args.sha}
        result = request("POST", f"/v1/repositories/{args.repository_id}/files/content", body)
    else:
        raise AssertionError(args.cmd)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

Example flow:

```bash
python letta_repos.py create shared-notes
python letta_repos.py list
python letta_repos.py attach repo-api-... "$LETTA_AGENT_ID" --permissions read_write
python letta_repos.py files repo-api-... --depth 3
python letta_repos.py write repo-api-... notes/todo.md $'- item 1\n'
```

## Recommended agent workflow

1. Check auth: verify `LETTA_API_KEY` is set; ask the user for the correct organization key if not.
2. Identify self: use `LETTA_AGENT_ID` when available.
3. List attached repositories: `GET /v1/agents/{agent_id}/repositories`.
4. If the needed repository is not attached, list org repositories and attach by ID.
5. Prefer reading files before updating and use `content_sha256` preconditions for edits.
6. Respect `permissions`: do not modify a repository attached as `read`.
7. After attaching, tell the user the repository may appear in prompt/filesystem context on the next agent context refresh or sandbox bootstrap.

## Troubleshooting

- `401 Unauthorized`: `LETTA_API_KEY` is missing, invalid, or expired.
- `403 Forbidden`: the API key organization does not match the agent/repository organization.
- `404 Repository not found`: wrong repository ID or not in this organization.
- `404 Agent not found`: wrong agent ID or not visible to this organization.
- `409 Repository name already exists`: choose a unique repository name.
- `409 File content precondition failed`: re-read the file and retry with the new `content_sha256`.
- `400 Cannot unlink primary repository`: `memory` is the agent's primary repo and cannot be detached.
