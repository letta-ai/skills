---
name: path-tracing
description: Guide for reverse-engineering and recreating programmatically-generated ray-traced images. This skill should be used when tasks involve analyzing a target image to determine rendering parameters, implementing path tracing or ray tracing algorithms, matching scene geometry and lighting, or achieving high similarity scores between generated and target images.
---

# Path Tracing

## Overview

This skill provides guidance for tasks involving reverse-engineering ray-traced or path-traced images—analyzing a target image to extract scene parameters (camera position, geometry, materials, lighting) and implementing a renderer that produces a matching output. These tasks typically require achieving high similarity scores (e.g., 0.99+) between generated and target images.

## Approach

### Phase 1: Analysis Before Implementation

Before writing any rendering code, thoroughly analyze the target image to extract parameters:

1. **Identify scene components**: List all visible elements (sky/background, ground plane, objects, shadows, reflections)
2. **Sample pixel values systematically**: Extract RGB values at key locations to determine:
   - Background/sky gradient direction and colors
   - Floor pattern (checkerboard scale, colors)
   - Object colors and material properties
   - Shadow colors and positions
3. **Derive mathematical relationships**: Calculate gradient formulas, pattern frequencies, and geometric positions from sampled data
4. **Document assumptions explicitly**: Write down every derived parameter with justification

### Phase 2: Fast Iteration Loop

Establish an efficient testing workflow before attempting full-resolution renders:

1. **Create downscaled test versions**: Use 10-20x smaller resolution (e.g., 240x180 instead of 2400x1800) for parameter tuning
2. **Calculate expected render times**: For path tracing, time ≈ width × height × samples_per_pixel × rays_per_sample. A 2400×1800×100 render means 432 million rays—estimate this upfront
3. **Implement the exact evaluation metric**: If the task uses normalized L2 similarity, implement and track that specific metric, not a proxy like RMS error
4. **Parameterize the renderer**: Create a single codebase where scene parameters can be easily adjusted without rewriting code

### Phase 3: Component-by-Component Verification

Verify each scene component independently before combining:

1. **Sky/background first**: Match the gradient exactly in isolation
2. **Ground plane second**: Verify checkerboard pattern scale and colors
3. **Primary geometry third**: Position and size the main object(s)
4. **Shadows and secondary effects last**: These depend on correct primary geometry

For each component:
- Render only that component against a neutral background
- Compare against the corresponding region in the target
- Achieve acceptable error before moving on

### Phase 4: Full Resolution Validation

Only after parameters are tuned on low resolution:

1. Run a medium-resolution test (e.g., 800x600) to verify scaling
2. Execute full-resolution render with validated parameters
3. Compare using the exact evaluation metric

## Common Pitfalls

### Gradient Direction Errors
- **Symptom**: Sky appears inverted (darker at horizon when it should be brighter, or vice versa)
- **Prevention**: Sample multiple points along the gradient axis and verify the direction mathematically before implementing

### Horizontal vs Vertical Gradient Confusion
- **Symptom**: Image appears wrong at edges or center
- **Prevention**: Sample corner pixels explicitly to detect horizontal gradients; document whether brightness increases or decreases toward edges

### Arbitrary Parameter Guessing
- **Symptom**: Making incremental guesses (0.08, 0.09, 0.075, 0.05) without analysis
- **Prevention**: Use dimensional analysis—calculate expected values from sampled data mathematically

### Underestimating Render Time
- **Symptom**: Timeouts during rendering, incomplete output files
- **Prevention**: Calculate expected runtime upfront; start with sample counts of 10-30 for testing, only increase for final validation

### Proxy Metric Mismatch
- **Symptom**: Low RMS error but failing the actual similarity threshold
- **Prevention**: Implement and use the exact evaluation metric from the start

### Incomplete Render Validation
- **Symptom**: Comparing against incomplete/corrupted output files
- **Prevention**: Verify output file size matches expected dimensions before comparison; check PPM/image headers

## Verification Strategies

### Pre-Implementation Verification
- [ ] All scene components identified and listed
- [ ] Pixel values sampled at 10+ key locations
- [ ] Mathematical formulas derived for gradients/patterns
- [ ] Expected render time calculated
- [ ] Evaluation metric implemented

### Parameter Tuning Verification
- [ ] Using 10-20x downscaled resolution for testing
- [ ] Each component verified independently
- [ ] No arbitrary parameter guessing—all values derived from analysis
- [ ] Error tracked using exact evaluation metric

### Final Validation Verification
- [ ] Medium-resolution test passed before full resolution
- [ ] Output file size/format validated before comparison
- [ ] Full-resolution render completed without timeout
- [ ] Final similarity score meets requirements

## Process Management

### Long-Running Renders
- Use background processes for renders expected to exceed 30 seconds
- Implement progress indicators (line count, file size monitoring)
- Consider incremental output formats that can be resumed

### File Format Validation
- Verify PPM/image headers match expected format exactly
- Check for proper line endings and byte counts
- Validate output dimensions match target dimensions

## Mathematical Foundations

### Ray-Sphere Intersection
For sphere at center `C` with radius `r`, ray origin `O` and direction `D`:
- Compute discriminant: `b² - 4ac` where `a = D·D`, `b = 2D·(O-C)`, `c = (O-C)·(O-C) - r²`
- Handle floating-point precision at grazing angles

### Checkerboard Pattern
For a floor at y=0 with checker size `s`:
- Pattern: `(floor(x/s) + floor(z/s)) % 2`
- Scale factor must be derived from observed pattern, not guessed

### Sky Gradients
- Vertical gradient: Typically based on ray direction's y-component
- Horizontal gradient: Based on ray direction's x-component or distance from center
- Document interpolation formula: linear vs smoothstep vs other
