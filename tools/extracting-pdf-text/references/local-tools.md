# Local PDF Extraction Tools

## PyMuPDF (fitz) + pymupdf4llm

**Best for**: Fast extraction, LLM-optimized output, complex layouts.

**Speed**: Fastest option (~0.01s per page)

### Installation
```bash
pip install pymupdf4llm
# or with uv
uv pip install pymupdf4llm
```

### Usage

```python
import pymupdf4llm

# Basic extraction to markdown
md_text = pymupdf4llm.to_markdown("document.pdf")

# With options
md_text = pymupdf4llm.to_markdown(
    "document.pdf",
    pages=[0, 1, 2],  # specific pages (0-indexed)
    page_chunks=True,  # return list of page chunks for RAG
)

# For RAG systems - get chunks with metadata
chunks = pymupdf4llm.to_markdown("document.pdf", page_chunks=True)
for chunk in chunks:
    print(f"Page {chunk['metadata']['page']}: {chunk['text'][:100]}...")
```

### Strengths
- Fastest Python PDF library
- Good structure preservation (headings, lists)
- LLM-optimized markdown output
- Handles images and complex layouts
- Active development

### Limitations
- Struggles with some scanned documents
- Table extraction less reliable than pdfplumber

---

## pdfplumber

**Best for**: Table extraction, machine-generated PDFs, detailed layout control.

**Speed**: Moderate (~0.1s per page)

### Installation
```bash
pip install pdfplumber
```

### Usage

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        # Extract text
        text = page.extract_text()
        
        # Extract tables
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                print(row)
        
        # Visual debugging
        im = page.to_image()
        im.draw_rects(page.chars)
        im.save("debug.png")
```

### Table Extraction Options

```python
# Custom table settings for complex tables
table_settings = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 3,
    "join_tolerance": 3,
}

tables = page.extract_tables(table_settings)
```

### Strengths
- Excellent table detection and extraction
- Fine-grained control over extraction
- Visual debugging tools
- Good for structured documents

### Limitations
- Slower than PyMuPDF
- Does not work well on scanned PDFs
- Built on pdfminer.six (can be memory-heavy)

---

## unstructured

**Best for**: RAG systems, semantic chunking, multi-format support.

**Speed**: Slower (includes ML models)

### Installation
```bash
pip install unstructured[pdf]
# For full features including OCR:
pip install unstructured[all-docs]
```

### Usage

```python
from unstructured.partition.pdf import partition_pdf

# Basic extraction
elements = partition_pdf("document.pdf")

for element in elements:
    print(f"{element.category}: {element.text[:100]}")

# With OCR for scanned documents
elements = partition_pdf(
    "scanned.pdf",
    strategy="ocr_only",  # or "hi_res" for best quality
)

# Chunking for RAG
from unstructured.chunking.title import chunk_by_title
chunks = chunk_by_title(elements)
```

### Strengths
- Semantic element detection (titles, paragraphs, tables)
- Built-in chunking strategies for RAG
- Multi-format support (PDF, DOCX, HTML, etc.)
- OCR support included

### Limitations
- Heavier dependencies
- Slower processing
- More complex setup

---

## pytesseract + pdf2image

**Best for**: Scanned PDFs when API access unavailable.

**Speed**: Slow (~1-3s per page)

### Prerequisites
```bash
# macOS
brew install tesseract poppler

# Ubuntu
apt-get install tesseract-ocr poppler-utils
```

### Installation
```bash
pip install pytesseract pdf2image Pillow
```

### Usage

```python
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path("scanned.pdf", dpi=300)

# OCR each page
for i, image in enumerate(images):
    text = pytesseract.image_to_string(image, lang="eng")
    print(f"Page {i+1}:\n{text}")

# Multiple languages
text = pytesseract.image_to_string(image, lang="eng+fra+deu")
```

### Strengths
- Free and open source
- Works offline
- Supports 100+ languages

### Limitations
- Requires system dependencies (Tesseract, Poppler)
- Lower accuracy than cloud OCR services
- No structure preservation

---

## Comparison Summary

| Tool | Speed | Tables | Scanned PDFs | RAG-Ready |
|------|-------|--------|--------------|-----------|
| pymupdf4llm | Fastest | Good | Limited | Yes |
| pdfplumber | Moderate | Excellent | No | Manual |
| unstructured | Slow | Good | Yes (with OCR) | Yes |
| pytesseract | Slow | No | Yes | No |

### Decision Guide

1. **Need speed?** → pymupdf4llm
2. **Need tables?** → pdfplumber
3. **Building RAG?** → unstructured or pymupdf4llm with page_chunks
4. **Scanned docs, no API?** → pytesseract (or unstructured with OCR)
5. **Scanned docs, have budget?** → Mistral OCR API (see api-services.md)

---

## Additional Tools Worth Knowing

### marker-pdf (Datalab)

**Best for**: End-to-end PDF to Markdown conversion, RAG pipelines.

Built on Surya OCR engine. Very popular for document processing pipelines.

```bash
pip install marker-pdf
marker_single input.pdf --output_dir ./output --output_format markdown
```

Features:
- Outputs clean Markdown, JSON, or HTML
- Handles complex layouts
- Optional LLM post-processing for cleanup
- GPU-accelerated

### surya

**Best for**: Core OCR engine, multilingual text detection.

The OCR engine that powers marker-pdf. Good for custom pipelines.

```bash
pip install surya-ocr
```

### docling (IBM)

**Best for**: Enterprise document parsing, structured extraction.

```bash
pip install docling
```

### MinerU

**Best for**: Academic papers, complex multi-column layouts.

Open source PDF parser with excellent layout detection.

```bash
pip install magic-pdf
```

### PaddleOCR (Baidu)

**Best for**: Chinese/multilingual documents, structured forms.

```bash
pip install paddlepaddle paddleocr
```

Excellent for Asian languages. Requires some tuning for optimal results.

---

## Full Comparison

| Tool | Speed | Scanned PDFs | Tables | RAG-Ready | Best For |
|------|-------|--------------|--------|-----------|----------|
| pymupdf4llm | Fastest | Limited | Good | Yes | Speed |
| pdfplumber | Moderate | No | Excellent | Manual | Tables |
| marker-pdf | Moderate | Yes | Good | Yes | End-to-end |
| unstructured | Slow | Yes | Good | Yes | RAG |
| pytesseract | Slow | Yes | No | No | Free OCR |
| MinerU | Moderate | Yes | Good | Yes | Academic |
| PaddleOCR | Fast | Yes | Good | Manual | Multilingual |
