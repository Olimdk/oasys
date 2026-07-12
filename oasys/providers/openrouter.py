"""OpenRouter provider — fetches the live list of free models, supports streaming."""
import time
import json
import httpx
from .base import Provider, RateLimitError
from ..keystore import get_key
from oasys import settings as settings_mod

_CACHE = {"models": [], "ts": 0}
CACHE_TTL = 3600


def _fallback_model() -> str:
    try:
        return settings_mod.load().get("fallback_free_model") or "meta-llama/llama-3.3-70b-instruct:free"
    except Exception:
        return "meta-llama/llama-3.3-70b-instruct:free"


class OpenRouterProvider(Provider):
    name = "openrouter"

    def __init__(self):
        self.api_key = get_key("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not set. Run /key openrouter <key> or copy "
                ".env.example to .env and add your key."
            )
        self.base_url = "https://openrouter.ai/api/v1"

    def free_models(self) -> list[str]:
        now = time.time()
        if _CACHE["models"] and now - _CACHE["ts"] < CACHE_TTL:
            return _CACHE["models"]
        try:
            resp = httpx.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15,
            )
            resp.raise_for_status()
            all_models = resp.json()["data"]
            free = [m["id"] for m in all_models if m["id"].endswith(":free")]
            if free:
                _CACHE["models"] = free
                _CACHE["ts"] = now
                return free
        except Exception:
            pass
        return _CACHE["models"] or [_fallback_model()]

    def _post(self, client, messages, model):
        resp = client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages},
        )
        if resp.status_code == 429:
            raise RateLimitError(f"rate limited (429) for {model}")
        resp.raise_for_status()
        return resp.json()

    async def complete(self, messages: list[dict], model: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            data = self._post(client, messages, model)
            return {
                "content": data["choices"][0]["message"]["content"],
                "model_used": model,
                "usage": data.get("usage", {}),
            }

    async def stream_complete(self, messages: list[dict], model: str):
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": messages, "stream": True},
            ) as resp:
                if resp.status_code == 429:
                    raise RateLimitError(f"rate limited (429) for {model}")
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
