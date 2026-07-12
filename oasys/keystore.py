"""Read/write provider API keys in the user .env file inside OASYS_HOME."""
import os
from pathlib import Path
from dotenv import load_dotenv
from oasys import OASYS_HOME

ENV_PATH = OASYS_HOME / ".env"

KNOWN_PROVIDERS = {
    "openrouter": "OPENROUTER_API_KEY",
}


def load_env() -> None:
    load_dotenv(ENV_PATH)


def get_key(name: str) -> str | None:
    load_env()
    return os.getenv(name)


def set_key(name: str, value: str) -> Path:
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
    """Return a mapping of env var -> masked value for every known provider key."""
    load_env()
    names = set(KNOWN_PROVIDERS.values())
    try:
        from oasys import settings as settings_mod
        for p in settings_mod.list_providers():
            env = p.get("api_key_env")
            if env:
                names.add(env)
    except Exception:
        pass
    out = {}
    for var in sorted(names):
        val = os.getenv(var)
        out[var] = ("..." + val[-4:]) if val else None
    return out


def env_var_for(provider: str) -> str:
    return KNOWN_PROVIDERS.get(provider.lower(), f"{provider.upper()}_API_KEY")
