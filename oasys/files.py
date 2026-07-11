"""File read/write with diff preview. Edits apply immediately and the diff
is always shown in the log so you can see exactly what changed."""
import difflib
from pathlib import Path


def read_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"[ERROR] File not found: {path}"
    try:
        return p.read_text(errors="ignore")
    except Exception as e:
        return f"[ERROR] {e}"


def diff_preview(path: str, new_content: str) -> str:
    p = Path(path).expanduser()
    old_content = p.read_text(errors="ignore") if p.exists() else ""
    diff = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    text = "".join(diff)
    return text or "[no changes]"


def write_file(path: str, new_content: str) -> tuple[str, str]:
    """Returns (diff_text, result_message). Applies immediately — no
    interactive confirmation, since that doesn't work reliably inside a
    Textual TUI. Review the diff shown in the log after each edit."""
    diff = diff_preview(path, new_content)
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_content)
        return diff, f"[OK] Wrote {path} ({len(new_content)} bytes)"
    except Exception as e:
        return diff, f"[ERROR] {e}"
