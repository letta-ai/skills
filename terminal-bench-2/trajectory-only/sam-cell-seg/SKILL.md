---
name: sam-cell-seg
description: This skill provides guidance for tasks involving MobileSAM or Segment Anything Model (SAM) for cell segmentation, mask refinement, and polygon extraction from images. Use when working with SAM-based image segmentation pipelines, converting masks to polygons, processing CSV-based coordinate data, or integrating deep learning segmentation models into processing scripts.
---

# SAM Cell Segmentation

## Overview

This skill guides the implementation of image segmentation pipelines using MobileSAM or SAM (Segment Anything Model), particularly for cell segmentation tasks. These tasks typically involve refining initial mask coordinates, converting masks to polygons, handling overlapping regions, and outputting structured data formats like CSV.

## When to Use This Skill

- Tasks involving SAM or MobileSAM for image segmentation
- Converting segmentation masks to polygon coordinates
- Processing CSV files containing initial mask/coordinate data
- Refining coarse segmentation masks using deep learning models
- Cell or object segmentation in microscopy images

## Approach Strategy

### Phase 1: Understand Input/Output Requirements

Before writing any code:

1. **Examine input data format thoroughly**
   - Read sample CSV files to understand column structure
   - Identify coordinate formats (x,y pairs, bounding boxes, etc.)
   - Check for edge cases in input data (empty rows, invalid coordinates)

2. **Clarify output requirements**
   - Exact output format expected (CSV columns, data types)
   - How polygons should be represented (list of points, WKT, etc.)
   - Whether to preserve original data or create new structure

3. **Identify model requirements**
   - Which SAM variant is needed (SAM, MobileSAM, SAM-HQ)
   - Model checkpoint locations
   - Expected input image formats

### Phase 2: Design Before Implementation

1. **Map the complete data flow**
   - Input CSV → Parse coordinates → Generate prompts → Run SAM → Convert masks → Output CSV
   - Identify all transformation steps

2. **Plan function decomposition**
   - CSV parsing and validation
   - Coordinate transformation (if needed)
   - SAM model loading and inference
   - Mask post-processing (overlap removal, refinement)
   - Mask-to-polygon conversion
   - Output formatting

3. **Identify dependencies and their availability**
   - Core: PyTorch, numpy, PIL/OpenCV
   - SAM-specific: segment-anything, mobile_sam
   - Transitive dependencies: Check if dependencies like `timm` are available

### Phase 3: Implementation Guidelines

1. **Trust stated package availability**
   - If task specifies packages will be available in test environment, do not spend time on installation debugging
   - Focus on writing correct logic rather than environment setup

2. **Build incrementally with validation**
   - Implement and test each function independently
   - Use mock objects for unavailable dependencies during development
   - Create unit tests for data transformation functions

3. **Handle SAM model integration carefully**
   ```python
   # Standard SAM setup pattern
   from segment_anything import sam_model_registry, SamPredictor

   sam = sam_model_registry["vit_h"](checkpoint="path/to/checkpoint")
   predictor = SamPredictor(sam)
   predictor.set_image(image)

   # For MobileSAM
   from mobile_sam import sam_model_registry as mobile_sam_registry
   ```

4. **Mask-to-polygon conversion pattern**
   ```python
   import cv2
   import numpy as np

   def mask_to_polygon(mask):
       """Convert binary mask to polygon coordinates."""
       contours, _ = cv2.findContours(
           mask.astype(np.uint8),
           cv2.RETR_EXTERNAL,
           cv2.CHAIN_APPROX_SIMPLE
       )
       if not contours:
           return None
       # Return largest contour
       largest = max(contours, key=cv2.contourArea)
       return largest.squeeze().tolist()
   ```

5. **Overlap removal strategies**
   - Assign pixels to mask with highest confidence score
   - Or assign to mask with largest area
   - Or use distance-based assignment

## Verification Strategy

### Critical: Never Claim Completion Without Execution

1. **Syntax validation is insufficient**
   - `py_compile` passing does not mean the script works
   - Import errors only appear at runtime

2. **Unit tests are necessary but not sufficient**
   - Test individual functions with mock data
   - BUT also test the complete pipeline end-to-end

3. **Required verification steps**
   - Run the complete script with actual input data
   - Verify output format matches requirements exactly
   - Check edge cases (empty masks, overlapping regions)

### Mock Testing for Unavailable Dependencies

When SAM/MobileSAM cannot be loaded in development:

```python
class MockSAMPredictor:
    """Mock predictor for testing pipeline logic."""
    def set_image(self, image):
        self.image_shape = image.shape[:2]

    def predict(self, point_coords=None, box=None, **kwargs):
        # Return dummy mask matching image dimensions
        h, w = self.image_shape
        mask = np.zeros((1, h, w), dtype=bool)
        if box is not None:
            x1, y1, x2, y2 = map(int, box)
            mask[0, y1:y2, x1:x2] = True
        return mask, [0.9], None
```

### Output Validation Checklist

- [ ] CSV has correct column headers
- [ ] Coordinate format matches specification
- [ ] No NaN or infinite values in output
- [ ] All input rows have corresponding output
- [ ] Polygon coordinates form valid closed shapes

## Common Pitfalls

### 1. Environment Debugging Instead of Logic Development

**Problem**: Spending excessive time on `pip install` and PyTorch version issues.

**Solution**: If task states packages are available in test environment, write the script assuming they work. Focus on correctness of logic.

### 2. Incomplete File Verification

**Problem**: Not viewing complete file contents after edits, leading to truncated or corrupted code.

**Solution**: Always re-read files after editing, especially after multi-edit operations. Verify the entire file is syntactically correct.

### 3. Premature Success Claims

**Problem**: Declaring task complete based on unit tests alone without running the actual pipeline.

**Solution**: Define success criteria that require actual execution:
- Script runs without errors
- Output file is generated
- Output format matches specification
- Sample outputs are visually/logically correct

### 4. Missing Transitive Dependencies

**Problem**: Script imports library A, which imports library B (not in allowed list).

**Solution**: Check import chains for deep learning libraries. Common hidden dependencies:
- MobileSAM → timm
- segment-anything → specific PyTorch versions
- opencv-python → numpy version requirements

### 5. Ignoring Edge Cases

**Problem**: Not handling empty masks, invalid coordinates, or boundary conditions.

**Required edge case handling**:
- Empty mask after SAM refinement → fall back to original or skip
- Coordinates outside image bounds → clip or skip
- Very small masks (< N pixels) → filter or flag
- Non-contiguous masks → handle multiple components

### 6. Creating Excessive Documentation

**Problem**: Creating README.md, SOLUTION_SUMMARY.md, verification checklists instead of ensuring core script works.

**Solution**: Focus on the deliverable. Documentation is secondary to a working script.

## Recommended Workflow

1. Read and understand input format completely
2. Design complete data flow on paper/mentally
3. Implement helper functions with tests
4. Implement SAM integration (or mock if unavailable)
5. Implement complete pipeline
6. Test with actual data
7. Verify output format
8. Only then declare completion

## Resources

For SAM-specific implementation details, refer to:
- Segment Anything documentation for model usage patterns
- OpenCV documentation for contour detection and polygon approximation
- NumPy documentation for mask manipulation operations
