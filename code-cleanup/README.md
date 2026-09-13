# Code Cleanup Skill

Targeted cleanup skills for AI-assisted code maintenance. Each sub-skill focuses on exactly
one concern, produces a diagnostic summary before making changes, and can be run independently.

## Usage

In Claude Code:
```
/code-cleanup
```

Or trigger a specific sub-skill:
- "clean up dead code"
- "audit error handling"
- "add type annotations"
- "extract long functions"

## Sub-Skills

### 1. Dead Code (`prompts/dead-code.md`)
Finds and removes unused imports, unreachable code, and dead functions.
- Uses language-specific linters (ruff F401/F841, eslint no-unused-vars, cargo check)
- Cross-references function definitions against callers
- Confidence-rated findings (HIGH/MEDIUM/LOW)
- Preserves `__init__.py` exports, test fixtures, CLI entry points

### 2. Error Handling (`prompts/error-handling.md`)
Finds bare except/catch blocks, silent failures, and missing error handling.
- Detects bare `except:`, empty `catch {}`, swallowed errors
- Flags API/DB/file operations without error handling
- Checks for dangerous patterns (Pokemon catching, lost tracebacks)
- Severity-rated findings (HIGH/MEDIUM/LOW)

### 3. Type Annotations (`prompts/type-annotations.md`)
Adds missing type annotations for Python (mypy) and TypeScript (strict mode).
- Measures current annotation coverage
- Prioritizes public API functions and ambiguous types
- Uses modern Python syntax (`list[str]`, `str | None`)
- Replaces TypeScript `any` with proper types
- Respects project conventions and Python version

### 4. Extract Functions (`prompts/extract-functions.md`)
Finds functions over 50 lines and extracts logical units.
- AST-aware function length detection (Python)
- Identifies logical sections by comments, blank lines, and nesting
- Proposes specific extractions with before/after previews
- Preserves transactional boundaries and error handling context

## How Each Sub-Skill Works

Every sub-skill follows the same pattern:

1. **Scan** — Search the codebase for the target pattern
2. **Diagnose** — Produce a summary table of findings with file paths and line numbers
3. **Confirm** — Present findings to the user before making changes
4. **Fix** — Apply targeted fixes, one file at a time
5. **Verify** — Run lint/tests to confirm nothing broke

## Running Order (Full Cleanup)

When running all sub-skills, the recommended order is:

1. **Dead code** — safest, only removes code, never adds
2. **Error handling** — adds safety nets, rarely breaks things
3. **Type annotations** — additive, improves tooling
4. **Extract functions** — structural refactoring, do last

Commit after each sub-skill for atomic, reviewable changes.

## File Structure

```
skills/code-cleanup/
  SKILL.md                           # Skill trigger and metadata
  README.md                          # This file
  prompts/
    dead-code.md                     # Unused imports, unreachable code, dead functions
    error-handling.md                # Bare except, silent failures, missing handlers
    type-annotations.md              # Missing types for Python and TypeScript
    extract-functions.md             # Long function detection and extraction
```
