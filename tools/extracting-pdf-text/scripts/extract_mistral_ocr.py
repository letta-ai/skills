#!/usr/bin/env python3
"""
Extract text from PDF using Mistral OCR API.
Best for complex layouts, scanned documents, and highest accuracy.

Usage:
    export MISTRAL_API_KEY="your-key"
    uv run extract_mistral_ocr.py input.pdf output.md
    uv run extract_mistral_ocr.py input.pdf  # prints to stdout
    uv run extract_mistral_ocr.py https://example.com/doc.pdf output.md  # URL input

Requirements (auto-installed by uv):
    mistralai
"""
# /// script
# requires-python = ">=3.10"
# dependencies = ["mistralai>=1.0.0"]
# ///

import os
import sys
import base64
from pathlib import Path


def extract_with_mistral_ocr(source: str) -> str:
    """
    Extract PDF content using Mistral OCR API.
    
    Args:
        source: Local file path or URL to PDF
        
    Returns:
        Extracted text in markdown format
    """
    from mistralai import Mistral
    
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    
    client = Mistral(api_key=api_key)
    
    # Determine if source is URL or local file
    if source.startswith("http://") or source.startswith("https://"):
        # URL-based document
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": source,
            }
        )
    else:
        # Local file - upload as base64
        file_path = Path(source)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        with open(file_path, "rb") as f:
            file_content = base64.standard_b64encode(f.read()).decode("utf-8")
        
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "base64",
                "base64": file_content,
            }
        )
    
    # Combine all pages into markdown
    output_parts = []
    for page in ocr_response.pages:
        output_parts.append(page.markdown)
    
    return "\n\n---\n\n".join(output_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run extract_mistral_ocr.py <input.pdf|url> [output.md]", file=sys.stderr)
        print("       MISTRAL_API_KEY environment variable must be set", file=sys.stderr)
        sys.exit(1)
    
    source = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = extract_with_mistral_ocr(source)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
        print(f"Extracted {len(result)} characters to {output_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
