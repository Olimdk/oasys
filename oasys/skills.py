"""Discovers and loads SKILL.md files (OASYS-local format).

OASYS is fully self-contained: skills live in oasys/skills/ only.
It does NOT read from ~/.claude (Claude Code) so the assistant has no
dependency on Claude Code being installed.
"""
from pathlib import Path
from dataclasses import dataclass

SKILLS_DIRS = [
    Path(__file__).parent / "skills",
]


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
