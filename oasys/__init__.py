"""OASYS - local autonomous coding assistant with a Claude Code-style TUI."""
from pathlib import Path
import os

__version__ = "0.2.1"

# Runtime data directory: config, API keys, and installed skills/plugins live here.
# Resolution order:
#   1. OASYS_DATA_HOME  (explicit data relocation, set by install.sh if provided)
#   2. OASYS_HOME       (legacy/alias)
#   3. ~/.oasys         (default)
# The installed package directory stays read-only; user data is kept separate
# so reinstalls and version rollbacks never disturb it.
_OASYS_DATA = os.environ.get("OASYS_DATA_HOME") or os.environ.get("OASYS_HOME")
OASYS_HOME = Path(_OASYS_DATA) if _OASYS_DATA else (Path.home() / ".oasys")
OASYS_HOME.mkdir(parents=True, exist_ok=True)
