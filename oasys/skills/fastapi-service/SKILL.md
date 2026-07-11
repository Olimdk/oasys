---
description: Building a new FastAPI service, REST endpoint, or backend microservice. Use when asked to scaffold, add, or extend a FastAPI-based API.
---

## Instructions
1. Create the service under `services/<name>/` with `main.py`, `requirements.txt`, `Dockerfile`, `tests/`.
2. Use Pydantic models for request/response validation.
3. Add a `/health` endpoint by default.
4. Write at least one pytest per endpoint before considering the task done.
5. Run `pytest` and `ruff check .` and report results before marking the goal step complete.

## Notes
Prefer `uv` or `pip-tools` for dependency pinning if the project already uses one of them; otherwise plain `requirements.txt` is fine.
