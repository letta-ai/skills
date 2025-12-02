---
name: extract-moves-from-video
description: Guidance for extracting text-based game commands, moves, or inputs from video recordings using OCR and frame analysis. This skill applies when extracting user inputs from screen recordings of text-based games (Zork, interactive fiction), terminal sessions, or any video where typed commands need to be recovered. It covers OCR preprocessing, region-of-interest extraction, domain-aware validation, and deduplication strategies.
---

# Extract Moves from Video

This skill provides structured guidance for extracting text-based commands or moves from video recordings, particularly for text-based games, terminal sessions, or any screen recording where typed inputs need to be recovered.

## When to Use This Skill

This skill applies when:
- Extracting game commands from recordings of text-based games (Zork, interactive fiction, MUDs)
- Recovering typed inputs from terminal session recordings
- Extracting user commands from any screen recording where text input is visible
- OCR-based extraction of sequential text entries from video

## Strategic Approach

### Phase 1: Environment Assessment

Before processing, assess the available tools and estimate resource requirements:

1. **Check available tools in one comprehensive sweep:**
   - FFmpeg for frame extraction
   - OCR engines (tesseract, pytesseract)
   - Image processing libraries (opencv-python, Pillow)
   - Python environment and package managers (pip, uv, conda)

2. **Analyze video characteristics:**
   - Duration and frame rate
   - Resolution and text clarity
   - Location of command input area (typically fixed position)
   - Text color contrast against background

3. **Estimate processing time:**
   - Benchmark OCR on 3-5 sample frames before full processing
   - Calculate expected total time based on frame count and benchmark

### Phase 2: Region of Interest (ROI) Identification

**Critical optimization**: Identify and crop to the command input region before OCR.

For text-based games like Zork:
- Command input typically appears at a fixed screen location (often bottom)
- Command prompts have consistent markers (e.g., `>` prefix)
- Cropping to ROI dramatically improves OCR accuracy and speed

To identify the ROI:
1. Extract a few sample frames where commands are visible
2. Manually or programmatically identify the bounding box of the input area
3. Apply consistent cropping to all frames before OCR

### Phase 3: Frame Extraction Strategy

Select frame extraction rate based on content characteristics:

- **Text-based games**: Commands persist on screen for seconds; 1-3 second intervals typically suffice
- **Fast-paced inputs**: May require higher frequency (0.5 second intervals)
- **Start conservative**: Begin with lower frequency, increase only if commands are missed

```bash
# Example: Extract frames at 1 frame per second
ffmpeg -i video.mp4 -vf "fps=1" frames/frame_%04d.png
```

### Phase 4: OCR Preprocessing

Apply preprocessing to improve OCR accuracy:

1. **Convert to grayscale**
2. **Apply thresholding** (binary threshold for high contrast text)
3. **Consider additional techniques if needed:**
   - Contrast enhancement
   - Noise reduction
   - Dilation/erosion for text clarity
   - Inversion if text is light on dark background

See `references/ocr_video_processing.md` for detailed preprocessing techniques.

### Phase 5: Domain-Aware Extraction and Validation

**Key insight**: Use domain knowledge to validate and correct OCR results.

For text-based games:
1. Obtain or construct a list of valid commands for the game
2. Use command vocabulary for spell-checking OCR output
3. Identify command syntax patterns (e.g., `VERB NOUN`, `DIRECTION`)
4. Flag entries that don't match known patterns for manual review

Common Zork-style commands include:
- Directions: n, s, e, w, ne, nw, se, sw, up, down
- Actions: get, take, drop, put, open, close, read, examine, look, inventory
- Combinations: `get lamp`, `put sword in case`, `open mailbox`

### Phase 6: Deduplication and Cleaning

Handle duplicates arising from:
- Same command captured across multiple frames
- OCR variations of the same command (e.g., "get lamp" vs "get 1amp")

Deduplication strategy:
1. Normalize whitespace and case
2. Use fuzzy matching to group similar entries
3. When OCR variations exist, prefer the version matching known vocabulary
4. Remove incomplete/partial commands (single letters that aren't valid directions)

### Phase 7: Validation

Before finalizing, validate the extracted command list:

1. **Syntax validation**: Verify commands match expected patterns
2. **Sequence plausibility**: Check that command order makes logical sense
3. **Coverage check**: Estimate if extracted count matches expected (based on video length)
4. **Interpreter testing** (if available): Run commands through a game interpreter to verify validity

## Common Pitfalls

1. **Skipping ROI extraction**: Processing full frames wastes time and reduces accuracy
2. **Inadequate preprocessing**: Raw frames often need contrast/threshold adjustments
3. **Ignoring domain knowledge**: Valid command vocabulary enables validation and correction
4. **Ad-hoc cleaning scripts**: Design one robust cleaning pipeline rather than multiple iterations
5. **No early validation**: Test on sample frames before processing entire video
6. **Timeout misestimation**: Benchmark before committing to full processing
7. **Capturing game output as commands**: Filter to only lines with command prompt markers

## Verification Checklist

- [ ] ROI identified and applied to frame extraction
- [ ] Preprocessing parameters tested on sample frames
- [ ] OCR benchmarked for time estimation
- [ ] Domain vocabulary used for validation
- [ ] Duplicates and near-duplicates removed
- [ ] Output validated against expected command syntax
- [ ] Command count reasonable for video duration
