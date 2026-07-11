"""First-run setup: writes .env (API key) and config.yaml.

Can run interactively, or non-interactively when OASYS_PROVIDER and
OASYS_API_KEY environment variables are supplied (used by install.sh).
"""
import os
from pathlib import Path
from oasys.keystore import set_key, env_var_for

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.yaml"

DEFAULT_CONFIG = (
    "provider: openrouter\n"
    "models: []\n"
    "max_agent_steps: 150\n"
    "show_live_stream: false\n"
    "voice:\n"
    "  input_enabled: false\n"
    "  output_enabled: false\n"
    "  tts_provider: none\n"
)


def write_config(provider: str) -> None:
    # Never clobber an existing config (preserves user customizations).
    if CONFIG_PATH.exists():
        return
    CONFIG_PATH.write_text(DEFAULT_CONFIG)
    print(f"Wrote {CONFIG_PATH}")


def main() -> None:
    provider = (
        os.environ.get("OASYS_PROVIDER")
        or input("Provider [openrouter]: ").strip()
        or "openrouter"
    )
    key = os.environ.get("OASYS_API_KEY")
    if key is None:
        key = input(f"API key for {provider}: ").strip()

    if key:
        env_var = env_var_for(provider)
        set_key(env_var, key)
        print(f"Saved {env_var} to {ROOT / '.env'} (persisted).")
    else:
        print("No API key provided — set one later with: /key <provider> <key>")

    write_config(provider)
    print("\nDone. Run: oasys   (or: python -m oasys.app)")


if __name__ == "__main__":
    main()
