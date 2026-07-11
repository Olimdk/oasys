"""Read/write config.yaml, including nested keys like voice.output_enabled."""
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

DEFAULTS = {
    "provider": "openrouter",
    "models": [],
    "max_agent_steps": 25,
    "show_live_stream": False,
    "voice": {"input_enabled": False, "output_enabled": False, "tts_provider": "none"},
}


def load() -> dict:
    if CONFIG_PATH.exists():
        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    else:
        data = {}
    merged = {**DEFAULTS, **data}
    merged["voice"] = {**DEFAULTS["voice"], **data.get("voice", {})}
    return merged


def save(config: dict) -> None:
    CONFIG_PATH.write_text(yaml.dump(config, sort_keys=False))


def set_key(dotted_key: str, value: str):
    """Supports 'provider' or nested 'voice.output_enabled'."""
    config = load()
    parts = dotted_key.split(".")
    target = config
    for p in parts[:-1]:
        if p not in target or not isinstance(target[p], dict):
            target[p] = {}
        target = target[p]

    last = parts[-1]
    if value.lower() in ("true", "false"):
        value = value.lower() == "true"
    elif value.isdigit():
        value = int(value)
    target[last] = value

    save(config)
    return config


def render(config: dict) -> str:
    lines = [
        f"provider: {config['provider']}",
        f"models: {config['models'] or '(auto: live free-model list)'}",
        f"max_agent_steps: {config['max_agent_steps']}",
        f"show_live_stream: {config['show_live_stream']}",
        f"voice.input_enabled: {config['voice']['input_enabled']}",
        f"voice.output_enabled: {config['voice']['output_enabled']}",
        f"voice.tts_provider: {config['voice']['tts_provider']}",
    ]
    return "\n".join(lines)
