---
name: polyglot-c-py
description: This skill provides guidance for creating polyglot files that are valid in both C and Python. It should be used when tasks require writing code that compiles and runs correctly as both a C program and a Python script, producing identical or specified output from each interpreter/compiler.
---

# Polyglot C-Python

## Overview

A polyglot file is a single source file that is syntactically valid in multiple programming languages and produces correct behavior when executed by each language's interpreter or compiler. Creating C-Python polyglots requires understanding how each language's parser and preprocessor handles the same text differently.

## Core Concepts

### Language Parsing Differences

**C Preprocessor Behavior:**
- Processes `#if 0` / `#endif` blocks by completely ignoring their contents
- Executes before the main compiler sees the code
- Single-line comments `//` hide content until end of line
- Multi-line comments `/* */` can span multiple lines

**Python Parser Behavior:**
- Triple-quoted strings `"""..."""` can hide arbitrary content, including C code
- Python parses the entire file before execution, so runtime exits like `sys.exit(0)` do not prevent parse errors
- Single-line comments `#` hide content until end of line
- The `#` character in C preprocessor directives is valid Python comment syntax

### Key Polyglot Patterns

**Pattern 1: Using `#if 0` to Hide Python Code from C**
```c
#if 0
# Python code here - C preprocessor ignores everything in this block
print("Hello from Python")
#endif
```

**Pattern 2: Using Triple-Quoted Strings to Hide C Code from Python**
```python
"""
// C code here - Python sees this as a multi-line string
int main() { return 0; }
"""
```

**Pattern 3: Combining Both Patterns**
The key insight is that `#if 0` and `"""` can work together:
- C sees: `#if 0` ... (ignored) ... `#endif` ... (C code) ... `#if 0` ... (ignored) ... `#endif`
- Python sees: `"""` (start string) ... (string content) ... `"""` (end string) ... Python code ... `"""` (start string) ... `"""` (end string)

## Implementation Approach

### Step 1: Understand the Requirements

Before writing any code:
- Identify what output each language version must produce
- Determine if the implementations need to share logic or can be independent
- Note any constraints on compilation flags or Python version

### Step 2: Design the File Structure

Plan the polyglot structure on paper first:

```
[Section hidden from C, visible to Python as string start]
[C code section]
[Section hidden from C, visible to Python as string end]
[Python code section]
[Section hidden from C, visible to Python as string (cleanup)]
```

### Step 3: Implement Incrementally

1. Write a minimal skeleton that compiles in C and runs in Python (even if it does nothing)
2. Add C functionality and verify compilation
3. Add Python functionality and verify execution
4. Test both together after each change

### Step 4: Handle the `"""` Delimiter Problem

The `"""` characters cause issues because:
- C sees them as a string literal that may not be properly terminated
- This generates warnings like "missing terminating `"` character"

**Solutions to avoid warnings:**

Option A: Place `"""` inside comments that both languages ignore:
```c
#if 0
"""
#endif
```

Option B: Use `//"""` so C sees it as a comment:
```c
//"""
```

Option C: Structure code so `"""` appears only within `#if 0` blocks

## Verification Strategy

### Mandatory Verification Steps

1. **Read the file after every edit** - Always verify the file content matches expectations using `cat` or the Read tool

2. **Compile without warnings** - Use `gcc -Wall -Wextra` and address all warnings:
   ```bash
   gcc -Wall -Wextra -o program file.py.c
   ```

3. **Test Python execution** - Verify Python runs without syntax errors:
   ```bash
   python3 file.py.c
   ```

4. **Compare outputs** - Test with multiple inputs and verify both versions produce identical/correct results:
   ```bash
   for i in 0 1 5 10 20; do
     echo "Input: $i"
     echo "C output: $(./program $i)"
     echo "Python output: $(python3 file.py.c $i)"
   done
   ```

### Test Cases to Include

- Edge cases (zero, negative numbers, empty input)
- Boundary conditions specific to the algorithm
- At least 5-6 representative inputs across the expected range

## Common Pitfalls

### Pitfall 1: Ignoring Compiler Warnings

**Problem:** The C compiler generates warnings about unterminated strings or other issues, but the code appears to work.

**Why it matters:** Warnings indicate the solution is fragile. With `-Werror` or in stricter environments, the build fails.

**Prevention:** Treat warnings as errors. Restructure the polyglot to eliminate all warnings before proceeding.

### Pitfall 2: Relying on Runtime Exit to Avoid Parse Errors

**Problem:** Attempting to use `sys.exit(0)` or similar to prevent Python from reaching unparseable code.

**Why it matters:** Python parses the entire file before executing anything. Parse errors occur regardless of runtime control flow.

**Prevention:** All code in the file must be syntactically valid Python. Hide invalid syntax inside strings.

### Pitfall 3: Not Verifying File State After Edits

**Problem:** Making edits and assuming they applied correctly without reading the file.

**Why it matters:** Edit operations can fail silently, be truncated, or apply incorrectly. The file state may not match expectations.

**Prevention:** Always read the complete file after any edit operation to confirm the content is correct.

### Pitfall 4: Testing Only One Language at a Time

**Problem:** Making changes and testing only C or only Python, not both.

**Why it matters:** Changes that fix one language often break the other. Both must be tested after every modification.

**Prevention:** Create a single test script that exercises both languages and run it after every change.

### Pitfall 5: Incomplete Edge Case Testing

**Problem:** Testing only "happy path" inputs like small positive integers.

**Why it matters:** Edge cases (negative numbers, zero, large values, no arguments) often reveal implementation differences or bugs.

**Prevention:** Include edge cases in the test suite from the start.

## References

See `references/polyglot_patterns.md` for additional polyglot structure examples and troubleshooting guidance.
