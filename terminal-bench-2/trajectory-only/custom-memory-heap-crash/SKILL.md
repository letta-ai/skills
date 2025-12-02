---
name: custom-memory-heap-crash
description: Debugging crashes related to custom memory heap implementations, particularly release-only crashes involving static destruction order, use-after-free during program shutdown, and memory lifecycle issues between custom allocators and standard library internals. This skill should be used when debugging segfaults or memory corruption that only occur in release/optimized builds, involve custom memory allocators or heap managers, or manifest during static object destruction after main() returns.
---

# Custom Memory Heap Crash Debugging

## Overview

This skill provides guidance for debugging crashes related to custom memory heap implementations, with particular focus on release-only crashes that occur during static destruction. These issues are notoriously difficult to diagnose because they involve subtle interactions between custom allocators, C++ standard library internals, and static initialization/destruction order.

## When to Apply This Skill

Apply this skill when encountering:
- Crashes that only occur in release/optimized builds but not in debug builds
- Segfaults during program shutdown (after `main()` returns)
- Use-after-free errors involving custom heap managers
- Memory corruption traced to static object destruction
- Crashes in standard library internals (locale, iostream, facets) with custom allocators

## Diagnostic Workflow

### Phase 1: Initial Crash Analysis

1. **Identify crash timing**: Determine if the crash occurs:
   - During normal execution
   - After `main()` returns (static destruction phase)
   - Only in release builds (not debug builds)

2. **Gather crash information**:
   - Use debugger to get stack trace at crash point
   - Note which memory addresses are involved
   - Identify if crash is in user code or library code

3. **Compare debug vs release behavior**:
   - Build both configurations and test
   - Note any differences in crash location or timing
   - Debug builds may use different allocation strategies (per-object vs pooled)

### Phase 2: Memory Lifecycle Analysis

1. **Map static object lifetimes**: Identify all static/global objects and their destruction order:
   - Custom heap managers
   - Singleton objects
   - Static containers or caches
   - Standard library static objects (locale facets, iostream buffers)

2. **Trace allocation sources**: For each allocation involved in the crash:
   - Determine which allocator was used (custom heap vs standard malloc)
   - Track when the allocation occurred relative to static object creation
   - Understand which destructor will free it

3. **Identify ordering conflicts**: Look for scenarios where:
   - Memory allocated from custom heap is accessed after heap destruction
   - Standard library internals allocate from custom heap unexpectedly
   - Static destruction order differs between debug and release builds

### Phase 3: Root Cause Investigation

1. **Examine library internals**: When crashes involve standard library:
   - Locale/facet registration (`_Facet_Register_impl`, `_Fac_tidy_reg_t`)
   - iostream initialization
   - Thread-local storage cleanup
   - Check library source code if available

2. **Understand optimization effects**: Release builds may:
   - Inline functions, changing allocation timing
   - Reorder operations
   - Eliminate debug-only code paths
   - Use different standard library implementations

3. **Verify assumptions**: Add temporary instrumentation to confirm:
   - When allocations actually occur
   - Which allocator services each allocation
   - Destruction order of static objects

## Solution Strategies

### Strategy 1: Force Early Initialization

Trigger library allocations before custom heap is created, ensuring they use standard malloc:

```cpp
void force_early_initialization() {
    // Force locale/facet initialization
    std::ostringstream oss;
    oss << 42;  // Triggers numeric facet registration
    std::locale loc = std::locale();

    // Force iostream initialization
    std::cout.flush();
    std::cerr.flush();
}

// Call this BEFORE creating custom heap
int main() {
    force_early_initialization();  // Standard malloc used
    create_custom_heap();          // Now safe to create heap
    // ...
}
```

### Strategy 2: Extend Heap Lifetime

Keep custom heap alive until after all dependent static objects are destroyed:

```cpp
// Use shared_ptr to extend lifetime
static std::shared_ptr<CustomHeap> g_heap;

// Or use atexit() for manual cleanup
void cleanup_heap() {
    // Destroy heap last
}
int main() {
    atexit(cleanup_heap);
    // ...
}
```

### Strategy 3: Track Allocation Sources

Implement tracking to identify which allocations came from custom heap:

```cpp
class CustomHeap {
    std::unordered_set<void*> tracked_allocations;
public:
    void* allocate(size_t size) {
        void* ptr = internal_alloc(size);
        tracked_allocations.insert(ptr);
        return ptr;
    }

    bool owns(void* ptr) {
        return tracked_allocations.count(ptr) > 0;
    }
};
```

### Strategy 4: Override Global Operators

Ensure all allocations route through custom heap consistently:

```cpp
void* operator new(size_t size) {
    if (g_custom_heap && g_custom_heap->is_active()) {
        return g_custom_heap->allocate(size);
    }
    return std::malloc(size);
}

void operator delete(void* ptr) noexcept {
    if (g_custom_heap && g_custom_heap->owns(ptr)) {
        g_custom_heap->deallocate(ptr);
    } else {
        std::free(ptr);
    }
}
```

## Verification Checklist

After implementing a fix, verify:

- [ ] Crash no longer occurs in release build
- [ ] Application still works correctly in debug build
- [ ] Memory sanitizers (Valgrind, ASan) report no errors
- [ ] Fix addresses root cause, not just symptoms
- [ ] Solution is robust to library implementation changes

## Common Pitfalls

### Pitfall 1: Incomplete Initialization Forcing
Simply calling `std::cout.flush()` may not trigger all necessary library initializations. Use operations that exercise the specific subsystems involved (locale formatting, facet registration, etc.).

### Pitfall 2: Assuming Consistent Ordering
Static destruction order can vary between:
- Debug and release builds
- Different compiler versions
- Different standard library implementations

### Pitfall 3: Ignoring "Still Reachable" Warnings
Valgrind's "still reachable" memory often indicates intentionally leaked static data, but verify it's not masking the actual issue.

### Pitfall 4: Over-Relying on Debug Builds
Debug builds may mask timing-dependent issues due to:
- Per-object allocation instead of pooling
- Additional safety checks
- Different optimization levels

## Debugging Tools and Techniques

### GDB Commands for Static Destruction
```bash
# Set breakpoint on static destructors
break __cxa_finalize

# Print static destruction order
info frame

# Watch memory access
watch *0xaddress
```

### Valgrind Usage
```bash
# Full memory check
valgrind --leak-check=full --track-origins=yes ./program

# Check with release build (may need debug symbols)
valgrind --leak-check=full ./program_release
```

### Compilation for Debugging Release Builds
```bash
# Release optimization with debug symbols
g++ -O2 -g -o program_release_debug source.cpp

# Address sanitizer (may change behavior)
g++ -O2 -fsanitize=address -o program_asan source.cpp
```

## References

For detailed technical information about memory lifecycle analysis and library internals, see `references/debugging_guide.md`.
