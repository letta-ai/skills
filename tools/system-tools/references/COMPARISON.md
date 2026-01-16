# Comparison with Letta Built-in Tools

This document explains why these system tools are needed alongside Letta's built-in tools.

## Letta Built-in File Tools (from extras.py)

### read_from_text_file
```python
def read_from_text_file(file_path: str, start_line: int = 0, max_chars: int = 500) -> str
```
- **Limitation**: 500 character maximum
- **Use case**: Quick peeks at small files

### append_to_text_file
```python
def append_to_text_file(file_path: str, content: str) -> str
```
- **Limitation**: Only appends, cannot overwrite
- **Use case**: Log files, accumulative content

## Our System Tools

### read_file_contents
```python
def read_file_contents(file_path: str) -> str
```
- **No character limit** - reads entire file
- **Use case**: Reading configuration files, source code, any full file

### write_file_contents
```python
def write_file_contents(file_path: str, content: str) -> str
```
- **Overwrites** existing content (not append)
- **Creates parent directories** automatically
- **Use case**: Writing configuration, updating files, creating new files

### execute_shell_command
```python
def execute_shell_command(command: str, timeout: int = 30) -> str
```
- **No Letta equivalent** - intentionally omitted for security
- **Timeout protection** prevents hanging
- **Use case**: Git operations, npm commands, system administration

### list_directory_contents
```python
def list_directory_contents(path: str = ".") -> str
```
- **No Letta equivalent**
- **Shows file sizes** for context
- **Use case**: Exploring project structure, finding files

## When to Use Which

| Task | Use This |
|------|----------|
| Quick file peek (<500 chars) | Letta's `read_from_text_file` |
| Read full file | Our `read_file_contents` |
| Append to log | Letta's `append_to_text_file` |
| Overwrite/create file | Our `write_file_contents` |
| Run shell commands | Our `execute_shell_command` |
| List directory | Our `list_directory_contents` |
| Execute Python code | Letta's built-in `run_code` |

## Security Note

`execute_shell_command` was intentionally omitted from Letta's built-ins for security in multi-tenant environments. Use it only in trusted, single-tenant deployments where agents need system access.
