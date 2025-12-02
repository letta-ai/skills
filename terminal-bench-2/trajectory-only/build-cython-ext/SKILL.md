---
name: build-cython-ext
description: Guidance for building and installing Cython extension packages, particularly when resolving compatibility issues with modern Python and NumPy versions. This skill applies when installing legacy Cython packages, fixing NumPy 2.0 deprecation errors, resolving Python 3.x compatibility issues in extension modules, or troubleshooting Cython compilation failures. Use this skill for tasks involving setup.py with Cython extensions, deprecated NumPy type errors, or installing packages to system Python environments.
---

# Building Cython Extension Packages

This skill provides systematic approaches for building Cython extension packages, with emphasis on resolving compatibility issues that arise with modern Python and NumPy versions.

## When to Use This Skill

- Installing legacy Cython packages that have not been updated for NumPy 2.0 or Python 3.x
- Encountering compilation errors related to deprecated NumPy types
- Building packages with `.pyx` Cython source files
- Installing extension packages to system or global Python environments
- Troubleshooting `setup.py` build failures for Cython projects

## Recommended Approach

### Phase 1: Pre-Build Analysis (Before Attempting to Build)

Conduct a comprehensive inventory of potential compatibility issues BEFORE attempting to build. This proactive approach prevents the inefficient cycle of build-fail-fix-rebuild.

**1. Identify All Deprecated NumPy Types**

Search for ALL known NumPy 2.0 deprecated type aliases simultaneously:

```bash
# Search in both Python (.py) and Cython (.pyx) files
grep -rn "np\.float[^0-9]" --include="*.py" --include="*.pyx" .
grep -rn "np\.int[^0-9]" --include="*.py" --include="*.pyx" .
grep -rn "np\.complex[^0-9]" --include="*.py" --include="*.pyx" .
grep -rn "np\.bool[^0-9]" --include="*.py" --include="*.pyx" .
grep -rn "np\.object[^0-9]" --include="*.py" --include="*.pyx" .
grep -rn "np\.str[^0-9]" --include="*.py" --include="*.pyx" .
```

**2. Check for Python 3.x Compatibility Issues**

```bash
# Common Python 2/3 compatibility issues
grep -rn "from fractions import gcd" --include="*.py" .
grep -rn "print " --include="*.py" .  # Python 2 print statements
grep -rn "xrange" --include="*.py" .
grep -rn "\.iteritems\|\.itervalues\|\.iterkeys" --include="*.py" .
```

**3. Examine Cython Files Specifically**

Cython `.pyx` files may contain C-level type declarations that need updating:

```bash
# Look for cdef declarations with deprecated types
grep -rn "cdef.*np\." --include="*.pyx" .
```

### Phase 2: Systematic Fixes

Apply fixes comprehensively before building, not reactively after each error.

**NumPy Type Replacements:**

| Deprecated | Replacement |
|------------|-------------|
| `np.float` | `np.float64` or `float` |
| `np.int` | `np.int64` or `int` |
| `np.complex` | `np.complex128` or `complex` |
| `np.bool` | `np.bool_` or `bool` |
| `np.object` | `np.object_` or `object` |
| `np.str` | `np.str_` or `str` |

**Type Checking Considerations:**

When replacing `isinstance()` checks, consider all relevant subtypes:

```python
# Instead of: isinstance(x, np.complex)
# Use: isinstance(x, (np.complexfloating, complex))
# This covers complex64, complex128, and Python's built-in complex
```

**Python 3.x Fixes:**

```python
# gcd import
# Old: from fractions import gcd
# New: from math import gcd
```

### Phase 3: Build and Install

**Installation Types:**

Understand the difference between installation methods:

- `pip install .` - Proper installation, copies package to site-packages
- `pip install -e .` - Editable/development install, links to source directory

When the task specifies "install to system/global Python environment," use `pip install .` (without `-e`).

**Clean Build Process:**

```bash
# Clean any previous build artifacts
python setup.py clean --all
rm -rf build/ dist/ *.egg-info/

# Build and install
pip install .
```

### Phase 4: Verification

**1. Verify Installation Location**

```bash
pip show <package-name>
python -c "import <package>; print(<package>.__file__)"
```

**2. Test All Extension Modules**

Run tests that specifically exercise Cython-compiled code paths:

```bash
# Run the test suite
python -m pytest tests/

# If specific test files exist for extensions, run those
python -m pytest tests/test_*.py -v
```

**3. Import Verification**

```python
# Verify each compiled extension can be imported
import <package>.<cython_module>
```

**4. Clean Rebuild Verification**

After all fixes, perform a clean rebuild to ensure no stale artifacts:

```bash
pip uninstall <package> -y
rm -rf build/
pip install .
```

## Common Pitfalls

1. **Reactive vs. Proactive Fixing**: Do not fix errors one-by-one as they appear. Search comprehensively first.

2. **Ignoring Cython Files**: The `.pyx` source files often contain the same deprecated types as `.py` files. Always check both.

3. **Incomplete Type Coverage**: When fixing `isinstance()` checks for complex numbers, account for all NumPy complex types (`complex64`, `complex128`) not just `complex128`.

4. **Editable Install When Global Is Required**: Using `pip install -e .` when the task requires a proper global installation leaves the package tied to the source directory.

5. **Stale Build Artifacts**: Failing to clean build directories before rebuilding can cause compiled extensions to use old code.

6. **Missing Extension Tests**: Verifying only Python code tests while leaving Cython extension tests unrun.

## Reference Materials

For a comprehensive list of NumPy 2.0 migration changes, see `references/numpy2_migration.md`.
