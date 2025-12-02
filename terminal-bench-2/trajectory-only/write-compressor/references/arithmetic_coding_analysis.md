# Arithmetic Coding Analysis Guide

This reference provides detailed guidance for analyzing arithmetic coding decoders and implementing compatible encoders.

## Decoder State Machine Analysis

### Key State Variables

Identify and document these variables in the decoder:

| Variable | Typical Name | Purpose |
|----------|--------------|---------|
| Fraction | `fraction`, `code`, `value` | Current position in probability interval (from input bytes) |
| Range | `range`, `r`, `high-low` | Size of current probability interval |
| Low | `low`, `base` | Lower bound of interval (encoder only, implicit in decoder) |
| Radix | `radix`, `base` | Typically 256 for byte-based coding |

### Renormalization Analysis

The renormalization step is critical. Document exactly when and how it occurs:

```
DECODER renormalization pattern:
while (range < threshold):
    range *= radix
    fraction = fraction * radix + (next_byte - offset)
```

The encoder must output bytes that satisfy this relationship. The critical insight:

```
ENCODER must output byte b such that:
    decoder_fraction_after = decoder_fraction_before * radix + (b - offset)
    AND decoder_fraction_after falls within [encoder_low, encoder_low + encoder_range)
```

### Deriving the Output Byte Formula

Given encoder state `(low, range)` and decoder state `(fraction, range)`:

1. After encoder outputs byte `b`, decoder computes:
   ```
   new_fraction = old_fraction * radix + (b - offset)
   ```

2. For correct decoding, `new_fraction` must satisfy:
   ```
   low <= new_fraction < low + range
   ```

3. Solving for `b`:
   ```
   low <= old_fraction * radix + (b - offset) < low + range
   low - old_fraction * radix + offset <= b < low + range - old_fraction * radix + offset
   ```

4. Choose `b` as the integer satisfying these bounds

## Building a Decoder Simulator

### Python Template

```python
class DecoderSimulator:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.fraction = 0
        self.range = 1  # Or initial range from decoder
        self.radix = 256
        self.offset = 1  # Or 0, depends on decoder

        # Initialize fraction from first N bytes
        for _ in range(NUM_INITIAL_BYTES):
            self._read_byte()

    def _read_byte(self):
        if self.pos < len(self.data):
            b = self.data[self.pos]
            self.pos += 1
            self.fraction = self.fraction * self.radix + (b - self.offset)
        else:
            self.fraction = self.fraction * self.radix  # EOF behavior

    def _renormalize(self):
        while self.range < RANGE_THRESHOLD:
            self.range *= self.radix
            self._read_byte()

    def get_bit(self, prob_zero, prob_total):
        """Decode one bit given probability model."""
        self._renormalize()

        split = (self.range * prob_zero) // prob_total

        if self.fraction < split:
            self.range = split
            return 0
        else:
            self.fraction -= split
            self.range -= split
            return 1

    def trace(self, operation, result):
        """Print debug trace."""
        print(f"{operation} -> {result}")
        print(f"  fraction=0x{self.fraction:08x} range=0x{self.range:08x}")
```

### Adding Tracing to Existing Decoder

If the decoder is in C, add debug output:

```c
// Add at key points in decoder
#ifdef DEBUG
fprintf(stderr, "get_bit: ctx=%d prob=[%d,%d] split=%d frac=%d -> bit=%d\n",
        context, prob_zero, prob_total, split, fraction, bit);
fprintf(stderr, "  after: fraction=%08x range=%08x\n", fraction, range);
#endif
```

Compile with `-DDEBUG` to enable tracing.

## Encoder Implementation Pattern

### Python Template

```python
class Encoder:
    def __init__(self):
        self.low = 0
        self.range = INITIAL_RANGE
        self.output = bytearray()
        self.radix = 256
        self.offset = 1

    def _renormalize(self):
        while self.range < RANGE_THRESHOLD:
            # Compute output byte
            byte_out = self._compute_output_byte()
            self.output.append(byte_out)

            # Update state (must match decoder's update)
            self.low = (self.low * self.radix) - (byte_out - self.offset)
            # Or equivalent transformation
            self.range *= self.radix

    def _compute_output_byte(self):
        # THIS IS THE CRITICAL FORMULA
        # Derive from decoder's renormalization
        # Example (actual formula depends on specific decoder):
        return ((self.low * self.radix) // SOME_FACTOR) + self.offset

    def encode_bit(self, bit, prob_zero, prob_total):
        """Encode one bit."""
        split = (self.range * prob_zero) // prob_total

        if bit == 0:
            self.range = split
        else:
            self.low += split
            self.range -= split

        self._renormalize()
```

### Verification Pattern

```python
def verify_encode_decode(bits, probs):
    """Verify encoder output decodes correctly."""
    encoder = Encoder()

    for bit, (p0, pt) in zip(bits, probs):
        encoder.encode_bit(bit, p0, pt)

    encoder.finalize()
    compressed = bytes(encoder.output)

    decoder = DecoderSimulator(compressed)
    decoded_bits = []

    for (p0, pt) in probs:
        decoded_bits.append(decoder.get_bit(p0, pt))

    assert bits == decoded_bits, f"Mismatch: {bits} != {decoded_bits}"
```

## Debugging State Divergence

When encoder and decoder states diverge:

### Step 1: Find Divergence Point

Add trace output to both encoder and decoder. Run and diff the outputs:

```bash
./encoder input.txt > encoder_trace.txt 2>&1
./decoder compressed.bin > decoder_trace.txt 2>&1
diff encoder_trace.txt decoder_trace.txt | head -50
```

### Step 2: Analyze First Difference

At the first difference:
- What operation caused it?
- What were the inputs (probabilities, bit value)?
- What were the states before?
- What calculation produced different results?

### Step 3: Check Calculations

Common sources of divergence:
- Integer division rounding differences
- Different order of operations
- Off-by-one in probability split
- Wrong renormalization threshold
- Missing or extra renormalization

### Step 4: Verify with Minimal Input

Create the smallest input that triggers the divergence:
- If divergence at operation N, create input requiring exactly N operations
- Trace through by hand to verify expectations

## Probability Model Synchronization

The encoder and decoder must maintain identical probability models.

### Context-Based Models

If the decoder uses context-based probabilities:

```python
# Both encoder and decoder must update identically
def update_model(context, bit):
    counts[context][bit] += 1
    if counts[context][0] + counts[context][1] > MAX_COUNT:
        counts[context][0] = (counts[context][0] + 1) // 2
        counts[context][1] = (counts[context][1] + 1) // 2
```

### Verification

After each bit:
- Log the context used
- Log the probability values
- Verify encoder and decoder agree

## Example Analysis Session

```
1. Read decoder source, identify state variables:
   - fraction: 32-bit, updated on renormalize
   - range: starts at 0x10000000
   - radix: 256

2. Find renormalization code:
   while (range < 0x01000000) {
       range <<= 8;
       fraction = (fraction << 8) + (getc(in) - 1);
   }

3. Derive encoder formula:
   - Decoder expects: fraction_new = fraction_old * 256 + (byte - 1)
   - Encoder must output byte such that fraction_new in [low, low+range)
   - Byte = ((low >> 24) + 1) -- example, verify carefully!

4. Create minimal test:
   - Encode single bit=0 with prob 128/256
   - Run decoder, verify output is 0

5. If test fails:
   - Add debug output
   - Compare state traces
   - Find divergence point
   - Fix formula and retry
```
