"""Routes requests through the configured provider, falling back across its free models."""
import asyncio
from oasys.providers import get_provider
from oasys.providers.base import RateLimitError
from oasys.settings import load as load_config


async def route_completion(messages: list[dict]) -> dict:
    config = load_config()
    provider = get_provider(config.get("provider", "openrouter"))
    candidates = config.get("models") or provider.free_models()

    last_error = None
    for model in candidates:
        try:
            result = await provider.complete(messages, model)
            return {
                "choices": [{"message": {"content": result["content"]}}],
                "_model_used": result["model_used"],
                "_usage": result.get("usage", {}),
            }
        except Exception as e:
            last_error = f"{model}: {e}"
            continue

    raise RuntimeError(f"All models failed for provider '{provider.name}'. Last error: {last_error}")


async def route_stream(messages: list[dict]):
    """Stream completions, falling back across models and retrying on 429.

    Yields (chunk_text, done, usage, model) tuples. On a rate-limit we back off
    and try the next candidate; other errors also advance to the next model.
    """
    config = load_config()
    provider = get_provider(config.get("provider", "openrouter"))
    candidates = list(config.get("models") or provider.free_models())

    last_error = None
    tried = set()
    for attempt in range(3):
        for model in candidates:
            if model in tried:
                continue
            try:
                async for chunk, done, usage in provider.stream_complete(messages, model):
                    yield chunk, done, usage, model
                return
            except NotImplementedError:
                try:
                    result = await provider.complete(messages, model)
                    yield result["content"], False, {}, model
                    yield "", True, result.get("usage", {}), model
                    return
                except Exception as e:
                    last_error = f"{model}: {e}"
                    continue
            except RateLimitError:
                tried.add(model)
                await asyncio.sleep(2 * (attempt + 1))
                continue
            except Exception as e:
                last_error = f"{model}: {e}"
                tried.add(model)
                continue
        if set(candidates) and tried >= set(candidates):
            break

    raise RuntimeError(f"All models failed for provider '{provider.name}'. Last error: {last_error}")
