---
description: Perform file read, write, create, delete, search, and list operations. Use when the user wants to read, write, create, delete, search, or list files (e.g., "read the file at X", "write Y to Z", "list Python files", "search for TODO in markdown").
---

# File Operations

Use the OASYS `file_ops` plugin or standard tools to fulfill file requests.

## Patterns
- **read**: Read a file's contents.
- **write/create**: Create or overwrite a file.
- **delete**: Remove a file.
- **search**: Search file contents recursively.
- **ls / list**: List a directory.

## Examples
- "Read the file at /home/user/document.txt"
- "Write 'Hello World' to /tmp/test.txt"
- "List all Python files in the current directory"
- "Search for 'TODO' in all markdown files"

## Notes
Prefer the agent's native file tools over shell where possible. Confirm before destructive deletes.
