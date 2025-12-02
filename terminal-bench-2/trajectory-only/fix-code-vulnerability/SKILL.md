---
name: fix-code-vulnerability
description: Guidance for identifying and fixing security vulnerabilities in code. This skill should be used when tasks involve fixing CWE-classified vulnerabilities, addressing security flaws, patching injection vulnerabilities, or responding to security-related test failures.
---

# Fix Code Vulnerability

## Overview

This skill provides a systematic approach for identifying, analyzing, and fixing security vulnerabilities in codebases. It emphasizes thorough test analysis, complete code path tracing, and proper security impact documentation to ensure fixes are comprehensive and correctly targeted.

## Workflow

### Step 1: Understand the Vulnerability Context

Before making any changes, gather complete context about the vulnerability:

1. **Run the existing test suite** to identify failing security tests
   - Failing tests often indicate the expected behavior and attack vectors
   - Note the specific test names and assertions

2. **Read complete test files** - not just snippets
   - Understand all test cases, including edge cases
   - Identify exact expected error types and messages
   - Note what characters, inputs, or patterns are being tested

3. **Identify the CWE classification** if provided
   - Research the specific vulnerability type (e.g., CWE-93 for CRLF Injection)
   - Consider related CWEs that may also apply (e.g., CWE-20: Improper Input Validation)

### Step 2: Trace All Code Paths

Security fixes must cover all entry points to the vulnerable code:

1. **Identify the vulnerable functions** - Start with functions mentioned in failing tests
2. **Trace callers** - Find all functions that call the vulnerable code
3. **Identify helper functions** - Look for central validation or processing functions
4. **Map entry points** - Document all ways user input can reach the vulnerable code

Key question: If validation is added to a helper function, will it propagate to all callers?

### Step 3: Analyze Security Impact

Before implementing the fix, document the security impact:

1. **Attack vector** - How could an attacker exploit this vulnerability?
2. **Impact** - What damage could result (e.g., HTTP response splitting, XSS, data exfiltration)?
3. **Affected components** - Which parts of the system are at risk?

This analysis helps ensure the fix addresses the root cause, not just symptoms.

### Step 4: Implement the Fix

When implementing the fix:

1. **Match test expectations exactly**
   - Verify error types match what tests expect (e.g., `ValueError` vs `SecurityError`)
   - Check if specific error message content is validated

2. **Fix at the right abstraction level**
   - Prefer fixing central helper functions that propagate to all callers
   - Avoid duplicating validation logic across multiple locations

3. **Handle all relevant inputs**
   - Check what characters/patterns need blocking (not just the obvious ones)
   - Consider Unicode variants (e.g., Unicode line separators for CRLF)
   - Consider null bytes, control characters, and encoding issues

### Step 5: Verify the Fix

Thorough verification is essential:

1. **Run the full test suite** - All tests should pass, not just security tests
2. **Test edge cases manually**:
   - Empty strings
   - Strings containing only control characters
   - Very long strings
   - Mixed valid and invalid input
   - Characters at string boundaries vs embedded

3. **Verify no regression** - Ensure the fix doesn't break legitimate use cases

## Common Pitfalls

### Incomplete Test Analysis
Reading only partial test files leads to assumptions about expected behavior. Always read the complete test file to understand all assertions and edge cases.

### Missing Code Paths
Fixing only the obvious vulnerable function while missing other entry points that bypass the fix. Always trace all callers and entry points.

### Assuming Error Types
Different frameworks expect different error types. Verify the exact exception class and message format expected by tests.

### Limited Character Coverage
Blocking only `\n` and `\r` when other control characters (like `\0`, tab, or Unicode line separators) should also be blocked.

### No Security Impact Documentation
Failing to document why the vulnerability matters makes code review harder and may lead to incomplete fixes.

### Premature Implementation
Starting to code before fully understanding the test expectations and all code paths affected.

## Verification Checklist

Before considering the fix complete:

- [ ] Read complete test files, not snippets
- [ ] Identified all CWEs that apply (not just the primary one)
- [ ] Traced all code paths to the vulnerable code
- [ ] Documented the security impact and attack vector
- [ ] Verified error types and messages match test expectations
- [ ] Fixed at the appropriate abstraction level
- [ ] Tested edge cases (empty strings, boundary conditions, Unicode)
- [ ] All tests pass (security and non-security tests)
- [ ] No regression in legitimate functionality
