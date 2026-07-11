"""Shell execution. No interactive confirm prompt -- input() cannot work
inside a Textual app since Textual owns the terminal. Safety is enforced
via the deny-pattern list instead. Runs off the main thread so it cannot
freeze the UI."""
import subprocess
import asyncio

DENY_PATTERNS = ["rm -rf /", ":(){ :|:& };:", "mkfs", "> /dev/sda"]


def _run_blocking(command: str, cwd: str | None) -> str:
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=60
        )
        out = result.stdout + result.stderr
        return out.strip() or "[OK] Command completed with no output."
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Command took too long (60s limit)."
    except Exception as e:
        return f"[ERROR] {e}"


async def run_shell(command: str, cwd: str | None = None) -> str:
    if any(bad in command for bad in DENY_PATTERNS):
        return f"[BLOCKED] Command matches a hard-deny pattern: {command}"
    return await asyncio.to_thread(_run_blocking, command, cwd)
