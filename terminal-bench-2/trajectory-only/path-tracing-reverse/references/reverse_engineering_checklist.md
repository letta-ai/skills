# Reverse Engineering Checklist

Use this checklist to ensure systematic and complete reverse engineering of binaries.

## Pre-Analysis Setup

- [ ] Create working directory for analysis artifacts
- [ ] Generate reference output from original binary
- [ ] Record exact file size of reference output
- [ ] Compute and save checksum of reference output
- [ ] Verify binary is executable and runs correctly

## Binary Inspection

### Symbol Extraction
- [ ] Run `nm ./binary` to list symbols
- [ ] Run `strings ./binary` to find embedded strings
- [ ] Run `objdump -t ./binary` for symbol table
- [ ] Identify named functions (not stripped)
- [ ] Note any meaningful string hints (function names, error messages)

### Disassembly
- [ ] Generate full disassembly with `objdump -d ./binary`
- [ ] Extract `.rodata` section for constants
- [ ] Extract `.data` section for initialized variables
- [ ] Identify `main` function entry point
- [ ] Map all function calls from main

### Constant Catalog
- [ ] List all floating-point constants from `.rodata`
- [ ] Decode each constant (float vs double)
- [ ] List integer immediates in instructions
- [ ] Document suspected purpose of each constant
- [ ] Cross-reference constants with assembly usage

## Output Format Analysis

### Header Analysis
- [ ] Identify output format (PPM, BMP, raw, etc.)
- [ ] Extract exact header bytes with `xxd`
- [ ] Document whitespace and formatting
- [ ] Note numeric representation (ASCII vs binary)
- [ ] Verify line ending style (LF vs CRLF)

### Data Layout
- [ ] Determine pixel order (RGB, BGR, etc.)
- [ ] Verify bits per component (8-bit, 16-bit)
- [ ] Check for padding or alignment bytes
- [ ] Confirm image dimensions from header

## Algorithm Reconstruction

### Control Flow
- [ ] Identify main loop structure
- [ ] Map nested loops (row/column iteration)
- [ ] Document loop bounds and counters
- [ ] Identify conditional branches

### Data Flow
- [ ] Trace input parameters to functions
- [ ] Map register usage patterns
- [ ] Identify array/buffer accesses
- [ ] Document return value handling

### Floating-Point Analysis
- [ ] Determine precision (float vs double)
- [ ] Identify FPU type (x87 vs SSE/AVX)
- [ ] Note mathematical operations (sin, cos, sqrt)
- [ ] Check for precision-sensitive operations

## Implementation

### Code Structure
- [ ] Match output format exactly first
- [ ] Implement background/base case
- [ ] Add geometry/objects incrementally
- [ ] Implement lighting/shading last

### Compilation
- [ ] Use matching compiler flags (-static, -lm)
- [ ] Match optimization level if known
- [ ] Consider -fno-fast-math for FP precision
- [ ] Test with same architecture (32/64-bit)

## Verification

### Automated Testing
- [ ] Create verification script
- [ ] Run after every code change
- [ ] Compare file sizes first
- [ ] Compare checksums second
- [ ] Find first differing byte on mismatch

### Debugging Mismatches
- [ ] File size differs: Check output format
- [ ] Checksum differs: Find first bad byte
- [ ] Convert byte offset to pixel coordinates
- [ ] Compare expected vs actual RGB values
- [ ] Trace calculation for that specific pixel

### Progressive Verification
- [ ] Header matches exactly
- [ ] Background pixels match (100%)
- [ ] Edge cases match (corners, boundaries)
- [ ] Object pixels match
- [ ] Full checksum verification passes

## Final Validation

- [ ] File sizes are identical
- [ ] Checksums match exactly
- [ ] Visual inspection confirms correctness
- [ ] Multiple runs produce consistent output
- [ ] Task success criteria explicitly satisfied
