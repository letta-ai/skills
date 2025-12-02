# OCR Video Processing Reference

Detailed guidance for preprocessing video frames and optimizing OCR extraction of text-based commands.

## Frame Extraction with FFmpeg

### Basic Extraction

```bash
# Extract at 1 frame per second
ffmpeg -i input.mp4 -vf "fps=1" output/frame_%04d.png

# Extract at 0.5 fps (one frame every 2 seconds)
ffmpeg -i input.mp4 -vf "fps=0.5" output/frame_%04d.png

# Extract specific time range
ffmpeg -i input.mp4 -ss 00:01:00 -to 00:02:00 -vf "fps=1" output/frame_%04d.png
```

### With Cropping (ROI Extraction)

```bash
# Crop to region: width:height:x:y
# Example: Crop bottom 100 pixels of 640x480 video
ffmpeg -i input.mp4 -vf "crop=640:100:0:380,fps=1" output/frame_%04d.png

# Combine crop with scaling for consistent size
ffmpeg -i input.mp4 -vf "crop=640:100:0:380,scale=1280:200,fps=1" output/frame_%04d.png
```

## Image Preprocessing with Python

### Basic Preprocessing Pipeline

```python
import cv2
import numpy as np

def preprocess_for_ocr(image_path):
    """Preprocess image for optimal OCR results."""
    # Load image
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply binary threshold
    # For dark text on light background:
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # For light text on dark background (invert first):
    # _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    return thresh
```

### Adaptive Thresholding

For varying lighting conditions across frames:

```python
def adaptive_preprocess(image_path):
    """Use adaptive thresholding for inconsistent backgrounds."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Adaptive threshold handles varying brightness
    thresh = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,  # Block size (odd number)
        2    # Constant subtracted from mean
    )

    return thresh
```

### Noise Reduction

```python
def denoise_image(img):
    """Apply denoising for cleaner OCR input."""
    # For grayscale images
    denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    return denoised

def morphological_cleanup(thresh):
    """Use morphology to clean up text edges."""
    kernel = np.ones((2, 2), np.uint8)

    # Erosion followed by dilation (opening) removes small noise
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Dilation followed by erosion (closing) fills small gaps
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

    return cleaned
```

### Contrast Enhancement

```python
def enhance_contrast(img):
    """Enhance contrast using CLAHE."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)
    return enhanced
```

## OCR with Tesseract

### Basic Usage

```python
import pytesseract
from PIL import Image

def extract_text(image_path):
    """Extract text from preprocessed image."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text
```

### Optimized Configuration

```python
def extract_text_optimized(image_path):
    """Extract text with optimized Tesseract config."""
    img = Image.open(image_path)

    # Custom configuration
    # --psm 6: Assume uniform block of text
    # --psm 7: Treat image as single text line
    # -c tessedit_char_whitelist: Limit to specific characters

    config = '--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789>., '

    text = pytesseract.image_to_string(img, config=config)
    return text
```

### Page Segmentation Modes (PSM)

Select appropriate PSM for content type:

| PSM | Description | Use Case |
|-----|-------------|----------|
| 3 | Fully automatic (default) | General purpose |
| 6 | Assume uniform block of text | Multiple command lines |
| 7 | Treat as single text line | Single command extraction |
| 11 | Sparse text, no order | Scattered text elements |
| 13 | Raw line, treat as single line | Very simple layouts |

## Command Extraction Patterns

### Identifying Command Prompts

```python
import re

def extract_commands_from_text(ocr_text, prompt_marker='>'):
    """Extract commands following a prompt marker."""
    commands = []

    for line in ocr_text.split('\n'):
        line = line.strip()

        # Look for lines starting with prompt marker
        if line.startswith(prompt_marker):
            # Extract command after prompt
            cmd = line[len(prompt_marker):].strip()
            if cmd:
                commands.append(cmd)

    return commands
```

### Fuzzy Matching for Validation

```python
from difflib import get_close_matches

VALID_COMMANDS = [
    'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw',
    'up', 'down', 'look', 'inventory', 'get', 'take',
    'drop', 'put', 'open', 'close', 'read', 'examine',
    'attack', 'kill', 'light', 'turn', 'move', 'push',
    'pull', 'climb', 'enter', 'exit', 'wait', 'save',
    'restore', 'restart', 'quit', 'score', 'verbose',
    'brief', 'superbrief'
]

def validate_command(cmd, valid_verbs=VALID_COMMANDS, cutoff=0.8):
    """Validate and potentially correct OCR'd command."""
    parts = cmd.lower().split()
    if not parts:
        return None

    verb = parts[0]

    # Check if verb matches or is close to valid command
    if verb in valid_verbs:
        return cmd.lower()

    matches = get_close_matches(verb, valid_verbs, n=1, cutoff=cutoff)
    if matches:
        # Replace with corrected verb
        parts[0] = matches[0]
        return ' '.join(parts)

    return None  # Invalid command
```

### Deduplication

```python
def deduplicate_commands(commands, similarity_threshold=0.85):
    """Remove duplicate and near-duplicate commands."""
    from difflib import SequenceMatcher

    unique = []

    for cmd in commands:
        cmd_normalized = cmd.lower().strip()

        is_duplicate = False
        for existing in unique:
            ratio = SequenceMatcher(None, cmd_normalized, existing).ratio()
            if ratio >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(cmd_normalized)

    return unique
```

## Complete Processing Pipeline Example

```python
import os
import cv2
import pytesseract
from pathlib import Path

def process_video_for_commands(video_path, output_dir, roi=None):
    """
    Complete pipeline for extracting commands from video.

    Args:
        video_path: Path to input video
        output_dir: Directory for intermediate files
        roi: Tuple of (x, y, width, height) for region of interest
    """
    frames_dir = Path(output_dir) / 'frames'
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract frames
    crop_filter = f"crop={roi[2]}:{roi[3]}:{roi[0]}:{roi[1]}," if roi else ""
    os.system(f'ffmpeg -i {video_path} -vf "{crop_filter}fps=1" {frames_dir}/frame_%04d.png')

    # Step 2: Process each frame
    all_commands = []

    for frame_path in sorted(frames_dir.glob('*.png')):
        # Preprocess
        img = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
        _, thresh = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)

        # OCR
        text = pytesseract.image_to_string(thresh, config='--psm 6')

        # Extract commands
        for line in text.split('\n'):
            if line.strip().startswith('>'):
                cmd = line.strip()[1:].strip()
                if cmd:
                    all_commands.append(cmd)

    # Step 3: Deduplicate
    unique_commands = deduplicate_commands(all_commands)

    # Step 4: Validate
    validated = [validate_command(cmd) for cmd in unique_commands]
    validated = [cmd for cmd in validated if cmd]

    return validated
```

## Troubleshooting

### Poor OCR Accuracy

1. **Check image resolution**: Scale up small text regions
2. **Adjust threshold values**: Experiment with different threshold levels
3. **Try different PSM modes**: Match mode to content layout
4. **Consider character whitelist**: Limit to expected character set

### Missing Commands

1. **Increase frame extraction rate**: Commands may appear between samples
2. **Check ROI boundaries**: Ensure entire command area is captured
3. **Verify prompt detection**: Confirm prompt marker is being recognized

### Too Many Duplicates

1. **Adjust similarity threshold**: Lower threshold for stricter matching
2. **Normalize before comparison**: Consistent case and whitespace handling
3. **Consider sequential dedup**: Only remove adjacent duplicates

### Processing Too Slow

1. **Reduce frame count**: Lower fps extraction rate
2. **Crop to ROI**: Process only relevant screen region
3. **Batch processing**: Process multiple frames in parallel
4. **Use appropriate image format**: PNG for quality, JPG for speed
