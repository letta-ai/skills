---
name: project-onboarding
description: Onboard a new project into the VSM system — audit, CLAUDE.md, config registration, Letta agents, and task filing
triggers:
  - "onboard this project"
  - "onboard project"
  - "new project setup"
  - "project onboarding"
tools_required:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - Task
  - TodoWrite
---

# Project Onboarding Skill

Scaffold-specific skill for onboarding a new project into the VSM autonomous agent system.
Goes from "here's a repo URL" to a fully registered project with CLAUDE.md, Asana integration,
Letta role agents, and prioritized standardization tasks.

## When to Use

- A new repository needs to be brought under VSM management
- An existing project was never fully registered (missing from PROJECT_REPOS, no Letta agents, etc.)
- Dustin adds a new project and wants it ready for autonomous task execution

## What It Does

1. **Audit** the repo (understand stack, structure, patterns)
2. **Generate CLAUDE.md** (100-200 lines, project-specific)
3. **Register in config files** (PROJECT_REPOS, ENUM_OPTIONS, LETTA_PROJECT_AGENTS)
4. **Create Asana project board** and add enum option for the project
5. **File standardization tasks** (security, quality, CI gaps)
6. **Create Letta role agents** for the project (S5 + common specialists)

## Workflow

Follow `prompts/onboard.md` for the full onboarding algorithm.

## Constraints

- This skill contains internal Asana GIDs, agent IDs, and infrastructure references
- It belongs in the private `skof` repo, NOT in public `sharedskills`
- The generic (non-scaffold) version lives in sharedskills for use on standalone repos
