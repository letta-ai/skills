# Weight Extraction Patterns

## Overview

This reference documents common patterns for extracting weights from PyTorch models for use in native C/C++ implementations.

## Basic Weight Extraction

### Loading a .pth File

```python
import torch
import json

# Load model weights
state_dict = torch.load('model.pth', map_location='cpu')

# If the file contains a full model (not just state_dict)
if hasattr(state_dict, 'state_dict'):
    state_dict = state_dict.state_dict()
```

### Inspecting Model Structure

```python
# Print all layer names and shapes
for name, param in state_dict.items():
    print(f"{name}: {param.shape}")
```

### Common Layer Naming Patterns

| PyTorch Layer | Weight Key | Bias Key |
|---------------|------------|----------|
| `nn.Linear` | `layer_name.weight` | `layer_name.bias` |
| `nn.Conv2d` | `layer_name.weight` | `layer_name.bias` |
| `nn.BatchNorm2d` | `layer_name.weight`, `layer_name.running_mean`, `layer_name.running_var` | `layer_name.bias` |

## Exporting to JSON

JSON format works well for simple models with small weight counts:

```python
import json
import torch

def export_to_json(state_dict, output_path):
    weights = {}
    for name, param in state_dict.items():
        # Convert tensor to nested Python list
        weights[name] = {
            'shape': list(param.shape),
            'data': param.cpu().numpy().flatten().tolist()
        }

    with open(output_path, 'w') as f:
        json.dump(weights, f)
```

### Loading JSON in C

Using cJSON library:

```c
cJSON *root = cJSON_Parse(json_string);
cJSON *layer = cJSON_GetObjectItem(root, "fc1.weight");
cJSON *shape = cJSON_GetObjectItem(layer, "shape");
cJSON *data = cJSON_GetObjectItem(layer, "data");

int rows = cJSON_GetArrayItem(shape, 0)->valueint;
int cols = cJSON_GetArrayItem(shape, 1)->valueint;

float *weights = malloc(rows * cols * sizeof(float));
for (int i = 0; i < rows * cols; i++) {
    weights[i] = (float)cJSON_GetArrayItem(data, i)->valuedouble;
}
```

## Exporting to Binary

Binary format is more efficient for larger models:

```python
import struct

def export_to_binary(state_dict, output_path):
    with open(output_path, 'wb') as f:
        # Write number of layers
        f.write(struct.pack('I', len(state_dict)))

        for name, param in state_dict.items():
            # Write layer name length and name
            name_bytes = name.encode('utf-8')
            f.write(struct.pack('I', len(name_bytes)))
            f.write(name_bytes)

            # Write number of dimensions and shape
            shape = param.shape
            f.write(struct.pack('I', len(shape)))
            for dim in shape:
                f.write(struct.pack('I', dim))

            # Write flattened data as float32
            data = param.cpu().numpy().flatten().astype('float32')
            f.write(data.tobytes())
```

### Loading Binary in C

```c
FILE *f = fopen("weights.bin", "rb");

uint32_t num_layers;
fread(&num_layers, sizeof(uint32_t), 1, f);

for (uint32_t i = 0; i < num_layers; i++) {
    // Read name
    uint32_t name_len;
    fread(&name_len, sizeof(uint32_t), 1, f);
    char *name = malloc(name_len + 1);
    fread(name, 1, name_len, f);
    name[name_len] = '\0';

    // Read shape
    uint32_t ndims;
    fread(&ndims, sizeof(uint32_t), 1, f);
    uint32_t *shape = malloc(ndims * sizeof(uint32_t));
    fread(shape, sizeof(uint32_t), ndims, f);

    // Calculate total size
    uint32_t size = 1;
    for (uint32_t j = 0; j < ndims; j++) {
        size *= shape[j];
    }

    // Read data
    float *data = malloc(size * sizeof(float));
    fread(data, sizeof(float), size, f);
}
```

## Weight Shape Conventions

### Linear Layers

PyTorch `nn.Linear(in_features, out_features)` stores:
- `weight`: shape `[out_features, in_features]`
- `bias`: shape `[out_features]`

Matrix multiplication: `output = input @ weight.T + bias`

Or equivalently: `output[i] = sum(weight[i][j] * input[j]) + bias[i]`

### Convolutional Layers

PyTorch `nn.Conv2d(in_channels, out_channels, kernel_size)` stores:
- `weight`: shape `[out_channels, in_channels, kernel_h, kernel_w]`
- `bias`: shape `[out_channels]`

## Verification During Extraction

Always verify extracted weights:

```python
def extract_and_verify(model_path, output_path):
    state_dict = torch.load(model_path, map_location='cpu')

    print("=== Weight Statistics ===")
    for name, param in state_dict.items():
        data = param.cpu().numpy()
        print(f"{name}:")
        print(f"  Shape: {data.shape}")
        print(f"  Min: {data.min():.6f}")
        print(f"  Max: {data.max():.6f}")
        print(f"  Mean: {data.mean():.6f}")
        print(f"  Std: {data.std():.6f}")

    # Export weights
    export_to_json(state_dict, output_path)

    # Verify by reloading
    with open(output_path, 'r') as f:
        loaded = json.load(f)

    for name, param in state_dict.items():
        original = param.cpu().numpy().flatten()
        exported = loaded[name]['data']
        diff = max(abs(a - b) for a, b in zip(original, exported))
        assert diff < 1e-6, f"Export verification failed for {name}"

    print("=== Export verified successfully ===")
```
