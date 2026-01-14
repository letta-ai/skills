#!/usr/bin/env python3
"""
Extract text from PDF using PyMuPDF (fitz).
Outputs LLM-optimized markdown using pymupdf4llm.

Usage:
    uv run extract_pymupdf.py input.pdf output.md
    uv run extract_pymupdf.py input.pdf  # prints to stdout

Requirements (auto-installed by uv):
    pymupdf4llm
"""
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf4llm>=0.0.17"]
# ///

import sys
from pathlib import Path


def extract_pdf_to_markdown(pdf_path: str) -> str:
    """Extract PDF content as LLM-optimized markdown."""
    import pymupdf4llm
    
    md_text = pymupdf4llm.to_markdown(pdf_path)
    return md_text


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run extract_pymupdf.py <input.pdf> [output.md]", file=sys.stderr)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    result = extract_pdf_to_markdown(input_path)
    
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
        print(f"Extracted {len(result)} characters to {output_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
