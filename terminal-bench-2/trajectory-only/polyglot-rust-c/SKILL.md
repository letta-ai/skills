---
name: polyglot-rust-c
description: Guidance for creating polyglot source files that compile and run correctly as both Rust and C/C++ programs. This skill should be used when asked to create code that is valid in multiple programming languages simultaneously, particularly Rust and C/C++ polyglots.
---

# Polyglot Rust-C

## Overview

This skill provides guidance for creating polyglot source files—single files that compile and execute correctly as programs in multiple languages. The focus is on Rust and C/C++ polyglots, which leverage comment syntax differences and preprocessor directives to hide language-specific code from each compiler.

## Critical Approach: Iterative Implementation Over Analysis

The most important principle for polyglot tasks is to **implement and test iteratively** rather than analyze extensively. Polyglot construction is inherently experimental—theoretical reasoning about syntax interactions often fails to predict actual compiler behavior.

### Anti-Pattern to Avoid

Spending excessive time analyzing potential approaches without writing code leads to:
- Circular reasoning about syntax possibilities
- Repeated exploration of the same ideas without progress
- Analysis paralysis preventing any solution

### Required Approach

1. **Time-box exploration**: Limit initial analysis to understanding the basic polyglot mechanisms, then commit to an approach
2. **Write code immediately**: Create the directory structure and write an initial attempt within the first few minutes
3. **Compile with both compilers**: Test with actual compilers to get real error messages
4. **Iterate based on errors**: Use compiler feedback to refine the approach
5. **Track attempts**: Maintain awareness of what has been tried and why it failed

## Polyglot Mechanisms

### Comment Syntax Differences

The key to Rust/C++ polyglots is exploiting how each language handles comments:

| Syntax | Rust Interpretation | C/C++ Interpretation |
|--------|---------------------|----------------------|
| `//` | Line comment | Line comment |
| `/* */` | Block comment | Block comment |
| `/*/` | Start of block comment (needs closing) | End then start of comment |
| `//*/` | Line comment | End of block comment |

### Preprocessor Directives

C/C++ preprocessor directives are treated as comments or ignored by Rust:
- `#if 0` / `#endif` blocks are skipped by C preprocessor
- Rust sees `#` as an attribute marker or ignores it in certain contexts

### Common Polyglot Patterns

**Pattern 1: Comment Toggle**
```
//* Rust code here
C++ code here
// */
```

**Pattern 2: Preprocessor Hide**
```
#if 0
Rust-only code
#endif
C++ code
```

**Pattern 3: Backslash Line Continuation**
```
//\
This line is part of the comment in C++ but visible in Rust
```

## Implementation Workflow

### Step 1: Set Up Environment

Create the required directory structure and files immediately:
```bash
mkdir -p /path/to/polyglot
touch /path/to/polyglot/main.rs  # or appropriate filename
```

### Step 2: Write Minimal Skeleton

Start with the simplest possible structure that demonstrates the polyglot mechanism:
```
// Minimal test - does this compile in both?
fn main() {} // Rust
int main() { return 0; } // C++
```

### Step 3: Compile and Test

Run both compilers and collect error messages:
```bash
# For Rust
rustc main.rs -o rust_output

# For C++
g++ main.rs -o cpp_output  # or use appropriate extension handling
```

### Step 4: Iterate on Errors

Address one compiler's errors at a time:
1. Fix Rust compilation errors first (often stricter)
2. Verify C++ still compiles
3. Repeat until both compile

### Step 5: Add Actual Logic

Once the skeleton works, add the required functionality incrementally:
1. Add one function at a time
2. Test after each addition
3. Handle input/output as required

## Verification Strategy

### Compilation Verification

Both compilers must succeed without errors:
```bash
rustc main.rs -o rust_binary && echo "Rust: OK"
g++ main.rs -x c++ -o cpp_binary && echo "C++: OK"
```

### Output Verification

Both executables must produce identical output for the same input:
```bash
echo "10" | ./rust_binary > rust_output.txt
echo "10" | ./cpp_binary > cpp_output.txt
diff rust_output.txt cpp_output.txt && echo "Output matches"
```

### Edge Case Testing

Test boundary conditions:
- Zero and negative inputs (if applicable)
- Large values (integer overflow considerations)
- Invalid input handling

## Common Pitfalls

### 1. Overthinking Without Testing

**Problem**: Extensive theoretical analysis without writing code
**Solution**: Commit to an approach within 2-3 minutes and test it

### 2. Forgetting to Use Tools

**Problem**: Reasoning about syntax without actually compiling
**Solution**: Always create files and run compilers to verify hypotheses

### 3. Not Tracking Attempts

**Problem**: Trying the same approach multiple times without realizing it
**Solution**: Document what has been tried and the specific failure mode

### 4. Ignoring Compiler Error Messages

**Problem**: Continuing to reason abstractly when compiler output provides concrete guidance
**Solution**: Read error messages carefully—they indicate exactly what needs fixing

### 5. Overcomplicating the Structure

**Problem**: Building elaborate comment nesting when simpler patterns exist
**Solution**: Start with established polyglot patterns before inventing new ones

### 6. Function Definition Differences

**Problem**: Forgetting that Rust uses `fn` while C++ uses return types
**Solution**: Use comment blocks to hide each language's function definitions from the other

## Algorithm Considerations

When implementing algorithms in polyglots:

### Fibonacci Example

Be aware of definition variations:
- Common: f(0)=0, f(1)=1
- Alternative: f(0)=1, f(1)=1

Verify the expected definition before implementing.

### Integer Overflow

- Rust may panic on overflow in debug mode
- C++ has undefined behavior for signed overflow
- Consider using appropriate types and bounds checking

## Resources

Reference material for polyglot construction is available in the `references/` directory.

### references/

Contains documentation on polyglot patterns and language-specific syntax details that inform the construction process.
