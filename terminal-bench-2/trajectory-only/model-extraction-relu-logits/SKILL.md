---
name: model-extraction-relu-logits
description: Guidance for extracting weight matrices from black-box ReLU neural networks using only input-output queries. This skill applies when tasks involve model extraction attacks, recovering hidden layer weights from neural networks, or reverse-engineering ReLU network parameters from query access.
---

# Model Extraction for ReLU Networks

## Overview

This skill provides guidance for extracting the weight matrix A1 from a two-layer ReLU network of the form `f(x) = A2 @ ReLU(A1 @ x)`, given only black-box query access (input-output pairs). The goal is typically to recover A1 "up to permutation and scaling"—meaning each row of the true A1 should have exactly one corresponding row in the extracted matrix.

## Critical Conceptual Foundation

### Understanding the Problem Structure

A two-layer ReLU network `f(x) = A2 @ ReLU(A1 @ x)` has specific geometric properties:

1. **Piecewise Linear Structure**: ReLU networks divide input space into regions where the function is linear
2. **Critical Hyperplanes**: The boundaries between regions are defined by hyperplanes `A1[i] @ x = 0` for each row i of A1
3. **Activation Patterns**: Within each region, a subset of neurons is "active" (positive pre-activation)

### Why Naive Fitting Fails

Training a new network to match input-output behavior does NOT guarantee recovery of A1:
- Multiple weight configurations can produce identical input-output mappings
- The optimization landscape has many equivalent minima
- Gradient descent may converge to a different (but functionally equivalent) solution

## Recommended Approaches

### Approach 1: Critical Point Detection (Preferred)

Exploit the piecewise linear structure to find hyperplane boundaries:

1. **Find Critical Points**: Locate inputs where neuron activations change (where `A1[i] @ x = 0` for some i)
2. **Compute Hyperplane Normals**: At critical points, compute gradients from both sides to identify the normal vector (row of A1)
3. **Iterate**: Repeat to recover all rows of A1

To find critical points:
- Sample random directions and binary search for activation changes
- Look for discontinuities in the gradient as a function of input

### Approach 2: Second-Order Information

Use Hessian information at carefully chosen points:

1. **Compute Hessians**: At points where multiple neurons are active, the Hessian contains information about A1
2. **Extract Rows**: The rank and structure of the Hessian reveal neuron directions
3. **Reconstruct A1**: Combine information from multiple points

### Approach 3: Gradient-Based with ICA (If Other Methods Fail)

Gradients at a point are linear combinations of active A1 rows:

1. **Collect Gradients**: Sample many gradients at random inputs
2. **Apply ICA**: Use Independent Component Analysis to separate mixed signals
3. **Verify Separation**: Ensure recovered components correspond to actual A1 rows

## Verification Strategy

Proper verification is essential. A misleading metric can cause false confidence.

### Correct Verification Criteria

1. **Unique Matching**: Each row of the extracted A1 must match EXACTLY ONE row of the true A1 (up to scaling)
2. **Complete Recovery**: ALL rows of the true A1 must be matched (no missing neurons)
3. **One-to-One Correspondence**: No two extracted rows should match the same true row

### Verification Implementation

```python
def verify_extraction(extracted_A1, true_A1, threshold=0.99):
    """
    Verify that extracted_A1 recovers true_A1 up to permutation and scaling.

    Returns:
        success: bool - True only if all rows uniquely matched
        matching: dict - Maps extracted row indices to true row indices
    """
    n_extracted = extracted_A1.shape[0]
    n_true = true_A1.shape[0]

    # Normalize rows for cosine similarity
    extracted_norm = extracted_A1 / np.linalg.norm(extracted_A1, axis=1, keepdims=True)
    true_norm = true_A1 / np.linalg.norm(true_A1, axis=1, keepdims=True)

    # Compute similarity matrix (handle sign ambiguity)
    similarity = np.abs(extracted_norm @ true_norm.T)

    # Find unique matches using Hungarian algorithm or greedy matching
    matched_true = set()
    matching = {}

    for i in range(n_extracted):
        best_j = np.argmax(similarity[i])
        if similarity[i, best_j] >= threshold:
            if best_j not in matched_true:
                matching[i] = best_j
                matched_true.add(best_j)

    # Success requires ALL true rows matched exactly once
    success = len(matched_true) == n_true

    return success, matching, len(matched_true)
```

### Red Flags in Verification

- Multiple extracted rows matching the same true row (incomplete extraction)
- High average similarity but low unique match count
- Missing neurons that never activate in the training distribution

## Common Pitfalls

### 1. Using Black-Box Information Incorrectly

**Mistake**: Reading source code to determine hidden layer dimensions.

**Correct Approach**: Estimate hidden dimension through probing:
- Vary input dimension and observe output rank
- Use gradient rank to estimate number of active neurons
- Probe at multiple points to account for dead neurons

### 2. Misleading Success Metrics

**Mistake**: Accepting high "average similarity" as success.

**Correct Approach**: Verify ALL of:
- Number of unique matches equals true hidden dimension
- One-to-one correspondence between extracted and true rows
- No duplicate matches

### 3. Ignoring Non-Uniqueness

**Mistake**: Assuming training a network will recover the original weights.

**Correct Approach**: Use geometric methods that exploit ReLU structure rather than functional fitting.

### 4. Missing Dead Neurons

**Mistake**: Not detecting neurons that never activate for the sample distribution.

**Correct Approach**:
- Sample from a wide distribution covering the input space
- Explicitly search for critical hyperplanes in unexplored regions
- Use theoretical bounds on the number of neurons

### 5. Numerical Precision Issues

**Mistake**: Using finite differences without considering numerical stability.

**Correct Approach**:
- Use appropriate step sizes for gradient estimation (typically 1e-5 to 1e-7)
- Average multiple gradient estimates
- Consider using automatic differentiation if available

## Workflow Decision Tree

```
START: Model Extraction Task
│
├─ Can you query gradients directly?
│   ├─ YES → Use Gradient-Based approaches
│   │         Consider ICA for separating mixed signals
│   └─ NO  → Use finite difference approximation
│            (requires more queries, less accurate)
│
├─ Do you know the hidden layer dimension?
│   ├─ YES → Verify through probing anyway
│   └─ NO  → Estimate via gradient rank analysis
│
├─ Choose primary extraction method:
│   ├─ Critical Point Detection (most reliable)
│   ├─ Second-Order (Hessian) Methods
│   └─ Gradient Collection + ICA (fallback)
│
└─ Verify extraction:
    ├─ Check unique match count = hidden dimension
    ├─ Confirm one-to-one correspondence
    └─ Test on held-out queries
```

## Resources

### references/

Consult `references/relu_extraction_theory.md` for detailed mathematical background on:
- Piecewise linear structure of ReLU networks
- Critical hyperplane detection algorithms
- ICA-based gradient separation techniques
