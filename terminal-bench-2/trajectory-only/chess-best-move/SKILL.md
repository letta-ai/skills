---
name: chess-best-move
description: Guide for analyzing chess positions from images and determining optimal moves. This skill should be used when asked to find the best move, checkmate, or tactical solution from a chess board image. It provides structured approaches for image-based chess analysis, piece detection calibration, position validation, and move verification.
---

# Chess Best Move

## Overview

This skill provides guidance for analyzing chess positions from images and determining the best move. It covers image processing techniques for detecting pieces, validating detected positions, and verifying candidate moves using chess engines.

## Critical Success Factors

Before attempting any chess image analysis:

1. **Calibrate first** - Identify exact RGB values of board squares and piece colors from the actual image
2. **Validate always** - Verify detected positions have exactly 2 kings and ≤16 pieces per side
3. **Debug incrementally** - Print visual representations square by square to verify detection
4. **Never guess** - If detection fails, acknowledge uncertainty rather than presenting unreliable results

## Workflow

### Phase 1: Image Calibration

Before attempting piece detection, calibrate against the actual image:

1. **Sample board square colors**
   - Extract RGB values from known light squares (e.g., a1 if white, or h1 if black)
   - Extract RGB values from known dark squares
   - Document the exact color palette for this specific board style

2. **Identify piece color signatures**
   - Find a clearly visible white piece and sample its colors
   - Find a clearly visible black piece and sample its colors
   - Note: Piece colors may differ significantly from board square colors

3. **Check for metadata**
   - Look for FEN notation in image metadata
   - Check for coordinate annotations that could assist analysis

### Phase 2: Position Detection

Apply structured detection with validation at each step:

1. **Grid detection**
   - Identify board boundaries (may not be full image)
   - Calculate square dimensions from detected boundaries
   - Verify 8x8 grid alignment

2. **Square-by-square analysis**
   - For each square, determine if occupied
   - Use calibrated thresholds from Phase 1
   - Output detection results in human-readable format for debugging

3. **Immediate validation checks**
   - Total pieces must be ≤32
   - White pieces must be ≤16
   - Black pieces must be ≤16
   - Exactly 1 white king and 1 black king
   - If any check fails, detection is incorrect - do not proceed

### Phase 3: Position Validation

After detection, validate the position is legal:

```python
def validate_position(board):
    """
    Validate a detected chess position.
    Returns (is_valid, errors) tuple.
    """
    errors = []

    # Count pieces
    white_kings = count_pieces(board, 'K')
    black_kings = count_pieces(board, 'k')
    white_pieces = count_all_white(board)
    black_pieces = count_all_black(board)

    # Validation rules
    if white_kings != 1:
        errors.append(f"Invalid: {white_kings} white kings (must be 1)")
    if black_kings != 1:
        errors.append(f"Invalid: {black_kings} black kings (must be 1)")
    if white_pieces > 16:
        errors.append(f"Invalid: {white_pieces} white pieces (max 16)")
    if black_pieces > 16:
        errors.append(f"Invalid: {black_pieces} black pieces (max 16)")
    if white_pieces + black_pieces > 32:
        errors.append(f"Invalid: {white_pieces + black_pieces} total pieces (max 32)")

    # Check pawn counts
    white_pawns = count_pieces(board, 'P')
    black_pawns = count_pieces(board, 'p')
    if white_pawns > 8:
        errors.append(f"Invalid: {white_pawns} white pawns (max 8)")
    if black_pawns > 8:
        errors.append(f"Invalid: {black_pawns} black pawns (max 8)")

    return len(errors) == 0, errors
```

### Phase 4: Move Analysis

Once position is validated, analyze for best move:

1. **Use a chess engine**
   - Load position into python-chess library
   - Use Stockfish or similar engine for analysis
   - Do not rely on pattern matching against famous puzzles

2. **Consider the task requirements**
   - Is there a forced checkmate?
   - Are multiple winning moves acceptable?
   - What is the time control (depth of analysis needed)?

3. **Verify the move**
   - Confirm the move is legal in the position
   - If checkmate is claimed, verify it leads to checkmate
   - Output move in requested notation (algebraic, UCI, etc.)

## Common Pitfalls

### Detection Failures

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Too many pieces detected (>32) | Detecting board squares as pieces | Recalibrate piece color thresholds |
| All light squares detected as white pieces | Threshold too low | Sample actual piece colors, not square colors |
| Inconsistent results across runs | Arbitrary threshold values | Use calibrated values from actual image |
| Wrong piece types | Color confusion | Separate detection of color vs piece type |

### Logic Errors

- **Circular reasoning**: Do not conclude position identity from partial matches
- **Overconfidence in guessing**: A 55% match is not reliable evidence
- **Ignoring validation failures**: If piece counts are wrong, detection is wrong

### Board Orientation

- Standard view: White pieces at bottom (ranks 1-2), Black at top (ranks 7-8)
- Check if board might be from Black's perspective (rotated 180°)
- Look for coordinate labels (a-h, 1-8) to confirm orientation

## Verification Checklist

Before submitting a solution, verify:

- [ ] Calibration was performed on the actual image
- [ ] Position passes all validation checks
- [ ] Exactly 2 kings detected (one per side)
- [ ] Total pieces ≤32
- [ ] Move was verified as legal using chess library
- [ ] If checkmate claimed, forced mate sequence was verified
- [ ] Uncertainty is acknowledged if detection was unreliable

## When Detection Fails

If position cannot be reliably detected:

1. **Acknowledge the limitation** - Do not present a guess as confident answer
2. **Explain what failed** - Which validation checks failed?
3. **Suggest alternatives**:
   - Ask user to provide FEN notation
   - Ask user to describe the position
   - Try different image processing approach
4. **Never resort to guessing** - Matching against famous puzzle databases is not solving the image analysis problem

## Resources

### References

- `references/chess_image_analysis.md` - Detailed guide for chess image processing techniques

### Scripts

- `scripts/validate_position.py` - Position validation utility
