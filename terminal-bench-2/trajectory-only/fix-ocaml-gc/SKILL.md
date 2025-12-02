---
name: fix-ocaml-gc
description: Guide for debugging and fixing bugs in the OCaml garbage collector runtime, particularly issues in memory management code like sweeping, pool management, and run-length compression. This skill should be used when encountering segfaults during OCaml bootstrap, debugging crashes in runtime/shared_heap.c or similar GC code, or investigating pointer arithmetic bugs in memory allocator implementations.
---

# OCaml Garbage Collector Bug Fixing

## Overview

This skill provides systematic approaches for debugging and fixing bugs in the OCaml garbage collector, with particular focus on the multicore runtime's shared heap implementation. GC bugs are notoriously difficult because they often manifest as intermittent crashes, may only appear during bootstrap builds, and involve complex pointer arithmetic in low-level C code.

## When to Apply This Skill

Apply this skill when encountering:
- Segmentation faults during OCaml bootstrap (building the compiler with itself)
- Crashes in `runtime/shared_heap.c` or related GC files
- Memory corruption traced to sweeping, marking, or pool management
- Bugs introduced by performance optimizations like run-length compression
- Pointer arithmetic errors in block iteration code

## Diagnostic Workflow

### Phase 1: Build System Understanding

Before debugging, understand the OCaml build process:

1. **Locate build documentation**: Check for `HACKING.adoc`, `INSTALL`, or `CONTRIBUTING.md` files that explain the build process and testing infrastructure.

2. **Understand bootstrap stages**: OCaml bootstraps itself in stages:
   - Stage 1: Build compiler with existing compiler
   - Stage 2: Rebuild compiler with Stage 1 compiler
   - Stage 3: Verify Stage 2 can rebuild itself identically

3. **Identify the failure point**: Determine which stage crashes and what operation triggers it (compilation, linking, running tests).

4. **Build with debug symbols**: Ensure debug symbols are available for meaningful stack traces:
   ```bash
   ./configure --enable-debug-runtime
   make clean && make world.opt
   ```

### Phase 2: Crash Analysis

1. **Obtain stack trace**: Use GDB to get a stack trace at the crash point:
   ```bash
   gdb --args ./ocamlopt.opt <crashing_args>
   (gdb) run
   (gdb) bt
   ```

2. **Identify the crashing function**: Note which function crashed and the memory address involved. For GC bugs, common crash locations include:
   - `pool_sweep` / `caml_sweep_pool`
   - `pool_allocate`
   - Marking functions
   - Header manipulation code

3. **Examine memory state**: Check pointer values and header contents:
   ```bash
   (gdb) p/x pointer_var
   (gdb) x/4gx block_address
   ```

### Phase 3: Code Investigation

1. **Search for relevant code**: Use grep to find sweep-related or allocator-related files:
   ```bash
   grep -r "pool_sweep\|sweep" runtime/
   grep -r "Wosize_hd\|Whsize_hd" runtime/
   ```

2. **Understand data structures**: Before modifying code, understand:
   - Block header format (size, color, tag fields)
   - Pool structure and block layout
   - How free blocks are represented
   - Run-length compression encoding (if applicable)

3. **Read surrounding comments**: GC code often has detailed comments explaining invariants and design decisions. Pay special attention to comments about:
   - What header fields mean for free vs allocated blocks
   - Size encoding (actual size vs count of consecutive blocks)
   - Iterator patterns and pointer advancement

4. **Trace the algorithm manually**: Work through the code by hand with concrete values to understand what should happen vs what is happening.

### Phase 4: Hypothesis Formation

1. **Identify pointer arithmetic patterns**: Look for code that advances pointers through memory:
   ```c
   p += Whsize_hd(hd);     // Advance by header-indicated size
   p += wh;                 // Advance by fixed block size
   p += wh * count;         // Advance by multiple blocks
   ```

2. **Check for inconsistent size usage**: A common bug pattern in run-length encoded data:
   - Header's `wosize` field may store a COUNT, not a SIZE
   - Code may incorrectly use `Wosize_hd(hd)` where it should use fixed block size
   - The fix often involves using the constant block size (`wh`) instead of computed size

3. **Consider multiple failure modes**: A crash may have multiple root causes:
   - The first bug found may not be the only bug
   - Similar patterns may exist in related code paths
   - Review all related functions, not just the crashing one

### Phase 5: Fix Implementation

1. **Make minimal changes**: Fix only the identified bug without refactoring surrounding code.

2. **Add clarifying comments**: Document the fix and why the original code was wrong:
   ```c
   /* Advance by fixed block size wh, not Whsize_hd(hd).
    * In run-length encoding, wosize stores the count of consecutive
    * free blocks, not the actual block size. */
   p += wh;
   ```

3. **Check for similar patterns**: Search the codebase for similar bug patterns:
   ```bash
   grep -n "Whsize_hd\|Wosize_hd" runtime/shared_heap.c
   ```

## Verification Strategy

### Required Testing

1. **Basic build test**: Verify the project builds successfully:
   ```bash
   make world.opt
   ```

2. **Bootstrap test**: Complete a full bootstrap to verify GC stability under heavy use:
   ```bash
   make bootstrap
   ```

3. **Run test suites**: Execute ALL relevant test suites, not just basic tests:
   ```bash
   make tests              # Full test suite
   cd testsuite && make    # Alternative test runner
   ```

4. **Run GC-specific tests**: Look for and run GC-focused tests:
   ```bash
   make -C testsuite/tests/gc-roots
   make -C testsuite/tests/weakref
   make -C testsuite/tests/ephemerons
   ```

5. **Run parallel/multicore tests**: For multicore GC bugs, test concurrent behavior:
   ```bash
   make -C testsuite/tests/parallel
   make -C testsuite/tests/domain
   ```

### Additional Verification

1. **Memory sanitizers**: If available, run with AddressSanitizer:
   ```bash
   ./configure CC="gcc -fsanitize=address"
   make clean && make world.opt
   ```

2. **Valgrind testing**: Run test programs under Valgrind:
   ```bash
   valgrind --leak-check=full ./program
   ```

3. **Stress testing**: Create or run memory-intensive test programs that exercise the specific code path.

## Common Pitfalls

### Pitfall 1: Accepting First Hypothesis Without Verification

**Wrong**: Find a plausible bug, fix it, and declare success after basic tests pass.

**Right**: Verify the hypothesis with debugging output or assertions before committing to the fix. Consider whether multiple bugs may exist.

### Pitfall 2: Insufficient Test Coverage

**Wrong**: Only run `tests/basic` and assume the fix is complete.

**Right**: Run the full test suite including GC-specific tests, parallel tests, and stress tests. A GC bug can manifest in many scenarios.

### Pitfall 3: Not Understanding the Data Structure

**Wrong**: Fix pointer arithmetic based on pattern matching without understanding what header fields mean.

**Right**: Fully understand the data structure layout:
- What does `wosize` mean for free blocks vs allocated blocks?
- How is run-length count encoded?
- What is the fixed block size (`wh`) vs variable size?

### Pitfall 4: Ignoring Related Code Paths

**Wrong**: Fix one occurrence of a bug pattern without checking for similar issues elsewhere.

**Right**: Search for all occurrences of the same pattern and verify each is correct:
```bash
grep -n "pattern" runtime/*.c
```

### Pitfall 5: Dismissing Test Infrastructure Errors

**Wrong**: Ignore errors like `make: *** [check-failstamp] Error 1` as "infrastructure issues."

**Right**: Investigate all test failures. Infrastructure errors may indicate real problems or may mask actual test failures.

### Pitfall 6: Not Verifying Build Completion

**Wrong**: Assume build succeeded because no immediate errors were displayed.

**Right**: Verify build completed fully:
```bash
ls -la ocamlopt.opt ocamlc.opt  # Check binaries exist
make world.opt 2>&1 | tail -20   # Check for trailing errors
```

## Edge Cases to Consider

When fixing GC bugs, verify behavior in these scenarios:

1. **Empty pools**: What happens when all blocks in a pool are free?
2. **Single free blocks**: Does the fix handle run-length count of 0 or 1?
3. **Pool boundaries**: Are there edge effects at the start or end of a pool?
4. **Mixed free/allocated**: Verify behavior with interleaved free and allocated blocks.
5. **Maximum sizes**: Test with maximum possible sizes for the data structure.
6. **Concurrent access**: For multicore GC, consider race conditions and memory ordering.

## Debugging Techniques

### Adding Temporary Instrumentation

Add printf debugging to verify hypotheses:
```c
fprintf(stderr, "sweep: p=%p hd=%lx wosize=%lu wh=%lu\n",
        (void*)p, hd, Wosize_hd(hd), wh);
```

### Using GDB Effectively

```bash
# Break at specific function
(gdb) break pool_sweep

# Conditional breakpoint
(gdb) break shared_heap.c:644 if wosize > 1000

# Watch memory location
(gdb) watch *0x7ffff7000000

# Print header interpretation
(gdb) p/x Hd_val(block)
(gdb) p Wosize_hd(Hd_val(block))
```

### Comparing Against Known-Good Version

If possible, compare against a working version:
```bash
git diff <known-good-commit> -- runtime/shared_heap.c
git log --oneline runtime/shared_heap.c  # Find relevant commits
```

## Summary Checklist

Before declaring a GC bug fixed, verify:

- [ ] Understood the data structure layout and encoding
- [ ] Identified the root cause with evidence (not just hypothesis)
- [ ] Checked for similar bug patterns in related code
- [ ] Full build completes successfully
- [ ] Bootstrap completes without crashes
- [ ] Full test suite passes (not just basic tests)
- [ ] GC-specific tests pass
- [ ] Parallel/multicore tests pass (if applicable)
- [ ] Added comments explaining the fix
- [ ] Considered and tested edge cases
