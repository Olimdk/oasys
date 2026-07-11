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

## Setup
```bash
git clone https://github.com/YOUR_USERNAME/oasys.git
cd oasys
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OpenRouter API key
python -m oasys.app
```

## Configuration
Edit `config.yaml` to change provider or pin specific models.

## Adding a provider
Implement `oasys/providers/base.py`'s `Provider` interface and register it in
`oasys/providers/__init__.py`.

## License
MIT
