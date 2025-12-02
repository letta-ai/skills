# ELF Format Reference

## ELF Header Structure

The ELF header is located at the beginning of every ELF file and describes the file's organization.

### Identification (e_ident) - First 16 bytes

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | Magic | `\x7fELF` (0x7f 0x45 0x4c 0x46) |
| 4 | 1 | Class | 1 = 32-bit, 2 = 64-bit |
| 5 | 1 | Data | 1 = little-endian, 2 = big-endian |
| 6 | 1 | Version | ELF version (usually 1) |
| 7 | 1 | OS/ABI | Target OS ABI |
| 8 | 8 | Padding | Unused, should be zero |

### 64-bit ELF Header (Elf64_Ehdr)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 16 | e_ident | Magic number and other info |
| 16 | 2 | e_type | Object file type |
| 18 | 2 | e_machine | Architecture |
| 20 | 4 | e_version | Object file version |
| 24 | 8 | e_entry | Entry point virtual address |
| 32 | 8 | e_phoff | Program header table file offset |
| 40 | 8 | e_shoff | Section header table file offset |
| 48 | 4 | e_flags | Processor-specific flags |
| 52 | 2 | e_ehsize | ELF header size in bytes |
| 54 | 2 | e_phentsize | Program header table entry size |
| 56 | 2 | e_phnum | Program header table entry count |
| 58 | 2 | e_shentsize | Section header table entry size |
| 60 | 2 | e_shnum | Section header table entry count |
| 62 | 2 | e_shstrndx | Section header string table index |

### 32-bit ELF Header (Elf32_Ehdr)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 16 | e_ident | Magic number and other info |
| 16 | 2 | e_type | Object file type |
| 18 | 2 | e_machine | Architecture |
| 20 | 4 | e_version | Object file version |
| 24 | 4 | e_entry | Entry point virtual address |
| 28 | 4 | e_phoff | Program header table file offset |
| 32 | 4 | e_shoff | Section header table file offset |
| 36 | 4 | e_flags | Processor-specific flags |
| 40 | 2 | e_ehsize | ELF header size in bytes |
| 42 | 2 | e_phentsize | Program header table entry size |
| 44 | 2 | e_phnum | Program header table entry count |
| 46 | 2 | e_shentsize | Section header table entry size |
| 48 | 2 | e_shnum | Section header table entry count |
| 50 | 2 | e_shstrndx | Section header string table index |

## Program Header Structure

Program headers describe segments used for runtime execution.

### 64-bit Program Header (Elf64_Phdr) - 56 bytes

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | p_type | Segment type |
| 4 | 4 | p_flags | Segment flags |
| 8 | 8 | p_offset | Segment file offset |
| 16 | 8 | p_vaddr | Segment virtual address |
| 24 | 8 | p_paddr | Segment physical address |
| 32 | 8 | p_filesz | Segment size in file |
| 40 | 8 | p_memsz | Segment size in memory |
| 48 | 8 | p_align | Segment alignment |

### 32-bit Program Header (Elf32_Phdr) - 32 bytes

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | p_type | Segment type |
| 4 | 4 | p_offset | Segment file offset |
| 8 | 4 | p_vaddr | Segment virtual address |
| 12 | 4 | p_paddr | Segment physical address |
| 16 | 4 | p_filesz | Segment size in file |
| 20 | 4 | p_memsz | Segment size in memory |
| 24 | 4 | p_flags | Segment flags |
| 28 | 4 | p_align | Segment alignment |

## Segment Types (p_type)

| Value | Name | Description |
|-------|------|-------------|
| 0 | PT_NULL | Unused entry |
| 1 | PT_LOAD | Loadable segment |
| 2 | PT_DYNAMIC | Dynamic linking info |
| 3 | PT_INTERP | Interpreter path |
| 4 | PT_NOTE | Auxiliary information |
| 5 | PT_SHLIB | Reserved |
| 6 | PT_PHDR | Program header table |
| 7 | PT_TLS | Thread-local storage |

**PT_LOAD segments** are the primary targets for memory extraction. These define regions of the file that are loaded into memory at runtime.

## Segment Flags (p_flags)

| Value | Name | Description |
|-------|------|-------------|
| 0x1 | PF_X | Execute permission |
| 0x2 | PF_W | Write permission |
| 0x4 | PF_R | Read permission |

## Common Load Addresses

| Architecture | Non-PIE Base | PIE Base |
|--------------|--------------|----------|
| x86-64 | 0x400000 | 0x0 (relative) |
| x86 (32-bit) | 0x08048000 | 0x0 (relative) |
| ARM64 | 0x400000 | 0x0 (relative) |
| ARM32 | 0x10000 | 0x0 (relative) |

## BSS Section Handling

When `p_memsz > p_filesz`:
- The file contains `p_filesz` bytes of initialized data
- The remaining `(p_memsz - p_filesz)` bytes are uninitialized (BSS)
- At runtime, BSS bytes are zero-initialized
- For extraction: decide whether to include zeros for BSS or only file-backed data

## Useful Commands

```bash
# Display ELF header
readelf -h <binary>

# Display program headers
readelf -l <binary>

# Display section headers
readelf -S <binary>

# Display all headers
readelf -a <binary>

# Hex dump of specific section
objdump -s -j .text <binary>

# Raw hex dump
hexdump -C <binary> | head -50
od -A x -t x1z <binary> | head -50
```
