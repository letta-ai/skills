---
name: security-audit
description: Run a comprehensive security audit on any codebase, checking for OWASP Top 10 and common vulnerability patterns
triggers:
  - "security audit"
  - "audit this codebase for vulnerabilities"
  - "find security bugs"
  - "check for vulnerabilities"
  - "security scan"
tools_required:
  - Bash
  - Read
  - Grep
  - Glob
  - Task
  - TodoWrite
---

# Security Audit Skill

Run a comprehensive, language-agnostic security audit on any codebase. Checks for SQL injection,
hardcoded secrets, CORS misconfigurations, path traversal, SSRF, auth bypass, race conditions,
command injection, and other OWASP Top 10 vulnerability classes.

## When to Use

- Before shipping a release or merging a large feature branch
- During periodic security reviews
- When onboarding a new codebase or dependency
- After a security incident to check for similar patterns
- When a task explicitly calls for security hardening

## Input

The user provides one of:
1. A directory or repository to audit (defaults to current working directory)
2. A specific file or module path to focus on
3. A vulnerability class to prioritize (e.g., "focus on injection vulnerabilities")

## Workflow

Follow `prompts/audit-prompt.md` for the full audit algorithm.

**Quick summary:**
1. **Discover** - Identify languages, frameworks, and entry points in the codebase
2. **Scan** - Search for vulnerability patterns across all source files
3. **Analyze** - Read flagged code in context to confirm or dismiss each finding
4. **Classify** - Assign severity (CRITICAL / HIGH / MEDIUM / LOW / INFO) per finding
5. **Report** - Output structured findings with file, line, issue, and fix

## Output Format

Each confirmed finding is reported as:

```
### [SEVERITY] Issue Title

- **File:** path/to/file.ext
- **Line:** 42
- **Category:** SQL Injection | Hardcoded Secret | SSRF | etc.
- **Issue:** Description of the vulnerability and its impact
- **Code:**
  ```
  vulnerable code snippet
  ```
- **Fix:** Specific remediation with corrected code example
```

A summary table is provided at the end:

| # | Severity | Category | File | Line | Issue |
|---|----------|----------|------|------|-------|
| 1 | CRITICAL | SQL Injection | src/db.py | 42 | User input in raw query |
| ... | ... | ... | ... | ... | ... |

## Constraints

- Only report confirmed vulnerabilities with evidence (file path + code)
- Do NOT report style issues, linting warnings, or non-security concerns
- False positives waste reviewer time — when uncertain, note confidence level
- Findings must be actionable: every issue must include a concrete fix
