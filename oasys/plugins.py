"""Plugin loader. Each plugin is a .py file in oasys/plugins/ exposing:
   NAME: str, DESCRIPTION: str, def run(args: str, ctx: dict) -> str
"""
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from typing import Callable

PLUGIN_DIR = Path(__file__).parent / "plugins"


@dataclass
class Plugin:
    name: str
    description: str
    run: Callable[[str, dict], str]


def discover_plugins() -> dict[str, Plugin]:
    plugins = {}
    if not PLUGIN_DIR.exists():
        return plugins
    for f in PLUGIN_DIR.glob("*.py"):
        if f.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            if hasattr(mod, "run"):
                plugins[getattr(mod, "NAME", f.stem)] = Plugin(
                    name=getattr(mod, "NAME", f.stem),
                    description=getattr(mod, "DESCRIPTION", ""),
                    run=mod.run,
                )
        except Exception:
            continue
    return plugins
