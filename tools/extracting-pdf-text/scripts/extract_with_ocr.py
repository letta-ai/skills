#!/usr/bin/env python3
"""
Extract text from scanned PDFs using local OCR (Tesseract).
Use this when API access is unavailable for scanned/image-based PDFs.

Usage:
    uv run extract_with_ocr.py input.pdf output.txt
    uv run extract_with_ocr.py input.pdf  # prints to stdout

Prerequisites:
    - Tesseract OCR installed: brew install tesseract (macOS)
    - Poppler for pdf2image: brew install poppler (macOS)

Requirements (auto-installed by uv):
    pytesseract, pdf2image, Pillow
"""
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytesseract>=0.3.10", "pdf2image>=1.16.0", "Pillow>=10.0.0"]
# ///

import sys
import shutil
from pathlib import Path


def check_dependencies():
    """Check that required system dependencies are installed."""
    if not shutil.which("tesseract"):
        print("Error: Tesseract not found. Install with: brew install tesseract", file=sys.stderr)
        sys.exit(1)
    
    # Check for poppler (pdftoppm)
    if not shutil.which("pdftoppm"):
        print("Error: Poppler not found. Install with: brew install poppler", file=sys.stderr)
        sys.exit(1)


def extract_pdf_with_ocr(pdf_path: str, lang: str = "eng") -> str:
    """
    Extract text from scanned PDF using OCR.
    
    Args:
        pdf_path: Path to PDF file
        lang: Tesseract language code (default: eng)
        
    Returns:
        Extracted text
    """
    import pytesseract
    from pdf2image import convert_from_path
    
    # Convert PDF pages to images
    images = convert_from_path(pdf_path, dpi=300)
    
    output_parts = []
    for i, image in enumerate(images, 1):
        # Run OCR on each page
        text = pytesseract.image_to_string(image, lang=lang)
        if text.strip():
            output_parts.append(f"--- Page {i} ---\n{text.strip()}")
    
    return "\n\n".join(output_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run extract_with_ocr.py <input.pdf> [output.txt] [--lang=eng]", file=sys.stderr)
        sys.exit(1)
    
    check_dependencies()
    
    input_path = sys.argv[1]
    output_path = None
    lang = "eng"
    
    for arg in sys.argv[2:]:
        if arg.startswith("--lang="):
            lang = arg.split("=")[1]
        else:
            output_path = arg
    
    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing PDF with OCR (language: {lang})...", file=sys.stderr)
    result = extract_pdf_with_ocr(input_path, lang=lang)
    
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
        print(f"Extracted {len(result)} characters to {output_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
