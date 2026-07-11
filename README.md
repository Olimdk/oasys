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

## Install (one command)

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

The installer clones OASYS into `~/.local/share/oasys`, creates a Python virtualenv,
installs dependencies, prompts for your provider + API key, and drops an `oasys` launcher
on your PATH. Pre-fill the key for an unattended install:

    OASYS_API_KEY=sk-or-... curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

Install somewhere else:

    OASYS_HOME=~/my-oasys curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

After install, just run `oasys`.

## Manual setup

    git clone https://github.com/Olimdk/oasys.git
    cd oasys
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python -m oasys.setup_wizard   # prompts for provider + API key
    python -m oasys.app

## Managing your API key

OASYS stores API keys in a gitignored `.env` file at the project root, so they are never
committed. Set or update a key at any time from inside the app:

    /key openrouter sk-or-v1-xxxx

Run `/key` (or `/key status`) to see which keys are set. The key is saved immediately and
persists across restarts — no need to edit files by hand. You can also re-run the setup
wizard (`python -m oasys.setup_wizard`) to (re)write the key.

## Configuration
Edit `config.yaml` to change provider or pin specific models. Runtime settings can also be
changed from the app with `/settings set <key> <value>`.

## Commands

    /help        this menu
    /skills      list loaded skills
    /plugins     list loaded plugins
    /run <p>     execute a plugin
    /model       show current model list
    /clear       reset conversation
    /compact     summarize history to save context
    /settings    view/change config
    /key         set or show API key status
    /plugin      install skills/plugins from a marketplace

## Adding a provider
Implement `oasys/providers/base.py`'s `Provider` interface and register it in
`oasys/providers/__init__.py`.

## License
MIT
