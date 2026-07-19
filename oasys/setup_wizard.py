"""First-run setup: writes config + .env into the user OASYS_HOME directory.

Can run interactively (TTY + no env key), or non-interactively when
OASYS_PROVIDER and/or OASYS_API_KEY environment variables are supplied (used
by install.sh). When there is no controlling terminal and no API key is
provided, the key prompt is skipped gracefully instead of crashing with
EOFError, so an automated install can still complete and the user can set the
key later from inside the app with `/key`.
"""
import os
import sys
from oasys import OASYS_HOME, settings as settings_mod
from oasys import keystore

CONFIG_PATH = settings_mod.CONFIG_PATH


def _prompt(prompt: str, default: str, secret: bool = False) -> str:
    """Prompt on a TTY; otherwise fall back to the default / env value."""
    if sys.stdin.isatty():
        if secret:
            import getpass
            val = getpass.getpass(prompt)
        else:
            val = input(prompt)
        return val.strip() or default
    # Non-interactive: do not read from stdin (would raise EOFError).
    return default


def write_config(provider: str) -> None:
    # Never clobber an existing config (preserves user customizations).
    if CONFIG_PATH.exists():
        return
    settings_mod.save(settings_mod.load())
    print(f"Wrote {CONFIG_PATH}")


def main() -> None:
    provider = (
        os.environ.get("OASYS_PROVIDER")
        or _prompt("Provider [openrouter]: ", "openrouter")
        or "openrouter"
    )
    key = os.environ.get("OASYS_API_KEY")
    if key is None:
        # Only prompt interactively; otherwise leave the key unset.
        key = _prompt(f"API key for {provider}: ", "", secret=True)

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
