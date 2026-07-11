# OASYS

A terminal AI coding assistant, styled after Claude Code, built to run entirely on free-tier
models. Provider-agnostic under the hood — starts with OpenRouter's free models, more
providers can be added.

## Features
- Claude Code-style TUI (Textual)
- Automatic fallback across free models if one is rate-limited or down
- Loads existing Claude Code `SKILL.md` skills from `~/.claude/skills`
- Gated shell execution (confirm-by-default, togglable to unattended)
- Pluggable provider system (`oasys/providers/`)

## Install (one line)

