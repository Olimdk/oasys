"""File read/write with diff preview and pre-edit backups.

Edits apply immediately (no interactive confirm inside the TUI) and a diff is
always shown. Before overwriting an existing file we stash the prior version
in OASYS_HOME/backups so an autonomous/bad edit is recoverable.
"""
import difflib
import shutil
import time
from pathlib import Path

from oasys import OASYS_HOME

BACKUP_DIR = OASYS_HOME / "backups"


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
    """Returns (diff_text, result_message). Applies immediately and keeps a
    timestamped backup of the previous version when the file already existed."""
    diff = diff_preview(path, new_content)
    p = Path(path).expanduser()
    try:
        if p.exists():
            try:
                BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%d-%H%M%S")
                dest = BACKUP_DIR / f"{ts}-{p.name}"
                shutil.copy2(p, dest)
            except Exception:
                pass  # backup is best-effort; don't fail the write
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_content)
        return diff, f"[OK] Wrote {path} ({len(new_content)} bytes)"
    except Exception as e:
        return diff, f"[ERROR] {e}"
