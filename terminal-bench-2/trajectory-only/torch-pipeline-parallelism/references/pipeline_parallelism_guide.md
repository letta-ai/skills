# Pipeline Parallelism Implementation Guide

## Understanding AFAB (All-Forward-All-Backward) Scheduling

AFAB is the simplest pipeline parallelism schedule:

1. **Forward Phase**: Process all microbatches through all stages sequentially
2. **Backward Phase**: Process all microbatches in reverse order

```
Timeline for 4 microbatches, 3 stages:

Forward Phase:
  Stage 0: [F0] [F1] [F2] [F3]
  Stage 1:      [F0] [F1] [F2] [F3]
  Stage 2:           [F0] [F1] [F2] [F3]

Backward Phase:
  Stage 2:                          [B3] [B2] [B1] [B0]
  Stage 1:                               [B3] [B2] [B1] [B0]
  Stage 0:                                    [B3] [B2] [B1] [B0]
```

## Model Partitioning Details

### Layer Distribution Formula

For a model with `N` layers distributed across `W` ranks:

```python
def get_layer_range(rank, world_size, num_layers):
    layers_per_rank = num_layers // world_size
    remainder = num_layers % world_size

    # Distribute remainder to first `remainder` ranks
    if rank < remainder:
        start = rank * (layers_per_rank + 1)
        end = start + layers_per_rank + 1
    else:
        start = rank * layers_per_rank + remainder
        end = start + layers_per_rank

    return start, end
```

### LLaMA-Style Model Structure

Typical structure to expect:
```
model
├── model
│   ├── embed_tokens          # Token embeddings (rank 0)
│   ├── layers                # Transformer layers (distributed)
│   │   ├── [0] DecoderLayer
│   │   ├── [1] DecoderLayer
│   │   └── ...
│   └── norm                  # Final layer norm (last rank)
└── lm_head                   # Output projection (last rank)
```

### Partition Data Structure

```python
@dataclass
class ModelPartition:
    layers: nn.ModuleList           # Assigned transformer layers
    embed_tokens: nn.Embedding      # Only for rank 0
    norm: nn.LayerNorm              # Only for last rank
    lm_head: nn.Linear              # Only for last rank
    rotary_emb: Optional[nn.Module] # Position embedding module
```

## Communication Protocol

### Shape Handshake

Before sending tensor data, communicate the shape:

```python
def send_tensor_with_shape(tensor, dst, device):
    # Send number of dimensions
    ndim = torch.tensor([tensor.ndim], dtype=torch.long, device=device)
    dist.send(ndim, dst=dst)

    # Send shape as single tensor
    shape = torch.tensor(list(tensor.shape), dtype=torch.long, device=device)
    dist.send(shape, dst=dst)

    # Send tensor data
    dist.send(tensor.contiguous(), dst=dst)

def recv_tensor_with_shape(src, dtype, device):
    # Receive number of dimensions
    ndim = torch.zeros(1, dtype=torch.long, device=device)
    dist.recv(ndim, src=src)

    # Receive shape
    shape = torch.zeros(ndim.item(), dtype=torch.long, device=device)
    dist.recv(shape, src=src)

    # Receive tensor data
    tensor = torch.zeros(tuple(shape.tolist()), dtype=dtype, device=device)
    dist.recv(tensor, src=src)

    return tensor
```

### Gradient Communication

During backward pass, gradients flow in reverse:

```python
def send_gradient(grad, dst, device):
    # Gradients must be contiguous
    grad_contig = grad.contiguous()
    send_tensor_with_shape(grad_contig, dst, device)

def recv_gradient(src, shape, dtype, device):
    grad = torch.zeros(shape, dtype=dtype, device=device)
    dist.recv(grad, src=src)
    return grad
```

## Position Embeddings Handling

### Rotary Position Embeddings (RoPE)

For LLaMA and similar models:

```python
def compute_position_embeddings(rotary_emb, seq_len, device, dtype):
    """
    Compute rotary embeddings for the given sequence length.

    Returns:
        Tuple of (cos, sin) tensors with shape (1, seq_len, head_dim)
    """
    # Create position IDs
    position_ids = torch.arange(seq_len, device=device).unsqueeze(0)

    # Get embeddings from the module
    # Implementation varies by transformers version
    cos, sin = rotary_emb(position_ids)

    return cos.to(dtype), sin.to(dtype)
```

### Passing Position Information Through Stages

Option 1: Recompute at each stage
```python
def forward_stage(partition, hidden_states, position_ids, rotary_emb):
    cos, sin = rotary_emb(position_ids)
    for layer in partition.layers:
        hidden_states = layer(hidden_states, position_embeddings=(cos, sin))
    return hidden_states
```

Option 2: Pass position embeddings through communication
```python
# Include position embeddings in the tensor being passed
# More communication overhead but simpler logic
```

## Loss Computation and Scaling

### Correct Scaling Pattern

```python
def compute_scaled_loss(logits, targets, num_microbatches):
    """
    Compute loss with proper scaling for pipeline parallelism.
    """
    loss_fn = nn.CrossEntropyLoss()

    # Reshape for loss computation
    logits_flat = logits.view(-1, logits.size(-1))
    targets_flat = targets.view(-1)

    # Compute unscaled loss
    loss = loss_fn(logits_flat, targets_flat)

    # Scale by number of microbatches
    # This ensures gradients sum to the correct value
    scaled_loss = loss / num_microbatches

    return scaled_loss
```

### Accumulating Gradients

```python
# Option 1: Scale loss before backward (preferred)
for mb_idx in range(num_microbatches):
    output = forward(...)
    loss = compute_loss(output, targets[mb_idx])
    (loss / num_microbatches).backward()

# Option 2: Scale gradients after (more complex)
for mb_idx in range(num_microbatches):
    output = forward(...)
    loss = compute_loss(output, targets[mb_idx])
    loss.backward()
# Then manually scale all gradients by 1/num_microbatches
```

## Edge Cases

### World Size = 1

```python
def train_step_pipeline_afab(model, inputs, targets, ...):
    rank = dist.get_rank() if dist.is_initialized() else 0
    world_size = dist.get_world_size() if dist.is_initialized() else 1

    # Skip communication for single rank
    if world_size == 1:
        # Run full model forward/backward
        outputs = model(inputs)
        loss = compute_loss(outputs, targets)
        loss.backward()
        return loss

    # Multi-rank pipeline logic...
```

### Variable Sequence Lengths

```python
def handle_variable_sequences(microbatches):
    """
    Handle microbatches with different sequence lengths.
    """
    # Option 1: Pad all to max length
    max_len = max(mb.size(1) for mb in microbatches)
    padded = [F.pad(mb, (0, 0, 0, max_len - mb.size(1))) for mb in microbatches]

    # Option 2: Process each with its own shape
    # Requires shape communication for each microbatch
```

### Empty Microbatch Handling

```python
def validate_microbatches(microbatches):
    """
    Validate microbatch list before processing.
    """
    if not microbatches:
        raise ValueError("Empty microbatch list")

    for i, mb in enumerate(microbatches):
        if mb.numel() == 0:
            raise ValueError(f"Empty microbatch at index {i}")
```

## Debugging Techniques

### Gradient Verification

```python
def verify_gradients(model):
    """
    Check that gradients are computed for all parameters.
    """
    no_grad_params = []
    for name, param in model.named_parameters():
        if param.requires_grad and param.grad is None:
            no_grad_params.append(name)

    if no_grad_params:
        print(f"Parameters without gradients: {no_grad_params}")
        return False
    return True
```

### Communication Debugging

```python
def debug_send_recv(tensor, operation, peer_rank):
    """
    Log communication operations for debugging.
    """
    rank = dist.get_rank()
    print(f"[Rank {rank}] {operation} tensor shape={tensor.shape} "
          f"dtype={tensor.dtype} peer={peer_rank}")
```

### Numerical Stability Checks

```python
def check_numerical_stability(tensor, name):
    """
    Check for NaN/Inf values in tensors.
    """
    if torch.isnan(tensor).any():
        print(f"NaN detected in {name}")
        return False
    if torch.isinf(tensor).any():
        print(f"Inf detected in {name}")
        return False
    return True
```

## Testing Checklist

- [ ] Syntax validation passes (`py_compile`)
- [ ] Imports work without errors
- [ ] `partition_model` correctly splits layers
- [ ] `forward_stage` produces correct output shapes
- [ ] Single-rank execution works (world_size=1)
- [ ] Multi-rank communication doesn't deadlock
- [ ] Gradients computed for all parameters
- [ ] Loss decreases over training iterations
- [ ] Gradient magnitudes match non-pipeline baseline
- [ ] No NaN/Inf values during training
