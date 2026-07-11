"""Plugin loader. Each plugin is a .py file exposing:
   NAME: str, DESCRIPTION: str, def run(args: str, ctx: dict) -> str

Plugins ship bundled inside the package AND can be installed by the user into
the OASYS_HOME/plugins directory.
"""
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from typing import Callable
from oasys import OASYS_HOME

BUNDLED_PLUGINS = Path(__file__).parent / "plugins"
USER_PLUGINS = OASYS_HOME / "plugins"


@dataclass
class Plugin:
    name: str
    description: str
    run: Callable[[str, dict], str]


def discover_plugins() -> dict[str, Plugin]:
    plugins = {}
    for base in (BUNDLED_PLUGINS, USER_PLUGINS):
        if not base.exists():
            continue
        for f in base.glob("*.py"):
            if f.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(f"oasys_user_plugin_{f.stem}", f)
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
