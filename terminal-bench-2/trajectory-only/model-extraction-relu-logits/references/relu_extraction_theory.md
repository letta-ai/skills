# ReLU Network Extraction: Mathematical Background

## Network Structure

Consider a two-layer ReLU network:

```
f(x) = A2 @ ReLU(A1 @ x)
```

Where:
- `x ∈ R^n` is the input
- `A1 ∈ R^{h×n}` is the first layer weight matrix (h hidden neurons)
- `A2 ∈ R^{m×h}` is the second layer weight matrix (m outputs)
- `ReLU(z) = max(0, z)` applied element-wise

## Piecewise Linear Structure

### Linear Regions

The ReLU function creates piecewise linear behavior. For any input x, define the activation pattern:

```
σ(x) = {i : A1[i] @ x > 0}
```

Within a region where σ(x) is constant, the network is linear:

```
f(x) = A2[:, σ(x)] @ A1[σ(x), :] @ x
```

### Critical Hyperplanes

The input space is partitioned by hyperplanes:

```
H_i = {x : A1[i] @ x = 0}
```

Each hyperplane H_i has normal vector A1[i] (the i-th row of A1).

**Key Insight**: Recovering the normal vectors to these hyperplanes recovers the rows of A1.

## Critical Point Detection Algorithm

### Finding Boundary Points

To find a point on hyperplane H_i:

1. **Start with two points** x₁, x₂ where neuron i has different activation states
2. **Binary search** along the line segment to find the transition point

```python
def find_critical_point(f, x1, x2, tol=1e-8):
    """Binary search for activation boundary between x1 and x2."""
    while np.linalg.norm(x2 - x1) > tol:
        mid = (x1 + x2) / 2
        # Check if gradient changes (indicates activation boundary)
        grad1 = estimate_gradient(f, x1)
        grad_mid = estimate_gradient(f, mid)

        if gradients_differ(grad1, grad_mid):
            x2 = mid
        else:
            x1 = mid

    return (x1 + x2) / 2
```

### Extracting Normal Vectors

At a critical point p on hyperplane H_i:

1. **Compute gradients from both sides**:
   - `g+ = lim_{ε→0+} ∇f(p + ε*d)` for some direction d
   - `g- = lim_{ε→0+} ∇f(p - ε*d)`

2. **The difference reveals the hyperplane normal**:
   - `g+ - g- = A2[:, i]^T * A1[i]` (up to sign)

3. **Normalize to get direction**:
   - The direction of A1[i] can be recovered from the gradient difference

```python
def extract_normal(f, critical_point, direction, eps=1e-6):
    """Extract hyperplane normal at critical point."""
    p_plus = critical_point + eps * direction
    p_minus = critical_point - eps * direction

    grad_plus = estimate_gradient(f, p_plus)
    grad_minus = estimate_gradient(f, p_minus)

    diff = grad_plus - grad_minus

    # diff is proportional to A2[:, i]^T @ A1[i]
    # For scalar output (m=1), diff is proportional to A1[i]
    return diff / np.linalg.norm(diff)
```

## ICA-Based Gradient Separation

### Theoretical Foundation

At a point x where neurons in set S are active:

```
∇f(x) = A2[:, S]^T @ A1[S, :]^T
```

If we collect gradients at many random points, we obtain mixtures of the rows of A1.

### ICA Formulation

Let G be a matrix where each row is a gradient at a random point:

```
G ≈ M @ A1
```

Where M encodes which neurons are active and their contribution via A2.

ICA attempts to find independent components, which correspond to individual rows of A1.

### Limitations

- ICA assumes statistical independence of sources (may not hold perfectly)
- Requires many samples to converge
- May not recover all rows if some neurons are rarely active together

```python
from sklearn.decomposition import FastICA

def extract_via_ica(f, n_samples, input_dim, hidden_dim):
    """Use ICA to extract A1 rows from gradient samples."""
    gradients = []

    for _ in range(n_samples):
        x = np.random.randn(input_dim)
        grad = estimate_gradient(f, x)
        gradients.append(grad)

    G = np.array(gradients)

    # Apply ICA
    ica = FastICA(n_components=hidden_dim, max_iter=1000)
    components = ica.fit_transform(G.T).T

    return components
```

## Estimating Hidden Dimension

When the hidden dimension h is unknown:

### Method 1: Gradient Rank Analysis

The rank of the gradient matrix reveals the number of distinct active neuron combinations:

```python
def estimate_hidden_dim(f, input_dim, n_samples=1000):
    """Estimate hidden dimension via gradient rank."""
    gradients = []

    for _ in range(n_samples):
        x = np.random.randn(input_dim) * 10  # Wide distribution
        grad = estimate_gradient(f, x)
        gradients.append(grad)

    G = np.array(gradients)
    _, s, _ = np.linalg.svd(G)

    # Count significant singular values
    threshold = s[0] * 1e-6
    hidden_dim = np.sum(s > threshold)

    return hidden_dim
```

### Method 2: Critical Point Counting

Count the number of distinct hyperplane normals found:

1. Run critical point detection multiple times
2. Cluster the resulting normals
3. The number of clusters estimates h

## Handling Edge Cases

### Dead Neurons

Neurons that never activate (A1[i] @ x <= 0 for all sampled x) cannot be detected.

**Mitigation**:
- Sample from a very wide distribution
- Probe systematically in different directions
- Use prior knowledge about expected hidden dimension

### Near-Parallel Hyperplanes

When two rows of A1 are nearly parallel, their hyperplanes are hard to distinguish.

**Mitigation**:
- Increase numerical precision
- Use multiple gradient samples near critical points
- Apply regularization in ICA

### Numerical Gradient Estimation

```python
def estimate_gradient(f, x, eps=1e-6):
    """Estimate gradient via central differences."""
    n = len(x)
    grad = np.zeros(n)

    for i in range(n):
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += eps
        x_minus[i] -= eps

        grad[i] = (f(x_plus) - f(x_minus)) / (2 * eps)

    return grad
```

**Step Size Selection**:
- Too large: Finite difference approximation error
- Too small: Floating-point precision issues
- Typical range: 1e-5 to 1e-7

## Complete Extraction Pipeline

```python
def extract_A1(f, input_dim, hidden_dim, n_iterations=100):
    """
    Complete pipeline to extract A1 from black-box ReLU network.

    Args:
        f: Function that computes network output
        input_dim: Dimension of input
        hidden_dim: Number of hidden neurons (estimate if unknown)
        n_iterations: Number of extraction attempts

    Returns:
        extracted_A1: Matrix of shape (hidden_dim, input_dim)
    """
    extracted_rows = []

    for _ in range(n_iterations * 10):  # Oversample
        # Generate random starting points
        x1 = np.random.randn(input_dim)
        x2 = np.random.randn(input_dim)

        # Find critical point
        try:
            critical = find_critical_point(f, x1, x2)

            # Extract normal
            direction = np.random.randn(input_dim)
            direction /= np.linalg.norm(direction)
            normal = extract_normal(f, critical, direction)

            extracted_rows.append(normal)
        except:
            continue

    # Cluster to find unique rows
    from sklearn.cluster import KMeans

    if len(extracted_rows) >= hidden_dim:
        extracted = np.array(extracted_rows)
        kmeans = KMeans(n_clusters=hidden_dim)
        kmeans.fit(extracted)
        return kmeans.cluster_centers_

    return np.array(extracted_rows)
```

## Verification Protocol

Always verify extraction with proper criteria:

```python
def comprehensive_verify(extracted_A1, true_A1):
    """
    Comprehensive verification of extraction quality.

    Returns detailed metrics beyond simple similarity.
    """
    from scipy.optimize import linear_sum_assignment

    # Normalize all rows
    ext_norm = extracted_A1 / np.linalg.norm(extracted_A1, axis=1, keepdims=True)
    true_norm = true_A1 / np.linalg.norm(true_A1, axis=1, keepdims=True)

    # Compute similarity matrix (absolute value for sign invariance)
    sim = np.abs(ext_norm @ true_norm.T)

    # Use Hungarian algorithm for optimal matching
    row_ind, col_ind = linear_sum_assignment(-sim)

    # Compute metrics
    matched_similarities = sim[row_ind, col_ind]
    unique_true_matched = len(set(col_ind))

    results = {
        'mean_similarity': np.mean(matched_similarities),
        'min_similarity': np.min(matched_similarities),
        'unique_matches': unique_true_matched,
        'total_true_rows': true_A1.shape[0],
        'complete_recovery': unique_true_matched == true_A1.shape[0],
        'all_high_quality': np.all(matched_similarities > 0.99)
    }

    return results
```
