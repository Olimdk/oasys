"""Read/write provider API keys in the user .env file inside OASYS_HOME.

The .env file lives in ~/.oasys (or $OASYS_HOME) and is gitignored, so keys
never get committed. Use set_key() to persist a key the user inserts (e.g. via
the /key command) and get_key() to read it back.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from oasys import OASYS_HOME

ENV_PATH = OASYS_HOME / ".env"

# Map of provider name -> env var that holds its API key.
KNOWN_PROVIDERS = {
    "openrouter": "OPENROUTER_API_KEY",
}


def load_env() -> None:
    """Load .env into os.environ (idempotent; does not clobber existing vars)."""
    load_dotenv(ENV_PATH)


def get_key(name: str) -> str | None:
    load_env()
    return os.getenv(name)


def set_key(name: str, value: str) -> Path:
    """Persist or update ``name=value`` in the project .env file.

    Existing lines (including comments) are preserved; only the matching
    key is replaced, or a new line is appended if it does not exist.
    The value is also exported into the current process environment so the
    change takes effect immediately without a restart.
    """
    OASYS_HOME.mkdir(parents=True, exist_ok=True)
    text = ""
    found = False
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                text += line + "\n"
                continue
            key, _, _ = line.partition("=")
            if key.strip() == name:
                text += f"{name}={value}\n"
                found = True
            else:
                text += line + "\n"
    if not found:
        text += f"{name}={value}\n"
    ENV_PATH.write_text(text)
    os.environ[name] = value
    return ENV_PATH


def key_status() -> dict:
    """Return a mapping of known env vars to a masked value or None."""
    load_env()
    out = {}
    for var in KNOWN_PROVIDERS.values():
        val = os.getenv(var)
        out[var] = ("..." + val[-4:]) if val else None
    return out


def env_var_for(provider: str) -> str:
    return KNOWN_PROVIDERS.get(provider.lower(), f"{provider.upper()}_API_KEY")
