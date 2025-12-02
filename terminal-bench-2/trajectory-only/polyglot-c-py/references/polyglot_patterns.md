# Polyglot Patterns Reference

## Complete Working Template

Below is a minimal complete polyglot structure that compiles without warnings and runs in both C and Python:

```c
#if 0
"""
#endif

#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("Hello from C\n");
    return 0;
}

#if 0
"""
print("Hello from Python")
"""
#endif
```

### How It Works

**What C sees:**
1. `#if 0` - start ignoring
2. `"""` - ignored (inside #if 0)
3. `#endif` - stop ignoring
4. `#include <stdio.h>` and `main()` function - compiled normally
5. `#if 0` - start ignoring
6. Everything until `#endif` - ignored
7. `#endif` - stop ignoring

**What Python sees:**
1. `#if 0` - comment (starts with #)
2. `"""` - start of triple-quoted string
3. `#endif` through the C code through `#if 0` - all inside the string
4. `"""` - end of triple-quoted string
5. `print("Hello from Python")` - executed
6. `"""` - start of another triple-quoted string
7. `#endif` - inside the string (string ends at EOF or next `"""`)

## Alternative Structures

### Structure A: Comment-Based Hiding

Uses `//` comments to hide `"""` from C:

```c
//"""
#include <stdio.h>
int main() { printf("C\n"); return 0; }
//"""
print("Python")
//"""
//"""
```

**Pros:** Simple, no preprocessor directives needed
**Cons:** Requires careful placement of `//` on every `"""` line

### Structure B: Nested Preprocessor Blocks

Uses multiple `#if 0` blocks:

```c
#if 0
"""
#endif
/* C code here */
#if 0
"""
#endif
# Python code here
#if 0
"""
#endif
```

**Pros:** Very explicit about what each language sees
**Cons:** More verbose

### Structure C: Using `#define` Tricks

```c
#define python_string_start "
#define python_string_end "

python_string_start"""
// C code here
int main() { return 0; }
"""python_string_end

print("Python")
```

**Note:** This is more complex and less reliable. Prefer simpler patterns.

## Troubleshooting Guide

### Problem: `warning: missing terminating " character`

**Cause:** The C compiler sees `"""` as three quote characters - an empty string `""` followed by an unterminated `"`.

**Solutions:**
1. Place `"""` inside `#if 0` blocks so the preprocessor removes it
2. Prefix with `//` to make it a comment: `//"""`
3. Use a different pattern that avoids `"""` in C-visible sections

### Problem: `SyntaxError: invalid syntax` in Python

**Cause:** Python is trying to parse C code that isn't hidden in a string.

**Solutions:**
1. Ensure all C code is inside a triple-quoted string
2. Check that `"""` delimiters are properly matched
3. Verify no C syntax exists outside string literals

### Problem: Code Compiles/Runs but Produces Wrong Output

**Debugging steps:**
1. Add debug prints to identify which code path executes
2. Check argument parsing in both languages
3. Verify algorithm implementation matches in both versions

### Problem: Works Locally but Fails in CI/Test Environment

**Common causes:**
1. Different compiler flags (CI may use `-Werror`)
2. Different Python version
3. Different argument handling

**Prevention:** Test with strict flags locally: `gcc -Wall -Wextra -Werror`

## Testing Checklist

Before considering a polyglot complete:

- [ ] Compiles with `gcc -Wall -Wextra -Werror` (no warnings)
- [ ] Runs with `python3` without syntax errors
- [ ] Produces correct output for all test inputs in C
- [ ] Produces correct output for all test inputs in Python
- [ ] Both versions produce identical output for same inputs
- [ ] Edge cases tested (0, negative, large values, no args)
- [ ] File content verified after final edit

## Argument Handling Comparison

### C Argument Parsing
```c
int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <number>\n", argv[0]);
        return 1;
    }
    int n = atoi(argv[1]);
    // use n
}
```

### Python Argument Parsing
```python
import sys
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <number>")
    sys.exit(1)
n = int(sys.argv[1])
# use n
```

## Common Algorithm: Fibonacci Example

A complete polyglot implementing Fibonacci:

```c
#if 0
"""
#endif

#include <stdio.h>
#include <stdlib.h>

long fib(int n) {
    if (n <= 1) return n;
    long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        long temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    int n = atoi(argv[1]);
    printf("%ld\n", fib(n));
    return 0;
}

#if 0
"""
import sys

def fib(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    n = int(sys.argv[1])
    print(fib(n))
"""
#endif
```
