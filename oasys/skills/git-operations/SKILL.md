---
description: Git repository management and operations. Use when the user wants git status, add, commit, push, pull, branch, or diff (e.g., "show git status", "commit with message X", "push branches", "create branch feature-x", "show diff").
---

# Git Operations

Use the OASYS `git_ops` plugin or `SHELL:` actions for repository tasks.

## Patterns
- **git_status**: `git status -s`
- **git_add**: `git add <files>` (or `git add -A`)
- **git_commit**: `git commit -m "message"`
- **git_push** / **git_pull**
- **git_branch**: `git checkout -b <name>`
- **git_diff**: `git diff` / `git diff --staged`

## Examples
- "Show the current git status"
- "Add all changed files and commit with message 'fix bug'"
- "Push all branches to origin"
- "Create a new branch named 'feature-x'"

## Notes
Follow repo conventions. Confirm force-push / destructive actions.
