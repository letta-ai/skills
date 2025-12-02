---
name: extract-elf
description: Guidance for extracting memory values from ELF (Executable and Linkable Format) binary files. This skill should be used when parsing ELF headers, extracting LOAD segments, dumping memory addresses and values, or converting binary data to structured output formats like JSON. Covers proper handling of 32-bit vs 64-bit ELF files, endianness, and segment types.
---

# Extract ELF

## Overview

This skill provides guidance for extracting memory values from ELF binary files. ELF extraction tasks typically involve parsing the ELF header to identify program headers, locating LOAD segments that define memory layout, and extracting the corresponding data as address-value pairs.

## Approach

### Step 1: Understand the Requirements

Before writing any code, clarify the expected output format:

1. **Address format**: Determine whether addresses should be absolute virtual addresses, relative offsets, or based on a specific load address (e.g., 0x400000 for non-PIE executables)
2. **Reference solution**: If a reference solution exists, examine it to understand the exact expected format and values
3. **Output structure**: Confirm the expected JSON/text format (array of objects, key-value pairs, etc.)
4. **Value format**: Determine if values should be hexadecimal strings, decimal integers, or another format

### Step 2: Parse ELF Headers

Parse the ELF file systematically:

1. **Magic bytes**: Verify the file starts with `\x7fELF`
2. **Class**: Determine 32-bit (1) or 64-bit (2) from byte offset 4
3. **Endianness**: Check byte offset 5 for little-endian (1) or big-endian (2)
4. **Header fields**: Extract based on class:
   - 64-bit: `e_phoff` at offset 32 (8 bytes), `e_phentsize` at offset 54 (2 bytes), `e_phnum` at offset 56 (2 bytes)
   - 32-bit: `e_phoff` at offset 28 (4 bytes), `e_phentsize` at offset 42 (2 bytes), `e_phnum` at offset 44 (2 bytes)

### Step 3: Process Program Headers

For each program header, extract segment information:

1. **p_type**: First 4 bytes - look for PT_LOAD (value 1)
2. **p_offset**: File offset where segment data begins
3. **p_vaddr**: Virtual address in memory
4. **p_filesz**: Size of segment in file (bytes to read)
5. **p_memsz**: Size of segment in memory (may be larger than filesz for BSS)

Key considerations:
- Only process PT_LOAD segments (type = 1)
- Handle cases where `p_memsz > p_filesz` (BSS sections require zero-filling)
- Account for alignment and padding requirements

### Step 4: Extract Memory Values

For each LOAD segment:

1. Seek to `p_offset` in the file
2. Read `p_filesz` bytes
3. If `p_memsz > p_filesz`, append zeros for the BSS portion
4. Convert bytes to 4-byte (32-bit) or 8-byte (64-bit) integers based on architecture
5. Map each value to its corresponding virtual address

## Verification Strategies

### Verify Code After Writing

Always verify file contents after writing code:

```bash
cat extract.js  # or the extraction script name
```

Truncated writes can produce syntax errors that may not be immediately obvious.

### Cross-Reference with System Tools

Use standard tools to validate understanding:

```bash
# Examine ELF structure
readelf -h binary.elf      # Header information
readelf -l binary.elf      # Program headers (segments)
readelf -S binary.elf      # Section headers

# Verify specific bytes
hexdump -C binary.elf | head -20   # First 20 lines
od -A x -t x1 binary.elf | head    # Hex dump with addresses
```

### Compare Against Reference Solution

If a reference solution exists:

1. Run both solutions on the same input
2. Compare output structure (keys, format)
3. Compare specific address-value pairs
4. Check address ranges match expectations

```bash
# Example comparison
diff <(jq -S . reference_output.json) <(jq -S . your_output.json)
```

### Validate Address Ranges

Verify extracted addresses make sense:

- Non-PIE executables typically load at 0x400000 (4194304 decimal)
- PIE executables may use relative addresses from 0
- Check that address ranges align with `p_vaddr` and `p_memsz` from headers

## Common Pitfalls

### Address Interpretation

**Problem**: Output addresses start from 0, but reference expects addresses like 0x400000.

**Cause**: PIE (Position Independent Executable) binaries have `p_vaddr` starting at 0, while non-PIE binaries have a fixed load address.

**Solution**: Check the binary type and reference solution. If the reference uses a base address, add it to relative addresses:

```javascript
const baseAddress = 0x400000;  // Common for non-PIE x86-64
const absoluteAddr = baseAddress + relativeAddr;
```

### BSS Section Handling

**Problem**: Memory size (`p_memsz`) exceeds file size (`p_filesz`).

**Cause**: BSS sections contain uninitialized data that doesn't exist in the file but occupies memory.

**Solution**: When `p_memsz > p_filesz`:
- Read `p_filesz` bytes from file
- Append `(p_memsz - p_filesz)` zero bytes
- Include these zeros in output if required

### Endianness Mismatch

**Problem**: Extracted values appear corrupted or nonsensical.

**Cause**: Reading bytes in wrong endian order.

**Solution**: Check ELF header byte 5:
- Value 1 = little-endian (most common on x86)
- Value 2 = big-endian

Use appropriate read functions:

```javascript
// Little-endian
buffer.readUInt32LE(offset)

// Big-endian
buffer.readUInt32BE(offset)
```

### Partial Reads at Boundaries

**Problem**: Segment size not divisible by word size (4 or 8 bytes).

**Cause**: The last few bytes don't form a complete word.

**Solution**: Handle boundary cases explicitly:
- Pad with zeros to complete the final word, or
- Exclude incomplete words based on requirements

### Architecture Assumptions

**Problem**: Code assumes 64-bit ELF but file is 32-bit (or vice versa).

**Cause**: Header offsets and sizes differ between 32-bit and 64-bit ELF.

**Solution**: Check ELF class first and branch accordingly:

```javascript
const elfClass = buffer.readUInt8(4);
if (elfClass === 1) {
  // 32-bit: different offsets and sizes
} else if (elfClass === 2) {
  // 64-bit: standard modern layout
}
```

## Resources

### references/

The `references/` directory contains detailed documentation:

- `elf_format.md`: Comprehensive ELF format specification with byte offsets and field descriptions
