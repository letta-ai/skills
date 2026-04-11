---
name: bare-repo-workspaces
description: Git worktree operations using Worktrunk (wt). LOAD THIS SKILL whenever the user mentions "worktree", "new worktree", "create a worktree", "switch to a branch", "start work on a new feature/branch", "new bare repo workspace", or asks to work in a new/existing worktree. DO NOT run raw `git worktree` commands — this skill handles the bare repo pattern and hook lifecycle. If the user's memory mentions "worktrees/" paths, this skill is REQUIRED. Covers: creating worktrees, switching branches, cleanup, and the copy-ignored workflow for .env propagation.
---

# Bare Repo Workspaces

Keep all your worktrees inside one project folder — clean, organized, self-contained.

> **Tooling**: [Worktrunk](https://worktrunk.dev) (`wt`) is the preferred tool for all worktree operations. It wraps `git worktree` with ergonomic commands, lifecycle hooks, and `copy-ignored` for cache/env sharing. Install: `brew install worktrunk && wt config shell install`.

## Scripts

This skill includes helper scripts in `scripts/`:

| Script | Purpose |
|--------|---------|
| `setup-workspace.sh` | One-time setup: create bare repo workspace from URL or upgrade existing checkout. |
| `doctor.sh` | Diagnose and fix bare repo workspace issues (e.g., Antigravity compatibility). |

### doctor.sh — Diagnose and fix workspace issues

```bash
# Diagnose only
bash ~/.letta/skills/bare-repo-workspaces/scripts/doctor.sh ~/Code/alliance/ragtime

# Diagnose and fix
bash ~/.letta/skills/bare-repo-workspaces/scripts/doctor.sh --fix ~/Code/alliance/skills
```

**Checks for:**
- Antigravity compatibility (repositoryformatversion, relative paths config)
- Relative vs absolute paths in `.git` files and `gitdir` files
- Missing `.git` pointer file at workspace root

**For daily workflow, use `wt` commands:**
- `wt switch --create feat/my-feature` — create a new worktree
- `wt switch main` — switch to existing worktree
- `wt list` — show all worktrees
- `wt remove feat/my-feature` — clean up after merge

**Use `setup-workspace.sh` only for initial workspace creation** — it handles edge cases like detaching HEAD before worktree creation.

## Why

Standard `git worktree add ../feature` scatters directories alongside real repos. After a few months, you can't tell worktrees from clones at a glance.

The bare repo pattern fixes this:

```
my-project/
├── .bare/           # all git data (bare clone)
├── .git             # pointer FILE (not folder) → .bare
├── main/             # primary worktree — source of truth for shared files
│   ├── .env         # REAL file (copied to new worktrees via copy-ignored)
│   └── apps/
│       └── server/.env  # REAL file
├── feat-my-feature/
└── fix-some-bug/
```

**Key principles:**
- `main/` is the **primary worktree** and source of truth for all shared files
- **All** worktrees — primary and feature branches alike — live directly in the workspace root, named using `{{ branch | sanitize }}` (slashes become dashes)
- Shared files (`.env`, build caches) are propagated to new worktrees automatically via `wt step copy-ignored` — no symlinks needed
- Tool-specific config folders that should be scoped to the whole project (not per-branch) belong at the **workspace root as real directories** — not inside worktrees, not as symlinks
- **Version manager config files** (`.prototools`, `.tool-versions`) must be **symlinked** at the workspace root to the primary worktree's file, so tools like proto/asdf resolve correct versions when the agent's shell starts in the workspace root (not a worktree). Create: `ln -s main/.prototools .prototools`

---

## Worktrunk Hooks (`.config/wt.toml`)

Commit this file to the repo — it's shared with the team and automates worktree setup:

```toml
# .config/wt.toml

[pre-start]
# Blocking — runs before post-start hooks or --execute
# ⚠️  Only fires when creating a NEW worktree (wt switch --create)
deps = "pnpm install"   # Node.js
# deps = "uv sync"      # Python

[post-start]
# Background — runs after worktree is ready
# ⚠️  Only fires when creating a NEW worktree (wt switch --create)
copy = "wt step copy-ignored"   # copies .env, build caches from main worktree

[post-switch]
# Background — runs after EVERY wt switch, including switching to existing worktrees
# Add this so deps stay current when you return to an old worktree
deps = "pnpm install"
```

> **Hook lifecycle summary**: `pre-start` → new worktrees only (blocking). `post-start` → new worktrees only (background). `post-switch` → every switch, new or existing (background). If you only have `pre-start` / `post-start`, running `wt switch main` on an existing worktree will **not** install deps.

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
# copying from main can produce stale/incorrect builds on feature branches.
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

# Global default — all repos use <branch-sanitized>/ at workspace root
worktree-path = "{{ branch | sanitize }}"
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
# repo_path is the workspace root; main worktree is a subdirectory
[pre-switch]
sync = "test -d \"{{ repo_path }}/main\" && git -C \"{{ repo_path }}/main\" pull --ff-only 2>/dev/null || true"
```

This runs before every `wt switch`, fast-forwarding the primary worktree to match origin. `test -d` ensures the hook skips gracefully when no worktree exists yet. `--ff-only` ensures it never creates merge commits, and `|| true` means it won't block if there's no network.

For repos where the primary worktree is a sibling (not inside the repo):
```toml
[projects."github.com/org/other-repo"]
worktree-path = "{{ branch | sanitize }}"
```

---

## Daily Workflow

### Create a feature worktree (interactive terminal)

> **⚠️ CRITICAL: Run `wt switch --create` from INSIDE the primary worktree (e.g., `main/`), NOT from the workspace root.**
>
> If run from the workspace root, `git rev-parse --show-toplevel` fails (not a work tree), `wt` falls back to `git-common-dir` (`.bare/`), and the worktree may be created inside `.bare/` instead of workspace root. Those malformed worktrees cause pre-commit to fail (`git toplevel unexpectedly empty`).

```bash
# 1. cd into the primary worktree FIRST
cd main

# 2. Create worktree + branch (shell integration required for cd)
wt switch --create feat/my-feature

# With a specific base branch:
wt switch --create feat/my-feature --base main

# Create and immediately launch Letta Code:
wt switch --create feat/my-feature -x "letta code ."
```

Worktrunk runs `pre-start` (blocking: deps install) then `post-start` (background: copy-ignored) automatically. If `[post-switch]` is configured, it also runs in the background after every switch.

### Create a feature worktree (non-interactive: Letta Code, CI, scripts)

**⚠️ Run from INSIDE the primary worktree** — same as interactive workflow. If run from workspace root, worktrees may be created under `.bare/` instead of workspace root.

**⚠️ `post-start` hooks do NOT fire in non-interactive shells** — shell integration is not active, so `wt step copy-ignored` never runs. `.env` and other gitignored files won't be copied unless you run the hook commands manually.

```bash
# 1. cd into the primary worktree FIRST
cd main

# 2. Create the worktree (pre-start hooks like `uv sync` still run)
wt switch --create feat/my-feature

# 3. cd into the new worktree
cd feat-my-feature

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
cd ~/projects/my-project/main
git pull
```

---

## Option A: Fresh Setup (from GitHub URL)

### Quick setup with setup-workspace.sh (recommended)

Use the setup script to automate the entire setup:

```bash
# Fresh setup from remote URL
bash ~/.letta/skills/bare-repo-workspaces/scripts/setup-workspace.sh <repo-url> <target-dir> [--copy-from <old-clone>] [--main-branch <branch>]

# Example:
bash ~/.letta/skills/bare-repo-workspaces/scripts/setup-workspace.sh git@github.com:etalab-ia/skills.git ~/Code/alliance/skills

# With optional env file copy from existing clone:
bash ~/.letta/skills/bare-repo-workspaces/scripts/setup-workspace.sh git@github.com:org/repo.git ~/projects/repo --copy-from ~/old-clone
```

The script handles:
- Bare clone with `--single-branch`
- `.git` pointer file creation
- Git config (fetch, relative paths, signing)
- Creating the primary worktree (detaches HEAD first to avoid conflicts)
- Copying `.env` files from an existing clone (if `--copy-from` provided)
- Creating placeholder directories (`feat/`, `fix/`, `hotfix/`, `docs/`)

---

### Manual setup (if setup-workspace.sh unavailable)

### Determine the workspace location

**When the user starts from a parent directory** (e.g., `~/Code/alliance`) and provides a GitHub URL (e.g., `git@github.com:etalab-ia/skills.git`):

1. **Derive the workspace name from the repo name** — extract the final segment before `.git`:
   - `git@github.com:etalab-ia/skills.git` → workspace name is `skills`
   - `https://github.com/org/my-project.git` → workspace name is `my-project`

2. **Create the workspace as a SUBDIRECTORY of the current working directory**:
   - Current directory: `~/Code/alliance`
   - GitHub URL: `git@github.com:etalab-ia/skills.git`
   - Workspace path: `~/Code/alliance/skills`

3. **Do NOT create the bare repo directly in the current directory** — this would pollute the parent with `.bare/`, `.git`, and worktree directories mixed alongside other projects.

```bash
# Example: User is in ~/Code/alliance, URL is git@github.com:etalab-ia/skills.git

# 1. Create the workspace directory as a subdirectory of current location
mkdir skills && cd skills

# Now in ~/Code/alliance/skills — proceed with bare clone
```

**When the user explicitly specifies a workspace path** (e.g., "create workspace at ~/projects/my-project"):

```bash
mkdir -p ~/projects/my-project && cd ~/projects/my-project
```

---

### Complete setup sequence

Once you've created and entered the workspace directory (whether derived from URL or explicitly specified), run the following:

```bash
# 2. Bare clone (--single-branch avoids creating 60+ stale local branches)
git clone --bare --single-branch git@github.com:org/repo.git .bare

# 3. Create the .git POINTER FILE (not a folder — this is the magic)
echo "gitdir: ./.bare" > .git

# 4. Configure fetch for all remote branches
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 5. Enable commit signing
git config commit.gpgsign true

# 6. Fetch all remote branches
git fetch --all

# 7. Create the primary worktree at workspace root
git worktree add main main
git -C main branch --set-upstream-to=origin/main main

# 9. Copy secrets into main/ (source of truth)
cp /path/to/old/.env main/.env
cp /path/to/old/apps/server/.env main/apps/server/.env
# ... etc

# 10. Install dependencies
cd main && pnpm install   # Node
# cd main && uv sync      # Python

# 11. Add worktrunk config
mkdir -p .config
cat > .config/wt.toml << 'EOF'
[pre-start]
deps = "pnpm install"

[post-start]
copy = "wt step copy-ignored"
EOF

# 12. Add .worktreeinclude to scope what copy-ignored copies
cat > main/.worktreeinclude << 'EOF'
.env
.envrc
.turbo/
# Note: .next/ is intentionally excluded (branch-specific cache, risky to copy)
EOF

# 13. Set worktree path in user config
wt config show   # verify project ID
# Add to ~/.config/worktrunk/config.toml:
# [projects."github.com/org/repo"]
# worktree-path = "{{ branch | sanitize }}"
```

---

## Option B: Upgrade Existing Workspace / Checkout (`--upgrade`)

Use the helper script to upgrade in place.

### 1) Standard checkout (`.git` directory) → bare workspace format

```bash
# IMPORTANT: run from OUTSIDE the workspace
bash ~/.letta/skills/bare-repo-workspaces/scripts/setup-workspace.sh --upgrade ~/projects/my-project --main-branch main
```

### 2) Existing bare workspace using `worktrees/` layout → root-level layout

```bash
# IMPORTANT: run from OUTSIDE the workspace
bash ~/.letta/skills/bare-repo-workspaces/scripts/setup-workspace.sh --upgrade ~/projects/my-project --main-branch main
```

The script auto-detects the workspace type and applies the right migration path.

### 3) Update Worktrunk user config

```toml
# ~/.config/worktrunk/config.toml
worktree-path = "{{ branch | sanitize }}"
```

### 4) Verify

```bash
git -C ~/projects/my-project worktree list
```

---

## Per-Ecosystem: Dependencies

### Node.js (pnpm)

```toml
[pre-start]
deps = "pnpm install"

[post-start]
copy = "wt step copy-ignored"  # copies .env, .turbo/ cache from primary worktree
```

**Gotchas:**
- Lock files (`pnpm-lock.yaml`) are git-tracked — already in every worktree, do NOT include in `.worktreeinclude`
- `.npmrc` with auth tokens → put in `main/`, add to `.worktreeinclude`

### Python (uv)

```toml
[pre-start]
deps = "uv sync"
# Don't copy .venv/ — virtual envs have hardcoded absolute paths
```

**Gotchas:**
- **Wrong venv**: If `VIRTUAL_ENV` points to another worktree's `.venv`, tests run against wrong code. Use `uv run python -m pytest` — always uses local `.venv`.
- **Stale shebangs**: `.venv/bin/*` scripts have path hardcoded. Moving the repo breaks them. Fix: `rm -rf .venv && uv sync`.
- **Pre-commit hooks + unstaged files**: If a hook auto-modifies a file with unstaged changes in the same file, commit rolls back. Fix: `git stash push -- <file>` before committing.

### Mixed Python + Node

```toml
[pre-start]
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
- `.cargo/credentials.toml` → put in `main/`, add to `.worktreeinclude`

---

## Gotchas Summary

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **`wt switch` can't cd** | Shell integration not installed | `wt config shell install` |
| **`.env` missing after `wt switch --create` in Letta Code / scripts** | `post-start` hooks require shell integration (interactive shell); non-interactive shells skip them entirely | **Always** run `cd <branch-sanitized> && wt step copy-ignored` manually after `wt switch --create` |
| **Hooks need approval** | Worktrunk security: project commands require one-time consent | Run `wt switch --create` and press `y` on first prompt |
| **66 stale local branches after bare clone** | `git clone --bare` without `--single-branch` | Always use `--single-branch` on bare clone |
| **`git push` fails: "no upstream configured"** | Bare clone worktrees don't auto-set tracking | `git branch --set-upstream-to=origin/<branch>` |
| **Wrong venv / tests run old code** | `VIRTUAL_ENV` pointing to different worktree's `.venv` | Use `uv run python -m pytest` |
| **Stale venv shebangs after repo move** | `.venv/bin/*` scripts have old path hardcoded | `rm -rf .venv && uv sync` |
| **Pre-commit hook conflict** | Hook modifies file; unstaged changes in same file cause rollback | `git stash push -- <file>` before committing |
| **Moon port conflict / orphaned server** | Moon v1 exits early in bare repos, child process stays on port | Use `just run <app>` to bypass moon for dev servers |
| **IDE shows wrong branch** | Opening workspace root instead of a specific worktree | Open `main/` or `feat-my-feature/` directly |
| **Shell dies after `mv` during in-place migration** | `mv` invalidates CWD — all commands fail | `cd` out of the repo before the rename |
| **`git worktree add` fails: "already used"** | Bare clone HEAD points to main branch, making it "used" | Detach HEAD first: `git symbolic-ref HEAD refs/heads/__bare_placeholder__` (setup-workspace.sh does this automatically) |
| **`wt switch --create` creates worktree in `.bare/` instead of workspace root** | Running `wt` from workspace root instead of inside primary worktree | `cd main` BEFORE `wt switch --create` |
| **Need to upgrade old `worktrees/` layout to root-level** | Earlier setup used `worktrees/<branch>` | Run `setup-workspace.sh --upgrade <workspace-dir>` from outside the workspace |
| **New worktree starts stale / conflicts** | Primary worktree behind `origin` when `wt switch --create` runs | Add `pre-switch` hook: `test -d \"{{ repo_path }}/main\" && git -C \"{{ repo_path }}/main\" pull --ff-only` |
| **Agent executes manual steps instead of using setup script** | Skill documentation showed manual steps before scripts section | Always check `scripts/` directory first — use `setup-workspace.sh` for fresh setup |
| **`pnpm install` (or `uv sync`) doesn't run when switching back to existing worktree** | `pre-start` / `post-start` only fire for NEW worktrees; `wt switch main` on an existing worktree skips them entirely | Add `[post-switch] deps = \"pnpm install\"` to `.config/wt.toml` |
| **Antigravity / IDE fails to open workspace** | `repositoryformatversion = 1` with `worktree.useRelativePaths = true` or `extensions.relativeWorktrees = true` breaks Git parsers | Run `doctor.sh --fix <workspace>` to fix |

---

## Rules

- **Use `wt` for all worktree operations** — `wt switch --create`, `wt list`, `wt remove`, `wt step prune`
- **Run `wt switch --create` from INSIDE the primary worktree** (`main/`) — NEVER from workspace root. Running from root can create malformed worktrees in `.bare/`
- `main/` is the **source of truth** for all shared files — pull frequently, **never commit work directly to it**
- **`wt step copy-ignored` + `.worktreeinclude`** handles gitignored files (`.env`, build caches) — no manual symlink setup needed
- **All** worktrees — including the primary — live at workspace root — configured via `worktree-path` in worktrunk user config
- Each worktree has its own `node_modules` / `.venv` — automate via `.config/wt.toml` hooks
- Keep 2–4 active worktrees max; `wt step prune` to remove stale ones
- Open a **specific worktree** in your IDE, not the workspace root
- Tool-specific config folders scoped to the whole project (not per-branch) belong at the **workspace root as real directories**, not inside worktrees
- **Version manager config files** (`.prototools`, `.tool-versions`) → **symlink** at workspace root to primary worktree's file (e.g., `ln -s main/.prototools .prototools`)
