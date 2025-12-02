# Compile-to-Constraints Methodology

This document describes principles for encoding complex business logic into limited formalisms such as regular expressions, SQL constraints, type systems, or declarative DSLs.

## Core Principles

### 1. Understand the Target Formalism's Limitations

Before attempting implementation, understand what the target formalism can and cannot express:

| Formalism | Can Express | Cannot Express |
|-----------|-------------|----------------|
| Regex | Pattern matching, substitution, alternation | Counting, arithmetic, complex conditionals |
| SQL CHECK | Value comparisons, simple boolean logic | Cross-row constraints, procedural logic |
| Type systems | Shape constraints, sum/product types | Runtime values, dependent relationships |

For regex specifically:
- Can match fixed patterns and character classes
- Can use alternation for enumerated cases
- Cannot count occurrences (only "one or more", "zero or more")
- Cannot perform arithmetic
- Cannot express "if X then Y" conditionals except by enumerating all cases

### 2. Enumerate All Cases

When the formalism lacks conditionals, every valid case must be explicitly enumerated:

**Example: Chess pawn moves**
Instead of: "If pawn on rank 2-6, can move forward one square"
Must write: Pattern for a2→a3, pattern for a3→a4, ..., pattern for h6→h7

This leads to large pattern sets but ensures correctness.

### 3. Transformation Pipeline Design

Complex logic often requires multiple transformation stages:

```
Raw Input → Normalized Form → Annotated Form → Transformed → Output Format
```

For each stage, document:
1. Input format (with example)
2. Output format (with example)
3. Transformation rules
4. Invariants that must hold

### 4. Incremental Verification

Never generate all patterns at once. Build incrementally:

1. **Single case**: Write one pattern for one specific instance
2. **Verify**: Test that single pattern matches correctly
3. **Generalize**: Write generator for similar patterns
4. **Verify**: Test generated patterns on known inputs
5. **Expand**: Move to next case category

### 5. String Representation Design

Choose string representations that make pattern matching tractable:

**Good representations:**
- Fixed-width fields (easier to match positions)
- Explicit delimiters between elements
- Coordinates embedded in the string for position reference

**Problematic representations:**
- Variable-length encodings
- Implicit structure (relying on position counting)
- Ambiguous delimiters

## Debugging Strategies

### Pattern Not Matching

When a pattern should match but doesn't:

1. Print the exact input string (check for hidden characters)
2. Print the exact pattern (check escaping)
3. Test pattern in isolation in a regex tester
4. Check character class membership ([a-z] vs [A-Z])
5. Check anchoring (^ and $)

### Wrong Output

When pattern matches but produces wrong output:

1. Verify capture groups are numbered correctly
2. Check backreference syntax ($1 vs \1 vs ${1})
3. Print intermediate transformation results
4. Verify ordering assumptions (which substring comes first)

### Escaping Issues

When patterns flow through multiple languages:

```
Python string → JSON serialization → Regex engine
```

Each stage may require different escaping:
- Python: Raw strings r'' avoid most issues
- JSON: Backslashes must be doubled (\ → \\)
- Regex: Metacharacters need escaping (. → \.)

**Debugging approach:** Print the pattern at each stage to verify escaping.

## Architecture Patterns

### Pattern Generator Architecture

```python
class PatternGenerator:
    def __init__(self):
        self.patterns = []

    def add_pattern(self, match, replace, description):
        """Add a single pattern with documentation."""
        self.patterns.append({
            'match': match,
            'replace': replace,
            'description': description
        })

    def generate_piece_patterns(self, piece_type):
        """Generate all patterns for one piece type."""
        # Generate patterns for this piece
        # Test patterns before adding
        pass

    def export(self, filename):
        """Export patterns to required format."""
        pass
```

### Test Harness Architecture

```python
class PatternTester:
    def __init__(self, patterns):
        self.patterns = patterns

    def test_single_pattern(self, input_str, expected_output, pattern_idx):
        """Test one specific pattern on one input."""
        pass

    def test_all_patterns(self, input_str, expected_outputs):
        """Test all patterns that should match an input."""
        pass

    def find_matching_patterns(self, input_str):
        """Debug: show which patterns match an input."""
        pass
```

## Chess-Specific Considerations

### FEN String Structure

```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
│                                            │ │    │ │ │
│                                            │ │    │ │ └─ Fullmove number
│                                            │ │    │ └─── Halfmove clock
│                                            │ │    └───── En passant target
│                                            │ └────────── Castling rights
│                                            └──────────── Active color
└───────────────────────────────────────────────────────── Board position
```

### Square Ordering in FEN

The board is serialized rank by rank, from rank 8 to rank 1:
- a8, b8, c8, d8, e8, f8, g8, h8 (rank 8)
- a7, b7, ... h7 (rank 7)
- ...
- a1, b1, ... h1 (rank 1)

This means:
- a8 appears before h8 (same rank, lower file first)
- h8 appears before a7 (rank 8 before rank 7)
- a8 appears before a1 (higher rank first)

### Move Categories by Complexity

1. **Easiest**: Knight moves (no blocking, fixed deltas)
2. **Easy**: King moves (no blocking, fixed deltas, but check considerations)
3. **Medium**: Pawn moves (direction depends on color, special cases)
4. **Hard**: Sliding pieces (blocking detection required)
5. **Hardest**: Special moves (castling, en passant, promotion)

### Blocking Detection for Sliding Pieces

For bishops, rooks, and queens, paths between squares must be clear. Approaches:

1. **Enumerate all path states**: Generate patterns for every possible blocker configuration (exponential)
2. **Negative lookahead**: Use regex negative lookahead to check path is empty (complex but compact)
3. **Multi-pass**: First pass identifies potential moves, second pass filters blocked ones

## Common Failure Modes

### Premature Generalization

**Symptom:** Generator produces thousands of patterns, tests fail mysteriously
**Cause:** Generalized before verifying the base case works
**Fix:** Always test single hardcoded patterns first

### Ordering Assumption Errors

**Symptom:** Patterns never match, or match wrong squares
**Cause:** Misunderstanding which square appears first in the string
**Fix:** Document ordering explicitly, test ordering functions in isolation

### Escaping Cascade

**Symptom:** Patterns work in testing but fail in production
**Cause:** Different escaping requirements at different stages
**Fix:** Print patterns at each stage, verify escaping is correct

### Incomplete Case Enumeration

**Symptom:** Some valid inputs produce no matches
**Cause:** Missing patterns for edge cases (board edges, special squares)
**Fix:** Systematic enumeration of all squares and directions
