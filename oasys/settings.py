"""Read/write config.yaml (in the user OASYS_HOME dir) plus skill/plugin dirs."""
import yaml
from pathlib import Path
from oasys import OASYS_HOME

CONFIG_PATH = OASYS_HOME / "config.yaml"
DEFAULT_CONFIG_FILE = Path(__file__).parent / "config_default.yaml"
USER_SKILLS_DIR = OASYS_HOME / "skills"
USER_PLUGINS_DIR = OASYS_HOME / "plugins"

DEFAULTS = {
    "provider": "openrouter",
    "models": [],
    "max_agent_steps": 150,
    "show_live_stream": False,
    "voice": {"input_enabled": False, "output_enabled": False, "tts_provider": "none"},
    "overnight_compact_every": 5,
    "providers": [],
    "goals": [],
    # --- additions ---
    "project_root": "",            # cwd for autonomous/overnight shell commands
    "shell_timeout": 120,          # seconds; agent shell commands are killed past this
    "fallback_free_model": "meta-llama/llama-3.3-70b-instruct:free",
    "max_history_tokens": 12000,   # compact overnight history once it exceeds this
}


def _ensure_config() -> None:
    if not CONFIG_PATH.exists() and DEFAULT_CONFIG_FILE.exists():
        OASYS_HOME.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(DEFAULT_CONFIG_FILE.read_text())


def load() -> dict:
    _ensure_config()
    if CONFIG_PATH.exists():
        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    else:
        data = {}
    merged = {**DEFAULTS, **data}
    merged["voice"] = {**DEFAULTS["voice"], **data.get("voice", {})}
    merged.setdefault("providers", [])
    merged.setdefault("goals", [])
    return merged


def save(config: dict) -> None:
    OASYS_HOME.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=False))


def set_key(dotted_key: str, value: str):
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


def get_key(dotted_key: str, config: dict | None = None) -> object:
    config = config or load()
    cur = config
    for p in dotted_key.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


# --- providers ---------------------------------------------------------------
def add_provider(name: str, base_url: str, api_key_env: str | None = None,
                 models: list | None = None, **extra) -> dict:
    config = load()
    providers = config.setdefault("providers", [])
    providers[:] = [p for p in providers if p.get("name") != name]
    entry = {"name": name, "base_url": base_url}
    entry["api_key_env"] = api_key_env or f"{name.upper()}_API_KEY"
    if models:
        entry["models"] = list(models)
    entry.update(extra)
    providers.append(entry)
    save(config)
    return entry


def remove_provider(name: str) -> bool:
    config = load()
    providers = config.get("providers", [])
    before = len(providers)
    providers[:] = [p for p in providers if p.get("name") != name]
    if len(providers) == before:
        return False
    save(config)
    return True


def list_providers() -> list:
    return load().get("providers", [])


# --- goals -------------------------------------------------------------------
def add_goal(text: str) -> int:
    config = load()
    goals = config.setdefault("goals", [])
    goals.append(text)
    save(config)
    return len(goals)


def remove_goal(index: int) -> str | None:
    config = load()
    goals = config.setdefault("goals", [])
    if 1 <= index <= len(goals):
        removed = goals.pop(index - 1)
        save(config)
        return removed
    return None


def clear_goals() -> None:
    config = load()
    config["goals"] = []
    save(config)


def get_goals() -> list:
    return load().get("goals", [])


# --- rendering ---------------------------------------------------------------
def render(config: dict | None = None) -> str:
    config = config or load()
    voice = config.get("voice", {})
    lines = [
        f"provider: {config.get('provider')}",
        f"models: {config.get('models') or '(auto: live free-model list)'}",
        f"max_agent_steps: {config.get('max_agent_steps')}",
        f"show_live_stream: {config.get('show_live_stream')}",
        f"voice.input_enabled: {voice.get('input_enabled')}",
        f"voice.output_enabled: {voice.get('voice.output_enabled', voice.get('output_enabled'))}",
        f"voice.tts_provider: {voice.get('tts_provider')}",
        f"overnight_compact_every: {config.get('overnight_compact_every')}",
        f"project_root: {config.get('project_root') or '(current dir)'}",
        f"shell_timeout: {config.get('shell_timeout')}s",
        f"fallback_free_model: {config.get('fallback_free_model')}",
        f"max_history_tokens: {config.get('max_history_tokens')}",
    ]
    goals = config.get("goals", [])
    lines.append(f"goals ({len(goals)}):")
    for i, g in enumerate(goals, 1):
        lines.append(f"  {i}. {g}")
    providers = config.get("providers", [])
    lines.append(f"providers ({len(providers)}):")
    for p in providers:
        models = p.get("models") or "(fetched live)"
        lines.append(f"  - {p.get('name')}: {p.get('base_url')} [key={p.get('api_key_env')}, models={models}]")
    return "\n".join(lines)
