# Project Onboarding (Scaffold-Specific)

Full project onboarding into the VSM autonomous agent system. Takes a repo URL and
produces a fully registered project with CLAUDE.md, Asana integration, Letta role agents,
and prioritized standardization tasks.

## Usage

In Claude Code:
```
/project-onboarding
```

Or trigger with natural language:
- "onboard this project"
- "set up this repo"
- "new project setup"

## Input

- **Repo URL** — GitHub URL (e.g., `https://github.com/dmoskov/newproject`)
- **Project name** — Short identifier (e.g., `nmk`, `bugdom`, `kit`)
- **Owner** — GitHub org/user (default: `dmoskov`)

## What It Does

| Phase | Description | Output |
|-------|-------------|--------|
| 1. Audit | Read configs, structure, key source files | Project understanding |
| 2. CLAUDE.md | Generate 100-200 line project guide | `CLAUDE.md` at repo root |
| 3. Security + Quality | Secrets, injection, error handling, tests | Prioritized findings |
| 4. Config Registration | Add to PROJECT_REPOS, ENUM_OPTIONS, VSM_PROJECT_GIDS | Config file updates |
| 5. File Tasks | Create Asana tasks for all findings | Asana tasks with custom fields |
| 6. Letta Agents | Create S5 + specialist agents | Agent IDs in LETTA_PROJECT_AGENTS |
| 7. Verify | Confirm all registrations, present summary | Verification report |

## Config Files Modified

| File | What Gets Added |
|------|-----------------|
| `common/project_config.py` | `PROJECT_REPOS` entry, `LETTA_PROJECT_AGENTS` entry |
| `asana_custom_fields_config.py` | `ENUM_OPTIONS["project"]` entry, `VSM_PROJECT_GIDS` entry, `PROJECT_MAPPING` entry |

## Letta Agents Created

| Agent | Naming Convention | Purpose |
|-------|-------------------|---------|
| S5 Policy | `vsm_policy_<project>` | Governance, project context, memory |
| Code Builder | `code_builder_<project>` | Feature implementation |
| Debugger | `debugger_<project>` | Bug investigation |
| Testing | `testing_<project>` | Test writing |
| Security | `security_<project>` | Security hardening |

## Integration

This skill integrates with the VSM task execution pipeline:
- Filed tasks are picked up by `meta_orchestrator.py` on the next 5-minute cycle
- Specialist agents are resolved by `resolve_specialist_agent_id()` using the naming convention
- The S5 agent is consulted by `fetch_letta_memory_context()` during task execution

## Why This Is Private

This skill contains internal Asana GIDs, Letta agent IDs, and infrastructure configuration
specific to the scaffold system. The generic version (without GIDs or VSM registration) lives
in the public `sharedskills` repo.

## Files

```
skills/project-onboarding/
  SKILL.md                    # Skill trigger and metadata
  README.md                   # This file
  prompts/
    onboard.md                # Full onboarding prompt (7 phases)
```
