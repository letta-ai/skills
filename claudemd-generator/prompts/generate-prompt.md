# CLAUDE.md Generator Prompt

You are generating a comprehensive CLAUDE.md for a project. This file is the source of truth
for all future AI-assisted sessions — it must be accurate, specific, and complete.

Follow every step below in order. Do not skip steps. Read before you write.

---

## INPUTS

Before starting, confirm:

- **Project root** — the directory to scan (default: current working directory)
- **Project name** — short identifier (e.g. `nmk`, `shadowsky`, `family-org`)

If the project is a remote repo not yet cloned:
```bash
git clone --depth=50 <REPO_URL> /tmp/<project-name>
cd /tmp/<project-name>
```

---

## STEP 1: SCAN PACKAGE CONFIGURATION

Read all of these that exist (skip ones that don't):

**JavaScript/TypeScript:**
- `package.json` — name, version, scripts, dependencies, devDependencies, engines
- `tsconfig.json`, `tsconfig.*.json` — compiler options, paths, strictness
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` (just check which exists)

**Python:**
- `pyproject.toml` — project metadata, dependencies, tool configs (ruff, pytest, black)
- `setup.py`, `setup.cfg` — legacy metadata
- `requirements.txt`, `requirements-dev.txt` — pinned dependencies
- `Pipfile` — pipenv config

**Rust:**
- `Cargo.toml` — package metadata, dependencies, features, workspace config

**Go:**
- `go.mod` — module path, Go version, dependencies

**Ruby:**
- `Gemfile` — dependencies and groups

**Other:**
- `Makefile`, `Justfile` — build/run commands
- `docker-compose.yml`, `Dockerfile*` — container setup
- `.env.example`, `.env.local.example` — environment variable definitions
- `README.md` — existing documentation (may be outdated but useful for context)

Extract from these files:
- Language and version
- Framework and version
- Database type (if referenced)
- Key dependencies and their purpose
- Build, test, lint, and run commands
- Required environment variables

---

## STEP 2: SCAN DIRECTORY STRUCTURE

Map the project layout:
```bash
find . -type f \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './__pycache__/*' \
  -not -path './venv/*' \
  -not -path './.venv/*' \
  -not -path './target/*' \
  -not -path './dist/*' \
  -not -path './build/*' \
  -not -path './.next/*' \
  -not -path './.nuxt/*' \
  -not -path './coverage/*' \
  -not -path './.tox/*' \
  | head -300
```

Count files by extension:
```bash
find . -type f \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './__pycache__/*' \
  -not -path './venv/*' \
  -not -path './.venv/*' \
  | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

Count total lines of code:
```bash
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.rs" -o -name "*.go" -o -name "*.rb" \) \
  -not -path './.git/*' -not -path './node_modules/*' -not -path './venv/*' -not -path './.venv/*' -not -path './target/*' \
  | xargs wc -l 2>/dev/null | tail -1
```

Identify:
- Top-level directories and their purpose
- Source code layout (monorepo? src/ directory? app/ directory?)
- Where tests live
- Where configuration lives
- Where infrastructure/deployment files live
- Non-obvious directories that need explanation

---

## STEP 3: SCAN CI/CD WORKFLOWS

Read all CI/CD configuration that exists:
- `.github/workflows/*.yml` — GitHub Actions
- `.gitlab-ci.yml` — GitLab CI
- `Jenkinsfile` — Jenkins
- `.circleci/config.yml` — CircleCI
- `netlify.toml`, `vercel.json`, `amplify.yml` — hosting platform configs
- `fly.toml`, `railway.json`, `render.yaml` — deployment platform configs

Extract:
- What triggers builds (push, PR, schedule)
- What CI runs (tests, lint, type-check, build)
- How deployment works
- Environment/secrets needed for CI

---

## STEP 4: SCAN ENVIRONMENT VARIABLES

Collect all environment variables from:
1. `.env.example` or `.env.local.example` — explicit variable list
2. CI workflow files — `env:` and `secrets.` references
3. Source code — `process.env.`, `os.environ`, `os.getenv`, `env::var` patterns

```bash
# .env files
cat .env.example 2>/dev/null || cat .env.local.example 2>/dev/null || true

# Source code references
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.rs" --include="*.go" \
  -oP '(?:process\.env\.|os\.environ\[|os\.getenv\(|env::var\()["\x27]?\K[A-Z_][A-Z0-9_]+' . \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv 2>/dev/null \
  | sort -u || true
```

For each variable, note:
- Whether it's required or optional
- What it's used for (API key, database URL, feature flag, etc.)
- Default value if any

---

## STEP 5: SCAN TEST SETUP

Determine:
- Test framework: jest, vitest, pytest, cargo test, go test, rspec, etc.
- Test location: `tests/`, `__tests__/`, `*.test.ts`, `*_test.py`, etc.
- Test configuration: `jest.config.*`, `vitest.config.*`, `pytest.ini`, `conftest.py`, `.mocharc.*`
- How to run tests (from package.json scripts, Makefile targets, or directly)
- Approximate test count and coverage if visible

```bash
# Count test files
find . -type f \( -name "*.test.*" -o -name "*.spec.*" -o -name "test_*.py" -o -name "*_test.py" -o -name "*_test.go" -o -name "*_test.rs" \) \
  -not -path './node_modules/*' -not -path './venv/*' -not -path './.venv/*' \
  | wc -l
```

---

## STEP 6: SCAN GIT HISTORY

Understand the project's development patterns:
```bash
# Recent commit messages (for conventions)
git log --oneline -20

# Active contributors
git shortlog -sn --no-merges -20

# Most-changed files (indicates hot spots)
git log --pretty=format: --name-only -50 | sort | uniq -c | sort -rn | head -15

# Branch naming convention
git branch -a | head -20
```

Extract:
- Commit message convention (conventional commits? prefix tags? issue references?)
- Branch naming pattern (feature/, fix/, task/, etc.)
- How many active contributors
- Development cadence (active or dormant)

---

## STEP 7: READ KEY SOURCE FILES

Read 3-5 representative source files to understand patterns:
- **Entry point**: `src/index.ts`, `main.py`, `src/main.rs`, `app.py`, `cmd/main.go`, etc.
- **A route/handler**: an API endpoint or page component
- **A model/schema**: database model, type definitions, or schema
- **A utility**: helper or shared module that reveals conventions

Look for:
- Error handling patterns (try/catch, Result types, error boundaries)
- Import style and module organization
- State management approach (if frontend)
- Database access patterns (ORM, raw queries, repository pattern)
- Authentication/authorization patterns
- Logging and observability
- Any existing `CLAUDE.md` or similar documentation

---

## STEP 8: GENERATE CLAUDE.md

Using everything gathered in Steps 1-7, generate the CLAUDE.md file.

### Template:

```markdown
# CLAUDE.md

## Project Overview
[One paragraph: what this project is, who uses it, what problem it solves.
Include the primary language and framework upfront.]

## Tech Stack
- **Language:** [language with version, e.g. "TypeScript 5.3 (strict mode)"]
- **Framework:** [framework with version, e.g. "Next.js 14.1 (App Router)"]
- **Database:** [type and location, e.g. "PostgreSQL on Supabase"]
- **Hosting:** [where it deploys, e.g. "Vercel"]
- **Key dependencies:** [list 3-5 important ones with what they do]

## Project Structure
```
[Annotated directory tree. Include EVERY top-level directory with a short description.
Go one level deeper for src/ or app/ directories. Example:]

├── src/
│   ├── app/           # Next.js App Router pages and layouts
│   ├── components/    # React components (organized by feature)
│   ├── lib/           # Shared utilities and helpers
│   ├── server/        # Server-side code (tRPC routers, db)
│   └── types/         # TypeScript type definitions
├── prisma/            # Database schema and migrations
├── public/            # Static assets
└── tests/             # Test files (mirrors src/ structure)
```

## Development

### Prerequisites
[Exact tools and versions needed. Be specific:]
- Node.js >= 18
- pnpm (install: `npm install -g pnpm`)
- PostgreSQL 15+ (or Docker)

### Setup
```bash
[Exact commands from clone to running. Number each step:]
git clone <repo-url>
cd <project>
cp .env.example .env.local
# Edit .env.local with your values
pnpm install
pnpm db:push    # or: npx prisma db push
```

### Build
```bash
[Exact build command]
```

### Test
```bash
[Exact test commands — separate unit, integration, e2e if applicable]
# Unit tests
pnpm test

# E2E tests
pnpm test:e2e
```

### Lint
```bash
[Exact lint and format commands]
pnpm lint
pnpm format
```

### Run locally
```bash
[Exact command to start dev server]
pnpm dev
# → http://localhost:3000
```

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `NEXTAUTH_SECRET` | Yes | Auth session encryption key |
| `NEXTAUTH_URL` | Yes | App URL (http://localhost:3000 for dev) |
[Include ALL variables discovered. Mark required vs optional.]

## Key Patterns and Conventions
[Bullet list of patterns actually used in this codebase. Be specific, not generic:]
- All API routes use tRPC with Zod validation — see `src/server/api/routers/` for examples
- Error handling: all async route handlers wrapped in `tryCatch()` from `src/lib/errors.ts`
- Database: Prisma ORM with migrations — run `pnpm db:migrate` after schema changes
- Auth: NextAuth.js with Google OAuth provider — config in `src/server/auth.ts`
- Commit messages follow conventional commits: `feat:`, `fix:`, `chore:`, etc.
- Branch naming: `feature/<description>` or `fix/<description>`

## Known Issues
[Anything that will trip up a developer or AI agent. If none found, omit this section.]
- `pnpm dev` requires PostgreSQL running — use `docker compose up db` if not installed locally
- The `GOOGLE_CLIENT_ID` env var must be set even in development (use test credentials)
- `src/legacy/` is being migrated — don't add new code there

## Database
[If applicable: ORM, migration approach, key models. Omit if no database.]
- ORM: Prisma
- Schema: `prisma/schema.prisma`
- Migrations: `pnpm db:migrate` (uses Prisma Migrate)
- Key models: User, Post, Comment, Tag

## Deployment
[How the app gets deployed. Include triggers and destinations.]
- Push to `main` triggers Vercel deployment
- Preview deployments on every PR
- Environment variables configured in Vercel dashboard
- Database migrations run manually before deploy: `pnpm db:migrate:deploy`
```

### Quality guidelines:

1. **Be specific, not generic.** Not "run the tests" but `pytest tests/ -v --tb=short`.
   Not "the API directory" but `src/app/api/`.

2. **Include actual paths.** Every directory reference should be a real path in the project.

3. **Capture architecture decisions.** "All pages are client components using tRPC hooks" is
   more valuable than a directory listing. Explain WHY things are organized the way they are.

4. **Target 100-200 lines.** Under 100 is too sparse to be useful. Over 200 means you're
   including information that should be in separate docs. Aim for the sweet spot.

5. **Include version numbers.** Frameworks and runtimes change behavior across versions.
   `Next.js 14 (App Router)` vs `Next.js 12 (Pages Router)` is a critical distinction.

6. **Omit empty sections.** If there's no database, don't include a Database section.
   If there are no known issues, drop that section. Only include what exists.

7. **Commands must work.** Every `bash` block should be copy-pasteable. Verify commands
   against what you found in package.json scripts, Makefile targets, or tool configs.

8. **Conventions over descriptions.** "Files use kebab-case naming" and "Components export
   default" are more useful than describing what each file contains.

---

## STEP 9: REVIEW AND SAVE

Before saving:

1. **Verify accuracy** — Cross-check commands against package.json/pyproject.toml/Makefile.
   Every command in the CLAUDE.md must match a real script or tool invocation.

2. **Verify paths** — Every path referenced must exist in the project.

3. **Verify completeness** — Does it cover everything an AI agent needs to start working
   on this project? Can someone clone the repo and get productive using only this file?

4. **Check line count** — Target 100-200 lines. If under 100, you're missing information.
   If over 200, you're including too much detail.

Show the generated CLAUDE.md to the user and ask for corrections before saving.

Save to the project root:
```bash
# Write CLAUDE.md
cat > CLAUDE.md << 'CLAUDEMD_EOF'
[generated content]
CLAUDEMD_EOF

# Verify
wc -l CLAUDE.md
```

---

## TIPS

- **Read before you write.** A CLAUDE.md written after reading 3 files will be worse than
  one written after reading 30. Do all 7 scan steps before generating.

- **Don't guess.** If you can't find how tests are run, say "No test configuration found"
  rather than guessing `npm test`. Wrong commands in CLAUDE.md are worse than missing ones.

- **Focus on what's unique.** Every Next.js app has `pnpm install`. What makes THIS project
  different? Custom scripts, unusual patterns, and project-specific gotchas are highest value.

- **Update, don't replace.** If a CLAUDE.md already exists, read it first. Preserve any
  human-written context that's still accurate, and update or expand sections that are
  incomplete or outdated.

- **Environment variables are critical.** A missing env var is the #1 reason setups fail.
  Be thorough here — check .env.example, CI configs, AND source code references.
