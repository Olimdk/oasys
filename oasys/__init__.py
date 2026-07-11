"""OASYS - local autonomous coding assistant with a Claude Code-style TUI."""
from pathlib import Path
import os

__version__ = "0.2.0"

# Runtime data directory: config, API keys, and installed skills/plugins live here.
# Override with the OASYS_HOME environment variable.
OASYS_HOME = Path(os.environ.get("OASYS_HOME", Path.home() / ".oasys"))
OASYS_HOME.mkdir(parents=True, exist_ok=True)
