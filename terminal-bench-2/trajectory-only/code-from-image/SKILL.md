---
name: code-from-image
description: Extracting code or pseudocode from images using OCR, then interpreting and implementing it. This skill should be used when tasks involve reading code, pseudocode, or algorithms from image files (PNG, JPG, screenshots) and converting them to executable code. Applies to OCR-based code extraction, image-to-code conversion, and implementing algorithms shown in visual formats.
---

# Code From Image

## Overview

Extract code, pseudocode, or algorithmic descriptions from images using OCR tools, then interpret and implement the extracted content as working code. This skill addresses the challenges of noisy OCR output, ambiguous character recognition, and verification of implementation correctness.

## Workflow

### Phase 1: Environment Setup

Before attempting OCR extraction:

1. **Install OCR dependencies** - Ensure tesseract and Python bindings are available:
   ```bash
   # Check for existing tools
   which tesseract
   # Install if needed
   apt-get install tesseract-ocr  # or equivalent for the system
   pip install pytesseract pillow
   ```

2. **Install image processing tools** - For preprocessing capabilities:
   ```bash
   pip install opencv-python
   # ImageMagick for command-line preprocessing
   apt-get install imagemagick
   ```

### Phase 2: Image Preprocessing

Raw OCR on unprocessed images often produces noisy output. Apply preprocessing to improve accuracy:

1. **Assess image quality** - Check contrast, resolution, and clarity before OCR
2. **Apply preprocessing techniques**:
   - Convert to grayscale
   - Increase contrast
   - Apply thresholding (binary or adaptive)
   - Resize if resolution is low
   - Denoise if needed

Example preprocessing pipeline:
```python
import cv2
from PIL import Image

# Load and preprocess
img = cv2.imread('code_image.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# Increase contrast
contrast = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
# Apply threshold
_, thresh = cv2.threshold(contrast, 127, 255, cv2.THRESH_BINARY)
# Save preprocessed image
cv2.imwrite('preprocessed.png', thresh)
```

3. **Try multiple preprocessing configurations** - Different images respond better to different techniques

### Phase 3: OCR Extraction

1. **Run OCR with multiple configurations**:
   ```python
   import pytesseract
   from PIL import Image

   # Try different PSM modes for code-like content
   # PSM 6: Assume uniform block of text
   # PSM 4: Assume single column of variable sizes
   text_psm6 = pytesseract.image_to_string(Image.open('preprocessed.png'), config='--psm 6')
   text_psm4 = pytesseract.image_to_string(Image.open('preprocessed.png'), config='--psm 4')
   ```

2. **Compare outputs** - Different configurations may capture different parts correctly

3. **Document raw OCR output** - Keep the original OCR text for reference when making interpretations

### Phase 4: Interpreting Noisy OCR Output

OCR output from code images is frequently corrupted. Apply systematic interpretation:

1. **Identify common OCR errors**:
   - `0` (zero) ↔ `O` (letter O)
   - `1` (one) ↔ `l` (lowercase L) ↔ `I` (uppercase i)
   - `6` appearing before text (often a misread character)
   - Missing or extra spaces
   - Special characters corrupted (`=` → `-`, `"` → `'`, etc.)
   - Variable names partially corrupted

2. **Document all assumptions** - When interpreting ambiguous OCR:
   - State what the OCR produced
   - State what interpretation is being made
   - Explain the reasoning

3. **Look for structural patterns**:
   - Assignment statements (look for `=` patterns)
   - Function calls (parentheses patterns)
   - Loop structures (indentation, keywords)
   - Common programming constructs

4. **Cross-reference with context**:
   - Variable naming conventions
   - Expected operations based on the task
   - Programming language syntax rules

### Phase 5: Implementation with Verification

When a verification hint or expected output is available:

1. **Implement the interpreted code**

2. **Test against expected output** - If a hint like "output starts with X" is provided:
   - Run the implementation
   - Check if output matches the hint
   - If not, revisit interpretations

3. **Try alternative interpretations systematically**:
   - When initial implementation fails verification
   - Create a list of ambiguous interpretations
   - Test each alternative methodically
   - Example alternatives to consider:
     - String encoding (bytes vs string)
     - Slice notation (characters vs bytes, 0-indexed vs 1-indexed)
     - Concatenation order
     - Hash output format (hex digest vs raw digest)

4. **Document the working interpretation** - Once verified, explain which interpretation worked and why

## Common Pitfalls

### OCR Quality Issues
- **Mistake**: Accepting noisy OCR output without improvement attempts
- **Solution**: Always try image preprocessing before OCR; compare multiple OCR configurations

### Undocumented Assumptions
- **Mistake**: Making silent assumptions about corrupted characters
- **Solution**: Explicitly document each interpretation decision with reasoning

### Single Interpretation Fixation
- **Mistake**: Committing to one interpretation without exploring alternatives
- **Solution**: When verification fails, systematically test alternative readings of ambiguous text

### Missing Edge Case Considerations
- **Mistake**: Not considering encoding, indexing, or format variations
- **Solution**: When working with:
  - Strings: Consider bytes vs unicode, encoding schemes
  - Slices: Consider byte slices vs character slices, hex vs raw
  - Hashes: Consider digest() vs hexdigest(), truncation points

### Inefficient Tool Setup
- **Mistake**: Installing tools one at a time, checking availability repeatedly
- **Solution**: Consolidate tool checks and installations at the start

## Verification Strategies

1. **Use hints strategically** - If output hints are provided, use them to validate interpretations early, not just for final verification

2. **Test intermediate results** - For multi-step algorithms, verify intermediate values when possible

3. **Compare multiple OCR outputs** - Run OCR with different settings and compare results to identify reliable vs uncertain portions

4. **Sanity check interpretations** - Does the interpreted code make logical sense? Are variable names reasonable? Is the algorithm plausible?

## Resources

Refer to `references/ocr_best_practices.md` for detailed guidance on OCR configuration options and image preprocessing techniques.
