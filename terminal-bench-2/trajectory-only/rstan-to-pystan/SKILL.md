---
name: rstan-to-pystan
description: This skill provides guidance for translating RStan (R-based Stan interface) code to PyStan (Python-based Stan interface). It should be used when converting Stan models from R to Python, migrating Bayesian inference workflows between languages, or adapting R data preparation logic to Python equivalents.
---

# RStan to PyStan Translation

## Overview

Translating RStan code to PyStan involves converting R data preparation, Stan model specification, and posterior sampling into equivalent Python code. Key challenges include API differences between RStan and PyStan 3, output format variations, and ensuring numerical stability across implementations.

## Translation Workflow

### Step 1: Read Complete Source Files

Before writing any code, ensure complete visibility of all source files.

**Critical Requirements:**
- Read the entire R script, not just the first portion. If output shows `[truncated]`, request remaining content
- Read the complete Stan model file (`.stan`) if separate from R script
- Read all data files to understand structure and column names

**Verification:**
- Confirm all hyperparameters are visible
- Confirm all data preparation logic is captured
- Confirm the full Stan model code block is obtained

### Step 2: Understand the Stan Model

Analyze the embedded or external Stan model:

- **Data block**: Identify all declared data variables, their types, and dimensions
- **Parameters block**: Note all parameters being estimated
- **Model block**: Understand the likelihood and prior specifications
- **Generated quantities**: Identify any derived quantities computed post-sampling

### Step 3: Map Data Preparation Logic

Translate R data preparation to Python equivalents:

| R Pattern | Python Equivalent |
|-----------|-------------------|
| `read.csv()` | `pd.read_csv()` |
| `cbind(1, x, y)` | `np.column_stack([np.ones(n), x, y])` |
| `matrix(data, nrow, ncol)` | `np.array(data).reshape(nrow, ncol)` |
| `dim(x)[1]` | `x.shape[0]` |
| `length(x)` | `len(x)` or `x.shape[0]` |
| `t(x)` | `x.T` |

### Step 4: Translate Sampling Parameters

Map RStan sampling parameters to PyStan 3:

| RStan Parameter | PyStan 3 Equivalent |
|-----------------|---------------------|
| `iter` | `num_samples + num_warmup` |
| `warmup` | `num_warmup` |
| `chains` | `num_chains` |
| `thin` | `save_warmup=False`, then thin manually |
| `seed` | `random_seed` |
| `control=list(adapt_delta=X)` | Configure via `stan.build()` arguments |

**Calculating equivalent samples:**
```
PyStan num_samples = (RStan iter - RStan warmup) / RStan thin
```

### Step 5: Handle PyStan 3 Output Format

**Critical API Difference:** PyStan 3 returns posterior samples in shape `(D, num_samples)`, not `(num_samples, D)`.

When extracting samples:
```python
# Correct approach for PyStan 3
samples = fit["parameter_name"]  # Shape: (D, num_samples)
mean_values = samples.mean(axis=1)  # Mean across samples
```

### Step 6: Construct Data Dictionary

PyStan requires data as a Python dictionary matching Stan data block declarations:

```python
data = {
    "N": int(n_observations),      # Use int() for scalars
    "D": int(n_dimensions),
    "X": X.tolist(),               # Convert numpy arrays to lists
    "y": y.tolist()
}
```

**Type considerations:**
- Stan expects integers for dimension declarations (use `int()`)
- Arrays can be passed as Python lists or numpy arrays
- Verify dimension ordering matches Stan's column-major convention

## Verification Strategies

### Before Coding

1. Confirm complete source file content (no truncation)
2. List all hyperparameters from R script
3. Document expected data shapes

### After Implementation

1. **Data shape validation**: Print shapes of all data arrays before passing to Stan
2. **Sample shape verification**: Print output shapes from `fit[param]` before processing
3. **Warning inspection**: Address any Stan warnings (divergences, Cholesky failures, etc.)
4. **Numerical sanity checks**: Verify posterior means are in reasonable ranges

### Debugging Output

Add comprehensive debugging in the first implementation:
```python
print(f"N = {N}, D = {D}")
print(f"X shape: {X.shape}")
print(f"y shape: {y.shape}")
# After sampling
for param in ["mu", "sigma", "beta"]:
    samples = fit[param]
    print(f"{param} shape: {samples.shape}, mean: {samples.mean()}")
```

## Common Pitfalls

### 1. Incomplete Source Reading

**Problem:** Proceeding with partial R script content leads to missing hyperparameters or model details.

**Prevention:** Always verify the complete file was read. Request continuation if truncated.

### 2. Output Shape Mismatch

**Problem:** Assuming PyStan returns `(num_samples, D)` when it actually returns `(D, num_samples)`.

**Prevention:** Print shapes immediately after extraction. Read PyStan 3 documentation before coding.

### 3. Ignoring Stan Warnings

**Problem:** Cholesky decomposition failures, divergent transitions, or low ESS indicate model issues.

**Prevention:** Treat warnings as potential errors. Investigate root cause before accepting results.

### 4. Matrix Construction Errors

**Problem:** R's `cbind(1, X[,1], X[,2])` creates design matrix differently than naive Python translation.

**Prevention:** Explicitly construct design matrices with `np.column_stack()` and verify shapes.

### 5. Inefficient Editing Cycles

**Problem:** Multiple failed edits due to string matching issues when patching files.

**Prevention:** Read current file state before editing. Use targeted, small edit strings. Consider rewriting entire sections.

## PyStan 3 Quick Reference

```python
import stan

# Compile model
model = stan.build(stan_code, data=data, random_seed=42)

# Sample
fit = model.sample(
    num_chains=4,
    num_samples=1000,
    num_warmup=1000,
    save_warmup=False
)

# Extract samples
samples = fit["parameter"]  # Shape: (D, num_samples) or (num_samples,) for scalars
df = fit.to_frame()         # All samples as DataFrame
```
