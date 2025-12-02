---
name: large-scale-text-editing
description: Guidance for transforming large text files (thousands to millions of rows) using text editors like Vim. This skill should be used when the task involves bulk text transformations, CSV manipulation, column reordering, regex-based find-and-replace operations, or when there are keystroke/efficiency constraints. Applies to tasks requiring macro-based editing, batch substitutions, or complex text processing where understanding the transformation pattern from input/output samples is needed.
---

# Large Scale Text Editing

## Overview

This skill provides guidance for efficiently transforming large text files using text editors (primarily Vim). It covers pattern recognition from input/output samples, macro-based transformations, and verification strategies for bulk operations on files with thousands to millions of rows.

## When to Use This Skill

- Transforming CSV or delimited text files with many rows
- Bulk find-and-replace operations with regex patterns
- Column reordering, reformatting, or restructuring text data
- Tasks with keystroke or efficiency constraints
- Any text transformation where a sample input/expected output is provided

## Approach

### 1. Understand the Transformation Requirements

Before writing any transformation code or macros:

1. **Sample the data appropriately** - Never attempt to read entire large files directly. Use `head`, `tail`, or `sed` to extract samples:
   ```bash
   head -n 20 input.csv > sample_input.csv
   head -n 20 expected.csv > sample_expected.csv
   ```

2. **Compare input and expected output** - Identify all differences:
   - Whitespace changes (trimming, removal)
   - Case changes (uppercase, lowercase)
   - Column/field reordering
   - Delimiter changes
   - Content transformations

3. **Spot-check throughout the file** - Do not assume all rows follow the same pattern:
   ```bash
   sed -n '1p;500000p;999999p' input.csv  # Check beginning, middle, end
   ```

4. **Check for edge cases** in the data:
   - Empty fields
   - Fields with more or fewer delimiters than expected
   - Special characters that may interfere with regex
   - Quoted fields containing delimiters

### 2. Plan the Transformation

Decompose the transformation into discrete, testable operations:

1. **List each transformation step** (e.g., remove whitespace, uppercase, reorder columns)
2. **Order steps logically** - Some transformations may depend on others
3. **Consider efficiency** - If keystroke constraints exist, plan to minimize redundant operations

### 3. Test on a Small Sample First

Always verify the transformation works correctly before applying to the full file:

1. Create a backup of the original file before any modifications:
   ```bash
   cp input.csv input.csv.backup
   ```

2. Test on a small subset:
   ```bash
   head -n 100 input.csv > test_input.csv
   # Apply transformation to test_input.csv
   # Compare with expected output
   ```

3. Validate results match expected output exactly:
   ```bash
   diff test_output.csv expected_subset.csv
   ```

### 4. Apply to Full File

Only after successful small-scale testing:

1. Ensure backup exists
2. Apply the transformation
3. Verify immediately (see verification strategies below)

## Vim-Specific Guidance

### Macro-Based Transformations

For repetitive operations across many lines:

1. **Record macros for each distinct operation**:
   - `qa` to start recording into register `a`
   - Perform the operation on one line
   - `q` to stop recording
   - `@a` to replay, `100@a` to replay 100 times

2. **Use `:normal` for applying normal-mode commands**:
   ```vim
   :%normal @a    " Apply macro a to all lines
   ```

3. **Use substitution for global changes**:
   ```vim
   :%s/\s\+//g           " Remove all whitespace
   :%s/.*/\U&/           " Uppercase entire line
   :%s/\([^,]*\),\([^,]*\),\([^,]*\)/\3,\2,\1/  " Reorder 3 columns
   ```

### Counting Keystrokes

If there are keystroke constraints:

1. **Count actual keystrokes, not escape sequences** - In Vimscript strings, `\\s` represents `\s` (one escape + one character)
2. **Document each macro's keystroke count separately**
3. **Consider that `:` commands count each character including the colon and Enter**

### Vim Script Files

For reproducible transformations, create a Vim script:

```vim
" transform.vim
" Load macros
let @a = 'macro_content_here'
let @b = 'another_macro_here'

" Apply transformations
%s/pattern/replacement/g
%normal @a

" Save and exit
wq
```

Run with: `vim -s transform.vim input.csv`

## Verification Strategies

### Mandatory Checks

1. **Byte-for-byte comparison** with expected output:
   ```bash
   diff output.csv expected.csv
   echo $?  # Should be 0 for identical files
   ```

2. **Line count verification**:
   ```bash
   wc -l output.csv expected.csv  # Must match
   ```

3. **Spot-check random rows**:
   ```bash
   diff <(sed -n '12345p' output.csv) <(sed -n '12345p' expected.csv)
   ```

### Additional Validation

- **Check file size** - Transformed file should be in expected size range
- **Verify no data loss** - Row counts should match (unless filtering)
- **Check encoding** - Ensure no corruption of special characters
- **Validate structure** - Correct number of columns/delimiters per row

## Common Pitfalls

### Data Handling

| Pitfall | Prevention |
|---------|------------|
| Reading entire large file into context | Use `head`, `tail`, `sed -n` for sampling |
| Assuming uniform data format | Spot-check throughout the file (beginning, middle, end) |
| Not handling edge cases | Check for empty fields, extra delimiters, special characters |
| No backup before transformation | Always `cp file file.backup` first |

### Vim-Specific

| Pitfall | Prevention |
|---------|------------|
| Incorrect keystroke counting | Count actual keystrokes, not escaped characters in scripts |
| Not validating macro contents | Use `:registers` to verify macro content before bulk apply |
| Regex metacharacter conflicts | Test patterns on sample data first |
| Using greedy patterns incorrectly | Use `[^,]*` instead of `.*` for CSV field matching |

### Verification

| Pitfall | Prevention |
|---------|------------|
| Only checking first N lines | Verify throughout: beginning, middle, end, random samples |
| Not using diff for exact comparison | Always `diff output expected` for definitive check |
| Ignoring exit codes | Check `$?` after operations to confirm success |

## Decision Tree

```
Task: Transform large text file
│
├─ Is the file > 1000 lines?
│  ├─ YES → Sample data first (head/tail/sed -n)
│  └─ NO → May read directly, but sampling still recommended
│
├─ Is there an expected output file?
│  ├─ YES → Compare samples to understand transformation
│  └─ NO → Clarify expected output format before proceeding
│
├─ Are there keystroke constraints?
│  ├─ YES → Plan macros carefully, count keystrokes accurately
│  └─ NO → Optimize for correctness over keystroke efficiency
│
├─ Ready to transform?
│  ├─ Create backup first
│  ├─ Test on small sample
│  ├─ Verify sample output matches expected
│  └─ Only then apply to full file
│
└─ After transformation:
   ├─ diff against expected output
   ├─ Verify line counts match
   └─ Spot-check random rows throughout file
```

## Resources

For detailed Vim commands and regex patterns, refer to `references/vim_editing_guide.md`.
