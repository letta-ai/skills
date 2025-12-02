---
name: modernize-scientific-stack
description: Guidance for modernizing legacy Python 2 scientific computing code to Python 3. This skill should be used when tasks involve converting outdated scientific Python scripts (using deprecated libraries like ConfigParser, cPickle, urllib2, or Python 2 syntax) to modern Python 3 equivalents with contemporary scientific stack (NumPy, pandas, scipy, matplotlib). Applies to data processing, analysis pipelines, and scientific computation modernization tasks.
---

# Modernize Scientific Stack

This skill provides guidance for converting legacy Python 2 scientific computing code to modern Python 3+ with contemporary libraries.

## Approach

### 1. Complete Codebase Analysis

Before writing any code, read all source files completely:

- Read the entire legacy script without truncation
- Read all configuration files (INI, YAML, JSON)
- Read sample data files to understand structure
- Document all imports, dependencies, and data flow

**Critical:** If a file read is truncated, explicitly request the remaining content. Incomplete analysis leads to missed modernization requirements.

### 2. Identify Modernization Requirements

Categorize changes needed:

**Python 2 to 3 Syntax:**
- `print` statements to `print()` functions
- `unicode`/`str` handling to Python 3 strings
- Division operators (`/` vs `//`)
- Exception syntax (`except Exception, e:` to `except Exception as e:`)

**Library Replacements:**
- `ConfigParser` → `configparser`
- `cPickle` → `pickle`
- `urllib2` → `urllib.request` or `requests`
- `StringIO` → `io.StringIO`
- File paths with strings → `pathlib.Path`

**Only modernize what is actually used.** Avoid listing library replacements for code not present in the source.

### 3. Environment Setup

Check available tools before assuming availability:

```bash
# Check for package managers
which pip python3 uv conda 2>/dev/null
```

Prefer tools already available. If installing new tools (like `uv`), verify installation succeeded before proceeding.

For PATH modifications, set once at the beginning:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Avoid repeating this in every command.

### 4. Dependency Management

When creating `requirements.txt` or `pyproject.toml`:

- Justify the choice between the two formats
- Include only necessary dependencies
- If the task specifies "at least one of" certain libraries, justify which ones are included and why

### 5. Implementation

**Write complete files:** Ensure Write tool calls contain the entire file content. After writing, verify the file:

```bash
# Verify file was written correctly
python -m py_compile script_name.py
wc -l script_name.py
```

**Verify file contents:** After writing critical files, read them back to confirm correctness:

```python
# Read back and verify
cat script_name.py | head -50
```

**Preserve functionality:** The modernized code must produce identical output to the original. Document expected outputs before implementation.

## Verification Strategy

### Syntax Validation

Always validate Python syntax before execution:

```bash
python -m py_compile modernized_script.py
```

### Functional Verification

1. **Run the modernized script** and capture output
2. **Independently verify results** using raw data (e.g., with pandas or manual calculation)
3. **Compare outputs** to ensure they match expected values

Consolidate verification into a single comprehensive test rather than multiple scattered commands.

### Edge Case Testing

Test beyond the happy path:

- **Missing files:** What happens if input files don't exist?
- **Malformed data:** How does the script handle missing or non-numeric values?
- **Unicode handling:** Verify special characters (like `°C`) render correctly
- **Configuration validation:** Confirm config values are actually used, not just readable

### Output Format Verification

If specific output format is required:
- Check exact string formatting
- Verify decimal precision
- Confirm units and labels match specifications

## Common Pitfalls

### File Write Truncation

**Problem:** Write tool calls may be truncated, resulting in incomplete files that appear successful.

**Solution:** After writing files:
1. Check file size matches expected content
2. Run syntax validation
3. Read back critical sections to verify completeness

### Incomplete Source Analysis

**Problem:** Truncated file reads lead to missed requirements.

**Solution:** If a Read operation shows truncation, explicitly request remaining content with offset parameter.

### Over-Analysis

**Problem:** Listing modernizations for code that doesn't exist in the actual requirements.

**Solution:** Focus analysis on what the task actually requires, not every possible Python 2 issue.

### Tool Availability Assumptions

**Problem:** Assuming tools like `uv` are installed.

**Solution:** Check tool availability first, use fallbacks (pip is almost always available).

### Repeated Operations

**Problem:** Running same setup commands (PATH export, tool checks) multiple times.

**Solution:** Consolidate setup into a single initial step.

### Missing Content Verification

**Problem:** Not verifying that written files contain intended content.

**Solution:** After every critical file write, validate syntax and optionally read back key sections.

## Decision Framework

When making implementation choices:

1. **Package management:** Use `requirements.txt` for simple projects, `pyproject.toml` for packages with build requirements
2. **Dependencies:** Include minimum necessary; justify optional dependencies
3. **Error handling:** Match the original script's behavior unless task explicitly requests improvements
4. **Code style:** Follow modern Python conventions (type hints optional unless specified)

## Output Checklist

Before marking task complete, verify:

- [ ] All source files were read completely (no truncation)
- [ ] Written files passed syntax validation
- [ ] Script produces correct output matching specifications
- [ ] Results independently verified against raw data
- [ ] Edge cases considered (even if not fully tested)
- [ ] No repeated/redundant operations in execution
