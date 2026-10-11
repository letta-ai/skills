# claudemd-generator

Generate a comprehensive CLAUDE.md for any project by scanning the codebase.

## What it does

Scans a project's source code, configuration, CI, and git history to produce a CLAUDE.md
file (100-200 lines) that serves as the definitive reference for AI-assisted development.

The 9-step scan covers:

1. **Package configuration** — language, framework, dependencies, scripts
2. **Directory structure** — layout, file counts, line counts
3. **CI/CD workflows** — build triggers, test steps, deployment
4. **Environment variables** — from .env files, CI configs, and source code
5. **Test setup** — framework, location, how to run
6. **Git history** — commit conventions, branch patterns, active contributors
7. **Key source files** — entry points, routes, models, utilities
8. **Generate CLAUDE.md** — assemble findings into structured document
9. **Review and save** — verify accuracy, check paths, confirm with user

## Usage

In Claude Code:
```
/claudemd-generator
```

Or trigger with natural language:
- "generate claude md"
- "create claude md for this project"
- "write a claudemd"

## Output

A `CLAUDE.md` file at the project root containing:

| Section | Content |
|---------|---------|
| **Project Overview** | What it is, who uses it, what problem it solves |
| **Tech Stack** | Language, framework, database, hosting, key deps (with versions) |
| **Project Structure** | Annotated directory tree |
| **Development** | Prerequisites, setup, build, test, lint, run commands |
| **Environment Variables** | Full table with required/optional and descriptions |
| **Key Patterns** | Coding conventions, error handling, auth, database access |
| **Known Issues** | Gotchas that trip up developers and AI agents |
| **Database** | ORM, schema, migrations (if applicable) |
| **Deployment** | CI/CD triggers, hosting, environment config |

## Quality targets

- **100-200 lines** — enough to be useful, not so long it gets ignored
- **Every command works** — copy-pasteable bash blocks verified against real configs
- **Every path exists** — no guessed or generic paths
- **Specific, not generic** — captures what makes THIS project different

## Origin

Based on the pattern that generated a 152-line CLAUDE.md for the nmk project in one prompt.
Extracted from the project-onboarding skill's Phase 2 into a standalone, focused skill.

## Files

```
skills/claudemd-generator/
  SKILL.md                           # Skill trigger and metadata
  README.md                          # This file
  prompts/
    generate-prompt.md               # Full 9-step generation prompt
```
