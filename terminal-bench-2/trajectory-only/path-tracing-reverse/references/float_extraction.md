# Extracting Floating-Point Constants from Binaries

This guide covers techniques for systematically extracting and decoding floating-point constants from compiled binaries.

## Where Constants Live

### .rodata Section

Most floating-point constants are stored in the read-only data section:

```bash
objdump -s -j .rodata ./binary
```

This outputs hex dumps like:
```
Contents of section .rodata:
 402000 00000000 0000f03f 00000000 00002440  .......?......$@
 402010 0000803f 00004040 cdcc4c3f 00000000  ...?..@@..L?....
```

### .data Section

Mutable initialized data may also contain constants:

```bash
objdump -s -j .data ./binary
```

### Inline in Instructions

Some constants are embedded directly in SSE/AVX instructions or loaded via `mov` instructions.

## Decoding Floating-Point Values

### IEEE 754 Single Precision (32-bit float)

Format: 1 sign bit, 8 exponent bits, 23 mantissa bits

```python
import struct

def decode_float(hex_string):
    """Decode 4-byte hex string to float (little-endian)"""
    bytes_le = bytes.fromhex(hex_string)
    return struct.unpack('<f', bytes_le)[0]

# Examples
decode_float('0000803f')  # 1.0
decode_float('00004040')  # 3.0
decode_float('cdcc4c3f')  # 0.8 (approximately)
decode_float('00000000')  # 0.0
decode_float('0000803f')  # 1.0
decode_float('000080bf')  # -1.0
```

### IEEE 754 Double Precision (64-bit double)

Format: 1 sign bit, 11 exponent bits, 52 mantissa bits

```python
def decode_double(hex_string):
    """Decode 8-byte hex string to double (little-endian)"""
    bytes_le = bytes.fromhex(hex_string)
    return struct.unpack('<d', bytes_le)[0]

# Examples
decode_double('0000000000002440')  # 10.0
decode_double('0000000000000000')  # 0.0
decode_double('000000000000f03f')  # 1.0
decode_double('182d4454fb210940')  # 3.14159265358979
```

## Common Float Patterns

### Frequently Used Values

| Value | Float (hex) | Double (hex) |
|-------|-------------|--------------|
| 0.0 | `00000000` | `0000000000000000` |
| 1.0 | `0000803f` | `000000000000f03f` |
| -1.0 | `000080bf` | `000000000000f0bf` |
| 0.5 | `0000003f` | `000000000000e03f` |
| 2.0 | `00000040` | `0000000000000040` |
| 3.0 | `00004040` | `0000000000000840` |
| 10.0 | `00002041` | `0000000000002440` |
| PI | `db0f4940` | `182d4454fb210940` |
| 255.0 | `00007f43` | `0000000000e06f40` |

### Recognizing Patterns

1. **Small positive floats**: Start with `3f` (exponent ~127)
2. **Negative values**: High bit set in last byte (e.g., `bf` instead of `3f`)
3. **Values 2-4**: Start with `40` (exponent ~128)
4. **Values near 255**: Start with `43` for float

## Systematic Extraction Script

```python
#!/usr/bin/env python3
"""Extract and decode all floating-point constants from a binary."""

import struct
import subprocess
import re

def get_rodata(binary_path):
    """Extract .rodata section hex dump."""
    result = subprocess.run(
        ['objdump', '-s', '-j', '.rodata', binary_path],
        capture_output=True, text=True
    )
    return result.stdout

def parse_hex_dump(dump):
    """Parse objdump hex output into bytes."""
    data = bytearray()
    for line in dump.split('\n'):
        # Match lines like: " 402000 00000000 0000f03f..."
        match = re.match(r'\s*[0-9a-f]+\s+([0-9a-f ]+)', line)
        if match:
            hex_part = match.group(1).replace(' ', '')[:32]  # 16 bytes max
            if hex_part:
                data.extend(bytes.fromhex(hex_part))
    return bytes(data)

def find_floats(data, base_addr=0):
    """Scan data for valid-looking floats."""
    results = []
    for i in range(0, len(data) - 3, 4):
        chunk = data[i:i+4]
        try:
            value = struct.unpack('<f', chunk)[0]
            # Filter for "reasonable" values
            if abs(value) < 1e10 and abs(value) > 1e-10 or value == 0:
                results.append((base_addr + i, chunk.hex(), value))
        except:
            pass
    return results

def find_doubles(data, base_addr=0):
    """Scan data for valid-looking doubles."""
    results = []
    for i in range(0, len(data) - 7, 8):
        chunk = data[i:i+8]
        try:
            value = struct.unpack('<d', chunk)[0]
            if abs(value) < 1e10 and abs(value) > 1e-10 or value == 0:
                results.append((base_addr + i, chunk.hex(), value))
        except:
            pass
    return results

if __name__ == '__main__':
    import sys
    binary = sys.argv[1] if len(sys.argv) > 1 else './mystery'

    dump = get_rodata(binary)
    data = parse_hex_dump(dump)

    print("Potential float constants:")
    for addr, hex_val, value in find_floats(data):
        print(f"  0x{addr:08x}: {hex_val} = {value}")

    print("\nPotential double constants:")
    for addr, hex_val, value in find_doubles(data):
        print(f"  0x{addr:08x}: {hex_val} = {value}")
```

## Cross-Referencing with Disassembly

After extracting constants, find where they're used:

```bash
# Find references to a specific address
objdump -d ./binary | grep "402000"

# Look for SSE load instructions
objdump -d ./binary | grep -E "(movss|movsd|movaps|movapd)"
```

### SSE Instruction Patterns

```asm
; Loading single float from memory
movss  xmm0, DWORD PTR [rip+0x1234]  ; Loads 32-bit float

; Loading double from memory
movsd  xmm0, QWORD PTR [rip+0x1234]  ; Loads 64-bit double

; Loading packed floats
movaps xmm0, XMMWORD PTR [rip+0x1234]  ; Loads 4 floats
```

## Determining float vs double

Key indicators in assembly:

| Instruction | Precision |
|-------------|-----------|
| `movss`, `addss`, `mulss`, `divss` | Single (float) |
| `movsd`, `addsd`, `mulsd`, `divsd` | Double |
| `cvtss2sd` | Convert float to double |
| `cvtsd2ss` | Convert double to float |

## Verifying Extracted Values

Once constants are identified, verify by:

1. Creating a test program using those exact values
2. Comparing specific outputs pixel-by-pixel
3. Using GDB to inspect values at runtime:

```bash
gdb ./binary
(gdb) break main
(gdb) run
(gdb) x/f 0x402000   # Print as float
(gdb) x/g 0x402000   # Print as double
```
