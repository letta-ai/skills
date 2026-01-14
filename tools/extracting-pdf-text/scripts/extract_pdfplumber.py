#!/usr/bin/env python3
"""
Extract text and tables from PDF using pdfplumber.
Best for machine-generated PDFs with tables.

Usage:
    uv run extract_pdfplumber.py input.pdf output.md
    uv run extract_pdfplumber.py input.pdf  # prints to stdout

Requirements (auto-installed by uv):
    pdfplumber
"""
# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber>=0.11.0"]
# ///

import sys
from pathlib import Path


def table_to_markdown(table: list[list]) -> str:
    """Convert a table (list of rows) to markdown format."""
    if not table or not table[0]:
        return ""
    
    # Clean None values
    table = [[cell or "" for cell in row] for row in table]
    
    lines = []
    # Header row
    lines.append("| " + " | ".join(str(cell) for cell in table[0]) + " |")
    # Separator
    lines.append("| " + " | ".join("---" for _ in table[0]) + " |")
    # Data rows
    for row in table[1:]:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    
    return "\n".join(lines)


def extract_pdf_with_tables(pdf_path: str) -> str:
    """Extract PDF content with tables formatted as markdown."""
    import pdfplumber
    
    output_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            output_parts.append(f"\n## Page {i}\n")
            
            # Extract tables first to identify their bounding boxes
            tables = page.extract_tables()
            table_bboxes = []
            
            if tables:
                # Find table locations
                for table_settings in page.find_tables():
                    table_bboxes.append(table_settings.bbox)
            
            # Extract text (excluding table areas if possible)
            text = page.extract_text() or ""
            if text.strip():
                output_parts.append(text.strip())
            
            # Add tables as markdown
            for j, table in enumerate(tables, 1):
                if table:
                    output_parts.append(f"\n### Table {j}\n")
                    output_parts.append(table_to_markdown(table))
    
    return "\n\n".join(output_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run extract_pdfplumber.py <input.pdf> [output.md]", file=sys.stderr)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    result = extract_pdf_with_tables(input_path)
    
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
        print(f"Extracted {len(result)} characters to {output_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
