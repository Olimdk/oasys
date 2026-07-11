"""OASYS plugin: summarize uncommitted git changes and flag risks."""
import subprocess

NAME = "summarize_changes"
DESCRIPTION = "Summarize uncommitted git changes and flag risky edits. Usage: /run summarize_changes"


def _git(cmd: str, cwd: str | None = None) -> str:
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"[error] {e}"


def run(args: str, ctx: dict) -> str:
    diff = _git("git diff HEAD")
    if not diff.strip():
        return "No uncommitted changes."
    files = _git("git diff HEAD --name-only").splitlines()
    n = len(files)
    lines = [f"Changed {n} file(s):", ", ".join(files[:30])]
    # crude risk heuristics
    risks = []
    low = sum(1 for l in diff.splitlines() if l.startswith("-") and "password" in l.lower())
    hard = sum(1 for l in diff.splitlines() if l.startswith(("+", "-")) and "TODO" in l)
    if low:
        risks.append(f"{low} line(s) touching 'password' — verify no secrets committed")
    if hard:
        risks.append(f"{hard} TODO/FIXME line(s) added — remember to follow up")
    if any("except:" in l or "except :" in l for l in diff.splitlines()):
        risks.append("bare 'except:' found — consider catching specific exceptions")
    lines.append("")
    lines.append("Risks:" if risks else "Risks: none obvious.")
    lines.extend(f"  - {r}" for r in risks)
    lines.append("")
    lines.append("--- raw diff (first 4000 chars) ---")
    lines.append(diff[:4000])
    return "\n".join(lines)
