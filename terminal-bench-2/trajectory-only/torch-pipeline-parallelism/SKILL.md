---
name: torch-pipeline-parallelism
description: This skill provides guidance for implementing PyTorch pipeline parallelism for distributed training of large language models. It should be used when implementing pipeline parallel training loops, partitioning transformer models across GPUs, or working with AFAB (All-Forward-All-Backward) scheduling patterns. The skill covers model partitioning, inter-rank communication, gradient flow management, and common pitfalls in distributed training implementations.
---

# PyTorch Pipeline Parallelism

## Overview

Pipeline parallelism distributes model layers across multiple GPUs/ranks, enabling training of models too large for a single device. This skill provides procedural guidance for implementing pipeline parallel training with proper model partitioning, communication patterns, and gradient handling.

## Key Concepts

### Pipeline Parallelism Architecture
- **Stage**: A subset of model layers assigned to one rank
- **Microbatch**: Input data split into smaller chunks processed sequentially
- **AFAB (All-Forward-All-Backward)**: Schedule where all forward passes complete before any backward passes begin
- **Activation caching**: Storing intermediate outputs for backward pass computation

### Critical Implementation Components
1. Model partitioning across ranks
2. Inter-rank tensor communication (send/recv)
3. Activation caching for backward pass
4. Loss computation and gradient scaling
5. Handling of model-specific components (embeddings, normalization, output heads)

## Implementation Approach

### Phase 1: Model Analysis and Planning

Before writing any code:

1. **Examine the target model architecture**
   - Identify the layer structure (e.g., `model.model.layers` for LLaMA)
   - Locate embedding layers, normalization layers, and output heads
   - Understand position embedding mechanisms (rotary, absolute, etc.)
   - Note any model-specific forward pass requirements

2. **Plan the partitioning strategy**
   - Determine how layers will be distributed across ranks
   - Decide which rank handles embeddings (typically rank 0)
   - Decide which rank handles the output head and loss (typically last rank)
   - Account for any shared parameters

3. **Design the communication protocol**
   - Shape communication before tensor data
   - Dtype preservation across ranks
   - Device placement consistency

### Phase 2: Implement Core Functions

Implement these functions in order, testing each before proceeding:

1. **`partition_model(model, rank, world_size)`**
   - Extract layer subsets for the given rank
   - Handle embedding layers for rank 0
   - Handle output head for final rank
   - Return a clean partition object or module list

2. **`forward_stage(partition, hidden_states, ...)`**
   - Process hidden states through partition layers
   - Handle position embeddings correctly
   - Return output hidden states

3. **`train_step_pipeline_afab(model, inputs, targets, ...)`**
   - Implement the full AFAB schedule
   - Manage microbatch iteration
   - Handle inter-rank communication
   - Compute and scale loss appropriately

### Phase 3: Communication Implementation

**Shape Communication Pattern:**
```python
# Sending shape (more efficient as single tensor)
shape_tensor = torch.tensor(list(output.shape), dtype=torch.long, device=device)
dist.send(shape_tensor, dst=next_rank)

# Receiving shape
shape_tensor = torch.zeros(num_dims, dtype=torch.long, device=device)
dist.recv(shape_tensor, src=prev_rank)
recv_shape = tuple(shape_tensor.tolist())
```

**Tensor Communication:**
```python
# Ensure contiguous memory and correct dtype
output = output.contiguous()
dist.send(output, dst=next_rank)

# Receive with matching dtype
recv_tensor = torch.zeros(recv_shape, dtype=dtype, device=device)
dist.recv(recv_tensor, src=prev_rank)
```

### Phase 4: Gradient Flow Management

**Critical Pattern for Pipeline Parallelism:**
```python
# During forward pass, cache inputs for backward
input_detached = input_tensor.detach().requires_grad_(True)
input_cache.append(input_detached)
output = forward_stage(partition, input_detached, ...)

# During backward pass, use cached inputs
for i in reversed(range(num_microbatches)):
    cached_input = input_cache[i]
    output = output_cache[i]
    output.backward(grad_output, retain_graph=False)
    grad_to_send = cached_input.grad
```

## Verification Strategy

### Level 1: Syntax and Import Validation
```python
import py_compile
py_compile.compile('pipeline_parallel.py', doraise=True)

# Also verify imports work
import pipeline_parallel
```

### Level 2: Unit Testing Components

**Test partitioning independently:**
```python
def test_partition_model():
    model = load_small_test_model()
    for rank in range(world_size):
        partition = partition_model(model, rank, world_size)
        assert partition is not None
        assert len(partition.layers) > 0
```

**Test forward stage in isolation:**
```python
def test_forward_stage():
    partition = get_test_partition()
    dummy_input = torch.randn(batch, seq_len, hidden_dim)
    output = forward_stage(partition, dummy_input, ...)
    assert output.shape == expected_shape
    assert not torch.isnan(output).any()
```

### Level 3: Single-Rank Integration Test

Before distributed testing, verify with world_size=1:
```python
def test_single_rank():
    # Should handle the degenerate case without communication
    os.environ['WORLD_SIZE'] = '1'
    os.environ['RANK'] = '0'
    dist.init_process_group(backend='gloo', ...)

    loss = train_step_pipeline_afab(model, inputs, targets, ...)
    assert loss is not None
    assert not torch.isnan(loss)
```

### Level 4: Multi-Rank Distributed Test

```python
# Launch with torchrun or mp.spawn
# Verify gradients are computed on all ranks
# Check that loss decreases over iterations
```

## Common Pitfalls

### 1. Truncated File Writes
**Problem**: Large code blocks may be truncated during file operations.
**Prevention**:
- Write functions incrementally, verifying each write completes
- After writing, read back the file and verify syntax
- Use smaller, complete edits rather than large file rewrites

### 2. Position Embedding Mishandling
**Problem**: Transformer models (especially LLaMA) use rotary position embeddings that require specific handling.
**Prevention**:
- Read the model's forward pass implementation before coding
- Verify how `rotary_emb` or position embeddings are computed
- Pass position IDs explicitly through stages if needed
- Test with the actual model's embedding mechanism

### 3. Incorrect Loss Scaling
**Problem**: Loss scaled incorrectly when using microbatches.
**Prevention**:
- Scale loss by `1/num_microbatches` once, not per iteration
- Apply scaling before backward pass: `(loss / num_microbatches).backward()`
- Verify gradient magnitudes match non-pipeline baseline

### 4. Communication Deadlocks
**Problem**: Send/recv operations block indefinitely.
**Prevention**:
- Ensure matching send/recv pairs across ranks
- Handle `world_size=1` case without communication calls
- Use non-blocking operations with proper synchronization if needed
- Test communication patterns in isolation first

### 5. Broken Gradient Graph
**Problem**: Using `detach()` incorrectly breaks gradient flow.
**Prevention**:
- Understand that `detach().requires_grad_(True)` creates a new leaf tensor
- Cache these leaf tensors for backward pass
- Verify gradients flow correctly with simple test cases

### 6. Architecture Assumptions
**Problem**: Code assumes specific model structure that may vary.
**Prevention**:
- Validate model structure before accessing attributes
- Use `hasattr()` checks for optional components
- Document which model architectures are supported

### 7. Dtype and Device Mismatches
**Problem**: Tensors on wrong device or with wrong dtype after communication.
**Prevention**:
- Explicitly specify dtype when creating receive buffers
- Verify device placement after each operation
- Use `.to(device=device, dtype=dtype)` consistently

### 8. Missing Return Values
**Problem**: Functions don't return expected values for testing/integration.
**Prevention**:
- Define function contracts before implementation
- Return loss values for training functions
- Return gradients or other diagnostics as needed

## References

For detailed implementation guidance, see `references/pipeline_parallelism_guide.md`.
