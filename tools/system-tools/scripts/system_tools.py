#!/usr/bin/env python3
"""
System tools for Letta agents.

Provides shell execution, file operations, and directory listing tools
that extend Letta's built-in capabilities.

These tools are designed to be registered with Letta via the SDK or REST API.
"""

import os
import subprocess
from typing import Optional


def execute_shell_command(command: str, timeout: int = 30) -> str:
    """
    Execute a shell command and return the output.

    Args:
        command: The shell command to execute
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        Command output including exit code, stdout, and stderr
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output_parts = [f"Exit code: {result.returncode}"]

        if result.stdout:
            output_parts.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"STDERR:\n{result.stderr}")

        return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {type(e).__name__}: {str(e)}"


def read_file_contents(file_path: str, base_dir: Optional[str] = None) -> str:
    """
    Read the contents of a file.

    Unlike Letta's built-in read_from_text_file (500 char limit), this tool
    reads the entire file without truncation.

    Args:
        file_path: Path to the file (relative or absolute)
        base_dir: Optional base directory for relative paths

    Returns:
        File contents with metadata, or error message
    """
    if base_dir and not file_path.startswith("/"):
        full_path = os.path.join(base_dir, file_path)
    else:
        full_path = file_path

    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return f"File: {full_path}\nLength: {len(content)} characters\n\n{content}"
    except FileNotFoundError:
        return f"Error: File not found: {full_path}"
    except PermissionError:
        return f"Error: Permission denied: {full_path}"
    except Exception as e:
        return f"Error reading file: {type(e).__name__}: {str(e)}"


def write_file_contents(file_path: str, content: str, base_dir: Optional[str] = None) -> str:
    """
    Write content to a file.

    Unlike Letta's built-in append_to_text_file (append only), this tool
    overwrites the file with the provided content.

    Creates parent directories if they don't exist.

    Args:
        file_path: Path to the file (relative or absolute)
        content: Content to write to the file
        base_dir: Optional base directory for relative paths

    Returns:
        Success message or error
    """
    if base_dir and not file_path.startswith("/"):
        full_path = os.path.join(base_dir, file_path)
    else:
        full_path = file_path

    try:
        # Create parent directories if needed
        parent_dir = os.path.dirname(full_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {full_path}"
    except PermissionError:
        return f"Error: Permission denied: {full_path}"
    except Exception as e:
        return f"Error writing file: {type(e).__name__}: {str(e)}"


def list_directory_contents(path: str = ".", base_dir: Optional[str] = None) -> str:
    """
    List the contents of a directory.

    Letta has no built-in equivalent for directory listing.

    Args:
        path: Directory path (relative or absolute). Default: current directory
        base_dir: Optional base directory for relative paths

    Returns:
        Formatted directory listing with file sizes, or error message
    """
    if base_dir and not path.startswith("/"):
        full_path = os.path.join(base_dir, path)
    else:
        full_path = path

    try:
        if not os.path.exists(full_path):
            return f"Error: Directory not found: {full_path}"
        if not os.path.isdir(full_path):
            return f"Error: Not a directory: {full_path}"

        entries = os.listdir(full_path)
        directories = []
        files = []

        for entry in sorted(entries):
            entry_path = os.path.join(full_path, entry)
            if os.path.isdir(entry_path):
                directories.append(entry)
            else:
                try:
                    size = os.path.getsize(entry_path)
                    files.append({"name": entry, "size": size})
                except OSError:
                    files.append({"name": entry, "size": 0})

        output = [f"Directory: {os.path.abspath(full_path)}"]
        if directories:
            output.append(f"\nDirectories ({len(directories)}):")
            for d in directories:
                output.append(f"  {d}/")
        if files:
            output.append(f"\nFiles ({len(files)}):")
            for f in files:
                output.append(f"  {f['name']} ({f['size']:,} bytes)")

        return "\n".join(output)

    except PermissionError:
        return f"Error: Permission denied: {full_path}"
    except Exception as e:
        return f"Error listing directory: {type(e).__name__}: {str(e)}"


# Tool definitions for REST API registration
# These include JSON schemas for proper tool registration

TOOLS = {
    "execute_shell_command": {
        "name": "execute_shell_command",
        "description": "Execute a shell command and return the output.",
        "func": execute_shell_command,
        "tags": ["shell", "system"],
        "json_schema": {
            "name": "execute_shell_command",
            "description": "Execute a shell command and return the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }
    },
    "read_file_contents": {
        "name": "read_file_contents",
        "description": "Read the contents of a file without character limits.",
        "func": read_file_contents,
        "tags": ["file", "read"],
        "json_schema": {
            "name": "read_file_contents",
            "description": "Read the contents of a file without character limits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (relative or absolute)"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    "write_file_contents": {
        "name": "write_file_contents",
        "description": "Write content to a file (overwrites existing content).",
        "func": write_file_contents,
        "tags": ["file", "write"],
        "json_schema": {
            "name": "write_file_contents",
            "description": "Write content to a file (overwrites existing content).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (relative or absolute)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    "list_directory_contents": {
        "name": "list_directory_contents",
        "description": "List the contents of a directory with file sizes.",
        "func": list_directory_contents,
        "tags": ["file", "directory"],
        "json_schema": {
            "name": "list_directory_contents",
            "description": "List the contents of a directory with file sizes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (default: current directory)",
                        "default": "."
                    }
                },
                "required": []
            }
        }
    }
}


if __name__ == "__main__":
    # Demo the tools
    print("=== System Tools Demo ===\n")

    print("1. execute_shell_command('echo Hello World')")
    print(execute_shell_command("echo Hello World"))
    print()

    print("2. list_directory_contents('.')")
    print(list_directory_contents("."))
    print()

    print("3. write_file_contents('/tmp/test.txt', 'Hello from Letta!')")
    print(write_file_contents("/tmp/test.txt", "Hello from Letta!"))
    print()

    print("4. read_file_contents('/tmp/test.txt')")
    print(read_file_contents("/tmp/test.txt"))
