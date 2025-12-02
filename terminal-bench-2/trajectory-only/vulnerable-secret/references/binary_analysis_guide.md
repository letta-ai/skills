# Binary Analysis Guide

## Detailed Tool Usage

### objdump

Disassemble specific functions:
```bash
objdump -d <executable> | grep -A 50 "<function_name>:"
```

Show all sections with contents:
```bash
objdump -s <executable>
```

### readelf

List all sections:
```bash
readelf -S <executable>
```

Dump specific section as hex:
```bash
readelf -x .rodata <executable>
readelf -x .data <executable>
```

Show dynamic symbols (for shared libraries):
```bash
readelf --dyn-syms <executable>
```

### strings

Extract strings with minimum length:
```bash
strings -n 8 <executable>    # Minimum 8 characters
```

Show offset of each string:
```bash
strings -t x <executable>    # Hex offset
strings -t d <executable>    # Decimal offset
```

## Buffer Overflow Exploitation

### Identifying Vulnerable Functions

Common vulnerable functions to look for:
- `gets()` - No bounds checking, always exploitable
- `strcpy()` - No bounds checking on destination
- `sprintf()` - No bounds checking on output buffer
- `scanf("%s", ...)` - No bounds checking on string input

### Crafting Exploits

1. **Determine buffer size** from disassembly (look for stack allocation)
2. **Find the return address offset** by sending increasing pattern lengths
3. **Locate target address** (flag print function, authentication bypass, etc.)
4. **Construct payload**: padding + target address

Example pattern generation:
```python
# Generate cyclic pattern to find offset
import string
pattern = ""
for i in range(100):
    pattern += string.ascii_uppercase[i % 26]
print(pattern)
```

### Stack Layout Analysis

In x86-64 disassembly, look for:
- `sub rsp, N` - Stack allocation (N bytes for local variables)
- `lea rax, [rbp-N]` - Local variable at offset N from base pointer
- `mov rdi, rax; call gets` - Buffer being passed to gets()

## XOR Encoding Analysis

### Identifying XOR in Disassembly

Look for patterns like:
```asm
mov    al, BYTE PTR [rbx+rcx]   ; Load encoded byte
xor    al, 0xNN                  ; XOR with key
mov    BYTE PTR [rdx+rcx], al   ; Store decoded byte
inc    rcx                       ; Increment counter
cmp    rcx, N                    ; Compare with length
jl     loop_start               ; Continue loop
```

### Extracting Encoded Data

1. Find the data section containing encoded bytes
2. Note the starting address and length from disassembly
3. Use readelf to dump the section
4. Extract the relevant byte range

### Decoding Script Template

```python
#!/usr/bin/env python3
import sys

def xor_decode(hex_data, key):
    """Decode XOR-encoded hex string with single-byte key."""
    # Remove any whitespace from hex data
    hex_data = hex_data.replace(" ", "").replace("\n", "")

    # Validate hex string
    if len(hex_data) % 2 != 0:
        print(f"Error: Hex string has odd length ({len(hex_data)})")
        sys.exit(1)

    # Decode
    encoded = bytes.fromhex(hex_data)
    decoded = bytes([b ^ key for b in encoded])

    return decoded

# Example usage
if __name__ == "__main__":
    hex_data = "YOUR_HEX_DATA_HERE"
    key = 0x00  # Replace with discovered key

    result = xor_decode(hex_data, key)
    print(f"Decoded: {result}")
    print(f"As string: {result.decode('utf-8', errors='replace')}")
```

## Authentication Bypass Analysis

### Finding Bypass Conditions

Search for comparison instructions near authentication messages:
```bash
objdump -d <executable> | grep -B 20 "Authentication"
```

Look for:
- `cmp` or `test` instructions
- Conditional jumps (`je`, `jne`, `jz`, `jnz`)
- String comparisons (`strcmp`, `strncmp`)

### Common Bypass Techniques

1. **Magic value input**: Look for hardcoded comparison values
2. **Buffer overflow to skip check**: Overwrite return address to bypass
3. **Integer overflow**: Manipulate length/counter checks
4. **Format string**: If printf-family used with user input

## Hex Data Cleaning

### From readelf Output

readelf hex dump format:
```
0x00001000 464c4147 7b746573 747d0000 00000000  FLAG{test}......
```

To extract only the hex bytes:
1. Remove the address column (first field)
2. Remove the ASCII representation (after spaces at end)
3. Concatenate remaining hex values
4. Remove internal spaces

### Cleaning Script

```python
def clean_readelf_hex(readelf_output):
    """Extract clean hex string from readelf -x output."""
    hex_bytes = []
    for line in readelf_output.strip().split('\n'):
        # Skip empty lines and headers
        if not line.strip() or not line.strip().startswith('0x'):
            continue

        # Split by whitespace
        parts = line.split()

        # Skip address (first part) and ASCII (parts after gap)
        # Hex parts are typically parts[1:5]
        for i, part in enumerate(parts[1:], 1):
            # Stop if we hit ASCII representation
            if len(part) != 8 or not all(c in '0123456789abcdefABCDEF' for c in part):
                break
            hex_bytes.append(part)

    return ''.join(hex_bytes)
```

## Verification Checklist

Before submitting a solution:

- [ ] Tool availability documented at start
- [ ] Intended vulnerability path attempted if indicated
- [ ] Hex data cleaned of whitespace
- [ ] Decoded output matches expected format (FLAG{...}, etc.)
- [ ] No trailing/leading garbage in extracted secret
- [ ] Output file written successfully
- [ ] Output file contents verified after write
