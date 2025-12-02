# SQLite WAL File Format Reference

## Overview

The Write-Ahead Log (WAL) is a journaling mechanism in SQLite that records database changes before they are committed to the main database file. Understanding the WAL format is essential for manual recovery operations.

## WAL File Structure

A WAL file consists of a header followed by zero or more frames:

```
+------------------+
| WAL Header       |  (32 bytes)
+------------------+
| Frame 1          |  (Header + Page)
+------------------+
| Frame 2          |  (Header + Page)
+------------------+
| ...              |
+------------------+
| Frame N          |  (Header + Page)
+------------------+
```

## WAL Header (32 bytes)

| Offset | Size | Description |
|--------|------|-------------|
| 0      | 4    | Magic number: 0x377f0682 (little-endian) or 0x377f0683 (big-endian) |
| 4      | 4    | File format version (currently 3007000) |
| 8      | 4    | Database page size |
| 12     | 4    | Checkpoint sequence number |
| 16     | 4    | Salt-1: random value, changes with each checkpoint |
| 20     | 4    | Salt-2: random value, changes with each checkpoint |
| 24     | 4    | Checksum-1: first part of header checksum |
| 28     | 4    | Checksum-2: second part of header checksum |

### Magic Number Detection

To identify a valid WAL file:

```bash
# Check for WAL magic bytes (little-endian)
xxd -l 4 file.db-wal
# Expected: 377f 0682

# Or in Python
with open('file.db-wal', 'rb') as f:
    magic = f.read(4)
    if magic == b'\x37\x7f\x06\x82':
        print("Valid WAL (little-endian)")
    elif magic == b'\x37\x7f\x06\x83':
        print("Valid WAL (big-endian)")
```

## Frame Structure

Each frame consists of a 24-byte header followed by a database page:

### Frame Header (24 bytes)

| Offset | Size | Description |
|--------|------|-------------|
| 0      | 4    | Page number (1-indexed, page 1 is first page of database) |
| 4      | 4    | Size of database file in pages after commit (0 if not commit frame) |
| 8      | 4    | Salt-1 copy (must match header salt-1) |
| 12     | 4    | Salt-2 copy (must match header salt-2) |
| 16     | 4    | Checksum-1: cumulative checksum part 1 |
| 20     | 4    | Checksum-2: cumulative checksum part 2 |

### Frame Page Data

Following the 24-byte header is the actual database page content. The size equals the page size specified in the WAL header.

## Checksum Algorithm

SQLite uses a cumulative checksum for WAL integrity:

```python
def wal_checksum(data, s0=0, s1=0, big_endian=False):
    """
    Calculate WAL checksum.

    Args:
        data: bytes to checksum (must be multiple of 8)
        s0, s1: initial checksum values
        big_endian: True if WAL uses big-endian format

    Returns:
        (s0, s1) checksum pair
    """
    fmt = '>II' if big_endian else '<II'
    for i in range(0, len(data), 8):
        a, b = struct.unpack(fmt, data[i:i+8])
        s0 = (s0 + a + s1) & 0xFFFFFFFF
        s1 = (s1 + b + s0) & 0xFFFFFFFF
    return s0, s1
```

## Recovery Techniques

### Extracting Frames Manually

```python
import struct

def parse_wal_file(filepath):
    """Parse WAL file and extract frames."""
    with open(filepath, 'rb') as f:
        # Read header
        header = f.read(32)
        magic = struct.unpack('<I', header[0:4])[0]
        big_endian = (magic == 0x377f0683)

        fmt = '>' if big_endian else '<'
        page_size = struct.unpack(f'{fmt}I', header[8:12])[0]

        frames = []
        frame_size = 24 + page_size

        while True:
            frame_header = f.read(24)
            if len(frame_header) < 24:
                break

            page_num = struct.unpack(f'{fmt}I', frame_header[0:4])[0]
            commit_size = struct.unpack(f'{fmt}I', frame_header[4:8])[0]

            page_data = f.read(page_size)
            if len(page_data) < page_size:
                break

            frames.append({
                'page_num': page_num,
                'is_commit': commit_size > 0,
                'data': page_data
            })

        return frames
```

### Identifying Valid Frames

To verify frame integrity:

1. Check that salt values in frame header match WAL header
2. Verify cumulative checksum
3. Confirm page number is within valid range

```python
def validate_frame(wal_header, frame_header, frame_data, prev_checksum):
    """Validate a WAL frame."""
    # Extract salts
    header_salt1 = struct.unpack('<I', wal_header[16:20])[0]
    header_salt2 = struct.unpack('<I', wal_header[20:24])[0]
    frame_salt1 = struct.unpack('<I', frame_header[8:12])[0]
    frame_salt2 = struct.unpack('<I', frame_header[12:16])[0]

    if header_salt1 != frame_salt1 or header_salt2 != frame_salt2:
        return False, "Salt mismatch"

    # Verify checksum
    s0, s1 = prev_checksum
    s0, s1 = wal_checksum(frame_header[:8], s0, s1)
    s0, s1 = wal_checksum(frame_data, s0, s1)

    expected_s0 = struct.unpack('<I', frame_header[16:20])[0]
    expected_s1 = struct.unpack('<I', frame_header[20:24])[0]

    if s0 != expected_s0 or s1 != expected_s1:
        return False, "Checksum mismatch"

    return True, (s0, s1)
```

## Common Encrypted WAL Patterns

### SQLCipher Detection

SQLCipher encrypts the entire WAL file including headers. Signs:
- No recognizable magic bytes
- High entropy throughout
- File size is multiple of page size + overhead

### Custom XOR Encryption

Some implementations XOR the WAL with a key:

```python
def try_xor_decrypt(data, key):
    """Attempt XOR decryption with given key."""
    if isinstance(key, int):
        key = bytes([key])
    key_len = len(key)
    result = bytearray(len(data))
    for i, byte in enumerate(data):
        result[i] = byte ^ key[i % key_len]
    return bytes(result)

# Test for valid WAL header after decryption
def detect_xor_key(encrypted_data, max_key_len=16):
    """Try to detect XOR key by checking for valid WAL magic."""
    expected_magic = b'\x37\x7f\x06\x82'

    for key_len in range(1, max_key_len + 1):
        # Derive key from expected magic
        key = bytes([encrypted_data[i] ^ expected_magic[i] for i in range(min(4, key_len))])
        if key_len > 4:
            # Extend key by trying variations
            continue

        decrypted = try_xor_decrypt(encrypted_data[:32], key)
        if decrypted[:4] == expected_magic:
            # Verify page size is reasonable
            page_size = struct.unpack('<I', decrypted[8:12])[0]
            if page_size in [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]:
                return key

    return None
```

## Database Page Structure (for reference)

Each database page recovered from WAL has specific structure based on page type:

| Page Type | First Byte | Description |
|-----------|------------|-------------|
| 0x02      | Interior index B-tree page |
| 0x05      | Interior table B-tree page |
| 0x0A      | Leaf index B-tree page |
| 0x0D      | Leaf table B-tree page |
| 0x00      | Overflow or free page |

### Extracting Records from Leaf Pages

```python
def parse_leaf_table_page(page_data):
    """Parse a leaf table B-tree page to extract records."""
    if page_data[0] != 0x0D:
        return []  # Not a leaf table page

    # Page header
    freeblock_start = struct.unpack('>H', page_data[1:3])[0]
    num_cells = struct.unpack('>H', page_data[3:5])[0]
    cell_content_start = struct.unpack('>H', page_data[5:7])[0]

    # Cell pointer array starts at offset 8
    cell_pointers = []
    for i in range(num_cells):
        offset = 8 + i * 2
        cell_ptr = struct.unpack('>H', page_data[offset:offset+2])[0]
        cell_pointers.append(cell_ptr)

    # Parse each cell (simplified)
    records = []
    for ptr in cell_pointers:
        # Each cell contains: payload_size (varint), rowid (varint), payload
        # This is simplified - full implementation needs varint parsing
        records.append({
            'offset': ptr,
            'raw': page_data[ptr:ptr+64]  # First 64 bytes for inspection
        })

    return records
```

## Useful Commands

### Quick WAL Inspection

```bash
# View WAL header
xxd -l 32 database.db-wal

# Check file entropy (high = likely encrypted)
ent database.db-wal | head -1

# Extract readable strings
strings -n 8 database.db-wal

# View hex dump with ASCII
hexdump -C database.db-wal | head -50

# Check file size and page alignment
stat database.db-wal
```

### SQLite Recovery Commands

```bash
# Attempt recovery using SQLite
sqlite3 database.db ".recover" > recovered.sql

# Dump what's possible
sqlite3 database.db ".dump" > dump.sql

# Check integrity
sqlite3 database.db "PRAGMA integrity_check;"

# Force checkpoint (merge WAL into main DB)
sqlite3 database.db "PRAGMA wal_checkpoint(TRUNCATE);"
```
