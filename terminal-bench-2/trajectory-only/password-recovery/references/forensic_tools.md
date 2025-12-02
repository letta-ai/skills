# Forensic Tools Reference

## Filesystem Recovery Tools

### extundelete (ext2/3/4)

Primary tool for recovering deleted files from ext filesystems.

**Installation check:**
```bash
which extundelete
```

**Key operations:**

```bash
# List all recoverable files
extundelete --list image.img

# Recover a specific file by path
extundelete --restore-file app/password.txt image.img

# Recover all deleted files
extundelete --restore-all image.img

# Output directory
extundelete --restore-all --output-dir ./recovered image.img
```

**Important notes:**
- Works only on ext2/3/4 filesystems
- Cannot recover files if blocks have been overwritten
- Recovered files appear in RECOVERED_FILES directory by default

### debugfs (ext2/3/4)

Interactive filesystem debugger for ext filesystems.

**Key commands within debugfs:**

```bash
debugfs image.img

# List directory contents including deleted files
ls -d /path/to/dir

# Show inode information
stat <inode_number>
stat /path/to/file

# Read file contents
cat /path/to/file

# Dump file to external location
dump /path/to/file /tmp/output.txt

# List deleted inodes
lsdel

# Show filesystem superblock
show_super_stats
```

**Searching for deleted content:**
```bash
# Within debugfs
lsdel          # List recently deleted inodes
ncheck <inode> # Get filename for inode
```

### testdisk

Multi-filesystem recovery tool supporting FAT, NTFS, ext, and more.

**Key operations:**

```bash
# Interactive mode
testdisk image.img

# Within testdisk:
# 1. Select partition table type
# 2. Analyze → Quick Search or Deeper Search
# 3. Browse files → copy to recover
```

**File recovery navigation:**
- Use arrow keys to navigate
- Press 'c' to copy selected files
- Press 'C' to copy current directory
- Red entries = deleted files

### photorec

File carving tool that recovers files by signature, ignoring filesystem.

**Key operations:**

```bash
# Interactive mode (recommended)
photorec image.img

# Command line
photorec /d /output/dir /cmd image.img search
```

**When to use photorec:**
- When filesystem is severely damaged
- When other tools fail
- When recovering specific file types by signature

### ntfsundelete (NTFS)

Recovery tool for NTFS filesystems.

```bash
# Scan for deleted files
ntfsundelete image.img --scan

# Recover specific file
ntfsundelete image.img --undelete --match "filename"

# Recover by inode
ntfsundelete image.img --undelete --inodes 123
```

## Disk Image Analysis Tools

### file

Identify file type by magic bytes.

```bash
file image.img
# Output examples:
# - "Linux rev 1.0 ext4 filesystem data"
# - "Zip archive data"
# - "data" (unrecognized format)
```

**Limitation:** May report "data" for valid filesystem images. Always verify with hex inspection.

### xxd / hexdump

Hex dump utilities for manual inspection.

```bash
# View first 256 bytes
xxd image.img | head -16

# View specific offset
xxd -s 1024 -l 256 image.img

# View superblock location (ext4)
xxd -s 1024 -l 128 image.img
```

**Common file signatures:**

| Signature (hex) | Format |
|-----------------|--------|
| 504B0304 | ZIP archive |
| 377ABCAF | 7z archive |
| 1F8B08 | gzip |
| 53EF (at offset 1080) | ext2/3/4 superblock magic |
| 4E544653 | NTFS |
| EB (at offset 0) | FAT boot sector |

### strings

Extract printable strings from binary data.

```bash
# Basic extraction (default min length 4)
strings image.img

# Minimum 8 characters
strings -n 8 image.img

# Include offset in output
strings -t x image.img

# Search specific patterns
strings image.img | grep -i "password"
strings image.img | grep -E "[A-Z0-9]{20,}"
```

### grep (binary search)

Search for patterns directly in binary files.

```bash
# Find byte offset of pattern
grep -boa "PASSWORD" image.img

# Find with context (note: context is byte-based, not line-based)
grep -oba "PASSWORD" image.img

# Count occurrences
grep -c "PASSWORD" image.img
```

## Mounting Disk Images

### Loop device mounting (Linux)

```bash
# Mount ext filesystem image
sudo mount -o loop,ro image.img /mnt/recovery

# Mount with offset (for partition images)
sudo mount -o loop,ro,offset=1048576 image.img /mnt/recovery

# Unmount
sudo umount /mnt/recovery
```

### kpartx (for partitioned images)

```bash
# Create loop devices for partitions
sudo kpartx -av image.img

# Access partitions as /dev/mapper/loop0p1, etc.
sudo mount /dev/mapper/loop0p1 /mnt/recovery

# Remove loop devices
sudo kpartx -dv image.img
```

## Archive Extraction

### ZIP files

```bash
# List contents
unzip -l archive.zip

# Extract all
unzip archive.zip

# Extract specific file
unzip archive.zip path/to/file.txt

# Test archive integrity
unzip -t archive.zip
```

### 7z files

```bash
# List contents
7z l archive.7z

# Extract all
7z x archive.7z

# Extract to specific directory
7z x archive.7z -o./output
```

## Best Practices

1. **Always work on copies** - Never modify original evidence
2. **Document everything** - Record commands, outputs, and observations
3. **Try structured recovery first** - Use filesystem-aware tools before raw searching
4. **Verify file format** - Don't assume based on extension or initial inspection
5. **Check multiple candidates** - Don't stop at first plausible result
6. **Validate context** - Examine bytes around any discovered data
