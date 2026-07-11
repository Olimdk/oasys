#!/usr/bin/env bash
#
# OASYS one-command installer (installs the package into a venv).
#   curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash
#
# Environment overrides:
#   OASYS_HOME     install directory   (default: ~/.local/share/oasys)
#   OASYS_BRANCH   git branch to clone (default: main)
#   OASYS_PROVIDER provider name       (default: openrouter)  - used with OASYS_API_KEY
#   OASYS_API_KEY  API key             (optional; prompted if omitted)
#
set -euo pipefail

OASYS_HOME="${OASYS_HOME:-$HOME/.local/share/oasys}"
REPO="https://github.com/Olimdk/oasys.git"
BRANCH="${OASYS_BRANCH:-main}"

echo "==> OASYS installer"

# --- dependency checks ---
need() { command -v "$1" >/dev/null 2>&1 || { echo "error: '$1' is required but not installed." >&2; exit 1; }; }
need git
need python3
need curl

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"; then
  echo "error: python3 >= 3.10 is required." >&2
  exit 1
fi

# --- clone / update ---
if [ -d "$OASYS_HOME/.git" ]; then
  echo "==> updating existing install at $OASYS_HOME"
  git -C "$OASYS_HOME" pull --ff-only
else
  echo "==> cloning OASYS into $OASYS_HOME"
  git clone --depth 1 -b "$BRANCH" "$REPO" "$OASYS_HOME"
fi

cd "$OASYS_HOME"

# --- virtualenv + install the package ---
if [ ! -d venv ]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet .

# --- API key / config (only if missing) ---
if [ ! -f "$HOME/.oasys/.env" ] || [ ! -f "$HOME/.oasys/config.yaml" ]; then
  if [ ! -f "$HOME/.oasys/.env" ]; then
    if [ -z "${OASYS_API_KEY:-}" ]; then
      read -r -p "Provider [openrouter]: " PROV
      PROV="${PROV:-openrouter}"
      read -r -s -p "API key for $PROV: " KEY
      echo
    else
      PROV="${OASYS_PROVIDER:-openrouter}"
      KEY="$OASYS_API_KEY"
    fi
    OASYS_PROVIDER="$PROV" OASYS_API_KEY="$KEY" python3 -m oasys.setup_wizard
  else
    python3 -m oasys.setup_wizard
  fi
fi

# --- launcher (the package provides a console script: venv/bin/oasys) ---
LAUNCHER_SRC="$OASYS_HOME/venv/bin/oasys"
if [ -w /usr/local/bin ]; then
  ln -sf "$LAUNCHER_SRC" /usr/local/bin/oasys
  echo "==> installed launcher: /usr/local/bin/oasys"
else
  BIN_DIR="$HOME/.local/bin"
  mkdir -p "$BIN_DIR"
  ln -sf "$LAUNCHER_SRC" "$BIN_DIR/oasys"
  if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo
    echo "NOTE: $BIN_DIR is not on your PATH. Add it with:"
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
  else
    echo "==> installed launcher: $BIN_DIR/oasys"
  fi
fi

echo
echo "==> OASYS installed."
echo "    Run it with:  oasys"
echo "    First run opens the TUI. Set a key anytime with:  /key openrouter <key>"
