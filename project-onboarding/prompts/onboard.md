# Project Onboarding Prompt — Scaffold VSM System

You are onboarding a new project into the VSM (Viable System Model) autonomous agent system.
Follow every step below in order. Do not skip steps. Show your work as you go.

This prompt is scaffold-specific. It references internal Asana GIDs, Letta agent IDs,
and infrastructure configuration files.

---

## INPUTS

Before starting, confirm these with the user:

- **Repo URL** — GitHub URL (e.g., `https://github.com/dmoskov/newproject`)
- **Project name** — Short identifier used in configs (e.g., `nmk`, `bugdom`, `kit`)
- **Owner** — GitHub org/user (default: `dmoskov`)
- **Default branch** — Usually `main`

If the repo is remote and not yet cloned:
```bash
git clone --depth=50 <REPO_URL> /tmp/<project-name>
cd /tmp/<project-name>
```

---

## PHASE 1: AUDIT THE REPO (~5 min)

Understand the project before touching anything.

### 1.1 Read configuration files

Read all of these that exist (skip ones that don't):
- `package.json`, `yarn.lock`, `pnpm-lock.yaml`
- `tsconfig.json`, `tsconfig.*.json`
- `pyproject.toml`, `setup.py`, `requirements.txt`, `Pipfile`
- `Cargo.toml`, `go.mod`, `Gemfile`
- `Makefile`, `Justfile`
- `docker-compose.yml`, `Dockerfile*`
- `.env.example`, `.env.local.example`
- `README.md`, `CONTRIBUTING.md`
- Any existing `CLAUDE.md`

### 1.2 Read CI/CD configuration

- `.github/workflows/*.yml`
- `.gitlab-ci.yml`, `Jenkinsfile`
- `netlify.toml`, `vercel.json`, `amplify.yml`

### 1.3 Survey directory structure

```bash
find . -type f -not -path './.git/*' -not -path './node_modules/*' \
  -not -path './__pycache__/*' -not -path './venv/*' -not -path './.venv/*' \
  -not -path './target/*' -not -path './dist/*' -not -path './build/*' \
  -not -path './.next/*' | head -200
```

Count files by type:
```bash
find . -type f -not -path './.git/*' -not -path './node_modules/*' \
  -not -path './__pycache__/*' -not -path './venv/*' | \
  sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

### 1.4 Read key source files

Identify and read 3-5 representative source files:
- Main entry point (`src/index.ts`, `main.py`, `src/main.rs`, `app.py`)
- A representative component/module
- Database models or schema if present
- API routes/endpoints if present

### 1.5 Present summary to user

- **What is this?** One-sentence description
- **Stack:** Language, framework, database, hosting
- **Build/Test/Run:** Key commands
- **Size:** File count, line count, language breakdown
- **Architecture:** Monorepo? Microservices? SPA? Serverless?

Wait for user confirmation before proceeding.

---

## PHASE 2: GENERATE CLAUDE.md (~5 min)

Create a comprehensive `CLAUDE.md` at the repo root. This is the source of truth for every
future AI-assisted session on this project.

### Required sections

```markdown
# CLAUDE.md

## Project Overview
[One paragraph: what this is, who it's for, what problem it solves]

## Tech Stack
- Language: [with version]
- Framework: [with version]
- Database: [type and where it runs]
- Hosting: [where it deploys]
- Key dependencies: [list the important ones]

## Project Structure
[Directory tree with explanations for non-obvious directories]

## Development

### Prerequisites
[What needs to be installed]

### Setup
[Exact commands to clone, install, configure]

### Build
[Exact build commands]

### Test
[Exact test commands — unit, integration, e2e separately]

### Lint
[Exact lint/format commands]

### Run locally
[Exact commands to start the dev server]

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
[Table from .env.example or discovered in code]

## Key Patterns and Conventions
[Bullet list of patterns: routing, state management, error handling, etc.]

## Known Issues
[Anything that will trip up a developer or agent]

## Database
[If applicable: models, migration approach, seed data]

## Deployment
[How CI/CD works, what triggers deploys, where it goes]
```

### Guidelines
- **Be specific** — not "run the tests" but `npm run test:e2e`
- **Include actual paths** — `src/app/api/` not "the API directory"
- **100-200 lines** is the sweet spot
- **Include version numbers** — frameworks change behavior between versions

Show the CLAUDE.md draft to the user before saving.

---

## PHASE 3: SECURITY + QUALITY AUDIT (~3 min)

### 3.1 Hardcoded secrets
```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
  --include="*.rs" --include="*.go" --include="*.env" --include="*.yml" \
  -E "(password|secret|api.?key|token|credential|private.?key)\s*[:=]\s*['\"][^'\"]{8,}" \
  . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv || true
```

### 3.2 Exposed endpoints
- Health/debug endpoints leaking internal state
- API routes without authentication
- CORS configured as `*` in production

### 3.3 Injection risks
- Raw SQL with string interpolation
- `dangerouslySetInnerHTML` or unsanitized user input
- `exec`, `eval`, `subprocess` with user input

### 3.4 Error handling
- Empty catch blocks or `catch (e) {}`
- Silent failures (errors caught but not logged)
- API calls without error handling

### 3.5 Test coverage
- Are there tests? What framework?
- Are tests running in CI?
- Approximate coverage?

### 3.6 Standard files check
- `.gitignore` comprehensive
- `.env` files in `.gitignore`
- `README.md` exists and is current
- Lock file committed

---

## PHASE 4: REGISTER IN SCAFFOLD CONFIG FILES

This is the scaffold-specific phase. Register the project in all required configuration files
so the VSM system recognizes and can dispatch tasks to it.

### 4.1 Add to PROJECT_REPOS

File: `claude-code-scaffold/scripts/maintenance/common/project_config.py`

Add entry to `PROJECT_REPOS` dict:
```python
PROJECT_REPOS = {
    # ... existing entries ...
    "<project-name>": ("<owner>", "<repo-name>", "<default-branch>"),
}
```

### 4.2 Add to ENUM_OPTIONS (Asana project enum)

File: `claude-code-scaffold/scripts/maintenance/asana_custom_fields_config.py`

**First**, create the enum option in Asana via API:
```bash
python3 -c "
import sys; sys.path.insert(0, 'claude-code-scaffold/scripts/maintenance')
from asana_direct_client import get_asana_client
client = get_asana_client()
# Add enum option to the 'project' custom field
result = client.post(
    f'/custom_fields/1212217440212712/enum_options',
    {'data': {'name': '<project-name>', 'enabled': True}}
)
print(f'Created enum option GID: {result[\"data\"][\"gid\"]}')"
```

Then add the returned GID to `ENUM_OPTIONS["project"]`:
```python
ENUM_OPTIONS = {
    "project": {
        # ... existing entries ...
        "<project-name>": "<NEW_GID>",
    },
    # ...
}
```

Also add to `PROJECT_MAPPING` dict in the same file:
```python
PROJECT_MAPPING = {
    # ... existing entries ...
    "<project-name>": ENUM_OPTIONS["project"]["<project-name>"],
}
```

### 4.3 Create Asana VSM project board

Create a dedicated Asana project for the new project's tasks:
```bash
python3 -c "
import sys; sys.path.insert(0, 'claude-code-scaffold/scripts/maintenance')
from asana_direct_client import get_asana_client
client = get_asana_client()
result = client.post('/projects', {'data': {
    'name': '<Project Name> - VSM Tasks',
    'workspace': '19421316985',
    'default_view': 'list',
}})
print(f'Created Asana project GID: {result[\"data\"][\"gid\"]}')"
```

Add the new project GID to `VSM_PROJECT_GIDS`:
```python
VSM_PROJECT_GIDS = {
    # ... existing entries ...
    "<project-name>": "<NEW_PROJECT_GID>",
}
```

### 4.4 Add to LETTA_PROJECT_AGENTS (after creating agents in Phase 6)

File: `claude-code-scaffold/scripts/maintenance/common/project_config.py`

After creating the Letta S5 agent in Phase 6, add:
```python
LETTA_PROJECT_AGENTS = {
    # ... existing entries ...
    "<project-name>": "<S5_AGENT_ID>",
}
```

---

## PHASE 5: FILE STANDARDIZATION TASKS (~5 min)

Compile all findings from Phase 3 into prioritized tasks. Each task must be:
- **Scoped to one file or concern** (per Task Scoping Rule: <50 changes, 30min-2hr)
- **Actionable** with exact file paths
- **Verifiable** with acceptance criteria

### Priority levels
- **P1 (Critical):** Security vulnerabilities, hardcoded secrets, data leaks
- **P2 (High):** Missing error handling, silent failures, no CI, broken tests
- **P3 (Medium):** Missing tests, no linter, stale dependencies, missing types
- **P4 (Low):** Code style, documentation gaps, nice-to-have improvements

### Task format
```
**[P1/P2/P3/P4] Title**
- Project: <project-name>
- File(s): `path/to/file.ts`
- Problem: [What's wrong]
- Fix: [What to do]
- Acceptance: [How to verify]
- Agent type: code-builder | security | testing | etc.
- Effort: S | M
```

### Filing tasks to Asana

File each task to the Crucible Task Queue with proper custom fields:

```python
import sys; sys.path.insert(0, 'claude-code-scaffold/scripts/maintenance')
from asana_direct_client import create_task_in_project

# Key GIDs for custom fields:
# project field:           1212217440212712
# task_type field:         1211707732306511
# effort_estimate field:   1211839914139719
# validation_status field: 1211707732306523
# execution_status field:  1212245877760144
# priority field:          1211707726119910

create_task_in_project(
    project_gid="1211710875848660",  # Crucible Task Queue
    name="[<project-name>] <task title>",
    notes="File: <path>\nProblem: <problem>\nFix: <fix>\nAcceptance: <criteria>",
    custom_fields={
        "1212217440212712": "<project-enum-gid>",         # project
        "1211707732306511": "<task-type-enum-gid>",       # task_type
        "1211839914139719": "1211839914139720",           # effort: S
        "1211707732306523": "1211839914468244",           # validation: Approved
        "1212245877760144": "1212245877760145",           # execution: Pending
        "1211707726119910": "<priority-gid>",             # priority
    },
)
```

Common enum GIDs for task filing:
| Field | Value | GID |
|-------|-------|-----|
| effort | S | `1211839914139720` |
| effort | M | `1211839914139721` |
| validation | Approved | `1211839914468244` |
| execution | Pending | `1212245877760145` |
| task_type | Feature | `1211707732306513` |
| task_type | Bug | `1211830600615621` |
| task_type | Security | `1211839914139712` |
| task_type | Testing | `1211707732306514` |
| task_type | DevOps | `1212759312107303` |
| priority | P0 | `1211707726119911` |
| priority | P1 | `1211707732306507` |
| priority | P2 | `1211707732306508` |
| priority | P3 | `1211707732306509` |

Also multi-home the task to the project's VSM board:
```python
# After creating the task, add it to the project's VSM board
from asana_direct_client import get_asana_client
client = get_asana_client()
client.post(f'/tasks/<TASK_GID>/addProject', {
    'data': {'project': '<VSM_PROJECT_GID>'}
})
```

---

## PHASE 6: CREATE LETTA ROLE AGENTS

Create persistent Letta agents for the project. These accumulate memory across task executions.

### 6.1 Create the Project S5 (Policy) agent

The S5 agent is the project's governance agent. It stores project context and
is consulted by task executors via `fetch_letta_memory_context`.

Agent naming convention: `vsm_policy_<project-name>`

```bash
python3 -c "
import sys; sys.path.insert(0, 'claude-code-scaffold/scripts/maintenance')
from letta_memory import create_agent

# Create the S5 agent
agent_id = create_agent(
    name='vsm_policy_<project-name>',
    description='System 5 Policy agent for <project-name>',
    tags=['system-5', '<project-name>', 'vsm'],
)
print(f'Created S5 agent: {agent_id}')
"
```

If `create_agent` is not available, use the Letta REST API directly:
```bash
curl -X POST http://letta.crucible-internal:8283/v1/agents \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "vsm_policy_<project-name>",
    "description": "System 5 Policy agent for <project-name>",
    "tags": ["system-5", "<project-name>", "vsm"],
    "model": "claude-opus-4-6",
    "embedding": "letta-free",
    "memory_blocks": [
      {"label": "project_context", "value": "<CLAUDE.md summary here>", "limit": 5000},
      {"label": "active_context", "value": "Newly onboarded project. No active work yet.", "limit": 5000}
    ]
  }'
```

### 6.2 Create common specialist agents

For projects that will use autonomous execution, create the most common specialists.
Naming convention: `{agent_type}_{project_name}`

Common specialist agents to create:
- `code_builder_<project>` — Feature implementation
- `debugger_<project>` — Bug investigation and fixing
- `testing_<project>` — Test writing and coverage
- `security_<project>` — Security hardening

```bash
# For each specialist:
python3 -c "
import sys; sys.path.insert(0, 'claude-code-scaffold/scripts/maintenance')
from letta_memory import create_agent

for agent_type in ['code_builder', 'debugger', 'testing', 'security']:
    agent_id = create_agent(
        name=f'{agent_type}_<project-name>',
        description=f'{agent_type} specialist for <project-name>',
        tags=[agent_type.replace('_', '-'), '<project-name>', 'specialist'],
    )
    print(f'Created {agent_type}: {agent_id}')
"
```

### 6.3 Update LETTA_PROJECT_AGENTS

After creating the S5 agent, add its ID to the static map (Phase 4.4):

File: `claude-code-scaffold/scripts/maintenance/common/project_config.py`
```python
LETTA_PROJECT_AGENTS = {
    # ... existing entries ...
    "<project-name>": "<S5_AGENT_ID_FROM_6.1>",
}
```

### 6.4 Initialize project VSM record

Run the VSM initialization script:
```bash
cd claude-code-scaffold
python scripts/maintenance/vsm/initialize_project_vsm.py \
  --project-id <project-name> --autonomy supervised
```

This creates the `project_vsm` database record with default settings.

---

## PHASE 7: COMMIT AND VERIFY

### 7.1 Commit CLAUDE.md to the target repo

```bash
cd /tmp/<project-name>
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md for AI-assisted development"
git push origin main
```

### 7.2 Commit config changes to scaffold repo

```bash
cd <scaffold-repo-path>
git add claude-code-scaffold/scripts/maintenance/common/project_config.py
git add claude-code-scaffold/scripts/maintenance/asana_custom_fields_config.py
git commit -m "feat: onboard <project-name> into VSM system"
git push origin main
```

### 7.3 Verify registration

Run a quick verification:
```bash
python3 -c "
import sys; sys.path.insert(0, 'claude-code-scaffold/scripts/maintenance')
from common.project_config import PROJECT_REPOS, LETTA_PROJECT_AGENTS
from asana_custom_fields_config import ENUM_OPTIONS, VSM_PROJECT_GIDS

project = '<project-name>'
checks = {
    'PROJECT_REPOS': project in PROJECT_REPOS,
    'ENUM_OPTIONS': project in ENUM_OPTIONS.get('project', {}),
    'VSM_PROJECT_GIDS': project in VSM_PROJECT_GIDS,
    'LETTA_PROJECT_AGENTS': project in LETTA_PROJECT_AGENTS,
}
for check, ok in checks.items():
    status = 'PASS' if ok else 'FAIL'
    print(f'  [{status}] {check}')
print()
print('All checks passed!' if all(checks.values()) else 'Some checks failed.')
"
```

### 7.4 Present summary

Show the user:
- **CLAUDE.md**: Location and line count
- **Config registrations**: PROJECT_REPOS, ENUM_OPTIONS, VSM_PROJECT_GIDS, LETTA_PROJECT_AGENTS
- **Asana**: Project board GID, enum option GID
- **Letta agents**: S5 agent ID + specialist agent IDs
- **Tasks filed**: Count by priority (P1/P2/P3/P4)
- **Next steps**: Which P1 tasks to tackle first

---

## TIPS

- **Don't install dependencies** during audit — just read configs
- **Read before you write** — understand the full picture before generating CLAUDE.md
- **Security first** — always audit security before quality
- **Show, don't commit** — show CLAUDE.md to user before saving
- **One step at a time** — confirm each phase with user before proceeding
- **Letta agents need the CLAUDE.md summary** — the S5 agent's `project_context` memory block
  should contain a concise version of the project's CLAUDE.md
- **Task Scoping Rule applies** — every filed task must be <50 line changes, 30min-2hr scope
