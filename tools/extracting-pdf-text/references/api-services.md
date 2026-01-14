# API Services for PDF Extraction

## Mistral OCR API (Recommended)

**Best for**: Complex layouts, scanned documents, multilingual content, math formulas.

**Pricing**: ~$1 per 1000 pages (very cost-effective)

**Accuracy**: 95%+ overall, 98%+ on scanned documents

### Features
- Outputs clean markdown preserving document structure
- Table recognition (96% accuracy)
- Math equation support (94% accuracy)
- Multilingual support (89% accuracy)
- Processes up to 2000 pages/minute

### API Usage

```python
from mistralai import Mistral
import base64

client = Mistral(api_key="your-key")

# From URL
response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": "https://example.com/doc.pdf",
    }
)

# From local file (base64)
with open("doc.pdf", "rb") as f:
    content = base64.standard_b64encode(f.read()).decode()

response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "base64",
        "base64": content,
    }
)

# Access results
for page in response.pages:
    print(page.markdown)
```

### Endpoint
- SDK: `client.ocr.process`
- REST: `POST https://api.mistral.ai/v1/ocr`

---

## OpenAI Vision (GPT-4V)

**Best for**: When you already have OpenAI API access and need to extract from image-heavy PDFs.

**Approach**: Convert PDF pages to images, send to GPT-4V for extraction.

**Pricing**: ~$0.01-0.03 per page (depends on image size and detail level)

### Usage Pattern

```python
from openai import OpenAI
from pdf2image import convert_from_path
import base64
from io import BytesIO

client = OpenAI()

def pdf_page_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Convert PDF to images
images = convert_from_path("doc.pdf", dpi=150)

for i, img in enumerate(images):
    b64 = pdf_page_to_base64(img)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all text from this document page. Preserve structure and formatting as markdown."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        }]
    )
    print(response.choices[0].message.content)
```

### Limitations
- Requires converting PDF to images first
- Higher cost per page than Mistral OCR
- May struggle with dense text

---

## Google Cloud Document AI

**Best for**: Enterprise workflows, high-volume processing, Google Cloud integration.

**Pricing**: $1.50 per 1000 pages (Form Parser), varies by processor type

### Processors
- Document OCR: General text extraction
- Form Parser: Structured form data
- Invoice Parser: Specialized invoice extraction
- Custom Document Extractor: Train on your document types

Not covered in detail here - see [Google Cloud documentation](https://cloud.google.com/document-ai/docs).

---

## AWS Textract

**Best for**: AWS ecosystem integration, form extraction, table detection.

**Pricing**: $1.50 per 1000 pages (text), $15 per 1000 pages (tables/forms)

### Features
- DetectDocumentText: Basic OCR
- AnalyzeDocument: Tables, forms, key-value pairs
- AnalyzeExpense: Receipt/invoice parsing

Not covered in detail here - see [AWS Textract documentation](https://docs.aws.amazon.com/textract/).

---

---

## Azure Document Intelligence

**Best for**: Enterprise workflows, highest accuracy on structured documents.

Formerly "Azure Form Recognizer". Ranked #1 in several 2025 OCR benchmarks.

**Pricing**: ~$1.50 per 1000 pages (Read model), higher for specialized models

### Features
- Prebuilt models for invoices, receipts, IDs, tax forms
- Custom model training
- Excellent table and form extraction
- Strong multilingual support

### Models
- **Read**: General OCR
- **Layout**: Structure + tables
- **Invoice/Receipt/ID**: Specialized extractors
- **Custom**: Train on your documents

Not covered in detail - see [Azure documentation](https://learn.microsoft.com/azure/ai-services/document-intelligence/).

---

## Comparison Summary

| Service | Cost/1000 pages | Best For | Output Format |
|---------|----------------|----------|---------------|
| Mistral OCR | ~$1 | General, scanned, complex | Markdown |
| Azure Doc Intel | ~$1.50 | Enterprise, forms, highest accuracy | JSON |
| OpenAI Vision | ~$10-30 | Image-heavy, existing OpenAI users | Text |
| Google Doc AI | $1.50+ | Enterprise, Google Cloud | JSON |
| AWS Textract | $1.50-15 | AWS users, forms | JSON |

**Recommendation**: Start with Mistral OCR for best price/performance ratio. Use Azure Document Intelligence if you need highest accuracy on forms/invoices.
