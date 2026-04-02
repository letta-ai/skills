# Security Audit Skill

Runs a comprehensive security audit on any codebase, checking for OWASP Top 10 and common
vulnerability patterns across all major languages and frameworks.

## Usage

Trigger the skill in Claude Code:
```
/security-audit
```

Or use natural language triggers:
- "security audit"
- "audit this codebase for vulnerabilities"
- "find security bugs"
- "check for vulnerabilities"
- "security scan"

## Input

Provide one of:
- **No input**: Audits the current working directory
- **Directory path**: Audits a specific directory or repository
- **File path**: Focuses audit on a specific file or module
- **Vulnerability class**: Prioritizes a specific category (e.g., "focus on injection vulnerabilities")

## What It Checks

| Category | Examples |
|----------|---------|
| **SQL Injection** | String concatenation in queries, f-string SQL, unsanitized input |
| **Hardcoded Secrets** | API keys, passwords, private keys, tokens in source code |
| **Command Injection** | `os.system()`, `eval()`, `exec()`, `shell=True` with user input |
| **Path Traversal** | File operations with user-controlled paths, `../` sequences |
| **SSRF** | HTTP requests with user-controlled URLs reaching internal services |
| **XSS** | `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, unescaped template output |
| **Auth Bypass** | Missing auth middleware, weak JWT config, timing-unsafe comparisons |
| **CORS Misconfig** | Wildcard origins with credentials, overly permissive policies |
| **Race Conditions** | Check-then-act without locking, non-atomic balance updates |
| **Insecure Deserialization** | `pickle.loads`, `yaml.load`, untrusted `ObjectInputStream` |
| **Cryptographic Issues** | MD5/SHA1 for security, weak ciphers, `Math.random()` for tokens |
| **Information Disclosure** | Debug mode in production, verbose error traces, leaked internals |

## Output

Each finding includes:

| Field | Description |
|-------|-------------|
| **Severity** | CRITICAL / HIGH / MEDIUM / LOW / INFO |
| **File** | Exact file path |
| **Line** | Line number |
| **Category** | Vulnerability class (SQL Injection, XSS, etc.) |
| **Issue** | What's wrong and what an attacker could do |
| **Code** | The vulnerable code snippet |
| **Fix** | Specific remediation with corrected code |

A summary table is provided at the end with totals by severity.

## How It Works

The skill follows a 5-step algorithm (see `prompts/audit-prompt.md`):

1. **Discover** - Identify languages, frameworks, and entry points
2. **Scan** - Search for vulnerability patterns across all source files
3. **Analyze** - Read flagged code in context to confirm or dismiss each candidate
4. **Classify** - Assign severity based on exploitability and impact
5. **Report** - Output structured findings with evidence and fixes

## Supported Languages

The audit patterns cover:
- Python (Flask, Django, FastAPI)
- JavaScript / TypeScript (Express, Node.js, React)
- Go (net/http, Gin)
- Java (Spring, Servlets)
- Rust
- Any language with similar patterns

## False Positive Policy

The skill is designed to minimize false positives:
- Every finding is confirmed by reading the code in context
- Data flow is traced from source (user input) to sink (vulnerable operation)
- Existing mitigations (parameterized queries, sanitizers) are checked
- Uncertain findings note their confidence level

## File Structure

```
skills/security-audit/
  SKILL.md                              # Skill trigger definition
  README.md                             # This file
  prompts/
    audit-prompt.md                     # Full audit algorithm and patterns
```
