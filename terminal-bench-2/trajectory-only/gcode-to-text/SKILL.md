---
name: gcode-to-text
description: Decode and interpret text content from G-code files by analyzing toolpath geometry and coordinate patterns. This skill should be used when extracting text, letters, or symbols that are encoded as movement commands in G-code files (e.g., 3D printing, CNC engraving, laser cutting). Applies to tasks like identifying what text a G-code file will print/engrave, reverse-engineering embossed or engraved text from toolpaths, or visualizing G-code geometry to reveal hidden content.
---

# G-code to Text Interpretation

## Overview

G-code files encode geometry as movement commands (X, Y, Z coordinates) rather than explicit text labels. When text is printed, engraved, or cut, the letter shapes exist only as coordinate sequences tracing their outlines. This skill provides strategies for extracting and interpreting text content from G-code by analyzing the geometric data itself.

## Critical Understanding

**G-code IS the content** - The text being printed/engraved is fully defined by the coordinate movements. There is no separate "text field" to extract. The challenge is transforming coordinate data back into recognizable letter shapes.

**Metadata is unreliable** - Filenames, comments, and labels (like M486 object names) may hint at content but are not authoritative. The actual geometric data is the source of truth.

**Avoid circular reasoning** - Never conclude that the printed text equals the filename (e.g., assuming "text.gcode" prints "text"). This is a common pitfall.

## Approach: Geometric Analysis

### Step 1: Identify Relevant Coordinate Sections

Locate the G-code sections that produce the text content:

1. Search for object labels or comments indicating text segments (e.g., `M486 S0` for "Embossed text")
2. Identify the coordinate commands (G0/G1 moves) within those sections
3. Extract X and Y coordinates for analysis

Example patterns to search:
```
; TYPE:.*[Tt]ext
M486.*[Tt]ext
; printing.*text
```

### Step 2: Extract and Visualize Coordinates

Transform coordinate data into a visual representation:

**Option A: Plot coordinates programmatically**
```python
import matplotlib.pyplot as plt

# Extract X,Y coordinates from G-code
x_coords = []
y_coords = []
# Parse G1 X... Y... commands and populate lists

plt.figure(figsize=(12, 4))
plt.plot(x_coords, y_coords, 'b-', linewidth=0.5)
plt.axis('equal')
plt.savefig('toolpath.png')
```

**Option B: ASCII art visualization**
For simpler cases, bin coordinates into a character grid:
```python
# Create a 2D grid and mark visited positions
# Print as ASCII characters to reveal letter shapes
```

**Option C: Analyze coordinate clusters**
Group coordinates by X-position ranges to identify individual letters.

### Step 3: Interpret Letter Shapes

Once visualized:
- Letters appear as distinct connected shapes
- Each letter typically occupies a separate X-coordinate range
- Compare shapes against known letter patterns
- Count distinct shapes to estimate word length

### Step 4: Validate Interpretation

Cross-check findings:
- Do the identified letters form a coherent word?
- Does the letter count match visible clusters?
- Are letter proportions consistent with typical fonts?

## Common Pitfalls

| Pitfall | Why It Fails | Better Approach |
|---------|--------------|-----------------|
| Inferring text from filename | Filename is arbitrary metadata | Analyze actual coordinates |
| Searching only for metadata/comments | Text is encoded in geometry, not labels | Parse and visualize coordinates |
| Concluding "cannot determine" without geometric analysis | The answer exists in the data | Attempt visualization or clustering |
| Over-relying on M486 labels | Labels describe sections, not content | Use labels to locate sections, then analyze geometry |

## Verification Strategies

1. **Visual confirmation**: Plot the toolpath - letters should be recognizable
2. **Bounding box analysis**: Each letter has a distinct X-range
3. **Path continuity**: Letters are typically drawn with connected strokes
4. **Coordinate density**: Text areas have higher coordinate density than travel moves

## When Direct Visualization Fails

If plotting tools are unavailable:

1. **Statistical analysis**: Calculate X-coordinate distribution to count letter clusters
2. **Bounding box extraction**: Find min/max X/Y for each continuous segment
3. **Segment length analysis**: Letters have characteristic path lengths
4. **Compare to known patterns**: If partial letters are visible, infer remaining content

## Key G-code Commands Reference

| Command | Purpose |
|---------|---------|
| G0 | Rapid move (travel, not printing) |
| G1 | Linear move (printing/cutting) |
| G2/G3 | Arc moves (curved letters) |
| M486 | Object labeling (slicer-dependent) |
| E parameter | Extrusion amount (positive = printing) |

## Decision Tree

```
Task: Extract text from G-code
│
├─ Is there explicit text metadata?
│   ├─ Yes → Use as hint only, verify with geometry
│   └─ No → Proceed directly to geometric analysis
│
├─ Can coordinates be extracted and plotted?
│   ├─ Yes → Visualize and interpret letter shapes
│   └─ No → Use statistical/clustering analysis
│
└─ Is the result ambiguous?
    ├─ Yes → Try multiple visualization methods
    └─ No → Report findings with confidence level
```

## Resources

### scripts/

This skill includes helper scripts for G-code analysis:
- `extract_coordinates.py` - Parse G-code and extract X/Y coordinate sequences
- `visualize_toolpath.py` - Generate visual plots of G-code geometry

### references/

- `gcode_reference.md` - Comprehensive G-code command reference
