# Custom Memory Heap Crash Debugging Guide

## Understanding the Problem Space

Custom memory heap implementations interact with the C++ runtime in complex ways. When a program uses custom allocators alongside the standard library, memory management becomes a shared responsibility between:

1. The custom heap manager (user code)
2. The C++ standard library (locale, iostream, containers)
3. The C runtime (malloc/free)
4. The operating system

Crashes occur when these components make incompatible assumptions about memory ownership and lifetime.

## Static Initialization and Destruction Order

### The SIOF Problem (Static Initialization Order Fiasco)

C++ does not guarantee the order of static object initialization across translation units. Similarly, destruction order follows reverse initialization order, but only within a translation unit.

```
Initialization: A -> B -> C (within TU1), X -> Y -> Z (within TU2)
Destruction:    Z -> Y -> X (within TU2), C -> B -> A (within TU1)
```

The order between TU1 and TU2 is undefined and may vary between builds.

### Common Destruction Order Issues

**Scenario**: Custom heap destroyed before library cleanup

```
1. Custom heap created (static global)
2. Library allocates facet nodes via custom heap
3. main() executes
4. main() returns
5. Custom heap destructor runs (heap memory freed)
6. Library cleanup runs, accesses freed heap memory -> CRASH
```

## C++ Standard Library Internals

### Locale and Facet System

The C++ locale system maintains a global registry of facets. When locale operations occur:

1. Facet objects are created via `_Facet_Register_impl()`
2. Nodes are allocated to track registered facets
3. These nodes persist until program termination
4. Cleanup occurs in `_Fac_tidy_reg_t::~_Fac_tidy_reg_t()`

If these nodes are allocated from a custom heap that is destroyed first, the cleanup code accesses freed memory.

### Operations That Trigger Facet Registration

- `std::ostringstream` with numeric output (`oss << 42`)
- `std::locale()` constructor
- `std::use_facet<>()` calls
- `std::num_put<>`, `std::num_get<>` usage
- `std::time_put<>`, `std::time_get<>` usage
- `std::money_put<>`, `std::money_get<>` usage

### iostream Static Objects

The standard streams (`std::cout`, `std::cin`, `std::cerr`) are static objects with their own initialization requirements. They may allocate buffers and locale data that persist until destruction.

## Debug vs Release Build Differences

### Allocation Strategy Differences

**Debug builds** often use:
- Per-object allocation (each allocation gets its own block)
- Guard bytes around allocations
- Fill patterns for uninitialized memory
- Delayed freeing (freed memory kept in pool)

**Release builds** often use:
- Pooled allocation (multiple objects per block)
- No guard bytes
- No fill patterns
- Immediate memory reuse

### Timing Differences

Release builds optimize aggressively, which can change:
- When allocations occur (inlining may move allocation sites)
- Order of operations (compiler reordering)
- Which code paths execute (dead code elimination)

### Manifestation Patterns

| Issue | Debug Behavior | Release Behavior |
|-------|----------------|------------------|
| Use-after-free | May work (memory not reused) | Crash or corruption |
| Double free | Detected by debug allocator | Heap corruption |
| Buffer overflow | Caught by guard bytes | Silent corruption |
| Uninitialized read | Predictable pattern | Undefined behavior |

## Systematic Debugging Approach

### Step 1: Reproduce in Controlled Environment

Build with debug symbols but release optimization:
```bash
g++ -O2 -g -o program_debug_release source.cpp
```

This preserves debug information while maintaining release behavior.

### Step 2: Capture Stack Trace

Use GDB to get the crash location:
```bash
gdb ./program
(gdb) run
(gdb) bt full
```

For crashes during static destruction:
```bash
(gdb) break __cxa_finalize
(gdb) run
(gdb) c  # Continue until crash
(gdb) bt full
```

### Step 3: Identify Memory Origin

Determine which allocator provided the memory:

```cpp
// Add instrumentation to custom heap
void* CustomHeap::allocate(size_t size) {
    void* ptr = internal_alloc(size);
    fprintf(stderr, "CUSTOM_ALLOC: %p size=%zu\n", ptr, size);
    return ptr;
}

void CustomHeap::deallocate(void* ptr) {
    fprintf(stderr, "CUSTOM_FREE: %p\n", ptr);
    internal_free(ptr);
}
```

### Step 4: Map Object Lifetimes

Create a timeline of static object creation and destruction:

```cpp
struct LifetimeTracker {
    const char* name;
    LifetimeTracker(const char* n) : name(n) {
        fprintf(stderr, "CONSTRUCT: %s\n", name);
    }
    ~LifetimeTracker() {
        fprintf(stderr, "DESTRUCT: %s\n", name);
    }
};

// Add to key static objects
static LifetimeTracker g_heap_tracker("CustomHeap");
```

### Step 5: Verify Fix Completeness

After implementing a fix:

1. Run Valgrind:
   ```bash
   valgrind --leak-check=full --track-origins=yes ./program
   ```

2. Run AddressSanitizer:
   ```bash
   g++ -O2 -fsanitize=address -o program_asan source.cpp
   ./program_asan
   ```

3. Test multiple compiler/library combinations if possible

## Advanced Techniques

### Intercepting Allocations

To identify which component makes allocations:

```cpp
// In a separate TU linked first
extern "C" void* malloc(size_t size) {
    static auto real_malloc = (void*(*)(size_t))dlsym(RTLD_NEXT, "malloc");
    void* ptr = real_malloc(size);

    // Print stack trace for each allocation
    void* bt[10];
    int n = backtrace(bt, 10);
    backtrace_symbols_fd(bt, n, STDERR_FILENO);

    return ptr;
}
```

### Detecting Static Destruction Phase

```cpp
static bool g_in_destruction = false;

struct DestructionDetector {
    ~DestructionDetector() { g_in_destruction = true; }
};
static DestructionDetector s_detector;

// In allocator
void* allocate(size_t size) {
    if (g_in_destruction) {
        fprintf(stderr, "WARNING: Allocation during destruction!\n");
    }
    // ...
}
```

### Forcing Specific Destruction Order

Use Schwarz counter (nifty counter) idiom:

```cpp
// heap_init.hpp
struct HeapInitializer {
    HeapInitializer();
    ~HeapInitializer();
};
static HeapInitializer s_heap_init;

// heap_init.cpp
static int s_init_count = 0;
HeapInitializer::HeapInitializer() {
    if (s_init_count++ == 0) {
        // First initialization - create heap
    }
}
HeapInitializer::~HeapInitializer() {
    if (--s_init_count == 0) {
        // Last destruction - destroy heap
    }
}
```

## Library-Specific Information

### GCC libstdc++

- Facet registration in `bits/locale_init.cc`
- Uses `_Facet_Register_impl()` for thread-safe registration
- Cleanup in `_Fac_tidy_reg_t::~_Fac_tidy_reg_t()`
- Node structure: linked list with `_Next` pointer

### Clang libc++

- Different facet registration mechanism
- May have different destruction timing
- Check `__locale` and related headers

### MSVC STL

- Uses different naming conventions
- Facet system in `<xlocale>` internals
- CRT cleanup distinct from C++ library cleanup

## Checklist for Analysis

Before implementing fixes, confirm:

- [ ] Exact crash location identified (file:line)
- [ ] Memory address causing crash is from custom heap
- [ ] Allocation point of problematic memory identified
- [ ] Destruction order of involved static objects mapped
- [ ] Root cause is ordering issue, not memory corruption
- [ ] Proposed fix addresses root cause
- [ ] Fix is portable across target platforms
