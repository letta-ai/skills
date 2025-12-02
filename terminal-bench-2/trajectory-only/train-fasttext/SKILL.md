---
name: train-fasttext
description: This skill provides guidance for training FastText text classification models with constraints on accuracy and model size. It should be used when training fastText supervised models, optimizing model size while maintaining accuracy thresholds, or when hyperparameter tuning for text classification tasks.
---

# Train FastText

## Overview

This skill provides structured approaches for training FastText supervised text classification models, particularly when balancing competing constraints like accuracy thresholds and model size limits. It covers hyperparameter tuning strategies, size optimization techniques, and common pitfalls to avoid.

## Pre-Training Analysis

Before starting any training, perform these critical assessments:

### 1. Estimate Training Time

Calculate approximate training time based on:
- Dataset size (number of samples and vocabulary)
- Target epochs
- Model complexity (dimension, wordNgrams)

**Rule of thumb**: For large datasets (>100k samples), expect 5-20+ minutes per training run. Plan iteration budget accordingly.

### 2. Understand Size Drivers

FastText model size is primarily determined by:
```
Size ≈ (vocabulary_size × dimension) + (bucket × dimension)
```

Key parameters affecting size:
- `dim`: Vector dimension (default 100)
- `bucket`: Number of hash buckets (default 2000000)
- `minCount`: Minimum word frequency to include (default 1)
- `minn/maxn`: Character n-gram range (default 0/0 for supervised)

### 3. Identify Target Tradeoffs

Before training, establish:
- Hard constraints (e.g., max file size, minimum accuracy)
- Soft preferences (e.g., prefer smaller model if accuracy is similar)
- Whether quantization will be used

## Training Strategy

### Phase 1: Quick Exploration (Use Data Subset)

To avoid wasting time on full dataset training during parameter exploration:

1. Create a 10-20% random sample of the training data
2. Run quick experiments (2-5 minutes each) to identify promising parameter ranges
3. Track accuracy vs. size for each configuration

```python
# Example: Create data subset for quick iteration
import random
with open('train.txt', 'r') as f:
    lines = f.readlines()
sample = random.sample(lines, len(lines) // 10)
with open('train_sample.txt', 'w') as f:
    f.writelines(sample)
```

### Phase 2: Systematic Parameter Search

Instead of arbitrary parameter changes, use structured exploration:

**For accuracy improvement:**
- Increase `epoch` (5 → 10 → 25)
- Increase `dim` (50 → 100 → 200)
- Add word n-grams (`wordNgrams=2` or `3`)
- Increase `lr` (0.1 → 0.5 → 1.0)

**For size reduction:**
- Increase `minCount` (1 → 5 → 10) - reduces vocabulary
- Decrease `bucket` (2000000 → 500000 → 200000)
- Decrease `dim` (100 → 50 → 25)
- Disable character n-grams (`minn=0, maxn=0`)

### Phase 3: Full Training

Once promising parameters are identified from Phase 1-2:
1. Train on full dataset
2. Evaluate both quantized and non-quantized models
3. Select model meeting all constraints

## Quantization Considerations

### When to Use Quantization

Quantization typically reduces model size by 5-10x but **degrades accuracy by 2-5%**.

Decision framework:
1. First, check if non-quantized model meets size requirement
2. If not, try reducing parameters (minCount, bucket, dim) on non-quantized model
3. Use quantization as last resort when parameter reduction alone is insufficient

### Quantization Options

```python
model.quantize(input='train.txt', retrain=True)  # Re-trains, better accuracy
model.quantize(input='train.txt', cutoff=100000)  # Limit vocabulary
model.quantize(input='train.txt', qnorm=True)     # Quantize norms
```

### Always Compare Both

After training, always check both versions:
```python
# Non-quantized
model.save_model('model.bin')
print(f"Non-quantized: {os.path.getsize('model.bin') / 1e6:.2f} MB")

# Quantized
model.quantize(input='train.txt')
model.save_model('model_quantized.ftz')
print(f"Quantized: {os.path.getsize('model_quantized.ftz') / 1e6:.2f} MB")
```

## Long-Running Training Management

### Background Execution Pattern

For training runs exceeding 2 minutes, use background execution:

```python
#!/usr/bin/env python3
import fasttext
import sys
import os

# Training with progress logging
print(f"Starting training...", flush=True)
model = fasttext.train_supervised(
    input='train.txt',
    epoch=10,
    dim=100,
    lr=0.5,
    wordNgrams=2,
    verbose=2  # Show progress
)

# Evaluate
result = model.test('test.txt')
print(f"Samples: {result[0]}, Precision: {result[1]:.4f}, Recall: {result[2]:.4f}")

# Save
model.save_model('model.bin')
print(f"Model size: {os.path.getsize('model.bin') / 1e6:.2f} MB")
```

Run with output capture:
```bash
python train.py > training.log 2>&1 &
echo $! > training.pid
```

Monitor progress:
```bash
tail -f training.log
```

## Verification Checklist

After training completion, verify:

1. **Accuracy meets threshold**
   ```python
   result = model.test('test.txt')
   assert result[1] >= required_accuracy, f"Accuracy {result[1]} below threshold"
   ```

2. **Model size meets constraint**
   ```python
   size_mb = os.path.getsize('model.bin') / 1e6
   assert size_mb <= max_size_mb, f"Size {size_mb}MB exceeds limit"
   ```

3. **Model loads correctly**
   ```python
   loaded = fasttext.load_model('model.bin')
   predictions = loaded.predict(['test sentence'])
   ```

## Common Pitfalls

### 1. Timeout Management

**Problem**: Training exceeds command timeout, causing incomplete runs.

**Solution**:
- Estimate training time before starting
- Use background execution for runs >2 minutes
- Set appropriate timeout values (10+ minutes for large datasets)

### 2. Zigzag Parameter Tuning

**Problem**: Randomly changing parameters without systematic approach wastes time.

**Solution**:
- Change one parameter at a time to understand its effect
- Use structured grid search or binary search for parameters
- Document each run's parameters and results

### 3. Over-Reliance on Quantization

**Problem**: Always using quantization without checking if non-quantized model could work.

**Solution**:
- Always evaluate non-quantized model first
- Try parameter reduction before quantization
- Understand quantization's accuracy cost (~2-5%)

### 4. No Validation Strategy

**Problem**: Training on full dataset every iteration is slow.

**Solution**:
- Use 10-20% sample for initial parameter exploration
- Only train on full data for final model
- Keep iteration cycles under 5 minutes during exploration

### 5. Ignoring Loss Function Choice

**Problem**: Using default loss function without considering alternatives.

**Solution**:
- `softmax`: Better for multi-class with mutually exclusive classes
- `ova` (one-vs-all): Better for multi-label or highly imbalanced classes
- `hs` (hierarchical softmax): Faster training for large label sets

### 6. Missing Text Preprocessing

**Problem**: Training on raw text without preprocessing.

**Solution**: Consider preprocessing steps:
- Lowercasing
- Punctuation removal/normalization
- Handling special characters
- Label format verification (`__label__prefix`)

## Parameter Reference

| Parameter | Default | Effect on Size | Effect on Accuracy |
|-----------|---------|----------------|-------------------|
| `dim` | 100 | Linear increase | Higher = better (diminishing) |
| `epoch` | 5 | None | Higher = better (overfitting risk) |
| `lr` | 0.1 | None | Task-dependent |
| `wordNgrams` | 1 | Moderate increase | 2-3 often helps |
| `minCount` | 1 | Lower = smaller vocab | Higher may hurt rare classes |
| `bucket` | 2000000 | Linear impact | Lower may hurt accuracy |
| `minn/maxn` | 0/0 | Higher = larger | Helps with misspellings |
| `loss` | softmax | None | Task-dependent |
