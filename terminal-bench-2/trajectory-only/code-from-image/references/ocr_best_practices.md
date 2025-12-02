# OCR Best Practices for Code Extraction

## Tesseract Configuration Options

### Page Segmentation Modes (PSM)

Tesseract's PSM setting controls how it segments the image into text blocks. For code images:

| PSM | Description | Best For |
|-----|-------------|----------|
| 3 | Fully automatic page segmentation (default) | General documents |
| 4 | Single column of variable text sizes | Code with comments |
| 6 | Single uniform block of text | Clean code blocks |
| 11 | Sparse text without order | Diagrams with labels |
| 12 | Sparse text with OSD | Mixed content |

Usage:
```python
pytesseract.image_to_string(image, config='--psm 6')
```

### OCR Engine Mode (OEM)

| OEM | Description |
|-----|-------------|
| 0 | Legacy engine only |
| 1 | Neural nets LSTM only |
| 2 | Legacy + LSTM |
| 3 | Default (based on availability) |

For code recognition, LSTM (OEM 1) often performs better:
```python
pytesseract.image_to_string(image, config='--oem 1 --psm 6')
```

### Character Whitelisting

For code with known character sets:
```python
# Allow only alphanumeric, common code symbols
config = '-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_=()[]{}:;,.+-*/<>!@#$%^&|~`"\' '
pytesseract.image_to_string(image, config=config)
```

## Image Preprocessing Techniques

### Grayscale Conversion

Always start with grayscale:
```python
import cv2
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

### Contrast Enhancement

#### Simple Contrast Adjustment
```python
# alpha > 1 increases contrast, beta adjusts brightness
enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=10)
```

#### CLAHE (Adaptive Histogram Equalization)
Better for uneven lighting:
```python
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
```

### Thresholding

#### Binary Threshold
Good for clean, high-contrast images:
```python
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
```

#### Otsu's Threshold
Automatically determines optimal threshold:
```python
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
```

#### Adaptive Threshold
Best for images with varying illumination:
```python
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
```

### Noise Reduction

#### Gaussian Blur (before thresholding)
```python
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
```

#### Morphological Operations (after thresholding)
```python
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
# Remove small noise
cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
# Fill small gaps
cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
```

### Resolution Scaling

Low-resolution images benefit from upscaling:
```python
# Scale up by 2x using bicubic interpolation
scaled = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
```

### Deskewing

For slightly rotated images:
```python
import numpy as np

def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated
```

## Complete Preprocessing Pipeline

A robust pipeline that tries multiple approaches:

```python
import cv2
import pytesseract
from PIL import Image
import numpy as np

def preprocess_for_ocr(image_path):
    """Try multiple preprocessing approaches and return results."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    results = {}

    # Approach 1: Simple threshold
    _, thresh1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    results['simple_threshold'] = thresh1

    # Approach 2: Otsu threshold
    _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results['otsu'] = thresh2

    # Approach 3: Adaptive threshold
    thresh3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    results['adaptive'] = thresh3

    # Approach 4: Contrast + Otsu
    contrast = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    _, thresh4 = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results['contrast_otsu'] = thresh4

    # Approach 5: Scaled up + Otsu
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh5 = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results['scaled_otsu'] = thresh5

    return results

def ocr_with_multiple_configs(image):
    """Run OCR with multiple configurations."""
    configs = [
        '--psm 6 --oem 1',
        '--psm 4 --oem 1',
        '--psm 6 --oem 3',
        '--psm 3 --oem 1',
    ]

    results = {}
    for config in configs:
        text = pytesseract.image_to_string(Image.fromarray(image), config=config)
        results[config] = text

    return results

def extract_code_from_image(image_path):
    """Full pipeline: preprocess and OCR with multiple approaches."""
    preprocessed = preprocess_for_ocr(image_path)

    all_results = {}
    for preprocess_name, image in preprocessed.items():
        ocr_results = ocr_with_multiple_configs(image)
        for config, text in ocr_results.items():
            key = f"{preprocess_name}_{config}"
            all_results[key] = text

    return all_results
```

## Common OCR Errors in Code

### Character Confusion Matrix

| Actual | Often Misread As |
|--------|------------------|
| `0` (zero) | `O`, `o`, `Q` |
| `1` (one) | `l`, `I`, `i`, `|` |
| `l` (ell) | `1`, `I`, `|` |
| `O` (oh) | `0`, `Q` |
| `=` | `-`, `—`, `_` |
| `"` | `"`, `''`, `` ` `` |
| `'` | `` ` ``, `'` |
| `_` | `-`, `—` |
| `(` | `{`, `[` |
| `)` | `}`, `]` |
| `:` | `;` |
| `.` | `,` |

### Common Code-Specific Errors

1. **Leading garbage characters**: Random characters before valid text (e.g., `6"` before a string)
2. **Merged lines**: Two lines of code merged into one
3. **Split tokens**: Single identifiers split into multiple words
4. **Lost indentation**: Whitespace not preserved
5. **Operator corruption**: `==` becoming `=`, `!=` becoming `!-` or `=`

### Resolution Strategies

1. **Compare multiple OCR outputs** to identify consistent vs unreliable portions
2. **Use context** - if surrounding code suggests a variable name, trust that pattern
3. **Apply syntax knowledge** - `if` won't be followed by `{` in Python
4. **Look for semantic meaning** - `SALT` makes more sense than `GALT` in cryptographic code
