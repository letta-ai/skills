# Data Merge Patterns Reference

## File Format Reading Patterns

### CSV Files

```python
import csv

def read_csv_source(filepath):
    records = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records
```

Key considerations:
- Always specify encoding (utf-8 is safest default)
- Use `newline=''` to handle cross-platform line endings
- DictReader automatically uses first row as headers

### JSON Files

```python
import json

def read_json_source(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Handle both array and object with records key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    return [data]
```

Key considerations:
- JSON may be an array or object containing an array
- Check for common wrapper keys: `records`, `data`, `items`, `results`

### Parquet Files

```python
import pandas as pd

def read_parquet_source(filepath):
    df = pd.read_parquet(filepath)
    return df.to_dict('records')
```

Alternative with pyarrow:
```python
import pyarrow.parquet as pq

def read_parquet_source(filepath):
    table = pq.read_table(filepath)
    return table.to_pydict()  # Returns {column: [values]}
```

Key considerations:
- Requires `pyarrow` or `pandas` with pyarrow backend
- Schema is embedded in file - use `pq.read_schema(filepath)` to inspect
- Column types are preserved (integers stay integers)

### XML Files

```python
import xml.etree.ElementTree as ET

def read_xml_source(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    records = []
    for item in root.findall('.//record'):  # Adjust xpath as needed
        record = {}
        for child in item:
            record[child.tag] = child.text
        records.append(record)
    return records
```

Key considerations:
- XML structure varies widely - inspect file first
- May need to handle attributes vs text content
- Consider `xmltodict` library for simpler conversion

## Type Coercion Patterns

### Safe Integer Conversion

```python
def safe_int(value):
    """Convert to int, handling None and strings."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if not pd.isna(value) else None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ('none', 'null', 'na'):
            return None
        return int(value)
    return None
```

### Date Normalization

```python
from datetime import datetime

DATE_FORMATS = [
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%m/%d/%Y',
    '%Y/%m/%d',
    '%d-%m-%Y',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%SZ',
]

def normalize_date(value, output_format='%Y-%m-%d'):
    """Parse various date formats and normalize to standard format."""
    if value is None or value == '':
        return None

    if isinstance(value, datetime):
        return value.strftime(output_format)

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(str(value).strip(), fmt)
            return dt.strftime(output_format)
        except ValueError:
            continue

    return str(value)  # Return original if no format matches
```

### Null Value Handling

```python
NULL_REPRESENTATIONS = {None, '', 'null', 'NULL', 'None', 'none', 'NA', 'N/A', 'n/a'}

def is_null_value(value):
    """Check if value represents null/missing."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in NULL_REPRESENTATIONS:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return False

def normalize_null(value):
    """Convert null representations to Python None."""
    return None if is_null_value(value) else value
```

## Field Mapping Patterns

### Simple Rename Mapping

```python
def apply_field_mapping(record, mapping):
    """
    Apply field name mapping to a record.
    mapping = {'source_field': 'canonical_field', ...}
    """
    result = {}
    for source_field, canonical_field in mapping.items():
        if source_field in record:
            result[canonical_field] = record[source_field]
    return result
```

### Mapping with Type Coercion

```python
def apply_typed_mapping(record, mapping):
    """
    Apply mapping with type conversion.
    mapping = {
        'source_field': ('canonical_field', converter_func),
        ...
    }
    """
    result = {}
    for source_field, (canonical_field, converter) in mapping.items():
        if source_field in record:
            result[canonical_field] = converter(record[source_field])
    return result

# Example usage
SOURCE_A_MAPPING = {
    'userId': ('user_id', safe_int),
    'userName': ('name', str),
    'userEmail': ('email', lambda x: x.lower().strip() if x else None),
    'createdDate': ('created_date', normalize_date),
}
```

## Merge Patterns

### Priority-Based Merge

```python
def merge_by_priority(records_by_source, key_field, source_priority):
    """
    Merge records from multiple sources with priority-based conflict resolution.

    records_by_source = {'source_a': [...], 'source_b': [...]}
    source_priority = ['source_a', 'source_b', 'source_c']  # highest first
    """
    merged = {}
    conflicts = []

    # Process sources in reverse priority (lowest first, highest overwrites)
    for source in reversed(source_priority):
        if source not in records_by_source:
            continue
        for record in records_by_source[source]:
            key = record[key_field]
            if key not in merged:
                merged[key] = {'_source': source, **record}
            else:
                # Check for conflicts and merge
                existing = merged[key]
                for field, new_value in record.items():
                    if field == key_field:
                        continue
                    old_value = existing.get(field)
                    if old_value is not None and new_value is not None:
                        if old_value != new_value:
                            conflicts.append({
                                'key': key,
                                'field': field,
                                'values': {
                                    existing['_source']: old_value,
                                    source: new_value
                                },
                                'selected': new_value,
                                'selected_source': source
                            })
                    # Higher priority source overwrites
                    if new_value is not None:
                        existing[field] = new_value
                        existing['_source'] = source

    # Clean up internal tracking
    for record in merged.values():
        record.pop('_source', None)

    return list(merged.values()), conflicts
```

### Conflict Detection (Separate from Merge)

```python
def detect_conflicts(records_by_source, key_field):
    """
    Detect all conflicts across sources without resolving them.
    Returns list of conflicts with all source values.
    """
    # Group by key
    by_key = {}
    for source, records in records_by_source.items():
        for record in records:
            key = record[key_field]
            if key not in by_key:
                by_key[key] = {}
            by_key[key][source] = record

    conflicts = []
    for key, source_records in by_key.items():
        if len(source_records) < 2:
            continue  # No conflict possible with single source

        # Get all fields across all sources for this key
        all_fields = set()
        for record in source_records.values():
            all_fields.update(record.keys())
        all_fields.discard(key_field)

        for field in all_fields:
            values = {}
            for source, record in source_records.items():
                if field in record and not is_null_value(record[field]):
                    values[source] = record[field]

            # Conflict exists if multiple sources have different non-null values
            unique_values = set(str(v) for v in values.values())
            if len(unique_values) > 1:
                conflicts.append({
                    'key': key,
                    'field': field,
                    'values': values
                })

    return conflicts
```

## Output Patterns

### JSON Output with Proper Null Handling

```python
import json

def write_json_output(records, filepath, indent=2):
    """Write records to JSON with proper null handling."""
    # Ensure None values become JSON null, not string "None"
    def clean_record(record):
        return {
            k: (None if v is None else v)
            for k, v in record.items()
        }

    cleaned = [clean_record(r) for r in records]

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=indent, default=str)
```

### Conflict Report Output

```python
def write_conflict_report(conflicts, filepath):
    """Write detailed conflict report."""
    report = {
        'total_conflicts': len(conflicts),
        'conflicts_by_key': {},
        'conflicts': conflicts
    }

    # Group by key for summary
    for conflict in conflicts:
        key = conflict['key']
        if key not in report['conflicts_by_key']:
            report['conflicts_by_key'][key] = []
        report['conflicts_by_key'][key].append(conflict['field'])

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
```

## Verification Patterns

### Comprehensive Verification Script

```python
def verify_merge_output(merged_records, conflicts, sources_info, key_field):
    """
    Verify merge output meets requirements.
    Returns (success: bool, issues: list)
    """
    issues = []

    # 1. Count verification
    expected_keys = set()
    for source_records in sources_info.values():
        for record in source_records:
            expected_keys.add(record[key_field])

    actual_keys = set(r[key_field] for r in merged_records)

    if expected_keys != actual_keys:
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        if missing:
            issues.append(f"Missing keys in output: {missing}")
        if extra:
            issues.append(f"Unexpected keys in output: {extra}")

    # 2. Type verification
    for record in merged_records:
        key_val = record.get(key_field)
        if not isinstance(key_val, int):
            issues.append(f"Key {key_val} is not integer: {type(key_val)}")

    # 3. Null value verification (no string "None")
    for record in merged_records:
        for field, value in record.items():
            if value == "None" or value == "null":
                issues.append(f"String null found: {record[key_field]}.{field} = '{value}'")

    # 4. Conflict count reasonableness
    if len(merged_records) > 0 and len(conflicts) > len(merged_records) * 10:
        issues.append(f"Suspiciously high conflict count: {len(conflicts)}")

    return len(issues) == 0, issues
```

### Sample-Based Verification

```python
def verify_sample_record(merged_record, sources_info, key_field, priority):
    """
    Trace a single record through all sources to verify merge correctness.
    """
    key = merged_record[key_field]
    print(f"\n=== Tracing record {key} ===")

    for source in priority:
        if source in sources_info:
            source_record = next(
                (r for r in sources_info[source] if r[key_field] == key),
                None
            )
            if source_record:
                print(f"\n{source}:")
                for field, value in source_record.items():
                    print(f"  {field}: {value}")

    print(f"\nMerged result:")
    for field, value in merged_record.items():
        print(f"  {field}: {value}")
```
