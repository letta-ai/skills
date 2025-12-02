---
name: financial-document-processor
description: Guidance for processing, classifying, and extracting data from financial documents (invoices, receipts, statements). This skill should be used when tasks involve OCR extraction, document classification, data validation from financial PDFs/images, or batch processing of financial documents. Covers safe file operations, incremental testing, and data extraction verification.
---

# Financial Document Processor

## Overview

This skill provides procedural guidance for processing financial documents such as invoices, receipts, and statements. It covers document classification, data extraction (amounts, VAT, dates), and batch processing workflows with emphasis on safe operations and verification.

## Critical Principles

### 1. Never Perform Destructive Operations Without Backup

Before any file move, delete, or modification operation:

1. Create explicit backups: `cp -r /app/documents /app/documents_backup`
2. Verify backup exists before proceeding: `ls -la /app/documents_backup`
3. Use copy-then-delete pattern instead of move when testing
4. Never chain `rm` with `mv` in a single command without verification between steps

**Dangerous pattern to avoid:**
```bash
# WRONG: Files deleted before move can execute
rm -f /app/invoices/*.pdf && mv /app/other/* /app/documents/
```

**Safe pattern:**
```bash
# CORRECT: Create backup first, verify, then operate
cp -r /app/documents /app/documents_backup
ls /app/documents_backup  # Verify backup
# Now proceed with operations
```

### 2. Test Incrementally on Single Documents First

Before processing a batch of documents:

1. Select one representative document from each category (invoice, receipt, statement)
2. Run extraction on the single document
3. Manually verify extracted values against the source document
4. Only proceed to batch processing after single-document validation succeeds

### 3. Validate Before Declaring Success

Never mark a task complete without verification:

1. Check that output files exist in expected locations
2. Verify extracted data contains non-zero/non-empty values where expected
3. Cross-reference a sample of extracted values against source documents
4. If extraction produces mostly zeros or empty values, the extraction logic is failing

## Document Processing Workflow

### Phase 1: Assessment

1. **Inventory documents**: List all files to process with types and counts
2. **Sample inspection**: Read/view 2-3 representative documents to understand format
3. **Identify challenges**: Note format variations (European decimals, date formats, multi-page documents)
4. **Plan extraction strategy**: Determine what tools/libraries are needed (OCR, PDF text extraction)

### Phase 2: Implementation with Safety

1. **Create working backup**: Always backup source documents before any processing
2. **Build extraction logic**: Implement one extraction pattern at a time
3. **Test on single document**: Validate each pattern before combining
4. **Handle edge cases explicitly**: See `references/extraction_patterns.md` for common patterns

### Phase 3: Batch Processing

1. **Process in small batches**: Start with 5-10 documents, verify results
2. **Implement logging**: Log each document processed with extraction results
3. **Flag low-confidence extractions**: Mark documents where extraction may have failed
4. **Generate summary only after verification**: Create summary.csv after confirming extraction quality

### Phase 4: Verification

1. **Spot-check results**: Manually verify 10-20% of extracted values
2. **Check for systematic failures**: Look for patterns in failed extractions
3. **Validate totals**: If summing amounts, verify against expected totals
4. **Confirm file organization**: Verify documents are in correct output directories

## Common Extraction Challenges

### European Number Formatting

European locales use comma as decimal separator (1.234,56 instead of 1,234.56):

```python
def parse_european_number(text):
    """Convert European format number to float."""
    # Remove thousand separators (periods)
    text = text.replace('.', '')
    # Convert decimal comma to period
    text = text.replace(',', '.')
    return float(text)
```

### VAT/Tax Amount Extraction

VAT may appear in multiple formats:
- "VAT: 20%", "VAT 20.00", "Tax: $20.00"
- May be absent entirely (set to 0 or empty string per requirements)
- May need calculation from gross/net amounts

### Total vs Amount Due

Invoices may have multiple "total" values:
- Subtotal (before tax)
- Total (after tax)
- Amount Due (final payable amount)

Prioritize "Amount Due" or final total when multiple values exist.

### OCR Quality Issues

For image-based documents:
- Implement confidence scoring when available
- Flag documents with low OCR confidence for manual review
- Consider pre-processing (contrast adjustment, deskewing) for poor quality scans

## Verification Checklist

Before declaring document processing complete, verify:

- [ ] All source documents accounted for (none missing)
- [ ] Documents classified to correct output directories
- [ ] Extracted amounts are non-zero for documents that should have amounts
- [ ] Date formats are consistent in output
- [ ] Summary CSV contains expected number of rows
- [ ] Spot-checked 10-20% of extractions against source documents
- [ ] No files were lost during processing (compare input/output counts)

## Resources

### references/

- `extraction_patterns.md` - Regex patterns and extraction strategies for common financial document formats

### When to Flag for Manual Review

Flag a document for manual review when:
- OCR confidence is below 80%
- Extracted total amount is 0 but document clearly shows amounts
- Multiple conflicting "total" values found
- Date cannot be parsed from document
- Document classification is ambiguous
