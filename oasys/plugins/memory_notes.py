"""OASYS plugin: persistent memory notes in ~/.oasys/memory.

Lets OASYS remember facts across sessions, mirroring the MCP 'memory' idea
but OASYS-native (plain Markdown files, no external server).
"""
from pathlib import Path

NAME = "memory_notes"
DESCRIPTION = "Persistent notes in ~/.oasys/memory. Usage: /run memory_notes <remember|recall|list|forget> [args]"

MEM_DIR = Path.home() / ".oasys" / "memory"
MEM_DIR.mkdir(parents=True, exist_ok=True)


def run(args: str, ctx: dict) -> str:
    parts = args.split(maxsplit=1)
    if not parts:
        return "[memory_notes] usage: remember <topic> <text> | recall <topic> | list | forget <topic>"
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if cmd == "remember":
        toks = rest.split(maxsplit=1)
        if len(toks) < 2:
            return "[memory_notes] usage: remember <topic> <text>"
        topic, text = toks
        f = MEM_DIR / f"{topic.replace('/', '_')}.md"
        with open(f, "a") as fh:
            fh.write(text + "\n")
        return f"[memory_notes] remembered '{topic}' -> {f}"

    if cmd == "recall":
        if not rest:
            return "[memory_notes] specify a topic to recall"
        f = MEM_DIR / f"{rest.replace('/', '_')}.md"
        if f.exists():
            return f"[memory_notes] {rest}:\n" + f.read_text()
        return f"[memory_notes] nothing remembered about '{rest}'"

    if cmd == "list":
        files = [p.stem for p in MEM_DIR.glob("*.md")]
        return "[memory_notes] topics: " + (", ".join(files) if files else "(none)")

    if cmd == "forget":
        f = MEM_DIR / f"{rest.replace('/', '_')}.md"
        if f.exists():
            f.unlink()
            return f"[memory_notes] forgot '{rest}'"
        return f"[memory_notes] no such topic: {rest}"

    return "[memory_notes] unknown subcommand"
