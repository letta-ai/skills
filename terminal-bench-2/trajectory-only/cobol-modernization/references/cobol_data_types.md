# COBOL Data Types Reference

## PICTURE Clause Symbols

| Symbol | Meaning | Python Equivalent |
|--------|---------|-------------------|
| `9` | Numeric digit (0-9) | `int` with formatting |
| `X` | Any character | `str` |
| `A` | Alphabetic only | `str` with validation |
| `V` | Implied decimal point | Divide/multiply by 10^n |
| `S` | Signed value | `int` (positive or negative) |
| `P` | Decimal scaling | Multiply by 10^n |
| `Z` | Zero-suppressed digit | Format with space padding |
| `.` | Decimal point (display) | Format string |
| `,` | Comma (display) | Format string |
| `$` | Currency symbol | Format string |
| `-` or `+` | Sign (display) | Format string |

## Common PICTURE Patterns

### Numeric Fields

| COBOL PICTURE | Length | Python Parsing | Python Formatting |
|---------------|--------|----------------|-------------------|
| `9(5)` | 5 bytes | `int(field)` | `f"{val:05d}"` |
| `9(10)` | 10 bytes | `int(field)` | `f"{val:010d}"` |
| `S9(5)` | 5 bytes* | `int(field)` | `f"{val:+05d}"` or handle sign |
| `9(5)V99` | 7 bytes | `int(field) / 100` | `f"{int(val*100):07d}"` |
| `9(3)V9(4)` | 7 bytes | `int(field) / 10000` | `f"{int(val*10000):07d}"` |

*Note: Sign may be stored in the last byte using overpunch or separate

### Alphanumeric Fields

| COBOL PICTURE | Length | Python Parsing | Python Formatting |
|---------------|--------|----------------|-------------------|
| `X(10)` | 10 bytes | `field.strip()` or `field` | `f"{val:<10}"` |
| `X(30)` | 30 bytes | `field.strip()` or `field` | `f"{val:<30}"` |
| `A(5)` | 5 bytes | `field.strip()` | `f"{val:<5}"` |

## Record Length Calculation

Calculate total record length by summing all field PICTURE lengths:

```
01 CUSTOMER-RECORD.
   05 CUST-ID       PIC X(5).      <- 5 bytes
   05 CUST-NAME     PIC X(30).     <- 30 bytes
   05 CUST-BALANCE  PIC 9(10).     <- 10 bytes
                                   --------
                                   45 bytes total
```

## File Handling Semantics

### READ Operation
- Reads next sequential record or specific key record
- Sets file status to indicate success/failure
- AT END clause triggers on end-of-file

Python equivalent:
```python
def read_record(file, record_length):
    data = file.read(record_length)
    if not data:
        return None  # AT END condition
    return data
```

### WRITE Operation
- Appends new record to file
- Used for new records only

Python equivalent:
```python
def write_record(file, record):
    file.write(record)
```

### REWRITE Operation
- Updates existing record in place
- Requires prior READ of the same record
- Record must be same length

Python equivalent (for sequential files):
```python
# Read all records into memory
records = []
while record := read_record(file, length):
    records.append(record)

# Modify specific record
records[index] = new_record

# Write all records back
with open(filename, 'wb') as f:
    for record in records:
        f.write(record)
```

### DELETE Operation
- Removes record from indexed file
- Record must be previously read

## Numeric Sign Conventions

COBOL has several ways to represent signed numbers:

### Trailing Overpunch (Common)
The last digit encodes the sign:

| Digit | Positive | Negative |
|-------|----------|----------|
| 0 | `{` | `}` |
| 1 | `A` | `J` |
| 2 | `B` | `K` |
| 3 | `C` | `L` |
| 4 | `D` | `M` |
| 5 | `E` | `N` |
| 6 | `F` | `O` |
| 7 | `G` | `P` |
| 8 | `H` | `Q` |
| 9 | `I` | `R` |

### Leading Separate Sign
`S9(5) SIGN LEADING SEPARATE` = 6 bytes: `+12345` or `-12345`

### Trailing Separate Sign
`S9(5) SIGN TRAILING SEPARATE` = 6 bytes: `12345+` or `12345-`

## USAGE Clause Effects

| USAGE | Storage | Python Handling |
|-------|---------|-----------------|
| DISPLAY (default) | Character format | Direct string parsing |
| COMP / BINARY | Binary integer | `struct.unpack()` |
| COMP-3 / PACKED-DECIMAL | Packed BCD | Custom decoding needed |
| COMP-1 | 4-byte float | `struct.unpack('f', ...)` |
| COMP-2 | 8-byte double | `struct.unpack('d', ...)` |

### COMP-3 Packed Decimal Decoding

```python
def decode_comp3(data: bytes) -> int:
    """Decode COMP-3 packed decimal."""
    result = 0
    for i, byte in enumerate(data[:-1]):
        result = result * 100 + (byte >> 4) * 10 + (byte & 0x0F)
    # Last byte: high nibble is digit, low nibble is sign
    last = data[-1]
    result = result * 10 + (last >> 4)
    sign = last & 0x0F
    if sign in (0x0D, 0x0B):  # Negative signs
        result = -result
    return result
```

## File Organization Types

| COBOL | Description | Python Equivalent |
|-------|-------------|-------------------|
| SEQUENTIAL | Records in order | Regular file, line-by-line |
| INDEXED | Key-based access | Dictionary or database |
| RELATIVE | Record number access | List or seek by offset |

## Common Translation Patterns

### Reading Fixed-Width Records

```python
def parse_record(line: str) -> dict:
    """Parse fixed-width COBOL record."""
    return {
        'field1': line[0:5].strip(),      # PIC X(5)
        'field2': int(line[5:15]),        # PIC 9(10)
        'field3': line[15:45].strip(),    # PIC X(30)
    }
```

### Writing Fixed-Width Records

```python
def format_record(data: dict) -> str:
    """Format as fixed-width COBOL record."""
    return (
        f"{data['field1']:<5}"    # PIC X(5) left-justified
        f"{data['field2']:010d}"  # PIC 9(10) zero-padded
        f"{data['field3']:<30}"   # PIC X(30) left-justified
    )
```

### Handling Implied Decimals

```python
# PIC 9(5)V99 - 7 digits with 2 implied decimal places
def read_decimal(field: str) -> float:
    return int(field) / 100

def write_decimal(value: float) -> str:
    return f"{int(value * 100):07d}"
```
