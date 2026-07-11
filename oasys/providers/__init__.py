"""Provider registry.

Built-in providers live in REGISTRY (below). User-added providers are read
from config.yaml (see oasys/settings.add_provider) and served via
GenericAPIProvider, so `/settings add provider ...` works with zero code.
"""
from .openrouter import OpenRouterProvider
from .generic import GenericAPIProvider
from oasys import settings as settings_mod

REGISTRY = {
    "openrouter": OpenRouterProvider,
    # Future: "openai": OpenAIProvider, "anthropic": AnthropicProvider, "ollama": OllamaProvider
}


def _config_providers() -> list:
    return settings_mod.load().get("providers", []) or []


def get_provider(name: str):
    for p in _config_providers():
        if p.get("name") == name:
            return GenericAPIProvider(p)
    if name not in REGISTRY:
        raise ValueError(f"Unknown provider '{name}'. Available: {available_providers()}")
    return REGISTRY[name]()


def available_providers() -> list:
    names = list(REGISTRY.keys())
    for p in _config_providers():
        if p.get("name") and p["name"] not in names:
            names.append(p["name"])
    return names
