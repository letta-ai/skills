---
name: regex-chess
description: Guidance for implementing chess move generation using only regular expressions. This skill applies to tasks requiring encoding game logic (chess, board games) into regex patterns, or more generally "compile-to-constraints" problems where complex business logic must be expressed in a limited formalism like regex. Use when the task involves generating legal moves, validating game states, or transforming position representations using pattern matching.
---

# Regex Chess

## Overview

This skill provides methodology for implementing chess move generation using regular expressions. The core challenge is encoding chess rules—piece movement, captures, special moves, and legality checking—entirely within regex pattern matching and substitution.

This belongs to a class of "compile-to-constraints" problems where business logic must be expressed in a limited formalism. Success requires understanding the target formalism's limitations, systematic decomposition, and incremental verification.

## Critical Prerequisites

Before writing any patterns:

### 1. Document the Transformation Pipeline

Create a clear specification of the exact string format at each transformation stage:

```
Stage 1: Raw FEN input
Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

Stage 2: After digit expansion (8 → ........)
Example: "rnbqkbnr/pppppppp/......../......../......../......../PPPPPPPP/RNBQKBNR w KQkq -"

Stage 3: After coordinate labeling (each square gets rank/file)
Example: "[a8:r][b8:n][c8:b]... [a1:R][b1:N]..."

Stage 4: After move applied
Example: "[a8:r][b8:n]... [a3:.][a4:P]..."

Stage 5: Final FEN output
Example: "rnbqkbnr/pppppppp/8/8/P7/8/1PPPPPPP/RNBQKBNR b KQkq a3 0 1"
```

### 2. Establish Coordinate Ordering

Determine definitively which squares come first in the string representation. In standard FEN:
- Rank 8 (black's back rank) comes before rank 1
- File 'a' comes before file 'h'
- So a8 < b8 < ... < h8 < a7 < ... < h1

This ordering affects every pattern that references two squares (moves, captures, sliding pieces).

### 3. Identify All Move Categories

Enumerate all move types that need patterns:
- Pawn single push (white: rank 2-6, black: rank 7-3)
- Pawn double push from starting rank (sets en passant square)
- Pawn captures (diagonal, including en passant)
- Pawn promotion (4 piece types × captures + pushes)
- Knight moves (8 directions from each square)
- Bishop/Rook/Queen sliding moves (with blocking detection)
- King single-step moves (8 directions)
- Castling (kingside and queenside, both colors)
- Move legality (king not in check after move)

## Recommended Approach

### Phase 1: Design Before Code

Spend significant time designing the architecture before writing patterns:

1. **Choose a string representation** that makes pattern matching tractable
2. **Document the representation** with concrete examples for each transformation
3. **Verify coordinate ordering** with a simple test case
4. **Decide how to handle blocking** for sliding pieces (bishops, rooks, queens)

### Phase 2: Incremental Development

Build and verify one piece type at a time:

1. Start with the simplest case: pawn single push (e.g., a2 to a3)
2. Write ONE pattern for this specific move
3. Test it works in isolation before generating more
4. Add complexity incrementally: other pawns, then captures, then other pieces

### Phase 3: Test-Driven Pattern Generation

For each piece type:

```
1. Write a single hardcoded pattern for one move
2. Verify it matches correctly on a test position
3. Verify it produces correct output
4. Only then generalize to generate all moves of that type
5. Test the full set before moving to next piece type
```

### Phase 4: Handle Special Cases

Only after basic moves work:
- En passant (requires tracking en passant square in FEN)
- Castling (requires checking castling rights, path clear, not through check)
- Promotion (requires different replacement patterns for each piece type)
- Move legality (filter moves where king ends in check)

## Common Pitfalls

### String Ordering Confusion

The most common bug is getting coordinate ordering wrong. If pattern expects source before destination but the string has them reversed, nothing will match.

**Prevention:** Write a helper function to determine ordering, test it explicitly:
```python
def square_comes_before(sq1, sq2):
    """Return True if sq1 appears before sq2 in the FEN string."""
    # Implement based on your coordinate system
    # TEST THIS FUNCTION IN ISOLATION
```

### Digit Expansion Timing

FEN uses digits for empty squares (e.g., "8" means 8 empty squares). Expanding these digits must happen at the right time:
- Expand AFTER removing move counters (or "0 1" becomes "0 .")
- Track which transformation stage each operation belongs to

### Escaping Across Languages

When patterns flow through multiple languages (Python generator → JSON → regex engine):
- Raw strings (`r''`) in Python
- JSON escaping for special characters
- Regex escaping for metacharacters

**Prevention:** Print patterns at each stage to verify escaping is correct.

### Generating Too Many Patterns at Once

Generating thousands of patterns before testing any is a recipe for debugging nightmares.

**Prevention:** Test individual patterns first. A single working pawn move is worth more than 10,000 broken patterns.

### Missing Trailing/Leading Characters

Off-by-one errors in pattern boundaries cause silent failures:
- Missing space after piece: "RNBQKBNRw" instead of "RNBQKBNR w"
- Missing separator between coordinates

**Prevention:** Include boundary markers in test assertions.

### Ignoring Move Legality

Generating pseudo-legal moves (moves that follow piece movement rules) is much easier than generating legal moves (moves that don't leave king in check). Plan for this from the start.

## Verification Strategy

### Unit Tests for Helpers

Test coordinate functions, ordering functions, and FEN parsing in isolation:
```python
assert square_index('a8') == 0
assert square_index('h1') == 63
assert square_comes_before('a8', 'h8') == True
assert square_comes_before('a1', 'a8') == False
```

### Single-Move Tests

Before bulk generation, verify specific moves:
```python
# Test: White pawn a2 to a3
input_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
result = apply_move(input_fen, "a2a3")
expected = "rnbqkbnr/pppppppp/8/8/8/P7/1PPPPPPP/RNBQKBNR b KQkq - 0 1"
assert result == expected
```

### Automated Test Loop

Create a script that regenerates patterns and runs all tests in one command:
```bash
#!/bin/bash
python generate_patterns.py && python run_tests.py
```

### Debug Pattern Matching

When patterns don't match, add debug output showing:
- The exact input string
- The pattern being applied
- Expected match location
- Actual match result

## Resources

See `references/compile_to_constraints.md` for general principles applicable to encoding logic in limited formalisms (regex, SQL constraints, type systems).
