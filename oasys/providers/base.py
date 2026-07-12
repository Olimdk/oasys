from abc import ABC, abstractmethod


class Provider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, messages: list[dict], model: str) -> dict:
        """Return dict with at least: {'content': str, 'model_used': str, 'usage': dict}"""
        ...

    @abstractmethod
    def free_models(self) -> list[str]:
        """List of model IDs this provider can use for free."""
        ...

    async def stream_complete(self, messages: list[dict], model: str):
        """Optional. Yield (chunk_text, done, usage) tuples as they arrive."""
        raise NotImplementedError
        yield  # pragma: no cover


class RateLimitError(Exception):
    """Raised when the provider returns HTTP 429 (rate limited / throttled)."""
