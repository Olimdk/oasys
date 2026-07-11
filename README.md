# OASYS

A terminal AI coding assistant, styled after Claude Code, built to run entirely on free-tier
models. Provider-agnostic under the hood - starts with OpenRouter's free models, more
providers can be added. Ships as a single Python package with everything built in:
TUI, skills, plugins, provider system, and an autonomous /overnight mode.

## Features
- Claude Code-style TUI (Textual)
- Automatic fallback across free models if one is rate-limited or down
- Bundled skills + plugins (extensible via marketplaces)
- Gated shell execution (confirm-by-default, togglable to unattended)
- Pluggable provider system (`/settings add provider ...`) - OpenAI-compatible APIs work
- Standing goals (`/goal`) and autonomous `/overnight <duration>` mode

## Install (one command)

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

The installer clones OASYS, creates a Python virtualenv, installs the package, prompts for
your provider + API key, and drops an `oasys` launcher on your PATH. Pre-fill the key for an
unattended install:

    OASYS_API_KEY=sk-or-... curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

Install somewhere else:

    OASYS_HOME=~/my-oasys curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

After install, just run `oasys`.

## Install (as a Python package)

From a clone:

    git clone https://github.com/Olimdk/oasys.git
    cd oasys
    python3 -m venv venv && source venv/bin/activate
    pip install .
    oasys

Or with pipx (recommended for a clean global install):

    git clone https://github.com/Olimdk/oasys.git
    cd oasys
    pipx install .

User data (config, API keys, installed skills/plugins) lives in `~/.oasys` (override with the
`OASYS_HOME` environment variable), so the installed package directory stays read-only.

## Managing your API key

OASYS stores API keys in a gitignored `~/.oasys/.env` file, so they are never committed. Set
or update a key at any time from inside the app:

    /key openrouter sk-or-v1-xxxx

Run `/key` (or `/key status`) to see which keys are set. The key is saved immediately and
persists across restarts - no need to edit files by hand. You can also re-run the setup
wizard (`python -m oasys.setup_wizard`) to (re)write the key.

## Configuration
Runtime config lives in `~/.oasys/config.yaml` (created from built-in defaults on first run).
Change it from the app with `/settings set <key> <value>`, or edit the file directly.

## Commands

    /help        this menu
    /skills      list loaded skills
    /plugins     list loaded plugins
    /run <p>     execute a plugin
    /model       show current model list
    /clear       reset conversation
    /compact     summarize history to save context
    /settings    view/change config (set/get/add provider/remove provider/providers)
    /key         set or show API key status
    /goal <text> set a standing objective (also: /goal list|remove <n>|clear)
    /overnight <duration>   run autonomously, e.g. /overnight 5h
    /stop        halt an /overnight run
    /plugin      install skills/plugins from a marketplace

## Adding a provider
No code required for any OpenAI-compatible chat-completions API. From the app:

    /settings add provider openai https://api.openai.com/v1 OPENAI_API_KEY gpt-4o-mini
    /settings set provider openai
    /key openai sk-...

This writes the provider into `~/.oasys/config.yaml` and it is available immediately.

## Autonomous / overnight mode
Set one or more goals, then let OASYS work unattended for a duration:

    /goal refactor the router for clarity
    /goal add tests for the plugins module
    /overnight 5h

It iterates: inspect repo state -> pick one small safe change -> implement it -> run tests ->
commit -> repeat, until the timer expires. Status shows a live countdown. Type `/stop` to halt.

## License
MIT
