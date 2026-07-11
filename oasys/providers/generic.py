"""Generic OpenAI-compatible API provider, fully configured from settings.

Lets users add any OpenAI-style chat-completions endpoint (OpenAI, Together,
Groq, Ollama, vLLM, LocalAI, etc.) via `/settings add provider ...` without
writing code. See oasys/settings.py for the config shape.
"""
import json
import httpx
from .base import Provider
from ..keystore import get_key


class GenericAPIProvider(Provider):
    def __init__(self, config: dict):
        self.cfg = config or {}
        self.name = self.cfg.get("name", "generic")
        self.base_url = str(self.cfg.get("base_url", "")).rstrip("/")
        if not self.base_url:
            raise RuntimeError(f"Provider '{self.name}' has no base_url configured.")
        self.api_key_env = self.cfg.get("api_key_env", f"{self.name.upper()}_API_KEY")
        self.models = list(self.cfg.get("models", []) or [])
        self.models_endpoint = self.cfg.get("models_endpoint", "/models")
        self.free_filter = self.cfg.get("free_filter", "")
        # Resolve key: env var first, then an inline api_key (for local/no-auth setups).
        self.api_key = get_key(self.api_key_env) or self.cfg.get("api_key", "")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def free_models(self) -> list[str]:
        if self.models:
            return list(self.models)
        try:
            resp = httpx.get(
                f"{self.base_url}{self.models_endpoint}",
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", data) if isinstance(data, dict) else data
            ids = [m["id"] for m in items if isinstance(m, dict) and "id" in m]
            if self.free_filter:
                ids = [i for i in ids if self.free_filter in i]
            if ids:
                return ids
        except Exception:
            pass
        return self.models or ["default"]

    async def complete(self, messages: list[dict], model: str) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": messages},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model_used": model,
                "usage": data.get("usage", {}),
            }

    async def stream_complete(self, messages: list[dict], model: str):
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": messages, "stream": True},
            ) as resp:
                resp.raise_for_status()
                usage = {}
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        obj = json.loads(payload)
                    except Exception:
                        continue
                    if obj.get("usage"):
                        usage = obj["usage"]
                    choices = obj.get("choices", [])
                    if choices:
                        content = choices[0].get("delta", {}).get("content")
                        if content:
                            yield content, False, {}
                yield "", True, usage
