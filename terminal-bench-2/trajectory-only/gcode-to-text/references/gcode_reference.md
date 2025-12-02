# G-code Reference for Text Extraction

This reference covers G-code commands and patterns relevant to extracting text content from G-code files.

## Core Movement Commands

### G0 - Rapid Move (Travel)
Non-printing movement, used to reposition between printing locations.
```
G0 X100 Y50 F3000    ; Move to X=100, Y=50 at 3000mm/min
G0 Z5                 ; Raise Z to 5mm
```
**For text extraction**: G0 moves indicate transitions between strokes or letters. A sequence of G0 moves often marks letter boundaries.

### G1 - Linear Move (Print/Cut)
Controlled movement, typically with extrusion or cutting.
```
G1 X110 Y50 E1.5 F1200    ; Move while extruding
G1 X110 Y60               ; Continue at same speed
```
**For text extraction**: G1 moves with positive E values are the actual printed strokes. These coordinates form the letter shapes.

### G2/G3 - Arc Moves
Clockwise (G2) and counter-clockwise (G3) arcs.
```
G2 X10 Y5 I5 J0     ; Clockwise arc, I/J are center offsets
G3 X10 Y5 R5        ; Counter-clockwise arc, R is radius
```
**For text extraction**: Common in curved letters (O, C, S, etc.). The start/end points plus I/J or R define the arc.

## Key Parameters

| Parameter | Meaning | Relevance to Text |
|-----------|---------|-------------------|
| X, Y | Position coordinates | Define letter geometry |
| Z | Height | Layer changes, not usually relevant for single-layer text |
| E | Extrusion amount | Positive = printing, negative/zero = travel |
| F | Feed rate (speed) | May differ between outline and infill |

## Section Markers

### Comments
```
; TYPE:Embossed text
; printing "Hello"
; LAYER:1
```

### M486 Object Labels (PrusaSlicer/SuperSlicer)
```
M486 S0         ; Start object 0
M486 A"Text"    ; Object 0 named "Text"
M486 S-1        ; End current object
```
**Note**: Object names in M486 are labels chosen by the user, not the actual text content.

### Marlin/Other Dialects
```
;MESH:text_object
;TYPE:WALL-OUTER
```

## Patterns for Text Identification

### Finding Text Sections
Search patterns (case-insensitive):
```
; TYPE:.*text
M486.*text
;MESH:.*text
; (emboss|engrav|letter)
```

### Identifying Letter Boundaries
1. **Z-hop or travel moves**: G0 commands between extrusion sequences
2. **Discontinuous X coordinates**: Gaps in X progression
3. **E retractions**: Negative E followed by G0 travel

Example letter transition:
```
G1 X10.5 Y20.1 E0.5    ; End of letter 'A'
G1 E-0.8               ; Retract
G0 Z0.4                ; Z-hop
G0 X12.0 Y18.5         ; Travel to letter 'B'
G0 Z0.2                ; Lower
G1 E0.8                ; Un-retract
G1 X12.0 Y22.0 E0.5    ; Start of letter 'B'
```

## Coordinate Analysis Techniques

### Bounding Box Per Segment
For each continuous extrusion segment, calculate:
- X_min, X_max, Y_min, Y_max
- Width = X_max - X_min
- Height = Y_max - Y_min

Letters typically have consistent heights and varying widths.

### X-Position Clustering
Text is typically printed left-to-right. Cluster coordinates by X-position to identify:
- Number of letters (count of clusters)
- Letter spacing (gaps between clusters)
- Individual letter widths

### Path Density Analysis
Text regions have high coordinate density compared to:
- Infill patterns (regular, repetitive)
- Perimeters (simple outlines)
- Travel moves (sparse, rapid)

## Common Slicer Behaviors

### PrusaSlicer
- Uses M486 for object labeling
- Comments prefixed with `; `
- TYPE comments for feature identification

### Cura
- Uses `;TYPE:` comments
- `;MESH:` for object names
- `;TIME_ELAPSED:` markers

### OrcaSlicer / BambuStudio
- Similar to PrusaSlicer
- May include additional metadata

## Debugging Tips

1. **Extract just coordinates**: Focus on X/Y values in G1 commands with E > 0
2. **Plot incrementally**: Visualize small sections to verify correct parsing
3. **Check coordinate scale**: Typical text might span 20-100mm in X
4. **Verify orientation**: Some G-code may have rotated or mirrored text
5. **Consider multiple layers**: Embossed text may be built up over several Z layers
