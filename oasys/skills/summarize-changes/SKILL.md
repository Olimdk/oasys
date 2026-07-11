---
description: Summarizes uncommitted git changes and flags anything risky. Use when the user asks what changed, wants a commit message, or asks to review their diff.
---

# Summarize Changes

Use the OASYS `summarize_changes` plugin, or run:

    SHELL: git diff HEAD

Then summarize the diff in 2-3 bullets and list risks (missing error handling, hardcoded values, tests to update). If empty, say there are no uncommitted changes.
