---
name: bare-repo-worktrees
description: Git worktree operations using Worktrunk (wt). LOAD THIS SKILL whenever the user mentions "worktree", "new worktree", "create a worktree", "switch to a branch", "start work on a new feature/branch", or asks to work in a new/existing worktree. DO NOT run raw `git worktree` commands — this skill handles the bare repo pattern and hook lifecycle. If the user's memory mentions "worktrees/" paths, this skill is REQUIRED. Covers: creating worktrees, switching branches, cleanup, and the copy-ignored workflow for .env propagation.
---

# Bare Repo Worktrees

Keep all your worktrees inside one project folder — clean, organized, self-contained.

> **Tooling**: [Worktrunk](https://worktrunk.dev) (`wt`) is the preferred tool for all worktree operations. It wraps `git worktree` with ergonomic commands, lifecycle hooks, and `copy-ignored` for cache/env sharing. Install: `brew install worktrunk && wt config shell install`.

## Why

Standard `git worktree add ../feature` scatters directories alongside real repos. After a few months, you can't tell worktrees from clones at a glance.

The bare repo pattern fixes this:

```
my-project/
├── .bare/           # all git data (bare clone)
├── .git             # pointer FILE (not folder) → .bare
└── worktrees/       # ALL worktrees live here — primary and feature branches alike
    ├── dev/         # primary worktree — source of truth for shared files
    │   ├── .env     # REAL file (copied to new worktrees via copy-ignored)
    │   └── apps/
    │       └── server/.env  # REAL file
    ├── feat-my-feature/
    └── fix-some-bug/
```

**Key principles:**
- `worktrees/dev/` (or `worktrees/main/`) is the **primary worktree** and source of truth for all shared files
- **All** worktrees — primary and feature branches alike — live inside `worktrees/`, named using `{{ branch | sanitize }}` (slashes become dashes)
- Shared files (`.env`, build caches) are propagated to new worktrees automatically via `wt step copy-ignored` — no symlinks needed
- Tool-specific config folders that should be scoped to the whole project (not per-branch) belong at the **workspace root as real directories** — not inside worktrees, not as symlinks
- **Version manager config files** (`.prototools`, `.tool-versions`) must be **symlinked** at the workspace root to the primary worktree's file, so tools like proto/asdf resolve correct versions when the agent's shell starts in the workspace root (not a worktree). Create: `ln -s worktrees/dev/.prototools .prototools`

---

## Worktrunk Hooks (`.config/wt.toml`)

Commit this file to the repo — it's shared with the team and automates worktree setup:

```toml
# .config/wt.toml

[post-create]
# Blocking — runs before post-start hooks or --execute
# ⚠️  Only fires when creating a NEW worktree (wt switch --create)
deps = "pnpm install"   # Node.js
# deps = "uv sync"      # Python

[post-start]
# Background — runs after worktree is ready
# ⚠️  Only fires when creating a NEW worktree (wt switch --create)
copy = "wt step copy-ignored"   # copies .env, build caches from primary worktree

[post-switch]
# Background — runs after EVERY wt switch, including switching to existing worktrees
# Add this so deps stay current when you return to an old worktree
deps = "pnpm install"
```

> **Hook lifecycle summary**: `post-create` → new worktrees only (blocking). `post-start` → new worktrees only (background). `post-switch` → every switch, new or existing (background). If you only have `post-create` / `post-start`, running `wt switch dev` on an existing worktree will **not** install deps.

### `.worktreeinclude` — scope what `copy-ignored` copies

By default `copy-ignored` copies ALL gitignored files. Scope it with `.worktreeinclude`:

```
# .worktreeinclude
# Must be gitignored AND listed here to be copied.

# Environment files
.env
.envrc

# Build caches
# .next/ intentionally excluded — Next.js incremental cache is branch-specific;
# copying from dev can produce stale/incorrect builds on feature branches.
# .turbo/ is safe — content-addressed, stale entries are ignored.
.turbo/
```

> **`.next/` vs `.turbo/`**: Don't copy `.next/` — its incremental cache is tied to specific file content and can produce incorrect builds if copied across branches. Do copy `.turbo/` — it's content-addressed; stale entries are simply ignored, valid hits speed up first builds.

### Project hooks require one-time approval

The first `wt switch --create` after the config lands will prompt:
```
▲ repo needs approval to execute 2 commands: [y/N]
```
Press `y` — saved to `~/.config/worktrunk/config.toml`, never asked again (unless the command changes).

---

## Worktrunk User Config

`worktree-path` at the **top level** of `~/.config/worktrunk/config.toml` is a global default that applies to every repo. Per-project entries under `[projects."..."]` override it when needed.

```toml
# ~/.config/worktrunk/config.toml

# Global default — all repos use worktrees/<branch-sanitized>/
worktree-path = "worktrees/{{ branch | sanitize }}"
```

If one repo needs a different layout, override just that one:

```toml
# Override for a specific project only
[projects."github.com/org/legacy-repo"]
worktree-path = "../.worktrees/{{ branch | sanitize }}"
```

### Auto-sync primary worktree before switch

`wt switch --create` branches from the local default branch. If the primary worktree is behind `origin`, new worktrees start stale — causing merge conflicts later. Add a `pre-switch` hook to auto-pull:

```toml
# ~/.config/worktrunk/config.toml
[pre-switch]
sync = "git -C {{ primary_worktree_path }} pull --ff-only 2>/dev/null || true"
```

This runs before every `wt switch`, fast-forwarding the primary worktree to match origin. `--ff-only` ensures it never creates merge commits, and `|| true` means it won't block if there's no network.

For repos where the primary worktree is a sibling (not inside the repo):
```toml
[projects."github.com/org/other-repo"]
worktree-path = "../worktrees/{{ branch | sanitize }}"
```

---

## Daily Workflow

### Create a feature worktree (interactive terminal)

> **⚠️ CRITICAL: Run `wt switch --create` from INSIDE the primary worktree (e.g., `worktrees/dev/` or `worktrees/main/`), NOT from the workspace root.**
>
> If run from the workspace root, `git rev-parse --show-toplevel` fails (not a work tree), `wt` falls back to `git-common-dir` (`.bare/`), and the worktree is created at `.bare/worktrees/<branch>` instead of `worktrees/<branch>`. Those malformed worktrees cause pre-commit to fail (`git toplevel unexpectedly empty`).

```bash
# 1. cd into the primary worktree FIRST
cd worktrees/dev   # or worktrees/main

# 2. Create worktree + branch (shell integration required for cd)
wt switch --create feat/my-feature

# With a specific base branch:
wt switch --create feat/my-feature --base dev

# Create and immediately launch Letta Code:
wt switch --create feat/my-feature -x "letta code ."
```

Worktrunk runs `post-create` (blocking: deps install) then `post-start` (background: copy-ignored) automatically. If `[post-switch]` is configured, it also runs in the background after every switch.

### Create a feature worktree (non-interactive: Letta Code, CI, scripts)

**⚠️ Run from INSIDE the primary worktree** — same as interactive workflow. If run from workspace root, worktrees are created in `.bare/worktrees/` instead of `worktrees/`.

**⚠️ `post-start` hooks do NOT fire in non-interactive shells** — shell integration is not active, so `wt step copy-ignored` never runs. `.env` and other gitignored files won't be copied unless you run the hook commands manually.

```bash
# 1. cd into the primary worktree FIRST
cd worktrees/dev   # or worktrees/main

# 2. Create the worktree (post-create hooks like `uv sync` still run)
wt switch --create feat/my-feature

# 3. cd into the new worktree
cd worktrees/feat-my-feature

# 4. Manually run post-start hook commands that were skipped
wt step copy-ignored
```

**Always run `wt step copy-ignored` after `wt switch --create`** in non-interactive contexts. Without it, `.env` files, `.letta/` directories, and any other files listed in `.worktreeinclude` will be missing.

### List worktrees

```bash
wt list              # status: staged, unstaged, ahead/behind remote
git worktree list    # plain git fallback (paths only)
```

### Clean up after PR merge

> **⚠️ Don't run `wt remove` from inside the worktree you're removing.** Your shell's CWD becomes invalid and subsequent commands fail. Switch to the primary worktree (or workspace root) first.

```bash
# 1. Switch OUT of the worktree first
cd ~/projects/my-project       # workspace root
# or: wt switch ^              # switch to primary worktree

# 2. Then remove
wt remove feat/my-feature      # removes worktree + deletes branch if merged
wt step prune                  # removes ALL worktrees whose branches are merged
```

### Update primary worktree

```bash
cd ~/projects/my-project/worktrees/dev
git pull
```

---

## Option A: Fresh Setup (from GitHub URL)

```bash
# 1. Create the workspace directory
mkdir ~/projects/my-project && cd ~/projects/my-project

# 2. Bare clone (--single-branch avoids creating 60+ stale local branches)
git clone --bare --single-branch git@github.com:org/repo.git .bare

# 3. Create the .git POINTER FILE (not a folder — this is the magic)
echo "gitdir: ./.bare" > .git

# 4. Configure fetch for all remote branches
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 5. Portable paths (workspace can be moved without breaking)
git config worktree.useRelativePaths true

# 6. Enable commit signing
git config commit.gpgsign true

# 7. Fetch all remote branches
git fetch --all

# 8. Create the primary worktree inside worktrees/
mkdir -p worktrees
git worktree add worktrees/dev dev
git -C worktrees/dev branch --set-upstream-to=origin/dev dev

# 9. Copy secrets into worktrees/dev/ (source of truth)
cp /path/to/old/.env worktrees/dev/.env
cp /path/to/old/apps/server/.env worktrees/dev/apps/server/.env
# ... etc

# 10. Install dependencies
cd worktrees/dev && pnpm install   # Node
# cd worktrees/dev && uv sync      # Python

# 11. Add worktrunk config
mkdir -p .config
cat > .config/wt.toml << 'EOF'
[post-create]
deps = "pnpm install"

[post-start]
copy = "wt step copy-ignored"
EOF

# 12. Add .worktreeinclude to scope what copy-ignored copies
cat > worktrees/dev/.worktreeinclude << 'EOF'
.env
.envrc
.turbo/
# Note: .next/ is intentionally excluded (branch-specific cache, risky to copy)
EOF

# 13. Set worktree path in user config
wt config show   # verify project ID
# Add to ~/.config/worktrunk/config.toml:
# [projects."github.com/org/repo"]
# worktree-path = "worktrees/{{ branch | sanitize }}"
```

---

## Option B: Migrate an Existing Checkout In-Place

> **⚠️ Run from OUTSIDE the repo.** The `mv` in step 1 invalidates the shell's CWD — all subsequent commands fail. `cd` out first, or restart your shell after the rename.

```bash
# 0. cd OUT of the repo first
cd ~/projects

# 1. Rename the existing clone out of the way
mv my-project my-project-old

# 2. Create the new workspace at the original path
mkdir my-project && cd my-project

# 3. Move .git → .bare
mv ~/projects/my-project-old/.git .bare

# 4. Create the pointer file
echo "gitdir: ./.bare" > .git

# 5. Fix bare repo config
git config core.bare false
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git config worktree.useRelativePaths true
git config commit.gpgsign true

# 6. Fetch remote refs
git fetch --all

# 7. Detach HEAD (prevents "already used by worktree" error)
git symbolic-ref HEAD refs/heads/__bare_placeholder__

# 8. Create primary worktree inside worktrees/
mkdir -p worktrees
git worktree add worktrees/dev dev
git -C worktrees/dev branch --set-upstream-to=origin/dev dev

# 9. Copy files from old clone (preserves uncommitted changes)
rsync -a --exclude='.git' --exclude='node_modules' --exclude='.venv' \
  ~/projects/my-project-old/ ~/projects/my-project/worktrees/dev/

# 10. Rebuild deps (shebangs are hardcoded to old path)
cd worktrees/dev
rm -rf node_modules && pnpm install   # Node
# rm -rf .venv && uv sync             # Python

# 11. Commit worktrunk config
mkdir -p .config
cat > .config/wt.toml << 'EOF'
[post-create]
deps = "pnpm install"

[post-start]
copy = "wt step copy-ignored"
EOF

cat > worktrees/dev/.worktreeinclude << 'EOF'
.env
.envrc
.turbo/
# Note: .next/ is intentionally excluded (branch-specific cache, risky to copy)
EOF

# 12. Set worktree path in user config
# ~/.config/worktrunk/config.toml:
# [projects."github.com/org/repo"]
# worktree-path = "worktrees/{{ branch | sanitize }}"

# 13. Verify
git worktree list
```

---

## Per-Ecosystem: Dependencies

### Node.js (pnpm)

```toml
[post-create]
deps = "pnpm install"

[post-start]
copy = "wt step copy-ignored"  # copies .env, .turbo/ cache from primary worktree
```

**Gotchas:**
- Lock files (`pnpm-lock.yaml`) are git-tracked — already in every worktree, do NOT include in `.worktreeinclude`
- `.npmrc` with auth tokens → put in `worktrees/dev/`, add to `.worktreeinclude`

### Python (uv)

```toml
[post-create]
deps = "uv sync"
# Don't copy .venv/ — virtual envs have hardcoded absolute paths
```

**Gotchas:**
- **Wrong venv**: If `VIRTUAL_ENV` points to another worktree's `.venv`, tests run against wrong code. Use `uv run python -m pytest` — always uses local `.venv`.
- **Stale shebangs**: `.venv/bin/*` scripts have path hardcoded. Moving the repo breaks them. Fix: `rm -rf .venv && uv sync`.
- **Pre-commit hooks + unstaged files**: If a hook auto-modifies a file with unstaged changes in the same file, commit rolls back. Fix: `git stash push -- <file>` before committing.

### Mixed Python + Node

```toml
[post-create]
deps = "uv sync && pnpm install"
```

---

## Monorepo: Nested Env Files

For monorepos with app-level secrets (`apps/server/.env`, `apps/client/.env`), list each in `.worktreeinclude`:

```
# .worktreeinclude
.env
apps/server/.env
apps/client/.env
apps/mobile/.env
apps/storybook/.env
.turbo/
# .next/ intentionally excluded — branch-specific, risky to copy
```

`wt step copy-ignored` handles the nested structure automatically — it copies each listed file from the primary worktree into the same path in the new worktree.

---

## Build Tool Gotchas

### Moon v1 (moonrepo)

Moon v1 doesn't support bare repo worktrees ([moonrepo/moon#2162](https://github.com/moonrepo/moon/issues/2162)):

1. **Git errors in moon tasks** — Workaround: `export GIT_WORK_TREE := justfile_directory()` in `justfile`
2. **Orphaned processes** — Moon exits early but dev servers keep running, holding ports. Fix: bypass moon for dev servers, use `just run <app>` directly.

Both issues are fixed in moon v2.

### Cargo (Rust)

- `target/` is per-worktree — add to `.worktreeinclude` for fast reflink copies
- `.cargo/credentials.toml` → put in `worktrees/dev/`, add to `.worktreeinclude`

---

## Gotchas Summary

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **`wt switch` can't cd** | Shell integration not installed | `wt config shell install` |
| **`.env` missing after `wt switch --create` in Letta Code / scripts** | `post-start` hooks require shell integration (interactive shell); non-interactive shells skip them entirely | **Always** run `cd worktrees/<branch> && wt step copy-ignored` manually after `wt switch --create` |
| **Hooks need approval** | Worktrunk security: project commands require one-time consent | Run `wt switch --create` and press `y` on first prompt |
| **66 stale local branches after bare clone** | `git clone --bare` without `--single-branch` | Always use `--single-branch` on bare clone |
| **`git push` fails: "no upstream configured"** | Bare clone worktrees don't auto-set tracking | `git branch --set-upstream-to=origin/<branch>` |
| **Wrong venv / tests run old code** | `VIRTUAL_ENV` pointing to different worktree's `.venv` | Use `uv run python -m pytest` |
| **Stale venv shebangs after repo move** | `.venv/bin/*` scripts have old path hardcoded | `rm -rf .venv && uv sync` |
| **Pre-commit hook conflict** | Hook modifies file; unstaged changes in same file cause rollback | `git stash push -- <file>` before committing |
| **Moon port conflict / orphaned server** | Moon v1 exits early in bare repos, child process stays on port | Use `just run <app>` to bypass moon for dev servers |
| **IDE shows wrong branch** | Opening workspace root instead of a specific worktree | Open `worktrees/dev/` or `worktrees/feat-my-feature/` directly |
| **Shell dies after `mv` during in-place migration** | `mv` invalidates CWD — all commands fail | `cd` out of the repo before the rename |
| **`git worktree add` fails: "already used"** | After `mv .git .bare`, HEAD still references dev | Detach HEAD first: `git symbolic-ref HEAD refs/heads/__bare_placeholder__` |
| **`wt switch --create` creates worktree in `.bare/worktrees/` instead of `worktrees/`** | Running `wt` from workspace root instead of inside primary worktree | `cd worktrees/dev` (or `worktrees/main`) BEFORE `wt switch --create` |
| **New worktree starts stale / conflicts** | Primary worktree behind `origin` when `wt switch --create` runs | Add `pre-switch` hook: `git -C {{ primary_worktree_path }} pull --ff-only` |
| **`pnpm install` (or `uv sync`) doesn't run when switching back to existing worktree** | `post-create` / `post-start` only fire for NEW worktrees; `wt switch dev` on an existing worktree skips them entirely | Add `[post-switch] deps = "pnpm install"` to `.config/wt.toml` |

---

## Rules

- **Use `wt` for all worktree operations** — `wt switch --create`, `wt list`, `wt remove`, `wt step prune`
- **Run `wt switch --create` from INSIDE the primary worktree** (`worktrees/dev/` or `worktrees/main/`) — NEVER from workspace root. Running from root creates malformed worktrees in `.bare/worktrees/`
- `worktrees/dev/` is the **source of truth** for all shared files — pull frequently, **never commit work directly to it**
- **`wt step copy-ignored` + `.worktreeinclude`** handles gitignored files (`.env`, build caches) — no manual symlink setup needed
- **All** worktrees — including the primary — live in `worktrees/` — configured via `worktree-path` in worktrunk user config
- Each worktree has its own `node_modules` / `.venv` — automate via `.config/wt.toml` hooks
- Keep 2–4 active worktrees max; `wt step prune` to remove stale ones
- Open a **specific worktree** in your IDE, not the workspace root
- Tool-specific config folders scoped to the whole project (not per-branch) belong at the **workspace root as real directories**, not inside worktrees
- **Version manager config files** (`.prototools`, `.tool-versions`) → **symlink** at workspace root to primary worktree's file (e.g., `ln -s worktrees/dev/.prototools .prototools`)
