---
name: code-cleanup
description: Targeted cleanup skills — dead code, error handling, types, function extraction. Run one or all.
triggers:
  - "code cleanup"
  - "clean up this code"
  - "dead code"
  - "error handling audit"
  - "add type annotations"
  - "extract functions"
tools_required:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - TodoWrite
---

# Code Cleanup Skill

A set of focused cleanup skills. Each targets exactly one concern and produces a diagnostic
summary before making any changes. Based on the "cleanup waves" pattern.

## Sub-Skills

| Sub-Skill | What It Does |
|-----------|--------------|
| `dead-code` | Remove unused imports, unreachable code, unused functions |
| `error-handling` | Find bare except/catch, missing error handling, silent failures |
| `type-annotations` | Add missing type annotations (Python: mypy, TS: strict mode) |
| `extract-functions` | Find functions >50 lines and extract logical units |

## Usage

Run all sub-skills sequentially:
```
/code-cleanup
```

Or run a specific sub-skill by mentioning it:
```
"clean up dead code"
"audit error handling"
"add type annotations"
"extract long functions"
```

## Workflow

Each sub-skill follows the same pattern:

1. **Scan** — Search the codebase for the target pattern
2. **Diagnose** — Produce a summary table of findings with file paths and line numbers
3. **Confirm** — Present findings to the user before making changes
4. **Fix** — Apply targeted fixes, one file at a time
5. **Verify** — Run lint/tests to confirm nothing broke

## Prompts

Each sub-skill has its own prompt in `prompts/`:

- `prompts/dead-code.md` — Unused imports, unreachable code, dead functions
- `prompts/error-handling.md` — Bare except, silent failures, missing handlers
- `prompts/type-annotations.md` — Missing types for Python (mypy) and TypeScript (strict)
- `prompts/extract-functions.md` — Long functions, logical extraction points

## Running All Sub-Skills

When triggered with the generic "code cleanup" command, run each sub-skill in order:
1. Dead code (safest — only removes, never adds)
2. Error handling (adds safety, rarely breaks things)
3. Type annotations (additive, improves tooling)
4. Extract functions (structural change — do last)

Commit after each sub-skill completes so changes are atomic and reviewable.
