# SAM Integration Patterns

## Model Loading Patterns

### Standard SAM

```python
import torch
from segment_anything import sam_model_registry, SamPredictor

def load_sam_predictor(checkpoint_path, model_type="vit_h", device=None):
    """Load SAM model and return predictor."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
    sam.to(device=device)
    predictor = SamPredictor(sam)
    return predictor
```

### MobileSAM

```python
from mobile_sam import sam_model_registry as mobile_registry
from mobile_sam import SamPredictor as MobileSamPredictor

def load_mobilesam_predictor(checkpoint_path, device=None):
    """Load MobileSAM model and return predictor."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    mobile_sam = mobile_registry["vit_t"](checkpoint=checkpoint_path)
    mobile_sam.to(device=device)
    predictor = MobileSamPredictor(mobile_sam)
    return predictor
```

## Inference Patterns

### Point-Based Prompting

```python
def segment_with_points(predictor, image, points, labels):
    """
    Segment using point prompts.

    Args:
        predictor: SAM predictor instance
        image: RGB image as numpy array (H, W, 3)
        points: Nx2 array of (x, y) coordinates
        labels: N array of labels (1=foreground, 0=background)

    Returns:
        mask: Binary mask (H, W)
        score: Confidence score
    """
    predictor.set_image(image)

    masks, scores, logits = predictor.predict(
        point_coords=points,
        point_labels=labels,
        multimask_output=False
    )

    return masks[0], scores[0]
```

### Box-Based Prompting

```python
def segment_with_box(predictor, image, box):
    """
    Segment using bounding box prompt.

    Args:
        predictor: SAM predictor instance
        image: RGB image as numpy array (H, W, 3)
        box: Bounding box as [x1, y1, x2, y2]

    Returns:
        mask: Binary mask (H, W)
        score: Confidence score
    """
    predictor.set_image(image)

    masks, scores, logits = predictor.predict(
        box=np.array(box),
        multimask_output=False
    )

    return masks[0], scores[0]
```

### Combined Prompting

```python
def segment_with_box_and_points(predictor, image, box, points=None, labels=None):
    """
    Segment using both box and point prompts for refinement.

    Box provides coarse localization, points refine the mask.
    """
    predictor.set_image(image)

    masks, scores, logits = predictor.predict(
        point_coords=points,
        point_labels=labels,
        box=np.array(box),
        multimask_output=False
    )

    return masks[0], scores[0]
```

## Batch Processing Pattern

```python
def process_multiple_regions(predictor, image, boxes):
    """
    Process multiple regions in same image efficiently.

    Set image once, then run multiple predictions.
    """
    predictor.set_image(image)  # Only do this once per image

    results = []
    for box in boxes:
        masks, scores, _ = predictor.predict(
            box=np.array(box),
            multimask_output=False
        )
        results.append({
            'mask': masks[0],
            'score': scores[0],
            'box': box
        })

    return results
```

## Mask Post-Processing

### Remove Small Components

```python
import cv2
import numpy as np

def remove_small_components(mask, min_area=100):
    """Remove connected components smaller than min_area."""
    mask_uint8 = mask.astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask_uint8, connectivity=8
    )

    cleaned_mask = np.zeros_like(mask)
    for i in range(1, num_labels):  # Skip background (0)
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            cleaned_mask[labels == i] = 1

    return cleaned_mask.astype(bool)
```

### Fill Holes

```python
def fill_holes(mask):
    """Fill holes in binary mask."""
    mask_uint8 = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(
        mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    filled = np.zeros_like(mask_uint8)
    cv2.drawContours(filled, contours, -1, 255, -1)
    return filled > 0
```

### Smooth Boundaries

```python
def smooth_mask_boundary(mask, kernel_size=5):
    """Smooth mask boundaries using morphological operations."""
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )
    mask_uint8 = mask.astype(np.uint8) * 255

    # Open then close to smooth
    smoothed = cv2.morphologyEx(mask_uint8, cv2.MORPH_OPEN, kernel)
    smoothed = cv2.morphologyEx(smoothed, cv2.MORPH_CLOSE, kernel)

    return smoothed > 0
```

## Overlap Resolution Strategies

### By Confidence Score

```python
def resolve_overlaps_by_score(masks_with_scores):
    """
    Resolve overlapping masks by assigning pixels to highest-scoring mask.

    Args:
        masks_with_scores: List of (mask, score) tuples

    Returns:
        List of non-overlapping masks
    """
    if not masks_with_scores:
        return []

    # Sort by score descending
    sorted_masks = sorted(masks_with_scores, key=lambda x: x[1], reverse=True)

    combined = np.zeros_like(sorted_masks[0][0], dtype=np.int32)
    final_masks = []

    for idx, (mask, score) in enumerate(sorted_masks, 1):
        # Only keep pixels not already assigned
        available = combined == 0
        new_mask = mask & available

        if new_mask.any():
            combined[new_mask] = idx
            final_masks.append(new_mask)
        else:
            final_masks.append(np.zeros_like(mask, dtype=bool))

    return final_masks
```

### By Area (Largest First)

```python
def resolve_overlaps_by_area(masks):
    """Assign overlapping pixels to largest mask."""
    if not masks:
        return []

    areas = [m.sum() for m in masks]
    sorted_indices = np.argsort(areas)[::-1]  # Largest first

    combined = np.zeros_like(masks[0], dtype=np.int32)
    final_masks = [None] * len(masks)

    for rank, idx in enumerate(sorted_indices, 1):
        mask = masks[idx]
        available = combined == 0
        new_mask = mask & available
        combined[new_mask] = rank
        final_masks[idx] = new_mask

    return final_masks
```

## Mask to Polygon Conversion

### Basic Conversion

```python
def mask_to_polygon(mask, simplify_tolerance=1.0):
    """
    Convert binary mask to polygon coordinates.

    Args:
        mask: Binary mask (H, W)
        simplify_tolerance: Douglas-Peucker simplification tolerance

    Returns:
        List of (x, y) coordinates, or None if no valid contour
    """
    contours, _ = cv2.findContours(
        mask.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # Get largest contour
    largest = max(contours, key=cv2.contourArea)

    # Simplify if requested
    if simplify_tolerance > 0:
        epsilon = simplify_tolerance * cv2.arcLength(largest, True) / 100
        largest = cv2.approxPolyDP(largest, epsilon, True)

    # Convert to list of (x, y) tuples
    coords = largest.squeeze()
    if coords.ndim == 1:
        return [(int(coords[0]), int(coords[1]))]

    return [(int(x), int(y)) for x, y in coords]
```

### Handle Multiple Components

```python
def mask_to_polygons(mask, min_area=50):
    """
    Convert mask with multiple components to list of polygons.

    Returns list of polygons, one per connected component.
    """
    contours, _ = cv2.findContours(
        mask.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    polygons = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area:
            coords = contour.squeeze()
            if coords.ndim == 1:
                continue  # Single point, skip
            polygon = [(int(x), int(y)) for x, y in coords]
            polygons.append(polygon)

    return polygons
```

## Error Handling Patterns

```python
def safe_segment(predictor, image, box, fallback_mask=None):
    """
    Segment with error handling and fallback.
    """
    try:
        predictor.set_image(image)
        masks, scores, _ = predictor.predict(
            box=np.array(box),
            multimask_output=False
        )

        mask = masks[0]

        # Validate mask is not empty
        if not mask.any():
            if fallback_mask is not None:
                return fallback_mask, 0.0
            return None, 0.0

        return mask, scores[0]

    except Exception as e:
        print(f"Segmentation failed: {e}")
        if fallback_mask is not None:
            return fallback_mask, 0.0
        return None, 0.0
```
