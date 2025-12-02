---
name: write-compressor
description: This skill provides guidance for implementing custom compression encoders that must be compatible with existing decoders (especially arithmetic coding). It should be used when the task requires writing a compressor/encoder that produces output compatible with a given decompressor/decoder, or when implementing arithmetic coding or similar bit-level compression schemes.
---

# Write Compressor

## Overview

This skill guides the implementation of compression encoders that must produce output compatible with an existing decoder. The key challenge is ensuring encoder state transitions exactly mirror decoder expectations—particularly critical for arithmetic coding where even minor state drift causes decompression failures.

## Critical Success Factors

### 1. Decoder-First Analysis

Before writing any encoder code:

1. **Create a decoder simulator in Python** - Reimplement the decoder logic to enable step-by-step tracing
2. **Trace with minimal inputs** - Create the smallest possible test cases (single bit, single byte) and manually compute expected values
3. **Map the state machine** - Document exactly how `fraction`, `range`, `low`, and other state variables change on each operation
4. **Derive the byte output formula mathematically** - Work out the exact relationship between encoder state and output bytes on paper before coding

### 2. Incremental Complexity Approach

Build encoder functionality in strict order of complexity:

1. **Single bit encoding** - Verify encoding a single 0 bit, then a single 1 bit
2. **Single integer encoding** - Verify encoding one small integer
3. **Multiple values** - Encode a sequence and verify each step
4. **Full compression** - Only attempt complete file compression after simpler cases work

Never skip to full file compression before validating simpler cases.

### 3. Dual Simulation Verification

Maintain both encoder and decoder implementations in Python that can be run side-by-side:

```
For each encoding operation:
  1. Run encoder to produce output
  2. Run decoder simulator consuming that output
  3. Assert encoder state matches decoder state
  4. Assert decoded value matches original value
```

### 4. State Synchronization

For arithmetic coding specifically:

- **Renormalization must match exactly** - The encoder's decision to output a byte must align with when the decoder expects to read one
- **Count arrays must stay synchronized** - Any probability model updates must happen identically in encoder and decoder
- **Range calculations must use identical formulas** - Integer division behavior must match

## Verification Strategy

### Unit Tests Before Integration

Create explicit unit tests for each encoding primitive:

```python
def test_encode_bit():
    # Test that encode_bit(0) followed by decode produces 0
    # Test that encode_bit(1) followed by decode produces 1

def test_encode_integer():
    # Test encoding/decoding small integers
    # Test boundary cases

def test_state_sync():
    # After each operation, encoder.low, encoder.range
    # must predict decoder.fraction, decoder.range
```

### Debug Output Protocol

Add comprehensive debug output to both encoder and decoder:

```
Operation: encode_bit(ctx=10, bit=1)
  Before: low=0x00000000 range=0x10000000
  Split:  0x08000000
  After:  low=0x08000000 range=0x08000000
  Output: [none]
```

Compare encoder debug output against decoder debug output line by line.

### Minimal Test Cases

Always start with the simplest possible test:

1. **Empty file** - Just header/footer, no data
2. **Single character** - Smallest meaningful compression
3. **Repeated character** - Tests probability updates
4. **Two-character alternation** - Tests context switching

## Common Pitfalls

### 1. Trial-and-Error Implementation

**Problem**: Creating multiple encoder implementations without understanding why each fails.

**Solution**: When an implementation fails, systematically determine the root cause:
- At which byte does decoder diverge?
- What value did encoder output vs. what decoder expected?
- Trace backward to find the state divergence point

### 2. Wrong Byte Output Formula

**Problem**: The renormalization formula for computing output bytes is often misunderstood.

**Solution**: If the decoder does:
```c
fraction = fraction * radix + (byte - 1)
```

Then mathematically derive what byte value steers `fraction` into the target range `[low, low+range)`. Do not guess—derive the formula.

### 3. Premature Optimization

**Problem**: Focusing on compression ratio or file size before achieving correctness.

**Solution**: Ignore size constraints until:
1. Single-bit encoding works
2. Full file compresses and decompresses correctly
3. Only then optimize for size

### 4. Testing Full Files Before Simple Cases

**Problem**: Attempting to compress a large file when basic operations are untested.

**Solution**: A segmentation fault or corrupted output on a full file provides almost no diagnostic information. Always verify with minimal inputs first.

### 5. Insufficient Decoder Analysis

**Problem**: Starting encoder implementation before fully understanding decoder behavior.

**Solution**: Spend significant time (potentially hours) analyzing the decoder:
- Read every line of decoder code
- Add debug output to the decoder
- Run decoder on known-good compressed files
- Document the state machine completely

## Workflow

### Phase 1: Analysis (Do Not Skip)

1. Read and annotate the decoder source code completely
2. Create a Python decoder simulator
3. Add debug output to trace every state transition
4. Run decoder on existing compressed files to understand expected behavior
5. Document the exact byte output formula mathematically

### Phase 2: Minimal Implementation

1. Implement encoder for single-bit encoding only
2. Add matching debug output to encoder
3. Verify encoder output decodes correctly
4. Compare state traces between encoder and decoder

### Phase 3: Incremental Extension

1. Add integer encoding, verify
2. Add any additional primitives (back-references, etc.), verify each
3. Implement full compression logic
4. Verify with progressively larger inputs

### Phase 4: Optimization (Only After Correctness)

1. Profile compression ratio
2. Adjust parameters for better compression
3. Verify correctness after each optimization change

## Red Flags

Stop and reassess if:

- Creating a third encoder implementation without understanding why previous ones failed
- Decoder produces segmentation fault (indicates fundamental state corruption)
- Debug output shows decoder reading unexpected values
- Tempted to "try different values" without mathematical justification
- Skipping minimal test cases to test on full file

## Resources

### references/arithmetic_coding_analysis.md

Detailed guide for analyzing arithmetic coding decoders, including:
- State variable identification
- Deriving the byte output formula mathematically
- Python templates for decoder simulator and encoder
- Step-by-step debugging of state divergence
- Probability model synchronization
