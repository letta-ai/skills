# Detailed Optimization Methodology for Batching Schedulers

This reference provides step-by-step guidance for deriving optimal parameters analytically.

## Step 1: Constraint Analysis

### Extract All Thresholds

From the task specification, identify:
- `max_cost`: Maximum allowed total cost
- `max_pad_ratio`: Maximum padding ratio (e.g., 0.15 means 15% padding allowed)
- `max_p95_latency`: P95 latency threshold
- `max_p99_latency`: P99 latency threshold
- `max_shapes`: Maximum number of unique shapes allowed

### Analyze Cost Model Components

Typical cost models include:
```
cost = base_cost + per_token_cost * padded_tokens + shape_cost * f(num_shapes)
```

Where `f(num_shapes)` is often quadratic. Identify exact coefficients.

## Step 2: Request Distribution Analysis

### Compute Statistics

For each request bucket:
```
bucket_stats = {
    "count": number of requests,
    "prompt_lengths": [list of prompt lengths],
    "gen_lengths": [list of generation lengths],
    "total_actual_tokens": sum of (prompt + gen) for all requests,
    "max_prompt": max(prompt_lengths),
    "max_gen": max(gen_lengths),
    "min_gen": min(gen_lengths),
    "gen_range": max_gen - min_gen
}
```

### Identify Shape Requirements

Minimum required shapes must cover:
- At least one shape with `prompt_dim >= max(all_prompt_lengths)`
- Shapes should be selected from available/allowed shape options

## Step 3: Derive Parameter Bounds

### Padding Budget Calculation

```
actual_tokens = sum of all (prompt_len + gen_len) across requests
max_padded_tokens = actual_tokens / (1 - max_pad_ratio)
padding_budget = max_padded_tokens - actual_tokens
```

### Generation Bucket Size Bound

For uniform bucketing:
```
# Worst-case padding per request = bucket_size - 1
# Total worst-case padding = num_requests * (bucket_size - 1) / 2 (average case)
# Setting average padding = padding_budget:
max_avg_bucket_size ≈ 2 * padding_budget / num_requests + 1
```

For safety margin, use:
```
safe_bucket_size = floor(0.8 * max_avg_bucket_size)
```

### Shape Count Bound

From cost constraint:
```
# If cost = A + B * tokens + C * shapes²
# And we have budget remaining after token costs:
shape_budget = (max_cost - A - B * estimated_tokens) / C
max_shapes = floor(sqrt(shape_budget))
```

## Step 4: Systematic Search Strategy

### For Single-Parameter Optimization

Use binary search when:
- The parameter has monotonic effect on a single metric
- Bounds are known

Example: Finding optimal `gen_bucket_size`
```
low = 1
high = derived_max_bucket_size
while high - low > 1:
    mid = (low + high) // 2
    metrics = evaluate(gen_bucket_size=mid)
    if metrics.pad_ratio <= threshold:
        low = mid  # can try larger buckets
    else:
        high = mid  # need smaller buckets
optimal = low
```

### For Multi-Parameter Optimization

When parameters interact:
1. Fix less-sensitive parameters first
2. Optimize most-impactful parameter
3. Fine-tune others

Priority order typically:
1. Shape selection (affects structural validity)
2. Generation bucket size (affects padding and batch count)
3. Batch assignment strategy (affects latency distribution)

## Step 5: Configuration Tracking Template

Maintain a log structure:
```
{
    "config_001": {
        "params": {
            "gen_bucket_size": 20,
            "shapes": [(512, 64), (1024, 64), (2048, 64)],
            "assignment_strategy": "greedy"
        },
        "metrics": {
            "cost": 12500,
            "pad_ratio": 0.142,
            "p95_latency": 45.2,
            "p99_latency": 52.1
        },
        "thresholds_passed": ["cost", "pad_ratio"],
        "thresholds_failed": ["p95_latency"],
        "notes": "Latency too high, try larger bucket"
    }
}
```

## Step 6: Trade-off Navigation

### Pad Ratio vs Latency Trade-off

- Smaller gen_bucket_size → lower pad_ratio, but more batches → higher latency
- Larger gen_bucket_size → higher pad_ratio, but fewer batches → lower latency

Find the sweet spot where both constraints are satisfied.

### Cost vs Flexibility Trade-off

- Fewer shapes → lower compilation cost, but coarser bucketing → more padding
- More shapes → higher compilation cost, but finer bucketing → less padding

Balance based on which constraint is tighter.

## Step 7: Failure Mode Analysis

When thresholds are not met:

| Failing Metric | Primary Adjustment | Secondary Adjustment |
|----------------|-------------------|---------------------|
| cost | Reduce shape count | Reduce padding (smaller buckets) |
| pad_ratio | Smaller gen bucket | Add intermediate shapes |
| p95_latency | Larger gen bucket | Rebalance batch sizes |
| p99_latency | Reduce batch count variance | Larger gen bucket |

## Example: Deriving Bucket Size for 5% Padding Budget

Given:
- 1000 requests with average gen_length = 50
- Total actual tokens = 1,000,000
- max_pad_ratio = 0.05

Calculation:
```
max_padded = 1,000,000 / 0.95 = 1,052,632
padding_budget = 52,632 tokens

# If using uniform buckets, average padding per request ≈ bucket_size/2
# Total padding ≈ 1000 * bucket_size/2 = 500 * bucket_size
# 500 * bucket_size <= 52,632
# bucket_size <= 105

# With safety margin (80%):
recommended_bucket_size = 84
```

This analytical approach replaces trial-and-error with directed optimization.
