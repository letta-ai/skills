# Cross-Compilation Checklist for Custom MIPS VMs

Use this checklist to ensure all critical steps are completed when cross-compiling for a custom MIPS VM.

## Pre-Compilation Analysis

- [ ] Read and analyze VM source code thoroughly
- [ ] Document syscall numbers and their mappings
- [ ] Identify syscall calling convention (register usage)
- [ ] Determine endianness (little-endian vs big-endian)
- [ ] Identify floating-point support (hard vs soft)
- [ ] Document memory layout (entry point, stack, heap)
- [ ] List any instruction limitations or unimplemented opcodes
- [ ] Identify ELF format expectations (sections, entry symbol)

## Header Preparation

- [ ] Scan all source files for `#include` statements
- [ ] Create complete list of required system headers
- [ ] Create stub headers for ALL required headers before first compile
- [ ] Verify stdarg.h handling for variadic functions
- [ ] Include proper type definitions (size_t, ssize_t, etc.)

## Standard Library Implementation

### Critical Functions (Must Be Complete)

- [ ] `printf` - with format specifier support (%d, %s, %x, %c, %p minimum)
- [ ] `sprintf` / `snprintf` - same format support
- [ ] `fprintf` - with file descriptor support
- [ ] `sscanf` - for configuration parsing
- [ ] `malloc` / `free` / `realloc` - proper heap management
- [ ] `memcpy` / `memset` / `memmove` - memory operations
- [ ] `strlen` / `strcmp` / `strcpy` / `strncpy` - string operations
- [ ] `atoi` / `atol` / `strtol` - number parsing
- [ ] `fopen` / `fread` / `fwrite` / `fclose` - file operations
- [ ] `fseek` / `ftell` - file positioning
- [ ] `open` / `read` / `write` / `close` - low-level I/O

### Verification Checklist

- [ ] No functions return 0 unconditionally
- [ ] No empty function bodies
- [ ] No TODO/stub comments in critical functions
- [ ] Format specifiers properly parsed and handled
- [ ] Error conditions properly reported

## Linker Configuration

- [ ] Entry point symbol matches VM expectations
- [ ] Text section address is correct
- [ ] Data section address is correct
- [ ] BSS section properly placed and zeroed
- [ ] Stack pointer initialized in startup code
- [ ] Map file generation enabled (-Wl,-Map=output.map)

## Compilation Verification

- [ ] No implicit function declaration warnings
- [ ] No ABI mismatch warnings (or properly addressed)
- [ ] ELF entry point verified with readelf
- [ ] Symbol table checked with nm
- [ ] Section layout verified with objdump

## Testing Progression

1. [ ] Minimal test program (print "Hello")
2. [ ] Syscall test program (test each syscall)
3. [ ] Memory allocation test
4. [ ] File I/O test
5. [ ] Complex string operations test
6. [ ] Full application

## Debugging When Things Go Wrong

### Program Terminates Early

- [ ] Get termination PC address from VM
- [ ] Look up address in map file
- [ ] Identify failing function
- [ ] Check for unimplemented instructions
- [ ] Verify syscall parameters are valid
- [ ] Check for stack overflow
- [ ] Verify memory addresses are in valid range

### No Output Produced

- [ ] Verify write syscall implementation
- [ ] Check stdout file descriptor (usually 1)
- [ ] Trace from printf to write syscall
- [ ] Check buffer flushing

### Unexpected Behavior

- [ ] Add diagnostic output at checkpoints
- [ ] Log all syscall invocations
- [ ] Verify data file paths
- [ ] Check endianness of data files
