"""Interactive first-run setup: writes .env and config.yaml."""
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    print("=== OASYS setup ===\n")
    provider = input("Provider [openrouter]: ").strip() or "openrouter"
    key = input(f"API key for {provider}: ").strip()

    env_path = ROOT / ".env"
    if provider == "openrouter":
        env_path.write_text(f"OPENROUTER_API_KEY={key}\n")
    else:
        env_path.write_text(f"{provider.upper()}_API_KEY={key}\n")
    print(f"Wrote {env_path}")

    config_path = ROOT / "config.yaml"
    config_path.write_text(f"provider: {provider}\nmodels: []\n")
    print(f"Wrote {config_path}")

    print("\nDone. Run: python -m oasys.app")


if __name__ == "__main__":
    main()
