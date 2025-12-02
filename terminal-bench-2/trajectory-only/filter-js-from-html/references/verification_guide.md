# Verification Guide for HTML JavaScript Filtering

This guide provides strategies for testing and verifying HTML sanitization implementations.

## 1. Testing Philosophy

### Defense in Depth
Test not just for correctness, but for security. Assume adversarial input. The goal is to prove the filter is secure, not just that it works on friendly input.

### Test Preservation
Never delete test files. They serve as:
- Documentation of what was tested
- Regression tests for future changes
- Evidence of thorough verification

### Complete Verification
After all edits, always verify:
1. The complete implementation (read the entire file)
2. Syntax correctness (run/compile the code)
3. Output correctness (compare expected vs actual)

## 2. Test Categories

### Category 1: Basic Functionality

Test that core filtering works:

```html
<!-- Input -->
<script>alert('xss')</script>
<div onclick="alert('xss')">Click</div>
<a href="javascript:alert('xss')">Link</a>

<!-- Expected: Scripts removed, events removed, javascript: removed -->
<div>Click</div>
<a>Link</a>
```

### Category 2: Format Preservation

Test that non-malicious content remains unchanged:

```html
<!-- This should remain EXACTLY as-is -->
<div class="test"   id='foo'>
    <p>Paragraph with    spaces</p>
    <br />
    <img src="image.jpg" alt="&amp; ampersand" />
    <span style="color: red;">Text</span>
</div>
```

Verify with byte-level diff:
```bash
diff <(cat original.html) <(cat filtered.html)
# Or for hex comparison:
xxd original.html > original.hex
xxd filtered.html > filtered.hex
diff original.hex filtered.hex
```

### Category 3: Case Sensitivity

Test mixed casing:

```html
<SCRIPT>alert(1)</SCRIPT>
<ScRiPt>alert(1)</ScRiPt>
<div ONCLICK="alert(1)">
<div OnClick="alert(1)">
<a HREF="JAVASCRIPT:alert(1)">
<a href="JaVaScRiPt:alert(1)">
```

### Category 4: Whitespace Handling

Test whitespace variations:

```html
<script >alert(1)</script>
<script	>alert(1)</script>
<div onclick = "alert(1)">
<div onclick
="alert(1)">
<a href=" javascript:alert(1)">
<a href="javascript :alert(1)">
<a href="java
script:alert(1)">
```

### Category 5: Entity Encoding

Test entity preservation and bypass attempts:

```html
<!-- These entities should be PRESERVED -->
<p>&amp; &lt; &gt; &quot;</p>
<p>&#38; &#60; &#62;</p>

<!-- These should be BLOCKED (encoded XSS) -->
<a href="&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;&#58;alert(1)">
<div onclick="&#97;lert(1)">
```

### Category 6: Dangerous Elements

Test removal of inherently dangerous elements:

```html
<iframe src="page.html"></iframe>
<iframe srcdoc="<script>alert(1)</script>"></iframe>
<object data="data:text/html,<script>alert(1)</script>">
<embed src="javascript:alert(1)">
<svg onload="alert(1)"><script>alert(1)</script></svg>
<meta http-equiv="refresh" content="0;url=javascript:alert(1)">
```

### Category 7: URL Scheme Variations

Test all dangerous URL schemes:

```html
<a href="javascript:alert(1)">
<a href="vbscript:alert(1)">
<a href="data:text/html,<script>alert(1)</script>">
<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">
<form action="javascript:alert(1)">
<input formaction="javascript:alert(1)">
<button formaction="javascript:alert(1)">
```

### Category 8: Error Handling

Test edge cases and error conditions:

```bash
# Empty file
touch empty.html
./filter.py empty.html

# Non-existent file
./filter.py nonexistent.html

# Invalid HTML
echo "<div><p></div></p>" > invalid.html
./filter.py invalid.html

# Binary file
echo -e "\x00\x01\x02" > binary.html
./filter.py binary.html

# Large file
python -c "print('<div>'*100000)" > large.html
./filter.py large.html
```

## 3. Verification Methods

### Method 1: Diff Comparison

For format preservation verification:

```bash
# Create safe version of original (manually verified)
cp original.html expected.html
# Edit expected.html to remove only XSS vectors

# Run filter
./filter.py original.html > actual.html

# Compare
diff expected.html actual.html
```

### Method 2: Security Testing

Use known XSS payloads:

```bash
# Create test file with XSS payloads
cat > xss_test.html << 'EOF'
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<body onload=alert(1)>
<svg onload=alert(1)>
<a href="javascript:alert(1)">click</a>
EOF

# Filter and check output contains NO executable content
./filter.py xss_test.html > filtered.html

# Search for remaining dangerous patterns
grep -iE "(script|onclick|onerror|onload|javascript:|data:)" filtered.html
# Should return nothing
```

### Method 3: Browser Testing

For complete XSS verification:

```bash
# Create test harness
cat > test_harness.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <script>
    window.xss_triggered = false;
    window.alert = function() { window.xss_triggered = true; };
    window.onerror = function() { return true; };
    </script>
</head>
<body>
<!-- FILTERED CONTENT GOES HERE -->
<script>
document.body.innerHTML += '<p>XSS Triggered: ' + window.xss_triggered + '</p>';
</script>
</body>
</html>
EOF

# Insert filtered content and open in browser
# xss_triggered should remain false
```

### Method 4: Automated Test Suite

Create a comprehensive test script:

```python
#!/usr/bin/env python3
import subprocess
import sys

tests = [
    # (input, must_not_contain, must_contain)
    ("<script>alert(1)</script>", ["<script"], []),
    ("<div onclick='x'>", ["onclick"], ["<div"]),
    ('<a href="javascript:x">', ["javascript:"], ["<a"]),
    ("<p>&amp;</p>", [], ["&amp;"]),  # Must preserve entities
    # Add more tests...
]

def run_test(input_html, must_not_contain, must_contain):
    # Write input
    with open('/tmp/test_input.html', 'w') as f:
        f.write(input_html)

    # Run filter
    result = subprocess.run(
        ['./filter.py', '/tmp/test_input.html'],
        capture_output=True, text=True
    )
    output = result.stdout

    # Check must_not_contain
    for pattern in must_not_contain:
        if pattern.lower() in output.lower():
            return False, f"Found forbidden pattern: {pattern}"

    # Check must_contain
    for pattern in must_contain:
        if pattern not in output:
            return False, f"Missing required pattern: {pattern}"

    return True, "PASS"

# Run all tests
passed = 0
failed = 0
for i, (inp, not_contain, contain) in enumerate(tests):
    success, msg = run_test(inp, not_contain, contain)
    status = "PASS" if success else "FAIL"
    print(f"Test {i+1}: {status} - {msg}")
    if success:
        passed += 1
    else:
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
```

## 4. Common Verification Mistakes

### Mistake 1: Visual Inspection Only
**Problem:** Output "looks right" but has subtle differences.
**Solution:** Use diff tools for exact comparison.

### Mistake 2: Testing Only Happy Path
**Problem:** Filter works on clean input, fails on adversarial input.
**Solution:** Include XSS bypass attempts in tests.

### Mistake 3: Deleting Test Evidence
**Problem:** Tests deleted, cannot verify or reproduce issues.
**Solution:** Keep all test files in a tests/ directory.

### Mistake 4: Not Verifying Complete Code
**Problem:** File truncated or corrupted during editing.
**Solution:** Read and verify entire file after all edits.

### Mistake 5: Incomplete Test Coverage
**Problem:** Only testing a few XSS vectors.
**Solution:** Use comprehensive test suite from references/xss_vectors.md.

## 5. Final Verification Checklist

Before declaring implementation complete:

- [ ] Read and verify the complete implementation file
- [ ] Run syntax/compilation check
- [ ] Execute all test categories
- [ ] Verify format preservation with diff
- [ ] Test all event handler attributes
- [ ] Test all dangerous URL schemes
- [ ] Test all dangerous elements
- [ ] Test encoding bypass attempts
- [ ] Test error handling
- [ ] Keep all test files
- [ ] Document any limitations or known issues
