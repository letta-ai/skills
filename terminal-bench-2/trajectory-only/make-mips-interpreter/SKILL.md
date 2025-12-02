---
name: make-mips-interpreter
description: Guide for implementing MIPS CPU interpreters/emulators, particularly for running compiled MIPS ELF binaries. This skill applies when building virtual machines to execute MIPS32 code, creating emulators for retro game ports (like Doom), or implementing CPU simulators. Use for tasks involving ELF parsing, instruction decoding, syscall emulation, and memory management for MIPS architecture.
---

# MIPS Interpreter Implementation

## Overview

This skill provides guidance for implementing a MIPS interpreter/emulator capable of running compiled MIPS ELF binaries. The key insight is that building an interpreter is fundamentally an **engineering task requiring iterative implementation**, not a pure research problem. Start coding early and iterate.

## Critical Anti-Pattern: Analysis Paralysis

The most common failure mode is excessive research without implementation. Avoid:
- Reading every source file before writing any code
- Trying to understand every detail of the target program
- Researching exhaustively before creating a basic structure

Instead: Create a skeleton implementation early, then fill in components as understanding grows.

## Implementation Strategy

### Phase 1: Scaffold First (Start Here)

Create the basic interpreter structure immediately, before deep research:

```javascript
// vm.js - Create this skeleton FIRST
class MIPSInterpreter {
  constructor() {
    this.registers = new Uint32Array(32);
    this.memory = null;  // Will be ArrayBuffer
    this.pc = 0;
    this.hi = 0;
    this.lo = 0;
  }

  loadELF(buffer) { /* TODO */ }
  step() { /* TODO */ }
  run() { /* TODO */ }
  handleSyscall() { /* TODO */ }
}
```

### Phase 2: ELF Loading

Implement ELF parsing to load the binary:

1. Parse ELF header to get entry point and program headers
2. Load PT_LOAD segments into memory at specified virtual addresses
3. Initialize PC to entry point (typically 0x400000 range for MIPS)
4. Handle BSS section (zero-initialized, may be large)

Key ELF details for MIPS:
- Machine type: 0x08 (MIPS)
- Check endianness from ELF header (e_ident[EI_DATA])
- Entry point from e_entry field
- Program headers define memory layout

### Phase 3: Core Instruction Execution

Implement instruction decode and execute loop:

1. **Fetch**: Read 4 bytes at PC
2. **Decode**: Extract opcode (bits 31-26) and determine format (R/I/J)
3. **Execute**: Perform the operation
4. **Advance**: Update PC (normally PC += 4, handle branches/jumps)

Start with these essential instruction categories:
- **ALU**: ADD, ADDU, SUB, AND, OR, XOR, NOR, SLT, SLTU
- **Immediate**: ADDI, ADDIU, ANDI, ORI, XORI, SLTI, SLTIU, LUI
- **Shifts**: SLL, SRL, SRA, SLLV, SRLV, SRAV
- **Memory**: LW, LB, LBU, LH, LHU, SW, SB, SH
- **Branches**: BEQ, BNE, BGTZ, BLEZ, BLTZ, BGEZ
- **Jumps**: J, JAL, JR, JALR
- **Special**: SYSCALL, MFHI, MFLO, MULT, MULTU, DIV, DIVU

### Phase 4: Syscall Emulation

Implement syscalls the target program uses. Common syscalls:
- File I/O: open, close, read, write
- Memory: brk, mmap
- Process: exit
- Time: gettimeofday

Map syscall numbers to handlers. Syscall number is in $v0 ($2), arguments in $a0-$a3 ($4-$7).

### Phase 5: Test and Iterate

Run the binary, observe failures, fix issues:
- Unimplemented instructions will crash - implement as discovered
- Missing syscalls will fail - add as needed
- Memory issues will manifest - debug with logging

## Verification Strategy

### Incremental Testing Milestones

1. **ELF loads**: Entry point and segments loaded correctly
2. **First instruction executes**: PC advances, registers change
3. **First function call works**: JAL/JR, stack operations
4. **First syscall handled**: write() outputs something
5. **Program runs to completion**: exit() called normally

### Debugging Techniques

- Log PC and instruction at each step (disable for performance later)
- Print register state on syscalls
- Compare against reference MIPS emulator (SPIM, MARS) for simple programs
- Create minimal test programs to verify specific instructions

## Common Pitfalls

### 1. Ignoring Delay Slots
MIPS has branch delay slots - the instruction after a branch executes before the branch takes effect. Many interpreters skip this for simplicity (works for most compiled code).

### 2. Sign Extension Errors
- LB, LH sign-extend; LBU, LHU zero-extend
- Immediate values in I-type instructions are sign-extended (except for logical ops)
- Failing to sign-extend causes subtle bugs

### 3. Endianness Mismatch
- MIPS can be big or little endian (check ELF header)
- JavaScript TypedArrays use host endianness
- May need DataView for explicit endianness control

### 4. Memory Size Underestimation
- BSS sections can be very large (>1GB for programs like Doom)
- Use sparse memory representation or on-demand allocation
- Don't allocate full address space upfront

### 5. Unsigned vs Signed Arithmetic
- JavaScript numbers are signed; use `>>> 0` for unsigned comparison
- ADDU, SUBU don't trap on overflow; ADD, SUB do (rarely matters)
- SLT vs SLTU: signed vs unsigned comparison

### 6. Multiplication Result Registers
- MULT/MULTU put 64-bit result in HI:LO
- MFHI/MFLO retrieve the values
- Don't forget to implement these

## Time Management

For a complex interpreter task:
- **Hour 1**: Scaffold + ELF loading
- **Hour 2**: Core ALU and memory instructions
- **Hour 3**: Branches, jumps, and basic syscalls
- **Hour 4+**: Iterate based on runtime failures

An incomplete but running interpreter beats thorough research with no code.

## Resources

Refer to `references/mips_instruction_reference.md` for instruction encoding details and opcode tables.
