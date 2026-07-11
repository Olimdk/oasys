"""First-run setup: writes config + .env into the user OASYS_HOME directory.

Can run interactively, or non-interactively when OASYS_PROVIDER and
OASYS_API_KEY environment variables are supplied (used by install.sh).
"""
import os
from oasys import OASYS_HOME, settings as settings_mod
from oasys import keystore

CONFIG_PATH = settings_mod.CONFIG_PATH


def write_config(provider: str) -> None:
    # Never clobber an existing config (preserves user customizations).
    if CONFIG_PATH.exists():
        return
    settings_mod.save(settings_mod.load())
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
        env_var = keystore.env_var_for(provider)
        keystore.set_key(env_var, key)
        print(f"Saved {env_var} to {keystore.ENV_PATH} (persisted).")
    else:
        print("No API key provided - set one later with: /key <provider> <key>")

    write_config(provider)
    print("\nDone. Run: oasys   (or: python -m oasys.app)")


if __name__ == "__main__":
    main()
