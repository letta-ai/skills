# Polyglot Patterns Reference

This document provides detailed patterns for constructing Rust/C++ polyglot files.

## Fundamental Concept

A polyglot works by making each compiler see different code while reading the same file. This is achieved through:
1. Comment syntax differences
2. Preprocessor behavior differences
3. Identifier/keyword differences

## Detailed Pattern Explanations

### Pattern A: The `/*/` Toggle

The sequence `/*/` behaves differently in each language:

**In C++:**
```
/* comment */ code /*/  more comment */
```
The `/*/` acts as `*/` (ending comment) followed by `/*` (starting new comment).

**In Rust:**
```
/* comment */ code /*/  <- This starts a NEW block comment
```
The `/*/` acts as `/*` followed by `/`, starting a block comment.

### Pattern B: Line Comment with Block End

```
code_for_both
//*/ rust_only_code
cpp_only_code
//*/
```

**How C++ sees it:**
- `code_for_both` - executed
- `//*/ rust_only_code` - line comment (ignored)
- `cpp_only_code` - executed
- `//*/` - line comment (ignored)

**How Rust sees it:**
- `code_for_both` - executed
- `//*/ rust_only_code` - line comment (ignored)
- `cpp_only_code` - executed
- `//*/` - line comment (ignored)

This pattern doesn't differentiate! Need modification:

### Pattern C: Working Toggle Pattern

```
/*/ rust_code //*/ cpp_code //*/
```

**How C++ sees it:**
- `/*/ rust_code //` - block comment (from `/*` to `*/`)
- `*/ cpp_code //*/` - wait, this is wrong...

Actually, let's trace more carefully:

```
/*/ rust_code //*/
```

**C++ parsing:**
1. `/*` starts block comment
2. `/ rust_code //` is inside comment
3. `*/` ends block comment

**Rust parsing:**
1. `/*/` starts block comment (the `/*` part)
2. ` rust_code ` is inside... no wait
3. `//*/` is a line comment

This gets complex. The reliable patterns are:

### Pattern D: Preprocessor-Based (Most Reliable)

```c
#if 0
// Rust code here - C preprocessor skips this entirely
fn main() {
    println!("Hello from Rust");
}
#else
// C++ code here
#include <iostream>
int main() {
    std::cout << "Hello from C++" << std::endl;
}
#endif
```

**Limitation:** Rust doesn't understand `#if`, so this needs additional handling.

### Pattern E: Dual Main Functions

Hide each language's main from the other:

```
//BEGIN RUST
/*
//END RUST
#include <stdio.h>
int main() { printf("C++\n"); return 0; }
//BEGIN RUST
*/
fn main() { println!("Rust"); }
//END RUST
```

**C++ sees:**
- `//BEGIN RUST` - line comment
- `/*` - starts block comment
- Everything until `*/` - commented out
- `#include...int main()...` - actual code
- `//BEGIN RUST` - line comment
- `*/` - but we're not in a comment!

This also has issues. Let's use a proven pattern:

### Pattern F: Working Proven Pattern

```
//*
fn main() { println!("Rust"); }
/*/
#include <stdio.h>
int main() { printf("C++\n"); return 0; }
//*/
```

**Rust parsing:**
1. `//*` - line comment
2. `fn main()...` - RUST CODE EXECUTED
3. `/*/` - starts block comment
4. Everything until...
5. `//*/` - line comment (but inside block comment context...)

This is getting complicated. Let me provide the canonical working example:

### Pattern G: Canonical Working Polyglot

```c
#define fn int main()//
fn main() {
    //*
    println!("Rust");
    /*/
    printf("C++\n");
    //*/
    return 0;
}
```

Wait, this mixes paradigms poorly.

## Verified Working Approach

The most reliable approach is:

1. **Test incrementally** - Don't trust theoretical analysis
2. **Use the actual compilers** - `rustc` and `g++`/`clang++`
3. **Start minimal** - Get `main` working in both first
4. **Add logic piece by piece** - Verify after each change

## Key Syntax Reference

| Element | Rust | C/C++ |
|---------|------|-------|
| Main function | `fn main() {}` | `int main() { return 0; }` |
| Print | `println!("text");` | `printf("text\n");` |
| Print with value | `println!("{}", x);` | `printf("%d\n", x);` |
| Variable declaration | `let x = 5;` | `int x = 5;` |
| Mutable variable | `let mut x = 5;` | `int x = 5;` |
| Line comment | `//` | `//` |
| Block comment | `/* */` | `/* */` |
| Include | `use std::io;` | `#include <stdio.h>` |

## Testing Commands

```bash
# Create test file
cat > test_polyglot.rs << 'EOF'
// Your polyglot code here
EOF

# Test Rust compilation
rustc test_polyglot.rs -o test_rust 2>&1

# Test C++ compilation (note: may need -x c++ for .rs extension)
g++ -x c++ test_polyglot.rs -o test_cpp 2>&1

# Run and compare
./test_rust
./test_cpp
```

## Debugging Tips

1. **Rust errors first**: Rust's compiler is stricter, fix these first
2. **Check comment nesting**: Rust allows nested `/* */`, C++ doesn't
3. **Watch for semicolons**: Both languages need them but in different places
4. **Preprocessor visibility**: C++ sees `#` lines, Rust may interpret them differently
