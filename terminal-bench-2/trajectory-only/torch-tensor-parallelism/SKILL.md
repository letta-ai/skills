---
name: torch-tensor-parallelism
description: This skill provides guidance for implementing tensor parallelism in PyTorch, specifically column-parallel and row-parallel linear layers. Use when implementing distributed neural network layers that split weights/activations across multiple ranks, working with torch.distributed for model parallelism, or implementing ColumnParallelLinear and RowParallelLinear classes.
---

# Torch Tensor Parallelism

## Overview

This skill provides structured guidance for implementing tensor-parallel linear layers in PyTorch. Tensor parallelism splits individual layers across multiple devices/processes, enabling training of models too large for a single device. The two primary patterns are column parallelism (splitting output features) and row parallelism (splitting input features).

## When to Use This Skill

Use this skill when:
- Implementing `ColumnParallelLinear` or `RowParallelLinear` classes
- Splitting weight matrices across ranks using `torch.distributed`
- Implementing layers that require `all_gather` or `all_reduce` communication patterns
- Debugging gradient flow or shape mismatches in distributed linear layers

## Critical Workflow: Verify Before Implementing

### Step 1: Analyze Test Requirements First

**CRITICAL**: Before writing any implementation code, thoroughly read and understand the test file.

Extract from tests:
1. **Weight sharding expectations**: Which dimension is split, what shapes are expected per rank
2. **Bias handling**: Is bias sharded, replicated, or handled specially
3. **Input expectations**: Does each rank receive full input or partitioned input
4. **Output expectations**: What shape should each rank produce
5. **Gradient requirements**: How gradients for weights and biases should match
6. **World sizes tested**: Typically 1, 2, and 4

Document findings before coding:
```markdown
## Extracted Specification

### ColumnParallelLinear
- Weight shape per rank: [out_features/world_size, in_features]
- Bias shape per rank: [out_features/world_size]
- Input: full [batch, in_features]
- Output: partial [batch, out_features/world_size]
- Combined output: concatenate along last dimension

### RowParallelLinear
- Weight shape per rank: [out_features, in_features/world_size]
- Bias shape per rank: [out_features] (full on each rank)
- Input: partial [batch, in_features/world_size]
- Output: partial [batch, out_features]
- Combined output: sum across ranks, then add bias
```

### Step 2: Trace Through with Concrete Examples

**Before writing code**, manually trace the computation with small numeric examples:

```
Example: world_size=2, in_features=4, out_features=2

Full weight W: [[a, b, c, d],
                [e, f, g, h]]  shape [2, 4]

Full input X: [x1, x2, x3, x4]  shape [batch, 4]

COLUMN PARALLEL (split output features):
  Rank 0: W_shard = [[a, b, c, d]]  shape [1, 4]
  Rank 1: W_shard = [[e, f, g, h]]  shape [1, 4]

  Rank 0 output: [x1*a + x2*b + x3*c + x4*d]  shape [batch, 1]
  Rank 1 output: [x1*e + x2*f + x3*g + x4*h]  shape [batch, 1]

  Gathered: concat → [y0, y1]  shape [batch, 2] ✓

ROW PARALLEL (split input features):
  Rank 0: W_shard = [[a, b], [e, f]]  shape [2, 2]
  Rank 1: W_shard = [[c, d], [g, h]]  shape [2, 2]

  Rank 0 input: [x1, x2]  shape [batch, 2]
  Rank 1 input: [x3, x4]  shape [batch, 2]

  Rank 0 partial: [x1*a + x2*b, x1*e + x2*f]  shape [batch, 2]
  Rank 1 partial: [x3*c + x4*d, x3*g + x4*h]  shape [batch, 2]

  All-reduce (sum): partial_0 + partial_1 = full output ✓
```

**Key insight**: Tracing reveals conceptual errors before implementation.

### Step 3: Implement with File Verification

When writing files:

1. **Write the complete implementation in a single operation**
2. **Immediately read back the file to verify it was written correctly**
3. **Check that no content was truncated**

```python
# After writing, verify:
# 1. File exists
# 2. All methods are complete (no truncated lines like "# Calculate output per)")
# 3. Forward method has return statement
# 4. All class definitions are closed
```

### Step 4: Verify Without Running Tests

If the test environment is unavailable, verify through logical analysis:

1. **Shape verification table**:
   ```
   | Component | Expected Shape | Actual in Code |
   |-----------|---------------|----------------|
   | Weight    | [out/ws, in]  | ✓ chunk(dim=0) |
   | Bias      | [out/ws]      | ✓ zeros(out/ws)|
   | Output    | [batch, out/ws]| ✓ matmul result|
   ```

2. **Trace a specific example through the code**:
   - Substitute actual numbers
   - Follow each line of forward()
   - Verify final shape matches expected

3. **Check gradient path**:
   - Verify all parameters participate in forward computation
   - Ensure no conditional logic blocks gradient flow

## Implementation Patterns

### Column Parallel Linear

Splits weight along output dimension (dim 0):

```python
class ColumnParallelLinear(nn.Module):
    def __init__(self, in_features, out_features, bias, master_weight):
        super().__init__()
        self.rank = dist.get_rank()
        self.world_size = dist.get_world_size()

        # Validate divisibility
        assert out_features % self.world_size == 0, \
            f"out_features ({out_features}) must be divisible by world_size ({self.world_size})"

        # Split weight along output dimension (dim 0)
        weight_chunks = torch.chunk(master_weight, self.world_size, dim=0)
        self.weight = nn.Parameter(weight_chunks[self.rank].contiguous())
        # Shape: [out_features/world_size, in_features]

        if bias:
            # Bias sharded same as output dimension
            local_out = out_features // self.world_size
            self.bias = nn.Parameter(torch.zeros(local_out, dtype=master_weight.dtype))
        else:
            self.register_parameter('bias', None)

    def forward(self, x):
        # x: [batch, in_features] - full input on all ranks
        output = torch.matmul(x, self.weight.t())
        # output: [batch, out_features/world_size]

        if self.bias is not None:
            output = output + self.bias

        return output  # Partial output, to be gathered
```

### Row Parallel Linear

Splits weight along input dimension (dim 1):

```python
class RowParallelLinear(nn.Module):
    def __init__(self, in_features, out_features, bias, master_weight):
        super().__init__()
        self.rank = dist.get_rank()
        self.world_size = dist.get_world_size()

        # Validate divisibility
        assert in_features % self.world_size == 0, \
            f"in_features ({in_features}) must be divisible by world_size ({self.world_size})"

        # Split weight along input dimension (dim 1)
        weight_chunks = torch.chunk(master_weight, self.world_size, dim=1)
        self.weight = nn.Parameter(weight_chunks[self.rank].contiguous())
        # Shape: [out_features, in_features/world_size]

        if bias:
            # Bias remains FULL on each rank
            self.bias = nn.Parameter(torch.zeros(out_features, dtype=master_weight.dtype))
        else:
            self.register_parameter('bias', None)

    def forward(self, x):
        # x: [batch, in_features/world_size] - partitioned input
        output = torch.matmul(x, self.weight.t())
        # output: [batch, out_features] - partial result

        # NOTE: In test context, bias is added AFTER all-reduce
        # Check test to determine exact bias handling
        if self.bias is not None:
            output = output + self.bias

        return output  # Partial result, to be reduced
```

## Critical Pitfalls

### 1. Truncated File Writes

**Problem**: File write operations may truncate, leaving incomplete implementations.

**Detection**: Code ends mid-line (e.g., `# Calculate output per)`) or methods lack return statements.

**Prevention**:
- Always read back files after writing
- Verify all method definitions are complete
- Check that closing parentheses/braces match opening ones

### 2. Wrong Weight Splitting Dimension

**Problem**: Splitting along the wrong dimension causes shape mismatches.

**Memory aid**:
- **Column parallel**: Split dim 0 (output features) → each rank computes different outputs
- **Row parallel**: Split dim 1 (input features) → each rank processes different inputs

**Verification**: After chunking, print shapes and verify they match expected dimensions.

### 3. Bias Duplication in Row Parallel

**Problem**: Adding full bias on all ranks before all-reduce multiplies bias by world_size.

**Solutions** (choose based on test requirements):
- Add bias only on rank 0 (asymmetric, may affect gradients)
- Add bias/world_size on each rank (scales to correct value after sum)
- Add bias after all-reduce (requires test to handle this)

**Critical**: Check test file to determine expected behavior.

### 4. Gradient Flow Blocked by Conditionals

**Problem**: Using `if rank == 0:` for bias addition means only rank 0 receives bias gradients.

**Detection**: After backward pass, check `bias.grad` on all ranks - some may be None or zero.

**Solution**: Ensure bias participates in forward on all ranks, or verify test expects asymmetric gradients.

### 5. Skipping Manual Verification

**Problem**: Assuming implementation is correct without tracing through examples.

**Solution**: Always trace at least one concrete example (world_size=2) through the implementation before considering it complete.

### 6. Ignoring Edge Cases

**Problem**: Implementation fails for world_size=1 or non-divisible dimensions.

**Verification checklist**:
- [ ] Works with world_size=1 (no actual splitting)
- [ ] Works with world_size=2 (basic splitting)
- [ ] Works with world_size=4 (more granular splitting)
- [ ] Appropriate error message if dimensions not divisible

## Verification Checklist

Before considering implementation complete:

- [ ] Read test file and documented exact requirements
- [ ] Traced computation manually with concrete example
- [ ] Verified file was written completely (no truncation)
- [ ] Weight split dimension matches parallelism type
- [ ] Bias handling matches test expectations
- [ ] All parameters receive gradients (trace backward pass)
- [ ] Edge cases handled (world_size=1, divisibility)
- [ ] If environment unavailable, performed logical verification with shape tables

## Quick Reference

### Shape Cheat Sheet

| Pattern | Weight Shape | Bias Shape | Input Shape | Output Shape |
|---------|-------------|-----------|------------|--------------|
| Column  | [O/ws, I]   | [O/ws]    | [B, I]     | [B, O/ws]    |
| Row     | [O, I/ws]   | [O]       | [B, I/ws]  | [B, O]       |

Where: O=out_features, I=in_features, ws=world_size, B=batch

### Split Dimension Reference

| Parallelism | Weight Split Dim | Effect |
|-------------|-----------------|--------|
| Column      | dim=0           | Each rank computes subset of outputs |
| Row         | dim=1           | Each rank processes subset of inputs |

### Communication Pattern

| Parallelism | Forward Combine | Backward to Input |
|-------------|-----------------|-------------------|
| Column      | all_gather (concat) | scatter/split |
| Row         | all_reduce (sum) | broadcast/replicate |
