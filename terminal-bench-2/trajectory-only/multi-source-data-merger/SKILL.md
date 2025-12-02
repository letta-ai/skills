---
name: multi-source-data-merger
description: This skill provides guidance for merging data from multiple heterogeneous sources (CSV, JSON, Parquet, XML, etc.) into unified output formats with conflict detection and resolution. Use when tasks involve combining data from different file formats, field mapping between schemas, priority-based conflict resolution, or generating merged datasets with conflict reports.
---

# Multi-Source Data Merger

## Overview

This skill guides the process of merging data from multiple heterogeneous sources into unified output formats. It covers reading diverse file formats, mapping fields across different schemas, detecting and resolving conflicts based on priority rules, and producing clean merged output with comprehensive conflict documentation.

## Workflow

### Phase 1: Source Analysis and Schema Discovery

Before writing any code, thoroughly inspect all source files to understand their structure:

1. **Identify all source files and their formats**
   - List all input files and determine their types (CSV, JSON, Parquet, XML, etc.)
   - Note which formats require special libraries (e.g., `pyarrow` or `pandas` for Parquet)

2. **Extract actual schemas from each source**
   - For readable formats (CSV, JSON, XML): Read and document exact field names
   - For binary formats (Parquet): Use appropriate tools to inspect schema
   - Never assume field names from task descriptions alone

3. **Document field mappings explicitly**
   - Create a clear mapping table: `source_field -> canonical_field`
   - Note type differences (e.g., `userId` as string vs integer)
   - Identify which fields exist in which sources

4. **Identify the merge key**
   - Determine which field(s) uniquely identify records across sources
   - Verify the key exists and is consistent across all sources

### Phase 2: Environment Setup

1. **Create isolated environment**
   - Use virtual environment (venv, conda, uv) for dependency isolation
   - Document all required dependencies before installation

2. **Install dependencies incrementally**
   - Install only what is needed for each format
   - Verify each library works before proceeding
   - Common dependencies: `pandas`, `pyarrow`, `openpyxl`, `xmltodict`

3. **Avoid repeated environment commands**
   - Set environment variables once at the start
   - Create helper scripts for repeated operations if needed

### Phase 3: Implementation Strategy

#### Modular Code Structure

Structure the solution with clear separation of concerns:

```
1. File readers (one function per format)
2. Field mappers (transform to canonical schema)
3. Merge logic (combine records by key)
4. Conflict detector (identify value differences)
5. Conflict resolver (apply priority rules)
6. Output writers (generate required formats)
```

#### Incremental Development

1. **Start with file reading**
   - Implement and test each reader independently
   - Verify data loads correctly before proceeding
   - Print sample records to confirm structure

2. **Implement field mapping**
   - Transform each source to canonical schema
   - Handle type coercion explicitly (strings to integers, date parsing)
   - Test mapping on sample records

3. **Build merge logic**
   - Combine all records by merge key
   - Track which source each value came from
   - Handle records that appear in only one source

4. **Add conflict detection**
   - Compare values across sources for same key
   - Define what constitutes a conflict clearly
   - Distinguish between: missing field, null value, different value

5. **Implement conflict resolution**
   - Apply priority rules consistently
   - Document which source "won" for each conflict
   - Preserve conflict information for reporting

### Phase 4: Verification Strategy

#### Verify Each Component

1. **Source reading verification**
   - Count records per source
   - Sample first/last records
   - Verify all expected fields present

2. **Merge verification**
   - Count unique keys in merged output
   - Verify: `merged_count = unique_keys_across_all_sources`
   - Check records appearing in multiple sources

3. **Conflict verification**
   - Manually trace at least one known conflict
   - Verify conflict count matches expectations
   - Check conflict resolution followed priority rules

4. **Output verification**
   - Validate output format (JSON structure, CSV headers)
   - Verify required fields present with correct types
   - Check for unintended None/null values

#### Verification Script Pattern

Create a dedicated verification step that checks:
- Record counts match expectations
- All required fields present
- Data types are correct
- No unexpected null values
- Conflict counts are reasonable

## Common Pitfalls

### Schema and Field Mapping

| Pitfall | Prevention |
|---------|------------|
| Assuming field names without verification | Always read and inspect actual source files first |
| Missing field type coercion | Explicitly convert types (especially IDs to integers) |
| Inconsistent date formats | Normalize all dates to a single format during mapping |
| None vs null vs missing confusion | Define explicit handling rules for each case |

### Conflict Detection

| Pitfall | Prevention |
|---------|------------|
| Unclear conflict definition | Document exactly what constitutes a conflict before coding |
| Missing vs null not distinguished | Treat "field not present" differently from "field is null" |
| Counting conflicts incorrectly | Define: per-field, per-record, or per-user-field combination |
| Not detecting all conflict types | Test with records that have conflicts in every field |

### Implementation

| Pitfall | Prevention |
|---------|------------|
| Writing full script without testing | Build incrementally, test each component |
| Syntax errors in large scripts | Validate script syntax before running |
| Truncated file writes | Verify complete file was written (check line count or file size) |
| No error handling for edge cases | Add try/catch for file operations and data parsing |

### Output Quality

| Pitfall | Prevention |
|---------|------------|
| String "None" instead of null | Use proper JSON null values, not string representations |
| Inconsistent output format | Validate output against schema/requirements |
| Missing records in merge | Verify all unique keys from all sources appear in output |
| Duplicate records | Check for and handle duplicates within single sources |

## Edge Cases Checklist

Before considering the implementation complete, verify handling of:

- [ ] Records appearing in only one source (no conflict possible)
- [ ] Records appearing in all sources with identical values (no conflict)
- [ ] Records with conflicts in every mapped field
- [ ] Fields that exist in some sources but not others
- [ ] Explicit null/empty values vs missing fields
- [ ] Type variations (string "123" vs integer 123)
- [ ] Date format variations across sources
- [ ] Duplicate records within a single source
- [ ] Empty source files
- [ ] Very large files (memory considerations)

## Output Requirements Checklist

For the merged data output:
- [ ] Correct file format (JSON, CSV, etc.)
- [ ] All required fields present
- [ ] Correct data types (especially numeric IDs)
- [ ] Proper null handling (not string "None")
- [ ] Records sorted if required

For the conflicts report:
- [ ] All conflicts documented
- [ ] Source of each conflicting value identified
- [ ] Resolution (winning value) clearly indicated
- [ ] Conflict count accurate and well-defined

## References

This skill includes a reference guide for detailed information:

### references/

- `data_merge_patterns.md` - Detailed patterns for common merge scenarios, type coercion strategies, and conflict resolution approaches
