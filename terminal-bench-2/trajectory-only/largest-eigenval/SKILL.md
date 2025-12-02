---
name: largest-eigenval
description: Guidance for finding the largest eigenvalue of small dense matrices with performance optimization. This skill should be used when tasks involve computing eigenvalues (especially the dominant/largest eigenvalue), optimizing numerical linear algebra routines, or improving performance of numpy/scipy matrix operations for small matrices (typically 2-10 in size).
---

# Largest Eigenvalue Computation

## Overview

This skill provides guidance for efficiently computing the largest eigenvalue of small dense matrices. The core challenge is that standard approaches (numpy, scipy) are already highly optimized for the underlying computation, so performance gains come from reducing Python wrapper overhead rather than algorithmic improvements.

## Problem Analysis Framework

Before implementing any solution, analyze the problem characteristics:

### Matrix Size Classification

| Size | Recommended Approach |
|------|---------------------|
| Small (2-10) | Reduce wrapper overhead via Cython/direct LAPACK calls |
| Medium (10-1000) | Standard numpy.linalg.eig is optimal |
| Large (1000+) | Iterative methods (scipy.sparse.linalg.eigs, power iteration) |

### Eigenvalue Characteristics to Consider

1. **Real vs Complex**: Check if the matrix is symmetric (real eigenvalues) or general (potentially complex eigenvalues)
2. **Dominant eigenvalue**: Determine if there's a clearly dominant eigenvalue or near-degenerate cases
3. **Matrix structure**: Exploit any special structure (symmetric, positive definite, sparse)

## Decision Tree for Optimization Strategy

```
START: Need to optimize eigenvalue computation
  │
  ├─ Is the matrix size small (N ≤ 10)?
  │   │
  │   ├─ YES → Focus on reducing Python wrapper overhead
  │   │         ├─ Option 1: Cython with direct LAPACK calls (recommended)
  │   │         └─ Option 2: Numba JIT (may add overhead for small matrices)
  │   │
  │   └─ NO → Is the matrix sparse?
  │           │
  │           ├─ YES → Use scipy.sparse.linalg.eigs
  │           └─ NO → Is N > 1000?
  │                   ├─ YES → Consider iterative methods
  │                   └─ NO → numpy.linalg.eig is likely optimal
  │
  └─ Can eigenvalues be complex?
      │
      ├─ YES → Avoid power iteration (fails for complex dominant eigenvalues)
      └─ NO (symmetric matrix) → Power iteration may work, but overhead concerns remain
```

## Common Pitfalls to Avoid

### Pitfall 1: Using Iterative Methods for Small Matrices

**Mistake**: Trying scipy.sparse.linalg.eigs or power iteration for small dense matrices.

**Why it fails**:
- scipy.sparse.linalg.eigs has minimum size requirements (k < N-1)
- Iterative methods have startup overhead that dominates for small matrices
- Power iteration fails for complex dominant eigenvalues

**Better approach**: For small matrices, the computation is already fast; optimize the wrapper overhead instead.

### Pitfall 2: Numba JIT Overhead

**Mistake**: Assuming Numba JIT will speed up small matrix operations.

**Why it fails**:
- JIT compilation has startup overhead
- For small matrices, the Python wrapper overhead is the bottleneck
- Numba cannot optimize LAPACK calls that numpy already uses

**Better approach**: Use Cython with direct LAPACK bindings to bypass Python entirely.

### Pitfall 3: Power Iteration with Complex Eigenvalues

**Mistake**: Using power iteration when the dominant eigenvalue may be complex.

**Why it fails**:
- Power iteration converges to the real dominant eigenvalue
- For rotation matrices or skew-symmetric matrices, dominant eigenvalues are often complex
- The method will either fail to converge or give incorrect results

**Better approach**: Always use full eigendecomposition methods that handle complex eigenvalues (numpy.linalg.eig or direct LAPACK dgeev).

### Pitfall 4: Not Profiling First

**Mistake**: Attempting algorithmic optimizations without understanding where time is spent.

**Why it fails**:
- For small matrices, numpy's LAPACK calls are microseconds
- The overhead is in Python wrapper layers, not the algorithm
- Changing the algorithm doesn't address the actual bottleneck

**Better approach**: Profile the code first to identify if the bottleneck is computation or wrapper overhead.

## Recommended Implementation Strategy

### For Small Dense Matrices (Primary Use Case)

1. **Profile the baseline**: Measure numpy.linalg.eig performance to establish baseline
2. **Implement Cython wrapper**: Create a direct LAPACK interface using scipy.linalg.cython_lapack
3. **Handle complex eigenvalues**: LAPACK's dgeev returns real and imaginary parts separately; reconstruct complex eigenvalues correctly
4. **Add fallback**: Include fallback to numpy when Cython module unavailable

### Cython Implementation Checklist

When implementing Cython LAPACK bindings:

- [ ] Import from scipy.linalg.cython_lapack (e.g., dgeev for general real matrices)
- [ ] Allocate work arrays with proper sizes (query optimal work size first)
- [ ] Handle LAPACK's separate real/imaginary eigenvalue arrays
- [ ] Reconstruct complex eigenvalues: `eigenvalues = wr + 1j * wi`
- [ ] Find largest by magnitude: `np.argmax(np.abs(eigenvalues))`
- [ ] Return both eigenvalue and corresponding eigenvector
- [ ] Include error handling for LAPACK info codes

### Build and Test Verification

- [ ] Compile Cython extension: `python setup.py build_ext --inplace`
- [ ] Verify import succeeds: `from eigen_fast import largest_eigen_fast`
- [ ] Test eigenvalue equation: `A @ eigenvec ≈ eigenval * eigenvec`
- [ ] Test with rotation matrices (complex eigenvalues)
- [ ] Test with skew-symmetric matrices (purely imaginary eigenvalues)
- [ ] Test fallback path works when Cython unavailable

## Verification Strategies

### Mathematical Verification

Verify the eigenvalue equation holds:
```python
residual = np.linalg.norm(A @ eigenvec - eigenval * eigenvec)
assert residual < 1e-10 * np.linalg.norm(A)
```

### Edge Case Testing

Test these specific matrix types:
1. **Rotation matrices**: Have complex eigenvalues on the unit circle
2. **Skew-symmetric matrices**: Have purely imaginary eigenvalues
3. **Identity matrix**: All eigenvalues equal (degenerate case)
4. **Matrices with repeated eigenvalues**: Test numerical stability
5. **Ill-conditioned matrices**: Test with high condition numbers

### Performance Verification

- Compare against numpy.linalg.eig baseline
- Run multiple trials to account for variance
- Test across the expected range of matrix sizes

## File Verification Best Practices

After writing any implementation files:

1. **Read back written files**: Verify content was written completely (no truncation)
2. **Test compilation**: Ensure Cython files compile without errors
3. **Test imports**: Verify the compiled module can be imported
4. **Test fallback**: Verify numpy fallback works when Cython unavailable
