#!/usr/bin/env bash
#
# OASYS one-command installer (installs the package into a venv).
#
#   Install the LATEST (rolling main):
#     curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash
#
#   Install a SPECIFIC RELEASE (one curl command per version):
#     curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/v0.2.0/install.sh | bash
#
#   You can still override the version explicitly if you like:
#     curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | OASYS_REF=v0.2.0 bash
#
#   Environment overrides:
#     OASYS_HOME     install directory   (default: ~/.local/share/oasys)
#     OASYS_BRANCH   git branch to clone (default: main)   - used only on first clone
#     OASYS_REF      git ref to pin/roll back to: tag | branch | commit
#                     (default: empty -> the OASYS_VERSION baked into this file)
#     OASYS_PROVIDER provider name       (default: openrouter)  - used with OASYS_API_KEY
#     OASYS_API_KEY  API key             (optional; prompted if omitted)
#
#   How per-version curl works: each release's install.sh has OASYS_VERSION
#   baked in (e.g. "v0.2.0"). When you fetch that release's install.sh from
#   GitHub, it checks out the matching tag automatically -- no guessing.
#
set -euo pipefail

OASYS_HOME="${OASYS_HOME:-$HOME/.local/share/oasys}"
REPO="https://github.com/Olimdk/oasys.git"
BRANCH="${OASYS_BRANCH:-main}"

# Baked per release. On 'main' this is empty (rolling latest).
OASYS_VERSION="v0.2.0"

# Resolve the ref to install: explicit override wins, else the baked version.
REF="${OASYS_REF:-${OASYS_VERSION}}"

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
  git -C "$OASYS_HOME" fetch --tags --force "$REPO"
  if [ -n "$REF" ]; then
    # Pin/roll back to an explicit release. This is what lets you go BACK
    # to a previous version if a newer release breaks things.
    echo "==> pinning to $REF"
    git -C "$OASYS_HOME" checkout --force "$REF"
  else
    # No ref requested: move forward on the configured branch (rolling latest).
    git -C "$OASYS_HOME" checkout --force "$BRANCH"
    git -C "$OASYS_HOME" pull --ff-only
  fi
else
  echo "==> cloning OASYS into $OASYS_HOME"
  if [ -n "$REF" ]; then
    # Clone full history (not shallow) so the tag/commit ref is reachable.
    git clone "$REPO" "$OASYS_HOME"
    git -C "$OASYS_HOME" checkout --force "$REF"
  else
    git clone --depth 1 -b "$BRANCH" "$REPO" "$OASYS_HOME"
  fi
fi

cd "$OASYS_HOME"

# --- virtualenv + install the package ---
if [ ! -d venv ]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --quiet --upgrade pip
# Force reinstall so a rollback to an older tree actually takes effect
# in the venv (otherwise the previously installed version can linger).
pip install --quiet --force-reinstall --no-deps .

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

# Report the active release so it is obvious what you are running.
ACTIVE="$(git -C "$OASYS_HOME" describe --tags --always 2>/dev/null || echo unknown)"
echo
echo "==> OASYS installed. Active release: $ACTIVE"
echo "    Run it with:  oasys"
if [ -n "$REF" ]; then
  echo "    Re-run this exact version:  curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/$REF/install.sh | bash"
else
  echo "    Re-run latest:  curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash"
fi
echo "    First run opens the TUI. Set a key anytime with:  /key openrouter <key>"
