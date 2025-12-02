# Verification Strategies

## Overview

Verifying that a native C/C++ implementation produces correct results is critical. This reference provides strategies for systematic verification against PyTorch reference implementations.

## Strategy 1: Layer-by-Layer Verification

Test each layer independently before testing the full forward pass.

### Python Reference Script

```python
import torch
import torch.nn as nn
import numpy as np

def verify_linear_layer(weight, bias, input_data, expected_output):
    """
    Verify a single linear layer computation.

    Args:
        weight: numpy array [out_features, in_features]
        bias: numpy array [out_features]
        input_data: numpy array [in_features]
        expected_output: numpy array [out_features] from C implementation
    """
    # PyTorch computation
    layer = nn.Linear(weight.shape[1], weight.shape[0])
    layer.weight.data = torch.from_numpy(weight).float()
    layer.bias.data = torch.from_numpy(bias).float()

    input_tensor = torch.from_numpy(input_data).float()
    pytorch_output = layer(input_tensor).detach().numpy()

    # Compare
    diff = np.abs(pytorch_output - expected_output)
    max_diff = diff.max()

    print(f"Max difference: {max_diff:.2e}")
    print(f"Mean difference: {diff.mean():.2e}")

    if max_diff > 1e-5:
        print("WARNING: Large difference detected!")
        # Find problematic indices
        problem_indices = np.where(diff > 1e-5)[0]
        for idx in problem_indices[:5]:  # Show first 5
            print(f"  Index {idx}: PyTorch={pytorch_output[idx]:.6f}, "
                  f"C={expected_output[idx]:.6f}")

    return max_diff < 1e-5
```

### C Debug Output

Add debug output to C implementation:

```c
void debug_layer_output(const char* layer_name, float* output, int size) {
    printf("=== %s output ===\n", layer_name);
    printf("First 5 values: ");
    for (int i = 0; i < 5 && i < size; i++) {
        printf("%.6f ", output[i]);
    }
    printf("\n");

    float sum = 0, min = output[0], max = output[0];
    for (int i = 0; i < size; i++) {
        sum += output[i];
        if (output[i] < min) min = output[i];
        if (output[i] > max) max = output[i];
    }
    printf("Min: %.6f, Max: %.6f, Mean: %.6f\n", min, max, sum / size);
}
```

## Strategy 2: Full Pipeline Verification

Compare end-to-end outputs between PyTorch and native implementation.

### Create Reference Outputs

```python
import torch
import json

def create_reference(model, image_path, output_path):
    """Generate reference output for comparison."""
    # Load and preprocess image (match preprocessing used in C)
    from PIL import Image
    import numpy as np

    img = Image.open(image_path).convert('L')  # Convert to grayscale
    img = img.resize((28, 28))  # Resize if needed

    # Convert to tensor and normalize
    img_array = np.array(img, dtype=np.float32) / 255.0
    input_tensor = torch.from_numpy(img_array).flatten().unsqueeze(0)

    # Run inference
    model.eval()
    with torch.no_grad():
        logits = model(input_tensor)
        probs = torch.softmax(logits, dim=1)
        prediction = logits.argmax(dim=1).item()

    # Save reference
    reference = {
        'input_shape': list(input_tensor.shape),
        'input_values': input_tensor.flatten().tolist()[:10],  # First 10 for verification
        'logits': logits[0].tolist(),
        'probabilities': probs[0].tolist(),
        'prediction': prediction
    }

    with open(output_path, 'w') as f:
        json.dump(reference, f, indent=2)

    print(f"Reference prediction: {prediction}")
    print(f"Logits: {logits[0].tolist()}")

    return reference
```

### Compare in C

```c
int verify_output(float* c_logits, int num_classes, const char* reference_path) {
    // Load reference JSON
    FILE* f = fopen(reference_path, "r");
    // ... parse JSON ...

    float max_diff = 0;
    for (int i = 0; i < num_classes; i++) {
        float diff = fabs(c_logits[i] - reference_logits[i]);
        if (diff > max_diff) max_diff = diff;
    }

    printf("Max logit difference: %.2e\n", max_diff);

    if (max_diff > 1e-4) {
        printf("ERROR: Output verification failed!\n");
        return 0;
    }

    printf("Output verification passed.\n");
    return 1;
}
```

## Strategy 3: Input Verification

Ensure input preprocessing matches between implementations.

### Common Preprocessing Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Wrong normalization range | Outputs are scaled incorrectly | Verify 0-1 vs -1 to 1 vs ImageNet |
| RGB vs BGR | Completely wrong results | Check channel order |
| Missing grayscale conversion | Wrong channel count | Add RGB to grayscale conversion |
| Alpha channel included | Extra input dimensions | Strip alpha channel |
| Row-major vs column-major | Scrambled results | Check memory layout |

### Input Verification Code

```python
def verify_input_preprocessing(image_path):
    """Print input preprocessing details for verification."""
    from PIL import Image
    import numpy as np

    img = Image.open(image_path)
    print(f"Original format: {img.mode}")
    print(f"Original size: {img.size}")

    # Convert to grayscale if needed
    if img.mode != 'L':
        img_gray = img.convert('L')
        print("Converted to grayscale")
    else:
        img_gray = img

    # Convert to numpy
    arr = np.array(img_gray, dtype=np.float32)
    print(f"Array shape: {arr.shape}")
    print(f"Value range: [{arr.min()}, {arr.max()}]")

    # Normalize
    arr_norm = arr / 255.0
    print(f"Normalized range: [{arr_norm.min():.4f}, {arr_norm.max():.4f}]")

    # Show corner values for comparison
    print(f"Top-left 3x3:\n{arr_norm[:3, :3]}")
    print(f"Bottom-right 3x3:\n{arr_norm[-3:, -3:]}")

    # Flatten order
    flat = arr_norm.flatten()
    print(f"First 10 flattened values: {flat[:10]}")
```

## Strategy 4: Numerical Stability Checks

### Check for NaN/Inf

```c
int check_numerical_stability(float* arr, int size, const char* name) {
    int nan_count = 0, inf_count = 0;
    float min_val = arr[0], max_val = arr[0];

    for (int i = 0; i < size; i++) {
        if (isnan(arr[i])) nan_count++;
        if (isinf(arr[i])) inf_count++;
        if (arr[i] < min_val) min_val = arr[i];
        if (arr[i] > max_val) max_val = arr[i];
    }

    if (nan_count > 0 || inf_count > 0) {
        printf("ERROR in %s: %d NaN, %d Inf values\n", name, nan_count, inf_count);
        return 0;
    }

    printf("%s range: [%.6f, %.6f]\n", name, min_val, max_val);
    return 1;
}
```

### Activation Function Verification

```c
// ReLU should never produce negative values
void verify_relu(float* pre_relu, float* post_relu, int size) {
    for (int i = 0; i < size; i++) {
        float expected = pre_relu[i] > 0 ? pre_relu[i] : 0;
        if (fabs(post_relu[i] - expected) > 1e-7) {
            printf("ReLU error at index %d: input=%.6f, output=%.6f, expected=%.6f\n",
                   i, pre_relu[i], post_relu[i], expected);
        }
    }
}
```

## Strategy 5: Automated Testing Script

Create a comprehensive test script:

```bash
#!/bin/bash
set -e

echo "=== PyTorch Model CLI Verification ==="

# 1. Generate reference output
echo "Step 1: Generating PyTorch reference..."
python3 generate_reference.py model.pth image.png reference.json

# 2. Run C implementation
echo "Step 2: Running C implementation..."
./cli_tool weights.json image.png > c_output.txt

# 3. Compare outputs
echo "Step 3: Comparing outputs..."
python3 compare_outputs.py reference.json c_output.txt

# 4. Run edge cases
echo "Step 4: Testing edge cases..."
./cli_tool weights.json nonexistent.png 2>&1 | grep -q "Error" && echo "Missing file handled OK"
./cli_tool weights.json 2>&1 | grep -q "Usage" && echo "Missing args handled OK"

echo "=== All tests passed ==="
```

## Debugging Checklist

When outputs don't match:

1. **Verify input values are identical**
   - Print first 10 flattened input values in both implementations
   - Check normalization range

2. **Check weight loading**
   - Print weight statistics (min, max, mean) after loading
   - Verify shapes match expected dimensions

3. **Trace through layers**
   - Add debug output after each layer
   - Compare intermediate activations

4. **Check matrix multiplication order**
   - PyTorch: `output = input @ weight.T + bias`
   - Verify C implementation uses same order

5. **Verify activation functions**
   - Test ReLU produces expected zeros for negative inputs
   - Check softmax sums to 1.0

6. **Check for precision issues**
   - Use double precision temporarily to rule out float32 errors
   - Check for overflow in intermediate computations
