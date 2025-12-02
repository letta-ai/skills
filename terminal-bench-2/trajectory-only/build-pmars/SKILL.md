---
name: build-pmars
description: Guide for building pMARS (Portable Memory Array Redcode Simulator) and similar software from Debian/Ubuntu source packages. Use this skill when tasks involve enabling source repositories, downloading distribution source packages, removing X11/GUI dependencies, modifying Makefiles, diagnosing segmentation faults, and building headless versions of applications. Applies to Core War simulators and similar legacy software with optional graphics support.
---

# Building pMARS from Distribution Sources

## Overview

This skill provides a systematic approach for building pMARS (and similar software) from Debian/Ubuntu source packages with modifications such as removing X11 dependencies. It emphasizes proper diagnosis of build and runtime issues, verification at each step, and understanding root causes before applying fixes.

## When to Use This Skill

Apply this skill when tasks require:
- Building pMARS or similar Core War simulators from source
- Downloading and extracting Debian/Ubuntu source packages
- Removing X11/GUI dependencies to create headless versions
- Modifying Makefiles to change build flags or library linkage
- Diagnosing and fixing segmentation faults in built software
- Working with DEB822-format apt source configurations

## Core Workflow

### Phase 1: Enable Source Repositories

Modern Debian/Ubuntu systems use DEB822 format for apt sources. Enable source packages correctly:

**Check current apt sources format:**
```bash
# Look for .sources files (DEB822 format) vs sources.list (traditional)
ls /etc/apt/sources.list.d/*.sources
cat /etc/apt/sources.list.d/debian.sources
```

**Enable sources in DEB822 format:**
```bash
# Check current Types field
grep "^Types:" /etc/apt/sources.list.d/debian.sources

# Add deb-src to Types line
sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/debian.sources
```

**Enable sources in traditional format:**
```bash
# Uncomment or add deb-src lines
sed -i 's/^#deb-src/deb-src/' /etc/apt/sources.list
```

**Update package cache:**
```bash
apt-get update
```

**Verification - critical step:**
```bash
# Read back the modified file to verify edit was correct
cat /etc/apt/sources.list.d/debian.sources

# Verify sources are enabled (should show deb-src entries)
apt-cache policy
```

**Common pitfall:** File edits may be truncated or malformed. Always read back the modified file to verify correctness before proceeding.

### Phase 2: Download Source Package

Install required tools and download the source:

```bash
# Install dpkg-dev for apt-get source functionality
apt-get install -y dpkg-dev

# Navigate to extraction directory
cd /app

# Download source package (automatically extracts)
apt-get source pmars
```

**What gets created:**
- `pmars_<version>.orig.tar.xz` - Original upstream source
- `pmars_<version>.debian.tar.xz` - Debian patches and metadata
- `pmars_<version>.dsc` - Package description file
- `pmars-<version>/` - Extracted and patched source directory

**Verification:**
```bash
# Verify extraction succeeded
ls -la /app/pmars-*/

# Check source directory structure
ls /app/pmars-*/src/
```

### Phase 3: Review Debian Patches First

Before making modifications, examine existing Debian patches:

```bash
cd /app/pmars-*/

# List available patches
ls debian/patches/

# Read patch series (order of application)
cat debian/patches/series

# Read individual patches to understand known issues
cat debian/patches/*.patch
```

**Why this matters:**
- Debian maintainers have often fixed known issues
- Understanding existing patches prevents duplicate work
- Some patches may reveal build system quirks
- Conflicts with custom modifications can be avoided

### Phase 4: Identify Build Configuration

Locate and understand the build configuration:

```bash
cd /app/pmars-*/src/

# Read Makefile header comments (often document options)
head -100 Makefile | grep "^#"

# Identify key variables
grep -E "^CFLAGS|^LIBS|^LIB|^CC" Makefile

# Look for X11-related flags
grep -i "x11\|xwin\|graphx" Makefile
```

**Common pMARS Makefile structure:**
```makefile
# Comments document available defines:
# -DEXT94      Enables ICWS'94 extensions
# -DXWINGRAPHX Enables X Window graphics
# -DGRAPHX     Enables general graphics support

CFLAGS += -O -DEXT94 -DXWINGRAPHX
LIB = -L/usr/X11R6/lib -lX11
```

### Phase 5: Remove X11 Dependencies

**Modify CFLAGS to remove graphics defines:**
```bash
# Remove -DXWINGRAPHX from CFLAGS
# Original: CFLAGS += -O -DEXT94 -DXWINGRAPHX
# Modified: CFLAGS += -O -DEXT94
```

**Remove or comment out library linkage:**
```bash
# Original: LIB = -L/usr/X11R6/lib -lX11
# Modified: LIB =
# OR comment out entirely: # LIB = -L/usr/X11R6/lib -lX11
```

**Verification after edit:**
```bash
# CRITICAL: Read back modified Makefile section
grep -E "^CFLAGS|^LIB" Makefile

# Verify X11 references removed
grep -i "x11\|xwin" Makefile
```

**Common pitfall:** Edits may not apply correctly or may be truncated. Always verify the modified section by reading it back.

### Phase 6: Build the Software

```bash
cd /app/pmars-*/src/
make clean
make
```

**Handle compiler warnings appropriately:**
- Warnings in C code may indicate real bugs
- Examine warnings rather than dismissing them
- Common legacy code warnings:
  - Implicit function declarations
  - Unused variables
  - Comparison between signed/unsigned

**Verification:**
```bash
# Verify binary was created
ls -lh pmars

# Check it's not linked to X11
ldd pmars | grep -i x11
# Expected: no output (no X11 linkage)

# Verify basic functionality
./pmars --help 2>&1 || ./pmars 2>&1 | head -5
```

### Phase 7: Install and Test

**Install to target location:**
```bash
cp /app/pmars-*/src/pmars /usr/local/bin/pmars
chmod +x /usr/local/bin/pmars

# Verify installation
ls -lh /usr/local/bin/pmars
which pmars
```

**Progressive testing approach:**

1. **Test minimal functionality first:**
   ```bash
   /usr/local/bin/pmars --help
   /usr/local/bin/pmars file1.red file2.red
   ```

2. **Add flags incrementally:**
   ```bash
   # Basic battle
   /usr/local/bin/pmars -b file1.red file2.red

   # With rounds
   /usr/local/bin/pmars -b -r 50 file1.red file2.red

   # With additional flags (test one at a time)
   /usr/local/bin/pmars -b -r 50 -f file1.red file2.red
   ```

3. **Identify problematic flags:**
   - If a flag causes crashes, note which flag
   - Determine if output requirements can be met without problematic flag
   - Investigate root cause before applying fixes

## Debugging Segmentation Faults

When encountering crashes, follow this systematic approach:

### Step 1: Establish Baseline

```bash
# Find minimal reproduction case
/usr/local/bin/pmars file1.red file2.red          # Test without flags
/usr/local/bin/pmars -b file1.red file2.red       # Add one flag
/usr/local/bin/pmars -b -r 50 file1.red file2.red # Add another

# Document which command works and which crashes
```

### Step 2: Use Debugger for Diagnosis

```bash
apt-get install -y gdb

# Get backtrace
gdb -batch -ex "run -b -r 50 -f file1.red file2.red" -ex "bt" /usr/local/bin/pmars

# Interactive debugging
gdb /usr/local/bin/pmars
(gdb) run -b -r 50 -f file1.red file2.red
(gdb) bt
```

### Step 3: Analyze the Discrepancy

**Critical insight:** If a crash occurs standalone but not under gdb, this indicates:
- Undefined behavior (memory layout differences)
- Timing-sensitive issues
- Uninitialized memory being used
- Memory corruption

**Do not assume a simple NULL check will fix the issue.** Investigate:
- What variable is NULL or uninitialized?
- Why is it in that state?
- Is this a symptom of a deeper initialization problem?

### Step 4: Understand Before Fixing

Before applying source code fixes:

1. **Read relevant source code sections**
2. **Understand the data flow** - trace where problematic variables are initialized
3. **Check if Debian patches address the issue**
4. **Document the root cause hypothesis**

**Example analysis:**
```c
// If crash occurs in checksum_warriors() dereferencing instBank
// Questions to ask:
// - When should instBank be initialized?
// - Are all warriors in endWar array properly initialized?
// - Is the iteration count correct?
```

### Step 5: Apply Targeted Fix

Only after understanding root cause:

```c
// Document why this fix is appropriate
// If instBank can legitimately be NULL when feature disabled:
if (instBank != NULL) {
    // proceed with operation
}
```

**Verify the fix:**
```bash
# Rebuild after source modification
make clean && make

# Read back modified source to verify edit
grep -A5 -B5 "your_fix" modified_file.c

# Test the specific failing scenario
/usr/local/bin/pmars -b -r 50 -f file1.red file2.red
```

## Common Pitfalls and Solutions

### Pitfall 1: File Edit Truncation

**Problem:** Edit operations may truncate strings or introduce errors.

**Prevention:**
```bash
# ALWAYS read back modified sections
cat modified_file | grep -A2 -B2 "modified_line"

# Verify file is syntactically valid (for known formats)
```

### Pitfall 2: Incomplete Diagnosis

**Problem:** Applying speculative fixes without confirming root cause.

**Prevention:**
- Use debugger to get exact crash location
- Read source code to understand context
- Document hypothesis before fixing
- If behavior differs between gdb and standalone, investigate why

### Pitfall 3: Bypassing Debian Build System

**Problem:** Modifying upstream Makefile directly may miss Debian patches.

**Consideration:**
```bash
# Check if debian/rules applies additional patches
cat debian/rules

# Alternative: use Debian's build system
dpkg-buildpackage -us -uc -b
```

### Pitfall 4: Ignoring Compiler Warnings

**Problem:** Warnings in C code may indicate real bugs.

**Prevention:**
```bash
# Examine warnings during build
make 2>&1 | grep -i warning

# Consider building with stricter flags for diagnosis
make CFLAGS="-Wall -Wextra"
```

### Pitfall 5: Not Verifying Test Files

**Problem:** Test input files may be malformed.

**Prevention:**
```bash
# Verify warrior files exist and have content
ls -l file1.red file2.red
head file1.red
```

## Priority Framework

When working on build tasks:

**P0 - Must Complete:**
- Binary builds successfully
- Binary installs to correct location
- Core functionality works (basic execution)
- Required output format matches specification

**P1 - Important:**
- All specified flags work correctly
- No X11 dependencies in final binary
- Clean build without errors

**P2 - Nice to Have:**
- No compiler warnings
- All optional features working
- Perfect adherence to original test command

**Apply framework:** If a specific flag causes issues but core output requirement can be met without it, evaluate whether the flag is truly required or just part of an example command.

## Verification Checklist

Before marking task complete:

- [ ] Source repositories enabled and verified
- [ ] Source package downloaded and extracted
- [ ] Debian patches reviewed for relevant fixes
- [ ] X11 dependencies removed from Makefile (verified by reading back)
- [ ] Binary compiled successfully
- [ ] Binary verified not linked to X11 (`ldd` shows no X11)
- [ ] Binary installed to correct location (`/usr/local/bin/pmars`)
- [ ] Basic functionality tested (minimal arguments)
- [ ] Required test command passes with expected output format
- [ ] Any source modifications verified by reading back the changes
- [ ] Root cause understood for any bugs fixed (not just symptoms masked)

## Quick Reference

```bash
# Enable sources (DEB822)
sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/debian.sources
apt-get update

# Download source
apt-get install -y dpkg-dev
cd /app && apt-get source pmars

# Modify Makefile (remove X11)
cd /app/pmars-*/src/
# Edit: Remove -DXWINGRAPHX from CFLAGS
# Edit: Comment out or clear LIB = -lX11 line

# Build and verify
make clean && make
ldd pmars | grep -i x11  # Should show nothing

# Install
cp pmars /usr/local/bin/pmars
chmod +x /usr/local/bin/pmars

# Test progressively
/usr/local/bin/pmars file1.red file2.red
/usr/local/bin/pmars -b -r 50 file1.red file2.red
```
