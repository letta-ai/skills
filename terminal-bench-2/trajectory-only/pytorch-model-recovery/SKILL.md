---
name: pytorch-model-recovery
description: This skill should be used when reconstructing PyTorch models from weight files (state dictionaries), checkpoint files, or partial model artifacts. It applies when the agent needs to infer model architecture from saved weights, rebuild models without original source code, or recover models from corrupted/incomplete saves. Use this skill for tasks involving torch.load, state_dict reconstruction, architecture inference, or model recovery in CPU-constrained environments.
---

# PyTorch Model Recovery

## Overview

This skill provides guidance for reconstructing PyTorch models when only weight files or state dictionaries are available. Model recovery tasks require careful analysis of weight tensor shapes to infer architecture, followed by systematic verification before attempting computationally expensive operations.

## Workflow

### Phase 1: Weight File Analysis

Before writing any model code, thoroughly analyze the saved weights:

1. **Load and inspect the state dictionary completely**
   ```python
   import torch
   weights = torch.load('weights.pt', map_location='cpu')

   # Print ALL keys and shapes - do not truncate
   for key, tensor in weights.items():
       print(f"{key}: {tensor.shape}")
   ```

2. **Identify architecture components from weight naming patterns**
   - `encoder.layer.X.*` → Number of encoder layers
   - `decoder.layer.X.*` → Number of decoder layers
   - `attention.num_heads` or weight shapes → Attention configuration
   - `fc.weight` shapes → Hidden dimensions
   - Embedding weights → Vocabulary size and embedding dimension

3. **Document the complete architecture specification**
   - Total number of each layer type
   - Hidden dimensions from weight shapes
   - Any special configurations (dropout rates may need defaults)

### Phase 2: Architecture Reconstruction

Reconstruct the model architecture to match the weights exactly:

1. **Build the model class matching all weight keys**
   - Every key in the state dict must have a corresponding parameter
   - Layer naming must match exactly (including indices)

2. **Verify architecture before proceeding**
   ```python
   # Test that state dict loads with strict=True
   model = YourModel(config)
   model.load_state_dict(weights, strict=True)
   print("Architecture matches weights successfully")
   ```

   If this fails, the architecture is incorrect. Fix before continuing.

### Phase 3: Minimal Verification Testing

Before running any training or expensive operations:

1. **Test a single forward pass**
   ```python
   with torch.no_grad():
       dummy_input = torch.randint(0, vocab_size, (1, 10))  # Minimal batch
       output = model(dummy_input)
       print(f"Forward pass successful, output shape: {output.shape}")
   ```

2. **Benchmark single-sample processing time**
   ```python
   import time
   start = time.time()
   with torch.no_grad():
       _ = model(dummy_input)
   elapsed = time.time() - start
   print(f"Single forward pass: {elapsed:.2f}s")
   ```

3. **Estimate full run time before committing**
   - If single pass takes X seconds, multiply by expected iterations
   - Factor in backward pass (~2-3x forward pass time)
   - Account for CPU-only constraints (10-100x slower than GPU)

### Phase 4: Execution with Resource Awareness

When running the actual recovery/training:

1. **Use aggressive memory optimization for CPU**
   ```python
   torch.set_num_threads(1)  # Prevent thread contention

   # Process in minimal batches
   batch_size = 1  # Start with 1, increase only if time permits

   # Use no_grad for any non-training operations
   with torch.no_grad():
       # inference code
   ```

2. **Implement progress monitoring**
   ```python
   import sys
   for i, batch in enumerate(dataloader):
       if i % 10 == 0:
           print(f"Processed {i}/{len(dataloader)}", flush=True)
           sys.stdout.flush()
   ```

3. **Save intermediate results**
   ```python
   # Save model periodically during training
   if epoch % save_interval == 0:
       torch.save(model.state_dict(), f'checkpoint_epoch_{epoch}.pt')
   ```

## Common Architecture Patterns

### Transformer Models

When weight keys contain `transformer`, `encoder`, `decoder`:

```python
# Infer from weights:
# - encoder.layer.0-N → num_encoder_layers = N+1
# - d_model from embedding weight shape[1]
# - nhead from attention weight shapes
# - dim_feedforward from fc1 weight shapes

config = {
    'd_model': weights['embedding.weight'].shape[1],
    'nhead': weights['encoder.layer.0.self_attn.in_proj_weight'].shape[0] // (3 * d_model),
    'num_encoder_layers': count_layers(weights, 'encoder.layer'),
    'num_decoder_layers': count_layers(weights, 'decoder.layer'),
    'dim_feedforward': weights['encoder.layer.0.linear1.weight'].shape[0],
}
```

### CNN Models

When weight keys contain `conv`, `bn`, `pool`:

```python
# Infer from weights:
# - in_channels from conv.weight.shape[1]
# - out_channels from conv.weight.shape[0]
# - kernel_size from conv.weight.shape[2:]
```

## Verification Checklist

Before considering the task complete:

- [ ] All weight keys load without warnings (`strict=True` succeeds)
- [ ] Forward pass completes without errors
- [ ] Output shapes match expected dimensions
- [ ] Model can be saved and reloaded successfully
- [ ] Final output file exists and is valid

## Critical Pitfalls to Avoid

### 1. Incomplete Weight Inspection

**Problem**: Truncating the weight key list leads to missing layers in architecture.

**Solution**: Always print the complete state dictionary. Request full output if truncated.

### 2. Skipping Architecture Verification

**Problem**: Running expensive training only to find architecture mismatch.

**Solution**: Always run `load_state_dict(weights, strict=True)` before any other operations.

### 3. Underestimating CPU Computation Time

**Problem**: Transformer operations on CPU can be 10-100x slower than GPU.

**Solution**:
- Benchmark single iteration first
- Use batch_size=1 initially
- Consider reducing model precision if acceptable
- Calculate expected runtime before committing

### 4. Reactive Timeout Handling

**Problem**: Repeatedly reducing iterations slightly after each timeout.

**Solution**: After first timeout, fundamentally reconsider approach:
- Can the task be split into smaller pieces?
- Can intermediate results be saved and resumed?
- Is there a simpler verification approach?

### 5. Missing Environment Validation

**Problem**: Ignoring warnings about missing libraries (NumPy, CUDA).

**Solution**: Check for and address environment issues before running main task:
```python
import warnings
warnings.filterwarnings('error')  # Catch warnings as errors initially

# Verify environment
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
try:
    import numpy as np
    print(f"NumPy version: {np.__version__}")
except ImportError:
    print("WARNING: NumPy not available - may affect performance")
```

### 6. No Fallback Strategy

**Problem**: Single approach with no backup plan when it fails.

**Solution**: Plan alternatives before starting:
- Can verification be done with smaller test data?
- Can the model be saved at intermediate state?
- Is there a minimal reproduction that proves correctness?

## References

See `references/model_architecture_patterns.md` for detailed weight-to-architecture mapping patterns for common model types.
