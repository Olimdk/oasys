"""Discovers and loads SKILL.md files (OASYS-local format).

Skills ship bundled inside the package AND can be installed by the user into
the OASYS_HOME/skills directory (so a read-only package install still works).
"""
from pathlib import Path
from dataclasses import dataclass
from oasys import OASYS_HOME

BUNDLED_SKILLS = Path(__file__).parent / "skills"
USER_SKILLS = OASYS_HOME / "skills"
SKILLS_DIRS = [BUNDLED_SKILLS, USER_SKILLS]


@dataclass
class Skill:
    name: str
    description: str
    path: Path
    content: str


def discover_skills() -> list[Skill]:
    found = []
    for base in SKILLS_DIRS:
        if not base.exists():
            continue
        for skill_dir in base.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                text = skill_md.read_text(errors="ignore")
                name = skill_dir.name
                desc = ""
                for line in text.splitlines():
                    if line.lower().startswith("description"):
                        desc = line.split(":", 1)[-1].strip()
                        break
                found.append(Skill(name=name, description=desc, path=skill_dir, content=text))
    return found


def skills_system_prompt(skills: list[Skill]) -> str:
    if not skills:
        return ""
    lines = ["Available skills (read the referenced SKILL.md before using one):"]
    for s in skills:
        lines.append(f"- {s.name}: {s.description} ({s.path})")
    return "\n".join(lines)
