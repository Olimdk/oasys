"""OASYS plugin: git operations (status, add, commit, push, pull, branch, diff)."""
import subprocess
from pathlib import Path

NAME = "git_ops"
DESCRIPTION = "Git status/add/commit/push/pull/branch/diff. Usage: /run git_ops <subcommand> [args]"


def _git(cmd: str, cwd: str | None = None) -> str:
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)
        out = (r.stdout + r.stderr).strip()
        return out or "[OK] done (no output)"
    except subprocess.TimeoutExpired:
        return "[git_ops] timeout (60s)"
    except Exception as e:
        return f"[git_ops] error: {e}"


def run(args: str, ctx: dict) -> str:
    parts = args.split(maxsplit=1)
    if not parts:
        return "[git_ops] usage: status | add <files> | commit <msg> | push | pull | branch <name> | diff [--staged]"
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if cmd == "status":
        return _git("git status -s")
    if cmd == "add":
        return _git(f"git add {rest or '-A'}")
    if cmd == "commit":
        if not rest:
            return "[git_ops] commit message required"
        return _git(f"git commit -m \"{rest}\"")
    if cmd == "push":
        return _git("git push")
    if cmd == "pull":
        return _git("git pull")
    if cmd == "branch":
        return _git(f"git checkout -b {rest}" if rest else "git branch")
    if cmd == "diff":
        return _git("git diff --staged" if "staged" in rest else "git diff")
    return "[git_ops] unknown subcommand"
