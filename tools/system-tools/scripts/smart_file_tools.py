#!/usr/bin/env python3
"""
Smart file tools for Letta agents.

These tools use LLM-powered extraction to return relevant snippets
instead of entire file contents, preventing context window blowup.
"""

import os
from typing import Optional


def smart_read_file(
    file_path: str,
    query: str,
    max_chars: int = 500,
    base_dir: Optional[str] = None
) -> str:
    """
    Read a file and return only the snippets relevant to your query.

    Uses LLM-powered extraction to find the most relevant parts of the file,
    preventing context window blowup while still giving you useful information.

    Args:
        file_path: Path to the file (relative or absolute)
        query: What you're looking for (e.g., "authentication logic", "error handling")
        max_chars: Maximum characters to return (default: 500)
        base_dir: Optional base directory for relative paths

    Returns:
        Relevant snippets with line numbers, or error message
    """
    import anthropic

    if base_dir and not file_path.startswith("/"):
        full_path = os.path.join(base_dir, file_path)
    else:
        full_path = file_path

    # Read the file
    try:
        with open(full_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return f"Error: File not found: {full_path}"
    except PermissionError:
        return f"Error: Permission denied: {full_path}"
    except Exception as e:
        return f"Error reading file: {type(e).__name__}: {str(e)}"

    # If file is small enough, just return it
    if len(content) <= max_chars:
        return f"File: {full_path} ({len(content)} chars)\n\n{content}"

    # Use LLM to extract relevant snippets
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fallback: return first max_chars with truncation notice
        return (
            f"File: {full_path} ({len(content)} chars, truncated - no ANTHROPIC_API_KEY)\n\n"
            f"{content[:max_chars]}\n\n[TRUNCATED - set ANTHROPIC_API_KEY for smart extraction]"
        )

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Add line numbers for reference
        lines = content.split('\n')
        numbered_content = '\n'.join(f"{i+1}: {line}" for i, line in enumerate(lines))

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Extract the most relevant snippets from this file for the query: "{query}"

Return ONLY the relevant code/text snippets with their line numbers.
Keep total output under {max_chars} characters.
Format each snippet as:
Lines X-Y:
```
<code>
```

If nothing is relevant, say "No relevant content found for: <query>"

FILE CONTENT:
{numbered_content}"""
            }]
        )

        snippets = response.content[0].text
        return f"File: {full_path} ({len(content)} chars)\nQuery: {query}\n\n{snippets}"

    except Exception as e:
        # Fallback on LLM error
        return (
            f"File: {full_path} ({len(content)} chars, truncated - LLM error: {e})\n\n"
            f"{content[:max_chars]}\n\n[TRUNCATED]"
        )


def smart_grep_file(
    file_path: str,
    pattern: str,
    context_lines: int = 2,
    max_matches: int = 5,
    base_dir: Optional[str] = None
) -> str:
    """
    Search a file for a pattern and return matching lines with context.

    A simpler alternative to smart_read_file when you know what you're
    looking for. Uses regex matching, no LLM required.

    Args:
        file_path: Path to the file
        pattern: Regex pattern to search for
        context_lines: Lines of context before/after each match (default: 2)
        max_matches: Maximum matches to return (default: 5)
        base_dir: Optional base directory for relative paths

    Returns:
        Matching snippets with line numbers and context
    """
    import re

    if base_dir and not file_path.startswith("/"):
        full_path = os.path.join(base_dir, file_path)
    else:
        full_path = file_path

    try:
        with open(full_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return f"Error: File not found: {full_path}"
    except PermissionError:
        return f"Error: Permission denied: {full_path}"
    except Exception as e:
        return f"Error reading file: {type(e).__name__}: {str(e)}"

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    matches = []
    for i, line in enumerate(lines):
        if regex.search(line):
            matches.append(i)

    if not matches:
        return f"No matches for '{pattern}' in {full_path}"

    # Collect snippets with context
    snippets = []
    seen_lines = set()

    for match_idx in matches[:max_matches]:
        start = max(0, match_idx - context_lines)
        end = min(len(lines), match_idx + context_lines + 1)

        # Skip if we've already shown these lines
        if start in seen_lines:
            continue

        snippet_lines = []
        for i in range(start, end):
            seen_lines.add(i)
            marker = ">>>" if i == match_idx else "   "
            snippet_lines.append(f"{marker} {i+1}: {lines[i].rstrip()}")

        snippets.append('\n'.join(snippet_lines))

    total_matches = len(matches)
    shown = min(max_matches, total_matches)

    result = [f"File: {full_path}", f"Pattern: {pattern}", f"Matches: {shown}/{total_matches}", ""]
    result.extend(snippets)

    if total_matches > max_matches:
        result.append(f"\n[{total_matches - max_matches} more matches not shown]")

    return '\n---\n'.join(result) if len(snippets) > 1 else '\n'.join(result)


# Tool definitions for registration
SMART_TOOLS = {
    "smart_read_file": {
        "name": "smart_read_file",
        "description": "Read a file and return only snippets relevant to your query. Uses LLM extraction to prevent context window blowup.",
        "func": smart_read_file,
        "tags": ["file", "read", "smart"],
        "json_schema": {
            "name": "smart_read_file",
            "description": "Read a file and return only snippets relevant to your query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "query": {
                        "type": "string",
                        "description": "What you're looking for (e.g., 'authentication logic', 'database connection')"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default: 500)",
                        "default": 500
                    }
                },
                "required": ["file_path", "query"]
            }
        }
    },
    "smart_grep_file": {
        "name": "smart_grep_file",
        "description": "Search a file for a pattern and return matching lines with context. No LLM required.",
        "func": smart_grep_file,
        "tags": ["file", "search", "grep"],
        "json_schema": {
            "name": "smart_grep_file",
            "description": "Search a file for a pattern and return matching lines with context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for"
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Lines of context before/after each match (default: 2)",
                        "default": 2
                    },
                    "max_matches": {
                        "type": "integer",
                        "description": "Maximum matches to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["file_path", "pattern"]
            }
        }
    }
}


if __name__ == "__main__":
    print("=== Smart File Tools Demo ===\n")

    # Test smart_grep_file (no LLM needed)
    print("1. smart_grep_file - searching for 'def ' in this file:")
    print(smart_grep_file(__file__, r"def \w+", context_lines=1, max_matches=3))
    print()

    # Test smart_read_file
    print("2. smart_read_file - finding 'error handling' in this file:")
    result = smart_read_file(__file__, "error handling", max_chars=500)
    print(result[:800] + "..." if len(result) > 800 else result)
