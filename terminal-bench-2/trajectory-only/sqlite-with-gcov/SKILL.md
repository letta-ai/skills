---
name: sqlite-with-gcov
description: This skill provides guidance for compiling software (particularly SQLite) with gcov code coverage instrumentation, installing to custom prefixes, and making binaries available system-wide. Use when tasks involve compiling C/C++ projects with coverage flags, installing software to non-standard locations, or ensuring PATH availability for installed binaries.
---

# Compiling Software with gcov Instrumentation

## Overview

This skill covers compiling C/C++ software with gcov code coverage instrumentation and installing it to a specified location while ensuring system-wide availability. The core challenge extends beyond compilation—it requires understanding how PATH modifications persist and how coverage data files are managed.

## Approach

### Phase 1: Source Preparation

1. Extract source archives to a **persistent** build directory (avoid `/tmp` if coverage data needs to persist)
2. Identify the build system (autotools, cmake, makefile)
3. Review available configure options for coverage support

### Phase 2: Configure with Coverage Flags

For autotools-based projects (like SQLite):

```bash
./configure --prefix=/target/install/path \
    CFLAGS="-fprofile-arcs -ftest-coverage -g -O0" \
    LDFLAGS="-lgcov"
```

Key flags explanation:
- `-fprofile-arcs`: Generate instrumentation for arc-based profiling
- `-ftest-coverage`: Generate gcov-compatible coverage notes (.gcno files)
- `-g`: Include debug symbols for meaningful coverage reports
- `-O0`: Disable optimization to ensure accurate line coverage mapping
- `-lgcov`: Link against gcov runtime library

### Phase 3: Build and Install

```bash
make -j$(nproc)
make install
```

### Phase 4: Make Binary Available in PATH

**Critical Decision Point:** Understand what "available in PATH" means for the specific execution context.

#### Option A: Symlinks (Recommended for system-wide availability)

```bash
ln -s /target/install/path/bin/sqlite3 /usr/local/bin/sqlite3
```

This approach:
- Works for all users and all shells
- Works for non-interactive scripts and processes
- Requires write access to `/usr/local/bin`

#### Option B: Profile script (Multi-user, shell-dependent)

```bash
echo 'export PATH="/target/install/path/bin:$PATH"' >> /etc/profile.d/sqlite.sh
```

This approach:
- Works for all users with login shells
- Does NOT work for non-interactive processes

#### Option C: User bashrc (Limited scope)

```bash
echo 'export PATH="/target/install/path/bin:$PATH"' >> ~/.bashrc
```

This approach:
- Only works for current user
- Only works for interactive bash shells
- Does NOT work for non-interactive processes or scripts

### Phase 5: Handle Library Dependencies

If shared libraries are installed:

```bash
# Add library path
echo '/target/install/path/lib' >> /etc/ld.so.conf.d/custom.conf
ldconfig
```

Or use symlinks:
```bash
ln -s /target/install/path/lib/libsqlite3.so /usr/local/lib/
ldconfig
```

## Verification Strategy

### Verify Binary Availability

Test in the expected execution context, not just the current shell:

```bash
# Test in new shell (tests bashrc/profile changes)
bash -c 'which sqlite3'

# Test for non-interactive processes
/usr/bin/env sqlite3 --version

# Test symlink directly
ls -la /usr/local/bin/sqlite3
```

### Verify Coverage Instrumentation

```bash
# Check binary has coverage symbols
nm /target/install/path/bin/sqlite3 | grep gcov

# Check file type includes debug info
file /target/install/path/bin/sqlite3
# Should show: "with debug_info, not stripped"

# Run binary and check for .gcda files
sqlite3 :memory: "SELECT 1;"
find /path/to/build/dir -name "*.gcda"
```

### Verify Library Availability

```bash
ldd /target/install/path/bin/sqlite3
# All libraries should resolve (no "not found")
```

## Common Pitfalls

### PATH Configuration Mistakes

| Method | Scope | Verification |
|--------|-------|--------------|
| ~/.bashrc | Current user, interactive bash only | `bash -c 'which binary'` |
| /etc/profile.d/*.sh | All users, login shells | New login session |
| /usr/local/bin symlink | System-wide, all processes | `which binary` in any context |

**Mistake:** Assuming `~/.bashrc` changes apply universally. They only affect interactive bash shells for the current user.

**Solution:** Use symlinks in `/usr/local/bin` for true system-wide availability, or verify in the actual execution context.

### Build Directory Location

**Mistake:** Building in `/tmp` when coverage data (.gcda files) needs to persist.

Coverage data files (.gcda) are written to the build directory when the instrumented binary runs. If the build directory is in `/tmp` and gets cleaned, coverage collection will fail.

**Solution:** Build in a persistent location, or set `GCOV_PREFIX` and `GCOV_PREFIX_STRIP` to redirect coverage output:

```bash
export GCOV_PREFIX=/persistent/coverage/output
export GCOV_PREFIX_STRIP=3
```

### Missing gcov Library

**Mistake:** Forgetting `-lgcov` in LDFLAGS.

**Symptom:** Linker errors about undefined references to `__gcov_*` functions.

**Solution:** Include `-lgcov` in LDFLAGS during configure.

### Optimization Level

**Mistake:** Using `-O2` or `-O3` with coverage flags.

**Symptom:** Coverage reports show unexpected results due to compiler optimizations (inlining, dead code elimination).

**Solution:** Use `-O0` for accurate coverage mapping.

## Decision Guide

```
Is the binary needed system-wide for all processes?
├─ Yes → Use symlink in /usr/local/bin
└─ No
    ├─ Needed for all login shells? → Use /etc/profile.d/
    └─ Only for current user interactive shells? → Use ~/.bashrc

Do coverage files need to persist beyond session?
├─ Yes → Build in persistent directory (not /tmp)
└─ No → /tmp is acceptable

Is the build directory ephemeral?
├─ Yes → Configure GCOV_PREFIX to redirect .gcda output
└─ No → Default coverage output location is fine
```
