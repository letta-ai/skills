# Financial Document Extraction Patterns

## Amount Extraction Regex Patterns

### US Format (comma thousands, period decimal)

```python
# Matches: $1,234.56, 1234.56, $1,234,567.89
us_amount_pattern = r'\$?\s*[\d,]+\.\d{2}'
```

### European Format (period thousands, comma decimal)

```python
# Matches: 1.234,56, €1.234.567,89
eu_amount_pattern = r'[€£]?\s*[\d.]+,\d{2}'
```

### Generic Amount (handles both)

```python
import re

def extract_amount(text, prefer_european=False):
    """Extract monetary amount from text, handling both formats."""
    if prefer_european:
        # European: 1.234,56
        match = re.search(r'[\d.]+,\d{2}', text)
        if match:
            value = match.group()
            value = value.replace('.', '').replace(',', '.')
            return float(value)

    # US: 1,234.56
    match = re.search(r'[\d,]+\.\d{2}', text)
    if match:
        value = match.group().replace(',', '')
        return float(value)

    return None
```

## Invoice Field Patterns

### Invoice Number

```python
invoice_patterns = [
    r'Invoice\s*#?\s*:?\s*(\w+[-/]?\d+)',
    r'Invoice\s+Number\s*:?\s*(\w+[-/]?\d+)',
    r'Inv\s*[#:]?\s*(\w+[-/]?\d+)',
    r'Bill\s*#?\s*:?\s*(\d+)',
]
```

### Date Extraction

```python
date_patterns = [
    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
    r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',     # YYYY-MM-DD (ISO)
    r'(\w+\s+\d{1,2},?\s+\d{4})',          # Month DD, YYYY
    r'(\d{1,2}\s+\w+\s+\d{4})',            # DD Month YYYY
]
```

### Total Amount Keywords

Priority order for finding the final payable amount:

```python
total_keywords = [
    'Amount Due',
    'Balance Due',
    'Total Due',
    'Grand Total',
    'Total Amount',
    'Total',
    'Net Amount',
]

def find_total_amount(text):
    """Find total amount with keyword priority."""
    for keyword in total_keywords:
        pattern = rf'{keyword}\s*:?\s*\$?\s*([\d,]+\.\d{{2}})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', ''))
    return None
```

### VAT/Tax Extraction

```python
vat_patterns = [
    r'VAT\s*:?\s*\$?\s*([\d,]+\.\d{2})',
    r'Tax\s*:?\s*\$?\s*([\d,]+\.\d{2})',
    r'GST\s*:?\s*\$?\s*([\d,]+\.\d{2})',
    r'Sales\s+Tax\s*:?\s*\$?\s*([\d,]+\.\d{2})',
    r'(\d+(?:\.\d+)?)\s*%\s*(?:VAT|Tax)',  # Percentage format: "20% VAT"
]
```

## Document Classification Patterns

### Invoice Indicators

```python
invoice_indicators = [
    r'\binvoice\b',
    r'\bbill\s+to\b',
    r'\bamount\s+due\b',
    r'\bpayment\s+terms\b',
    r'\bdue\s+date\b',
    r'\binv[.\s]*(?:no|number|#)',
]

def is_likely_invoice(text):
    """Check if document is likely an invoice."""
    text_lower = text.lower()
    matches = sum(1 for pattern in invoice_indicators
                  if re.search(pattern, text_lower))
    return matches >= 2  # Require at least 2 indicators
```

### Receipt Indicators

```python
receipt_indicators = [
    r'\breceipt\b',
    r'\btransaction\b',
    r'\bpaid\b',
    r'\bthank\s+you\b',
    r'\bchange\s+due\b',
    r'\bcash\b',
]
```

### Statement Indicators

```python
statement_indicators = [
    r'\bstatement\b',
    r'\baccount\s+summary\b',
    r'\bprevious\s+balance\b',
    r'\bcurrent\s+balance\b',
    r'\btransaction\s+history\b',
]
```

## Handling Multi-Value Extractions

When multiple amounts are found, use context to determine which is the total:

```python
def extract_with_context(text, pattern, context_words, window=50):
    """Extract value with surrounding context validation."""
    matches = list(re.finditer(pattern, text))

    for match in matches:
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        context = text[start:end].lower()

        if any(word in context for word in context_words):
            return match.group()

    return None

# Usage: Find the total that's near "amount due" or "grand total"
total = extract_with_context(
    text,
    r'\$?[\d,]+\.\d{2}',
    ['amount due', 'grand total', 'total due']
)
```

## Confidence Scoring

Implement confidence scoring to flag uncertain extractions:

```python
def extraction_confidence(extracted_data):
    """Score extraction confidence 0-100."""
    score = 100

    # Deduct for missing fields
    if not extracted_data.get('total_amount'):
        score -= 40
    if not extracted_data.get('date'):
        score -= 20
    if not extracted_data.get('invoice_number'):
        score -= 15

    # Deduct for suspicious values
    if extracted_data.get('total_amount', 0) == 0:
        score -= 30
    if extracted_data.get('vat_amount', 0) > extracted_data.get('total_amount', 1):
        score -= 25  # VAT shouldn't exceed total

    return max(0, score)
```

## OCR Pre-processing Tips

For better OCR results on financial documents:

1. **Contrast enhancement**: Increase contrast for faded documents
2. **Deskewing**: Straighten tilted scans
3. **Noise removal**: Remove speckles from poor quality scans
4. **Resolution**: Ensure at least 300 DPI for text extraction
5. **Binarization**: Convert to black/white for clearer text

```python
# Example with PIL/Pillow
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_for_ocr(image_path):
    """Preprocess image for better OCR results."""
    img = Image.open(image_path)

    # Convert to grayscale
    img = img.convert('L')

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    return img
```
