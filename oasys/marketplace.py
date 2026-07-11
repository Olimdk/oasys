"""Marketplace: clone GitHub repos of skills/plugins, install by name.

Bundled skills/plugins ship with the package; marketplace installs go into the
user-writable OASYS_HOME/skills and OASYS_HOME/plugins directories so a
read-only package install still supports extensions.

Usage (from the OASYS prompt):
  /plugin marketplace add jeffallan/claude-skills
  /plugin install fullstack-dev-skills@jeffallan-claude-skills
  /plugin list
"""
import subprocess
import shutil
import yaml
from pathlib import Path
from oasys import OASYS_HOME

MARKETPLACES_DIR = OASYS_HOME / "marketplaces"
REGISTRY_FILE = OASYS_HOME / "marketplaces.yaml"
# Install targets are user-writable (no package-dir writes needed).
OASYS_SKILLS_DIR = OASYS_HOME / "skills"
OASYS_PLUGINS_DIR = OASYS_HOME / "plugins"


def _load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return yaml.safe_load(REGISTRY_FILE.read_text()) or {}
    return {}


def _save_registry(reg: dict) -> None:
    OASYS_HOME.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(yaml.dump(reg))


def marketplace_add(repo: str) -> str:
    """repo like 'jeffallan/claude-skills' or a full git URL."""
    if repo.startswith("http") or repo.endswith(".git"):
        url = repo
        alias = repo.rstrip("/").split("/")[-1].replace(".git", "")
        owner = "custom"
    else:
        parts = repo.split("/")
        if len(parts) != 2:
            return f"[ERROR] expected 'owner/repo', got: {repo}"
        owner, name = parts
        url = f"https://github.com/{owner}/{name}.git"
        alias = f"{name}-{owner}"

    MARKETPLACES_DIR.mkdir(parents=True, exist_ok=True)
    dest = MARKETPLACES_DIR / alias

    if dest.exists():
        result = subprocess.run(["git", "-C", str(dest), "pull"], capture_output=True, text=True)
    else:
        result = subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], capture_output=True, text=True)

    if result.returncode != 0:
        return f"[ERROR] git failed: {result.stderr.strip()}"

    reg = _load_registry()
    reg[alias] = {"repo": repo, "url": url, "path": str(dest)}
    _save_registry(reg)
    return f"[OK] marketplace added as '{alias}' ({url})"


def marketplace_list() -> str:
    reg = _load_registry()
    if not reg:
        return "[no marketplaces added yet]"
    return "\n".join(f"{alias} - {info['url']}" for alias, info in reg.items())


def _find_item(marketplace_path: Path, item_name: str) -> Path | None:
    """Search the cloned repo for a folder matching item_name (case-insensitive)."""
    for p in marketplace_path.rglob("*"):
        if p.is_dir() and p.name.lower() == item_name.lower():
            return p
    return None


def install(spec: str) -> str:
    """spec like 'fullstack-dev-skills@jeffallan-claude-skills'."""
    if "@" not in spec:
        return "[ERROR] usage: /plugin install <name>@<marketplace-alias>"
    item_name, alias = spec.split("@", 1)
    reg = _load_registry()
    if alias not in reg:
        return f"[ERROR] unknown marketplace '{alias}'. Run /plugin marketplace list to see options."

    mkt_path = Path(reg[alias]["path"])
    found = _find_item(mkt_path, item_name)
    if not found:
        return f"[ERROR] no folder named '{item_name}' found in '{alias}'"

    skill_md = found / "SKILL.md"
    if skill_md.exists():
        dest = OASYS_SKILLS_DIR / found.name
        OASYS_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(found, dest)
        return f"[OK] installed skill '{found.name}' to {dest}"

    py_files = list(found.glob("*.py"))
    if py_files:
        OASYS_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        for f in py_files:
            shutil.copy(f, OASYS_PLUGINS_DIR / f.name)
        return f"[OK] installed plugin '{found.name}' ({len(py_files)} file(s)) to {OASYS_PLUGINS_DIR}"

    return f"[ERROR] '{found.name}' doesn't look like a skill (no SKILL.md) or plugin (no .py files)"
