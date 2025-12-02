---
name: llm-inference-batching-scheduler
description: Guidance for implementing batching schedulers for LLM inference systems with compilation-based accelerators. This skill applies when optimizing request batching to minimize cost while meeting latency thresholds, particularly when dealing with shape compilation costs, padding overhead, and multi-bucket request distributions. Use this skill for tasks involving batch planning, shape selection, generation-length bucketing, and cost-model-driven optimization for neural network inference.
---

# LLM Inference Batching Scheduler

This skill provides systematic approaches for designing batching schedulers that optimize LLM inference
workloads on compilation-based accelerators (TPUs, custom ASICs). The core challenge involves balancing
multiple competing objectives: minimizing compilation cost (fewer shapes), reducing padding waste
(tighter batches), and meeting latency thresholds (P95, P99 constraints).

## When to Apply This Skill

Apply this skill when:
- Designing batch schedulers for LLM inference with shape compilation constraints
- Optimizing request packing to minimize padding overhead
- Balancing cost metrics against latency thresholds
- Working with generation-length bucketing strategies
- Implementing plan files that assign requests to batches with specific shapes

## Core Concepts

### Shape Compilation Cost Model

Compilation-based accelerators require pre-compiled shapes. Each unique (prompt_length, generation_length)
shape incurs a one-time compilation cost. The total cost typically follows:

```
total_cost = per_token_cost × total_tokens + compilation_cost × num_shapes²
```

The quadratic term on `num_shapes` creates strong pressure to minimize unique shapes while the
per-token cost penalizes excessive padding.

### Padding Analysis Framework

Before implementing, calculate padding budgets mathematically:

1. **Identify the threshold constraints**: Extract max allowed cost, pad_ratio, and latency percentiles
2. **Calculate current baseline**: Sum actual tokens across all requests
3. **Derive padding budget**: `max_padded_tokens = actual_tokens / (1 - max_pad_ratio)`
4. **Compute allowable padding**: `padding_budget = max_padded_tokens - actual_tokens`

This budget constrains the maximum generation bucket size.

### Generation-Length Bucketing

Requests are grouped by generation length into buckets. The bucket size directly affects padding:

- **Smaller buckets**: Less padding waste, but more batches (higher P95 latency risk)
- **Larger buckets**: More padding waste, but fewer batches (better latency)

To derive optimal bucket size:
```
optimal_bucket_size ≈ padding_budget / num_requests_in_worst_bucket
```

## Systematic Approach

### Phase 1: Mathematical Analysis (Before Any Code)

1. **Parse the cost model completely**
   - Identify all cost components and their weights
   - Understand how shape count affects compilation cost
   - Map latency calculation formulas

2. **Analyze request distribution**
   - Compute statistics: prompt length distribution, generation length distribution
   - Identify required prompt shapes to cover all requests (max prompt length determines minimum shape)
   - Calculate baseline token counts per bucket

3. **Derive parameter bounds from constraints**
   - From pad_ratio threshold: calculate max padding tokens allowed
   - From cost threshold: calculate max compilation overhead
   - From latency thresholds: estimate max batch count implications

4. **Document derived constraints**
   - Write down: "Max padding = X tokens", "Max shapes = Y", "Gen bucket size must be ≤ Z"

### Phase 2: Systematic Parameter Search

Instead of ad-hoc trial-and-error, implement structured search:

1. **Define the parameter space**
   - Generation bucket sizes: range based on Phase 1 analysis
   - Shape configurations: enumerate valid combinations covering all prompt lengths

2. **Implement reusable evaluation**
   - Create a standalone validation function that computes all metrics
   - Return structured results: {cost, pad_ratio, p95_latency, p99_latency, valid: bool}

3. **Search systematically**
   - Grid search over small parameter spaces
   - Binary search when optimizing single parameters
   - Track all configurations and results

### Phase 3: Implementation with Invariant Checking

1. **Critical invariants to validate continuously**
   - All prompt lengths covered: `max(prompt_lengths) ≤ max(shape_prompt_dims)`
   - All requests assigned: `sum(batch_sizes) == total_requests`
   - Shape count within limit: `len(unique_shapes) ≤ max_shapes`

2. **Build validation into the workflow**
   - Check invariants after every modification
   - Fail fast when invariants break

## Common Pitfalls and Mitigations

### Pitfall 1: Removing Required Shapes

**Symptom**: Assertion errors about uncovered prompt lengths after optimizing shape count.

**Cause**: When reducing shapes for compilation cost, accidentally removing shapes needed for long prompts.

**Prevention**:
- Before removing any shape, verify: `shape_to_remove.prompt_dim < max(all_prompt_lengths)`
- Always keep at least one shape covering the maximum prompt length
- Implement a `required_shapes()` function that returns non-removable shapes

### Pitfall 2: Empirical Parameter Selection Without Mathematical Justification

**Symptom**: Cycling through bucket sizes (20, 21, 22...) without clear rationale, losing track of best configurations.

**Cause**: Not computing optimal parameters from constraints first.

**Prevention**:
- Calculate bounds analytically before testing
- If bucket_size=21 works but 20 doesn't, understand why mathematically
- Log all tested configurations with results

### Pitfall 3: Optimizing One Metric While Breaking Others

**Symptom**: Reducing pad_ratio but exceeding cost threshold, or vice versa.

**Cause**: Metrics are interconnected—fewer shapes increases padding, smaller buckets increase latency.

**Prevention**:
- Always evaluate ALL metrics after each change
- Create a multi-objective feasibility check
- Understand trade-off relationships before optimizing

### Pitfall 4: Inconsistent Configuration Tracking

**Symptom**: Re-testing configurations or forgetting which parameters achieved which results.

**Prevention**:
- Maintain a results log: `{config_hash: {params: {...}, metrics: {...}}}`
- Before testing, check if configuration was already evaluated
- Keep "best so far" state updated

### Pitfall 5: Late Validation of Structural Constraints

**Symptom**: Plan file passes metric thresholds but fails structural validation (duplicate requests, missing requests).

**Prevention**:
- Validate structure FIRST, before computing metrics
- Check: no duplicate request IDs, all request IDs present, batch counts match

## Verification Strategy

### Structural Verification (Run First)

```
1. Parse generated plan file
2. Extract all request IDs assigned to batches
3. Verify: set(assigned_ids) == set(all_request_ids)
4. Verify: len(assigned_ids) == len(all_request_ids)  # no duplicates
5. Verify: all shapes have prompt_dim >= max prompt in that batch
6. Verify: unique_shape_count <= max_allowed_shapes
```

### Metric Verification (Run After Structural)

```
1. Compute total padded tokens using shape dimensions
2. Compute actual tokens from request data
3. Calculate: pad_ratio = 1 - (actual / padded)
4. Compute cost using exact cost model formula
5. Simulate latency distribution, extract P95/P99
6. Compare all metrics against thresholds
```

### Iterative Verification Pattern

After any parameter change:
1. Generate new plan
2. Run structural verification → fix if broken
3. Run metric verification → analyze trade-offs
4. Update configuration tracking log
5. Decide next parameter adjustment based on which metrics are furthest from threshold

## Reference: Optimization Decision Tree

```
START
  │
  ├─ Is pad_ratio too high?
  │    └─ YES → Reduce generation bucket size OR add more prompt shapes
  │
  ├─ Is cost too high?
  │    └─ YES → Reduce number of unique shapes (but verify coverage!)
  │
  ├─ Is P95/P99 latency too high?
  │    └─ YES → Increase generation bucket size (larger batches, fewer total)
  │         OR redistribute requests across batches more evenly
  │
  └─ All metrics passing?
       └─ YES → DONE (record configuration as solution)
```

## Key Insight Summary

1. **Math first, code second**: Derive bounds from constraints before implementing
2. **Track everything**: Maintain configuration→results mapping
3. **Validate continuously**: Check invariants after every modification
4. **Understand trade-offs**: Metrics are interconnected; optimize with awareness
5. **Separate concerns**: Structure validation, metric computation, and parameter search should be independent, reusable components
