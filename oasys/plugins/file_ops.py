"""OASYS plugin: file operations (read, write, list, search, delete)."""
import os
from pathlib import Path

NAME = "file_ops"
DESCRIPTION = "Read/write/list/search files. Usage: /run file_ops <read|write|ls|search|delete> <args>"


def run(args: str, ctx: dict) -> str:
    parts = args.split(maxsplit=1)
    if not parts:
        return "[file_ops] usage: read <path> | write <path> <text> | ls <dir> | search <pattern> [path] | delete <path>"
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    try:
        if cmd == "read":
            p = Path(rest)
            if not p.exists():
                return f"[file_ops] not found: {rest}"
            return p.read_text(errors="ignore")[:8000]

        elif cmd == "write":
            toks = rest.split(maxsplit=1)
            if len(toks) < 2:
                return "[file_ops] usage: write <path> <text>"
            p = Path(toks[0])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(toks[1])
            return f"[file_ops] wrote {len(toks[1])} chars to {toks[0]}"

        elif cmd == "ls":
            d = Path(rest or ".")
            if not d.is_dir():
                return f"[file_ops] not a directory: {rest}"
            items = sorted(p.name + ("/" if p.is_dir() else "") for p in d.iterdir())
            return "\n".join(items[:200]) or "[empty]"

        elif cmd == "search":
            toks = rest.split()
            if not toks:
                return "[file_ops] usage: search <pattern> [path]"
            pattern = toks[0]
            base = toks[1] if len(toks) > 1 else "."
            hits = []
            for root, _, files in os.walk(base):
                for f in files:
                    if f.startswith("."):
                        continue
                    fp = os.path.join(root, f)
                    try:
                        if pattern.lower() in f.lower() or pattern.lower() in open(fp, errors="ignore").read().lower():
                            hits.append(fp)
                    except Exception:
                        continue
                    if len(hits) >= 50:
                        break
                if len(hits) >= 50:
                    break
            return "\n".join(hits) or "[no matches]"

        elif cmd == "delete":
            p = Path(rest)
            if p.exists():
                p.unlink() if p.is_file() else None
                return f"[file_ops] deleted {rest}"
            return f"[file_ops] not found: {rest}"

        return "[file_ops] unknown subcommand. Try: read/write/ls/search/delete"
    except Exception as e:
        return f"[file_ops] error: {e}"
