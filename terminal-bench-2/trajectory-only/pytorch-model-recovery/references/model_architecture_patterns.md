# Model Architecture Patterns from Weight Files

This reference provides detailed patterns for inferring PyTorch model architectures from weight file keys and tensor shapes.

## Weight Key Naming Conventions

### Standard PyTorch Naming

PyTorch modules create predictable key patterns:

| Module Type | Key Pattern | Example |
|-------------|-------------|---------|
| Linear | `{name}.weight`, `{name}.bias` | `fc1.weight`, `fc1.bias` |
| Conv2d | `{name}.weight`, `{name}.bias` | `conv1.weight`, `conv1.bias` |
| BatchNorm | `{name}.weight`, `{name}.bias`, `{name}.running_mean`, `{name}.running_var` | `bn1.weight` |
| LayerNorm | `{name}.weight`, `{name}.bias` | `norm.weight`, `norm.bias` |
| Embedding | `{name}.weight` | `embedding.weight` |
| LSTM | `{name}.weight_ih_l{layer}`, `{name}.weight_hh_l{layer}`, `{name}.bias_ih_l{layer}`, `{name}.bias_hh_l{layer}` | `lstm.weight_ih_l0` |
| GRU | `{name}.weight_ih_l{layer}`, `{name}.weight_hh_l{layer}`, `{name}.bias_ih_l{layer}`, `{name}.bias_hh_l{layer}` | `gru.weight_ih_l0` |
| MultiheadAttention | `{name}.in_proj_weight`, `{name}.in_proj_bias`, `{name}.out_proj.weight`, `{name}.out_proj.bias` | `self_attn.in_proj_weight` |

### Nested Module Naming

Nested modules create dot-separated paths:

```
model.encoder.layers.0.self_attn.in_proj_weight
│     │       │     │ │         └── Parameter name
│     │       │     │ └── Submodule name
│     │       │     └── Layer index
│     │       └── ModuleList name
│     └── Submodule name
└── Root module
```

## Inferring Dimensions from Shapes

### Linear Layers

```python
# fc.weight shape: (out_features, in_features)
# fc.bias shape: (out_features,)

linear_weight = weights['fc.weight']
in_features = linear_weight.shape[1]
out_features = linear_weight.shape[0]
```

### Convolutional Layers

```python
# conv.weight shape: (out_channels, in_channels, kernel_h, kernel_w)
# conv.bias shape: (out_channels,)

conv_weight = weights['conv1.weight']
out_channels = conv_weight.shape[0]
in_channels = conv_weight.shape[1]
kernel_size = conv_weight.shape[2:]  # (H, W) tuple
```

### Embedding Layers

```python
# embedding.weight shape: (num_embeddings, embedding_dim)

emb_weight = weights['embedding.weight']
vocab_size = emb_weight.shape[0]
embedding_dim = emb_weight.shape[1]
```

### LayerNorm / BatchNorm

```python
# norm.weight shape: (normalized_shape,) or (num_features,)

norm_weight = weights['norm.weight']
hidden_size = norm_weight.shape[0]
```

### MultiheadAttention

```python
# self_attn.in_proj_weight shape: (3 * embed_dim, embed_dim)
# The factor of 3 is for Q, K, V projections

attn_weight = weights['self_attn.in_proj_weight']
embed_dim = attn_weight.shape[1]
# To find num_heads, look for head_dim patterns or use common values (4, 8, 12, 16)
```

### LSTM / GRU

```python
# lstm.weight_ih_l0 shape: (4 * hidden_size, input_size) for LSTM
# lstm.weight_ih_l0 shape: (3 * hidden_size, input_size) for GRU

lstm_weight = weights['lstm.weight_ih_l0']
# For LSTM: 4 gates (input, forget, cell, output)
hidden_size = lstm_weight.shape[0] // 4
input_size = lstm_weight.shape[1]

# For GRU: 3 gates (reset, update, new)
hidden_size = lstm_weight.shape[0] // 3
```

## Counting Layers

To count layers in a ModuleList:

```python
def count_layers(weights, prefix):
    """Count number of layers matching a prefix pattern."""
    indices = set()
    for key in weights.keys():
        if key.startswith(prefix):
            # Extract the index after the prefix
            rest = key[len(prefix):]
            if rest.startswith('.'):
                rest = rest[1:]
            parts = rest.split('.')
            if parts[0].isdigit():
                indices.add(int(parts[0]))
    return len(indices)

# Example usage:
num_encoder_layers = count_layers(weights, 'encoder.layers')
num_decoder_layers = count_layers(weights, 'decoder.layers')
```

## Transformer Architecture Reconstruction

### Standard Transformer Encoder-Decoder

```python
def infer_transformer_config(weights):
    """Infer transformer configuration from weights."""

    config = {}

    # Find d_model from embedding or first linear layer
    if 'embedding.weight' in weights:
        config['d_model'] = weights['embedding.weight'].shape[1]
    elif 'encoder.layers.0.self_attn.in_proj_weight' in weights:
        config['d_model'] = weights['encoder.layers.0.self_attn.in_proj_weight'].shape[1]

    # Count encoder/decoder layers
    config['num_encoder_layers'] = count_layers(weights, 'encoder.layers')
    config['num_decoder_layers'] = count_layers(weights, 'decoder.layers')

    # Find feedforward dimension
    ff_key = 'encoder.layers.0.linear1.weight'
    if ff_key in weights:
        config['dim_feedforward'] = weights[ff_key].shape[0]

    # Infer num_heads (common values: 4, 8, 12, 16)
    # Often: d_model / num_heads = 64 (head_dim)
    d_model = config['d_model']
    for num_heads in [16, 12, 8, 4, 2, 1]:
        if d_model % num_heads == 0:
            head_dim = d_model // num_heads
            if head_dim in [32, 64, 128]:  # Common head dimensions
                config['nhead'] = num_heads
                break

    return config
```

### BERT-style Architecture

Key patterns for BERT:

```
bert.embeddings.word_embeddings.weight
bert.embeddings.position_embeddings.weight
bert.embeddings.token_type_embeddings.weight
bert.encoder.layer.{N}.attention.self.query.weight
bert.encoder.layer.{N}.attention.self.key.weight
bert.encoder.layer.{N}.attention.self.value.weight
bert.encoder.layer.{N}.attention.output.dense.weight
bert.encoder.layer.{N}.intermediate.dense.weight
bert.encoder.layer.{N}.output.dense.weight
bert.pooler.dense.weight
```

### GPT-style Architecture

Key patterns for GPT:

```
transformer.wte.weight  # Token embeddings
transformer.wpe.weight  # Position embeddings
transformer.h.{N}.ln_1.weight
transformer.h.{N}.attn.c_attn.weight  # Combined Q,K,V
transformer.h.{N}.attn.c_proj.weight
transformer.h.{N}.ln_2.weight
transformer.h.{N}.mlp.c_fc.weight
transformer.h.{N}.mlp.c_proj.weight
transformer.ln_f.weight
```

## CNN Architecture Reconstruction

### ResNet-style

Key patterns:

```
conv1.weight
bn1.weight, bn1.bias, bn1.running_mean, bn1.running_var
layer1.0.conv1.weight
layer1.0.bn1.weight
layer1.0.conv2.weight
layer1.0.bn2.weight
layer1.0.downsample.0.weight  # Skip connection (if present)
layer1.0.downsample.1.weight  # BatchNorm for skip
fc.weight, fc.bias  # Final classifier
```

### VGG-style

Key patterns:

```
features.0.weight  # Conv2d
features.1.weight  # BatchNorm (if present)
features.3.weight  # Conv2d
...
classifier.0.weight  # Linear
classifier.3.weight  # Linear
classifier.6.weight  # Linear
```

## Validation Patterns

### Check for Missing Keys

```python
def validate_model_weights(model, weights):
    """Validate model matches weights before loading."""
    model_keys = set(model.state_dict().keys())
    weight_keys = set(weights.keys())

    missing_in_model = weight_keys - model_keys
    missing_in_weights = model_keys - weight_keys

    if missing_in_model:
        print(f"Keys in weights but not in model: {missing_in_model}")
    if missing_in_weights:
        print(f"Keys in model but not in weights: {missing_in_weights}")

    return len(missing_in_model) == 0 and len(missing_in_weights) == 0
```

### Check Shape Compatibility

```python
def validate_shapes(model, weights):
    """Validate tensor shapes match."""
    model_state = model.state_dict()
    for key in weights:
        if key in model_state:
            if weights[key].shape != model_state[key].shape:
                print(f"Shape mismatch for {key}:")
                print(f"  Weights: {weights[key].shape}")
                print(f"  Model:   {model_state[key].shape}")
                return False
    return True
```
