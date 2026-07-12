"""Shell execution. No interactive confirm prompt -- input() cannot work
inside a Textual app since Textual owns the terminal. Safety is enforced via
a deny-pattern list (anchored regexes) instead. Runs off the main thread so
it cannot freeze the UI."""
import os
import re
import subprocess
import asyncio

# Hard-deny patterns. Each is an anchored regex matching only the genuinely
# destructive invocations (e.g. `rm -rf /` exactly, NOT `rm -rf /home/...`).
DENY_REGEXES = [
    re.compile(r"rm\s+-rf\s+/\s*$"),                 # rm -rf /            (root)
    re.compile(r"rm\s+-rf\s+~\s*$"),                 # rm -rf ~            (home, exact)
    re.compile(r"rm\s+-rf\s+~/"),                    # anything under home
    re.compile(r"rm\s+-rf\s+\.\s*$"),                # rm -rf .            (cwd exact)
    re.compile(r"rm\s+-rf\s+\./\s*$"),               # rm -rf ./           (cwd exact)
    re.compile(r":\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),  # fork bomb
    re.compile(r"\bmkfs\b"),
    re.compile(r">\s*/dev/sd"),
    re.compile(r"\bwipefs\b"),
    re.compile(r"dd\s+if=/dev/"),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"chmod\s+-R\s+(000|777)\s+/\s*$"),   # chmod -R 000/777 /  (root)
]

# Configurable per-command timeout (seconds). Env OASYS_SHELL_TIMEOUT overrides.
SHELL_TIMEOUT = float(os.environ.get("OASYS_SHELL_TIMEOUT", "120"))


def _blocked(command: str) -> bool:
    return any(rx.search(command) for rx in DENY_REGEXES)


def _run_blocking(command: str, cwd: str | None) -> str:
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=SHELL_TIMEOUT
        )
        out = result.stdout + result.stderr
        return out.strip() or "[OK] Command completed with no output."
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Command took too long ({SHELL_TIMEOUT:.0f}s limit)."
    except Exception as e:
        return f"[ERROR] {e}"


async def run_shell(command: str, cwd: str | None = None) -> str:
    if _blocked(command):
        return f"[BLOCKED] Command matches a hard-deny pattern: {command}"
    return await asyncio.to_thread(_run_blocking, command, cwd)
