---
name: build-pov-ray
description: Guidance for compiling POV-Ray 2.2 (a 1990s-era ray tracing software) from source on modern Linux systems. This skill should be used when the task involves downloading, extracting, and building POV-Ray 2.2 or similar legacy/historical software that requires special handling for modern compiler compatibility.
---

# Build POV-Ray 2.2

## Overview

POV-Ray 2.2 is a ray tracing program from the early 1990s. Building it on modern systems requires careful handling of archive formats, legacy code compatibility, and outdated build systems. This skill provides guidance for compiling historical software that predates modern build toolchains.

## Pre-Build System Reconnaissance

Before downloading or building, perform system reconnaissance to understand the environment:

1. **Check available build tools:**
   - `gcc --version` - Verify GCC is available and note version (older code may need compatibility flags)
   - `make --version` - Confirm make is installed
   - `which uncompress` or `which gzip` - Check for .Z file decompression capability

2. **Check target directory state:**
   - Verify the output directory exists or can be created
   - Check available disk space

3. **Check for required dependencies:**
   - X11 development libraries (libx11-dev or similar) if building with display support
   - Math libraries (usually included with libc)

## Source Acquisition Strategy

POV-Ray 2.2 source code is distributed across multiple archive files:

1. **Archive components:**
   - POVSRC - Source code
   - POVDOC - Documentation
   - POVSCN - Sample scene files

2. **Download sources (in order of preference):**
   - Official POV-Ray FTP archives
   - Archive.org mirrors
   - University FTP mirrors

3. **Archive format considerations:**
   - Files typically use `.TAR.Z` format (compress + tar)
   - Decompress with `uncompress` or `gzip -d`, then extract with `tar`
   - Some systems may need `zcat file.TAR.Z | tar xvf -`

## Build Process Workflow

### Step 1: Extract Archives

```bash
# For .TAR.Z files
uncompress POVSRC.TAR.Z
tar xvf POVSRC.TAR

# Alternative if uncompress unavailable
gzip -d POVSRC.TAR.Z
tar xvf POVSRC.TAR

# Or in one command
zcat POVSRC.TAR.Z | tar xvf -
```

### Step 2: Examine Build System

Before running make:
- Read README, INSTALL, or similar documentation files
- Identify the build system (likely simple Makefile, not autoconf)
- Check for platform-specific directories (unix/, linux/, x11/)
- Identify which Makefile to use for the target platform

### Step 3: Apply Compatibility Fixes

Legacy C code often requires modifications for modern compilers:

1. **Implicit function declarations:**
   - Add missing `#include` statements
   - Common missing headers: `<stdlib.h>`, `<string.h>`, `<unistd.h>`

2. **K&R style function definitions:**
   - May need conversion to ANSI C style
   - Or use compiler flags: `-std=gnu89` or `-traditional`

3. **Compiler flag adjustments:**
   - Add `-w` to suppress warnings that are now errors
   - Use `-fcommon` if there are multiple definition errors
   - Consider `-m32` if code assumes 32-bit architecture

4. **Deprecated functions:**
   - `gets()` → `fgets()`
   - Old memory functions may need updates

### Step 4: Compile

```bash
# Navigate to appropriate source directory
cd source/unix  # or similar

# Edit Makefile if needed to adjust:
# - CC (compiler)
# - CFLAGS (add compatibility flags)
# - LIBS (ensure math library -lm is included)

make
```

### Step 5: Verify Build

After successful compilation:
- Confirm the `povray` (or `x-povray`) executable exists
- Test with a simple scene file: `./povray +Itest.pov +Otest.tga`
- Check the output image was created

## Common Pitfalls and Solutions

### Pitfall: Dead Download Links
Historical software archives may have moved or disappeared.
- **Solution:** Have multiple mirror sources ready; check archive.org

### Pitfall: .TAR.Z Decompression Failure
Modern systems may not have `uncompress` installed.
- **Solution:** Use `gzip -d` or `zcat` as alternatives

### Pitfall: Implicit Function Declaration Errors
Modern GCC (10+) treats implicit function declarations as errors.
- **Solution:** Add appropriate `#include` headers or use `-Wimplicit-function-declaration` to downgrade to warning

### Pitfall: Multiple Definition Errors
GCC 10+ changed default to `-fno-common`.
- **Solution:** Add `-fcommon` to CFLAGS

### Pitfall: Missing X11 Libraries
Build may fail looking for X11 headers or libraries.
- **Solution:** Install `libx11-dev` package or build without X11 if a non-graphical version is acceptable

### Pitfall: 32-bit vs 64-bit Issues
Old code may assume 32-bit `int` and pointer sizes.
- **Solution:** Try `-m32` flag if available, or patch size-dependent code

## Verification Checklist

After build completion, verify:

1. [ ] Executable file exists and has execute permissions
2. [ ] Running `./povray` (or equivalent) shows version/help information
3. [ ] Test render completes without errors
4. [ ] Output image file is created and viewable

## Contingency Planning

If the build fails at any stage:

1. **Download fails:** Try alternative mirrors, archive.org
2. **Extraction fails:** Try different decompression tools
3. **Compilation fails:**
   - Read error messages carefully
   - Apply appropriate compiler flags
   - Patch source code if necessary
4. **Runtime fails:** Check for missing shared libraries with `ldd`
