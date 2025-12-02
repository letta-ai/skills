# NumPy 2.0 Migration Reference

This reference provides detailed information about deprecated types and breaking changes in NumPy 2.0 relevant to Cython extension builds.

## Deprecated Type Aliases

NumPy 2.0 removed several type aliases that were deprecated since NumPy 1.20. These aliases previously mapped to Python built-in types but caused confusion and inconsistency.

### Removed Aliases and Their Replacements

| Removed Alias | Python Built-in Equivalent | NumPy Equivalent |
|---------------|---------------------------|------------------|
| `np.bool` | `bool` | `np.bool_` |
| `np.int` | `int` | `np.int_` or `np.intp` |
| `np.float` | `float` | `np.float64` |
| `np.complex` | `complex` | `np.complex128` |
| `np.object` | `object` | `np.object_` |
| `np.str` | `str` | `np.str_` |

### Choosing the Right Replacement

**For Array dtype Specifications:**

```python
# Old (deprecated)
arr = np.array([1.0, 2.0], dtype=np.float)

# New - use explicit bit-width types
arr = np.array([1.0, 2.0], dtype=np.float64)
```

**For Type Checking with isinstance():**

```python
# Old (deprecated)
if isinstance(x, np.float):
    ...

# New - check for NumPy floating types
if isinstance(x, np.floating):  # Catches float16, float32, float64, etc.
    ...

# Or for specific precision
if isinstance(x, np.float64):
    ...

# Or if Python float is also acceptable
if isinstance(x, (np.floating, float)):
    ...
```

**For Complex Number Type Checking:**

```python
# Old (deprecated)
if isinstance(x, np.complex):
    ...

# New - comprehensive approach
if isinstance(x, (np.complexfloating, complex)):
    # Catches complex64, complex128, and Python's built-in complex
    ...
```

### Search Patterns for Finding Deprecated Usage

Use these grep patterns to find deprecated usage (the `[^0-9]` ensures you don't match `float64`, `int32`, etc.):

```bash
# Find np.float (but not np.float64, np.float32, etc.)
grep -E "np\.float[^0-9_]|np\.float$" --include="*.py" --include="*.pyx" -r .

# Find np.int (but not np.int64, np.int32, etc.)
grep -E "np\.int[^0-9_]|np\.int$" --include="*.py" --include="*.pyx" -r .

# Find np.complex (but not np.complex128, etc.)
grep -E "np\.complex[^0-9_]|np\.complex$" --include="*.py" --include="*.pyx" -r .

# Find np.bool (but not np.bool_)
grep -E "np\.bool[^_]|np\.bool$" --include="*.py" --include="*.pyx" -r .

# Find np.object (but not np.object_)
grep -E "np\.object[^_]|np\.object$" --include="*.py" --include="*.pyx" -r .

# Find np.str (but not np.str_)
grep -E "np\.str[^_]|np\.str$" --include="*.py" --include="*.pyx" -r .
```

## Cython-Specific Considerations

### Type Declarations in .pyx Files

Cython files may use NumPy types in `cdef` declarations:

```cython
# Old (deprecated)
cdef np.float x = 1.0

# New
cdef np.float64_t x = 1.0
```

### Cython dtype Objects

When using NumPy dtypes in Cython for typed memoryviews or ndarray declarations:

```cython
# Old (deprecated)
cdef np.ndarray[np.float_t, ndim=2] arr

# New - using explicit types
cdef np.ndarray[np.float64_t, ndim=2] arr
```

### Import Statements in Cython

Ensure proper cimport statements:

```cython
cimport numpy as np
import numpy as np

# For typed memoryviews
from numpy cimport float64_t, int64_t, complex128_t
```

## Python 3.x Compatibility Issues

These issues often accompany NumPy deprecation issues in legacy packages:

### gcd Function

```python
# Python 2 / early Python 3 (deprecated location)
from fractions import gcd

# Python 3.5+
from math import gcd
```

### Print Function

```python
# Python 2 (syntax error in Python 3)
print "hello"

# Python 3
print("hello")
```

### Dictionary Methods

```python
# Python 2 (removed in Python 3)
for k, v in d.iteritems():
    ...

# Python 3
for k, v in d.items():
    ...
```

### Integer Division

```python
# Python 2 behavior (integer division)
5 / 2  # Returns 2

# Python 3 behavior (true division)
5 / 2  # Returns 2.5
5 // 2  # Returns 2 (explicit integer division)
```

## Error Messages Reference

Common error messages and their causes:

### AttributeError for Deprecated Types

```
AttributeError: module 'numpy' has no attribute 'float'
```

**Cause**: Using `np.float`, `np.int`, `np.complex`, etc. with NumPy 2.0+

**Solution**: Replace with explicit types (`np.float64`, `np.int64`, etc.)

### ImportError for gcd

```
ImportError: cannot import name 'gcd' from 'fractions'
```

**Cause**: Python 3.9+ removed `gcd` from `fractions` module

**Solution**: Import from `math` instead: `from math import gcd`

### Compilation Errors in Cython

```
Error compiling Cython file:
...
cdef np.float x
         ^
'float' is not a type identifier
```

**Cause**: Using deprecated type alias in Cython type declaration

**Solution**: Use `np.float64_t` or appropriate typed variant
