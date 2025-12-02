---
name: break-filter-js-from-html
description: This skill provides guidance for XSS filter bypass tasks where the goal is to craft HTML payloads that execute JavaScript despite sanitization filters. Use this skill when tasks involve bypassing HTML sanitizers (like BeautifulSoup), exploiting parser differentials between server-side sanitizers and browsers, or security testing/CTF challenges involving XSS filter evasion.
---

# XSS Filter Bypass Methodology

## Overview

This skill provides a systematic approach for bypassing HTML/JavaScript sanitization filters in authorized security testing contexts (CTF challenges, penetration testing, security research). The methodology emphasizes understanding filter mechanisms before attempting bypasses, avoiding trial-and-error approaches in favor of systematic analysis.

## Phase 1: Filter Analysis

Before attempting any bypasses, thoroughly analyze the filter implementation:

### Identify the Sanitization Library
- Determine which library performs sanitization (BeautifulSoup, DOMPurify, html-sanitizer, etc.)
- Identify the parser being used (html.parser, lxml, html5lib for BeautifulSoup)
- Research known quirks and bypass techniques for that specific library/parser combination

### Map Filter Behavior
Create a systematic map of what the filter blocks vs. preserves:

1. **Blocked Elements**: Test which HTML tags are removed
   - Script-related: `<script>`, `<noscript>`
   - Frame-related: `<iframe>`, `<frame>`, `<object>`, `<embed>`
   - Other dangerous: `<base>`, `<link>`, `<meta>`

2. **Blocked Attributes**: Test which attributes are stripped
   - Event handlers: `onclick`, `onload`, `onerror`, `onmouseover`, etc.
   - URL attributes with javascript: `href="javascript:..."`, `src="javascript:..."`

3. **Preserved Elements**: Identify what passes through unchanged
   - Standard HTML elements: `<div>`, `<span>`, `<p>`, `<img>`, `<a>`, `<style>`
   - SVG elements: `<svg>`, `<animate>`, `<set>`
   - Math elements: `<math>`

### Examine Filter Implementation
- Read the filter source code if available
- Look for regex-based filtering (often bypassable)
- Check if filtering is case-sensitive
- Determine if the filter runs once or recursively

## Phase 2: Systematic Bypass Categories

Organize bypass attempts by category rather than random trial-and-error:

### Category 1: Parser Differential Exploits
Different parsers interpret malformed HTML differently. The server-side sanitizer may parse HTML differently than the browser:

- **Nested tag confusion**: `<noscript><style></noscript><img src=x onerror=alert(1)></style>`
- **Comment injection**: `<!--<script>-->alert(1)<!--</script>-->`
- **Encoding mismatches**: UTF-7, charset switching

### Category 2: Alternative JavaScript Execution Vectors
If `<script>` is blocked, identify other execution paths:

- **SVG with script**: `<svg><script>alert(1)</script></svg>`
- **SVG event handlers**: `<svg onload=alert(1)>`
- **SVG animate**: `<svg><animate onbegin=alert(1)>`
- **Math elements**: `<math><maction actiontype="statusline#http://evil">`

### Category 3: Event Handler Variations
If standard event handlers are blocked:

- **Less common events**: `onfocus`, `onblur`, `onanimationend`, `ontransitionend`
- **Attribute injection**: Breaking out of attribute context
- **Data attributes with event delegation**

### Category 4: URL-Based Execution
- **javascript: protocol in href**: `<a href="javascript:alert(1)">`
- **data: URLs**: `<a href="data:text/html,<script>alert(1)</script>">`
- **Encoded payloads**: URL encoding, HTML entities, mixed encoding

### Category 5: CSS-Based Attacks
- **CSS expressions** (legacy IE): `<div style="background:expression(alert(1))">`
- **CSS injection for data exfiltration**
- **@import with data URLs**

## Phase 3: Testing Methodology

### Build a Testing Harness First
Before testing individual payloads, create infrastructure for efficient testing:

```python
# Example: Test multiple payloads at once
payloads = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    # ... more payloads
]

for payload in payloads:
    filtered = apply_filter(payload)
    print(f"Input: {payload}")
    print(f"Output: {filtered}")
    print(f"Preserved: {payload == filtered}")
    print("---")
```

### Two-Stage Verification
1. **Stage 1 - Filter preservation**: Does the payload survive the filter?
2. **Stage 2 - Browser execution**: Does the filtered payload execute in the browser?

Run Stage 1 tests first to eliminate non-viable candidates before slower browser testing.

### Document All Attempts
Maintain a log of:
- What was tried
- Why it failed (filtered out vs. didn't execute)
- Insights gained for next attempt

## Phase 4: Verification and Validation

### Multiple Verification Steps
- Run the verification test multiple times
- Check all success criteria, not just the primary indicator
- Examine the filtered output for anomalies (duplicate tags, malformed HTML)

### Cross-Browser Considerations
- A bypass working in Chrome may not work in Firefox or Safari
- Identify which browser the test environment uses
- Document browser-specific behavior

### Handle Verification Discrepancies
If initial tests pass but final verification fails:
- Re-read the task requirements
- Check for additional validation steps
- Examine timing issues or race conditions
- Verify the test environment matches expectations

## Common Pitfalls to Avoid

### Premature Success Declaration
- Do not celebrate after a single test pass
- Run additional verification rounds
- Check the overall task status, not just test output

### Workarounds vs. Understanding
- Avoid hacky workarounds that mask underlying issues
- If the test expects files in unexpected locations, understand why before copying files
- Workarounds may introduce inconsistencies

### Inefficient Trial-and-Error
- Do not try random XSS vectors without a systematic framework
- Research before attempting; look up known bypass techniques first
- Understand why previous attempts failed before trying similar approaches

### Ignoring Malformed Output
- Pay attention to duplicate or malformed tags in filtered output
- Malformed output may indicate an unstable bypass
- Question whether the solution is reliable

### Missing Root Cause Analysis
When a bypass works, understand WHY:
- How does the sanitizer parse the payload?
- What browser behavior enables execution?
- Is this a stable, reliable technique or a fragile edge case?

## Reference Resources

For authorized security testing contexts, these resources provide bypass techniques:

- OWASP XSS Filter Evasion Cheat Sheet
- PortSwigger Web Security Academy
- HTML5 Security Cheatsheet
- BeautifulSoup documentation on parser differences
- Browser-specific parsing quirks documentation
