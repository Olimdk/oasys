"""Provider registry. Add new providers here so users can pick one in config.yaml."""
from .openrouter import OpenRouterProvider

REGISTRY = {
    "openrouter": OpenRouterProvider,
    # Future: "openai": OpenAIProvider, "anthropic": AnthropicProvider, "ollama": OllamaProvider
}


def get_provider(name: str):
    if name not in REGISTRY:
        raise ValueError(f"Unknown provider '{name}'. Available: {list(REGISTRY.keys())}")
    return REGISTRY[name]()
