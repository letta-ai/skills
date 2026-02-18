---
name: bare-repo-worktrees
description: Migrate a Git repository to the bare repo + worktree pattern, where all worktrees live inside one project directory. Use when setting up a repo for parallel branch development, converting an existing clone, or when the user mentions bare repo, worktree organization, or working on multiple branches simultaneously.
license: MIT
---

# Bare Repo Worktrees

Migrate a standard Git clone to the bare repo pattern for clean, self-contained worktree management.

## Why

Standard `git worktree add ../feature` scatters worktree directories alongside the repo. The bare repo pattern keeps everything inside one workspace folder, making it easy to manage shared files (secrets, IDE config) across all branches:

```
my-project/
├── .bare/           # all git data
├── .git             # pointer file → .bare
├── .envs/           # ALL .env files live here (symlinked into each worktree)
│   ├── .env
│   ├── .envrc
│   └── apps/
│       ├── backend/.env
│       └── frontend/.env
├── .letta/          # shared agent settings (symlinked into each worktree)
├── main/            # worktree: main branch
│   ├── .env         → symlink → ../.envs/.env
│   ├── .letta       → symlink → ../.letta
│   └── apps/
│       └── backend/.env → symlink → ../../.envs/apps/backend/.env
├── feat/
│   └── my-feature/  # worktree: feature branch (symlinks auto-created)
├── fix/
├── hotfix/
└── docs/
```

**Key principle:** Secrets and shared config live at the workspace root and are **symlinked** into each worktree — never duplicated. Updating one file updates all worktrees instantly.

## Migration

Run the migration script, passing the repo URL and target directory:

```bash
bash ~/.letta/skills/bare-repo-worktrees/scripts/migrate.sh \
  <repo-url> <target-dir> \
  [--copy-envs-from <old-clone>] \
  [--main-branch <branch>]
```

Example — migrating an existing clone, with `dev` as the primary branch:

```bash
bash ~/.letta/skills/bare-repo-worktrees/scripts/migrate.sh \
  git@github.com:org/repo.git ~/projects/repo \
  --copy-envs-from ~/projects/repo-old \
  --main-branch dev
```

The script handles:
1. Bare clone + `.git` pointer file creation
2. Fetch config for all remote branches
3. Portable relative paths (`worktree.useRelativePaths`)
4. Commit signing enabled
5. Primary worktree creation with tracking branch set
6. Discovery of **all** `.env` / `.envrc` / `.env.*` files in the old clone → stored in `.envs/`
7. Automatic symlinking of all env files and `.letta/` into the primary worktree
8. Scaffold directories: `feat/`, `fix/`, `hotfix/`, `docs/`

After migration:
```bash
cd ~/projects/repo/main   # or your primary branch name
<package-manager> install  # install dependencies
git worktree list          # verify setup
```

## Daily Workflow

### Create a feature worktree

Use `new-worktree.sh` — it creates the worktree and symlinks all shared files automatically:

```bash
cd <workspace-root>
bash ~/.letta/skills/bare-repo-worktrees/scripts/new-worktree.sh feat/my-feature main
```

What it does:
- Creates `feat/my-feature/` checked out to a new branch from `main`
- Symlinks every file in `.envs/` into the matching path inside the worktree
- Symlinks `.letta/` into the worktree root

Then install deps:
```bash
cd feat/my-feature && <package-manager> install
```

To check out an **existing** remote branch instead:
```bash
# new-worktree.sh detects it and sets up tracking automatically
bash ~/.letta/skills/bare-repo-worktrees/scripts/new-worktree.sh feat/existing-branch
```

### Re-link shared files in an existing worktree

If a worktree is missing symlinks (e.g., after manually adding one):

```bash
cd <workspace-root>
bash ~/.letta/skills/bare-repo-worktrees/scripts/new-worktree.sh --link-only feat/my-feature
```

### Clean up after PR merge

```bash
cd <workspace-root>
git worktree remove feat/my-feature
```

### Update primary branch

```bash
cd <workspace-root>/main
git pull
```

## Monorepo `.env` Handling

For monorepos with nested env files, store them in `.envs/` mirroring their original relative paths:

```
.envs/
├── .env             # repo root
├── .envrc           # direnv
└── apps/
    ├── backend/.env
    ├── frontend/.env
    └── frontend/.env.test
```

`link-envs.sh` and `new-worktree.sh` handle this recursively using absolute symlink paths, which avoids broken links for deeply nested worktree names like `feat/my-feature`.

## Fix an Existing Worktree Without Symlinks

If a worktree already has copied (not symlinked) `.env` files, migrate to symlinks:

```bash
WORKSPACE=/path/to/workspace-root
WORKTREE=main   # the worktree to fix

# 1. Move env files into .envs/, preserving directory structure
mkdir -p "$WORKSPACE/.envs"
find "$WORKSPACE/$WORKTREE" \
  \( -name ".env" -o -name ".env.*" -o -name ".envrc" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" | while read f; do
    relpath="${f#$WORKSPACE/$WORKTREE/}"
    mkdir -p "$(dirname "$WORKSPACE/.envs/$relpath")"
    mv "$f" "$WORKSPACE/.envs/$relpath"
    ln -sf "$WORKSPACE/.envs/$relpath" "$f"
  done

# 2. Re-link any other existing worktrees
bash ~/.letta/skills/bare-repo-worktrees/scripts/new-worktree.sh --link-only "$WORKSPACE/feat/other-branch"
```

## Scripts

| Script | Purpose |
|---|---|
| `scripts/migrate.sh` | One-shot migration from a standard clone to bare repo pattern |
| `scripts/new-worktree.sh` | Create a worktree with all shared files symlinked |
| `scripts/link-envs.sh` | Core helper — symlink `.envs/` contents into a worktree |

## Rules

- Primary worktree (`main/` or `dev/`) — pull frequently, use as stable reference
- `.env` files live in `.envs/` at workspace root, **symlinked** into each worktree — never copied
- `.letta/` lives at workspace root, **symlinked** into each worktree
- Each worktree gets its own `node_modules` / `.venv` — install deps after creation
- Use absolute symlink paths — relative paths break for nested names like `feat/my-feature`
- Name worktrees after branches: directory = branch = no confusion
- Keep 2–4 active worktrees; remove stale ones with `git worktree remove`
- Open a **specific worktree** in your IDE, not the workspace root
