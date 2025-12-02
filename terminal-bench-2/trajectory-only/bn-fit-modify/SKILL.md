---
name: bn-fit-modify
description: Guidance for Bayesian Network DAG structure recovery, parameter learning, and causal intervention tasks. This skill should be used when tasks involve recovering DAG structure from observational data, learning Bayesian Network parameters, performing causal interventions (do-calculus), or generating samples from modified networks. Applies to tasks mentioning Bayesian networks, DAG recovery, structure learning, causal inference, or interventional distributions.
---

# Bayesian Network DAG Recovery and Modification

## Overview

This skill provides guidance for tasks involving Bayesian Network structure learning, parameter estimation, and causal interventions. These tasks typically require recovering a Directed Acyclic Graph (DAG) from observational data, fitting parameters to the recovered structure, and generating samples under interventions.

## Critical Concepts

### DAG Recovery vs Correlation Analysis

**Correlation does not imply direct edges.** Two variables may be highly correlated because:
- They share a common ancestor (confounder)
- One causes the other through intermediate variables
- They are connected through a collider structure

Using correlation-based greedy approaches for DAG recovery is fundamentally flawed and will produce incorrect structures.

### Markov Equivalence Classes

Many DAGs encode the same conditional independence relationships and cannot be distinguished from observational data alone. When edge directionality is ambiguous, apply any task-specified rules (e.g., alphabetical ordering) consistently.

### Interventions vs Observations

An intervention (do-operator) differs from conditioning:
- **Observation**: P(Y | X=x) - what is Y when we observe X=x
- **Intervention**: P(Y | do(X=x)) - what is Y when we force X=x

Interventions remove all incoming edges to the intervened variable.

## Workflow for DAG Recovery Tasks

### Step 1: Data Exploration

Before structure learning, characterize the data:

1. Check variable types (continuous, discrete, mixed)
2. Examine data size and dimensionality
3. Identify potential issues (missing values, outliers)
4. Compute basic statistics for validation later

```python
import pandas as pd
import numpy as np

data = pd.read_csv('data.csv')
print(f"Shape: {data.shape}")
print(f"Types: {data.dtypes}")
print(f"Statistics:\n{data.describe()}")
```

### Step 2: Structure Learning Method Selection

Select an appropriate algorithm based on data characteristics:

**For Continuous Data:**
- PC algorithm with Fisher's Z test for conditional independence
- GES (Greedy Equivalence Search) with BIC scoring
- NOTEARS (differentiable structure learning)

**For Discrete Data:**
- PC algorithm with Chi-squared or G-test
- Hill-climbing with BDeu or K2 score

**For Mixed Data:**
- Conditional Gaussian tests
- Mixed-variable structure learning algorithms

### Step 3: Handle Memory and Computational Constraints

Structure learning algorithms can be memory-intensive. When encountering memory issues (exit code 137, OOM):

1. **Subsample the data** - Use 1000-5000 points for structure learning
2. **Reduce variable set** - Focus on core variables if possible
3. **Use efficient implementations** - Consider `causal-learn` or R's `bnlearn`

```python
# Subsample for structure learning
subsample = data.sample(n=min(2000, len(data)), random_state=42)
```

**Never fall back to correlation-based approaches** when proper methods fail. Instead, fix the computational issue.

### Step 4: Structure Learning Implementation

Use established libraries with proper conditional independence testing:

```python
# Option 1: pgmpy with constraint-based learning
from pgmpy.estimators import PC
from pgmpy.estimators import HillClimbSearch, BicScore

# For smaller datasets
pc = PC(data)
model = pc.estimate(variant='stable', max_cond_vars=4)

# Option 2: causal-learn library
from causallearn.search.ConstraintBased.PC import pc
from causallearn.utils.cit import fisherz

cg = pc(data.values, alpha=0.05, indep_test=fisherz)
```

### Step 5: Apply Ambiguity Resolution Rules

When edge directionality is ambiguous (within the same Markov equivalence class), apply task-specified rules systematically:

```python
def apply_alphabetical_rule(edges, rule="first_is_child"):
    """
    Apply alphabetical ordering rule for ambiguous edges.

    Args:
        edges: List of (parent, child) tuples
        rule: "first_is_child" means alphabetically first node is child
    """
    resolved = []
    for parent, child in edges:
        if rule == "first_is_child":
            # Alphabetically first should be child
            if parent < child:
                # parent comes first alphabetically, should be child
                resolved.append((child, parent))
            else:
                resolved.append((parent, child))
    return resolved
```

### Step 6: Validate Recovered Structure

**Always validate the DAG before proceeding:**

1. **Verify acyclicity** - The graph must be a DAG
2. **Check connectivity** - Ensure expected relationships exist
3. **Compare implied independencies** - Test against data

```python
import networkx as nx

G = nx.DiGraph(edges)

# Verify DAG
assert nx.is_directed_acyclic_graph(G), "Graph contains cycles!"

# Print structure for verification
print("Recovered DAG edges:")
for edge in G.edges():
    print(f"  {edge[0]} -> {edge[1]}")
```

### Step 7: Parameter Learning

Fit parameters appropriate to the data type:

**Continuous Data (Linear Gaussian):**
```python
from pgmpy.models import LinearGaussianBayesianNetwork

lg_model = LinearGaussianBayesianNetwork(edges)
lg_model.fit(data)

# Verify parameters produce reasonable samples
samples = lg_model.simulate(1000)
print("Original stats:", data.describe())
print("Sampled stats:", samples.describe())
```

**Discrete Data:**
```python
from pgmpy.models import BayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator

model = BayesianNetwork(edges)
model.fit(data, estimator=MaximumLikelihoodEstimator)
```

### Step 8: Perform Intervention

To compute interventional distributions:

1. Remove all incoming edges to the intervened variable
2. Set the variable to the intervention value
3. Sample from the modified network

```python
def apply_intervention(model, edges, var, value):
    """
    Apply do(var=value) intervention.

    Returns modified edges and intervention value.
    """
    # Remove incoming edges to intervened variable
    modified_edges = [(p, c) for p, c in edges if c != var]

    return modified_edges, {var: value}
```

### Step 9: Generate and Validate Samples

Generate samples and verify they match expected properties:

```python
# Generate samples under intervention
intervention_samples = modified_model.simulate(n_samples)

# Verify intervention took effect
assert all(intervention_samples[intervened_var] == intervention_value)

# Compare non-intervened variable distributions
for var in non_intervened_vars:
    orig_mean = data[var].mean()
    sample_mean = intervention_samples[var].mean()
    orig_std = data[var].std()
    sample_std = intervention_samples[var].std()

    # Check for reasonable similarity (allowing for intervention effects)
    print(f"{var}: Original mean={orig_mean:.2f}, Sample mean={sample_mean:.2f}")
```

## Common Pitfalls

### 1. Using Correlation for Structure Learning

**Wrong approach:** Greedily selecting edges based on correlation strength.

**Why it fails:** Correlation doesn't distinguish direct from indirect relationships or confounded associations.

**Correct approach:** Use conditional independence testing (PC algorithm) or score-based methods with appropriate scoring functions.

### 2. Ignoring Memory Constraints

**Wrong approach:** Abandoning proper methods when they fail due to memory.

**Correct approach:** Subsample data, reduce conditioning set size, or use more efficient implementations.

### 3. Misapplying Alphabetical Rules

**Example rule:** "For ambiguous edges, the alphabetically first node is the child."

Given nodes M and R with an ambiguous edge:
- M comes before R alphabetically
- Therefore M should be the child
- Correct edge: R → M

### 4. Not Validating the DAG

Always verify:
- Graph is acyclic
- Structure is reasonable given domain knowledge
- Generated samples have similar statistical properties to original data

### 5. Incorrect Output Format

Pay attention to required formats:
- Edge format: `parent,child` vs `child,parent` vs `to,from`
- CSV headers if required
- Sample output format

## Verification Checklist

Before submitting results, verify:

- [ ] Structure learning used proper conditional independence testing
- [ ] DAG is verified to be acyclic
- [ ] Alphabetical (or other) ordering rules applied correctly to ALL ambiguous edges
- [ ] Parameters learned from data, not assumed
- [ ] Intervention correctly removes incoming edges to intervened variable
- [ ] Generated samples show intervened variable at correct value
- [ ] Non-intervened variable statistics are reasonable
- [ ] Output format matches task requirements exactly

## Libraries and Tools

**Python:**
- `pgmpy` - Bayesian network structure and parameter learning
- `causal-learn` - Causal discovery algorithms
- `networkx` - Graph manipulation and validation
- `dowhy` - Causal inference framework

**R:**
- `bnlearn` - Comprehensive Bayesian network library (often more memory-efficient)
- `pcalg` - PC algorithm implementation

**When to use R:** Consider R's `bnlearn` if Python implementations run into memory issues, as it's often more optimized for large-scale structure learning.
