---
name: compile-compcert
description: Guidance for building CompCert, a formally verified C compiler. This skill applies when tasks involve compiling CompCert from source, setting up Coq/OCaml environments with opam, or building software with strict proof assistant dependencies. Use for CompCert compilation, Coq-dependent project builds, or formal verification toolchain setup.
---

# Building CompCert (Verified C Compiler)

## Overview

CompCert is a formally verified optimizing C compiler. Building it requires careful coordination of Coq (proof assistant), OCaml, and Menhir (parser generator) versions. The primary challenge is ensuring version compatibility across all dependencies before beginning compilation.

## Critical Pre-Build Analysis

Before installing any dependencies, perform these steps in order:

### 1. Obtain Source First

Download and extract the CompCert source before installing dependencies:
- Download the specific version tarball from GitHub releases or official mirrors
- Extract and locate the `configure` script
- Read the configure script to identify supported Coq versions

### 2. Check Version Requirements

Examine CompCert's configure script to find exact dependency requirements:
- Supported Coq version range (often specific minor versions only)
- Required OCaml version
- Required Menhir version
- The configure script typically contains explicit version checks

### 3. Verify System Compatibility

Check system requirements before proceeding:
- Architecture (x86_64 is most commonly supported for full backend)
- Operating system (Linux is primary target)
- Available memory (builds can be memory-intensive)
- Disk space for build artifacts

## Dependency Installation Approach

### Environment Setup with opam

CompCert requires opam (OCaml Package Manager) for managing OCaml and Coq:

1. Initialize opam if not already done
2. Create a switch with appropriate OCaml version
3. Set up the environment: `eval $(opam env)`
4. Install dependencies in correct order: OCaml → Menhir → Coq

### Version Selection Strategy

To avoid wasted effort from incompatible versions:

1. Check CompCert's configure script BEFORE installing Coq
2. Install the highest compatible Coq version within the supported range
3. Ensure Menhir version matches requirements
4. Verify all versions after installation

## Build Process

### Configuration

Run configure with appropriate target:
- Common targets: `x86_64-linux`, `x86_32-linux`, `arm-linux`
- Check available targets with `./configure --help`
- Note the installation prefix and binary locations

### Compilation

Build considerations:
- Full build includes proof checking and can be memory-intensive
- If encountering OOM (Out of Memory) errors:
  - Reduce parallel jobs (`make -j1` instead of parallel)
  - Consider adding swap space if in a container that allows it
  - Monitor memory usage during proof checking phases

### Installation and Verification

After successful build:
- Note where `ccomp` binary is installed
- Create symlinks if binary needs to be at a specific location
- Test with a simple C program compilation
- Verify the reported version matches expected version

## Common Pitfalls

### Dependency Order Mistakes

- Installing Coq before checking CompCert's requirements wastes time
- Multiple failed installation attempts consume significant resources
- Always read project requirements before installing dependencies

### Memory Issues

- Coq proof checking is memory-intensive
- Container environments may have memory limits
- Swap creation may be restricted in some environments
- Sequential builds (`-j1`) use less memory than parallel builds

### Environment Persistence

- opam environment must be sourced in each shell session
- `eval $(opam env)` needed before running opam-installed tools
- Consider setting up persistent environment configuration

### Version Verification

- CompCert version reported at runtime may differ from release tag
- Version 3.13.1 source may report as "3.13" at runtime
- Verify functionality rather than relying solely on version strings

## Verification Checklist

Before considering the task complete:

1. [ ] Binary exists at required location
2. [ ] `ccomp --version` executes without error
3. [ ] Simple C program compiles successfully
4. [ ] Generated executable runs correctly
5. [ ] Any linker warnings are understood (some are benign)

## Resource Management

### Cleanup Considerations

After successful build:
- Source tarballs can be removed
- Extracted source directories may be kept for reference or removed
- Build artifacts in source tree consume significant space

### Security Notes

- Verify source downloads against official checksums when available
- Building from official release tarballs preferred over arbitrary commits
- Note and investigate any unexpected warnings during compilation
