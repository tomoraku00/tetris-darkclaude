# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    keywords: list
    content: str


def _parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end == -1:
        return {}, text
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                meta[key] = [v.strip().strip("\"\'") for v in val[1:-1].split(",") if v.strip()]
            else:
                meta[key] = val.strip("\"\'")
    return meta, "\n".join(lines[end + 1:]).strip()


def load_skills(skills_dir=None):
    if skills_dir is None:
        skills_dir = Path.cwd() / ".darkclaude" / "skills"
    skills_dir = Path(skills_dir)
    if not skills_dir.exists():
        return []
    skills = []
    for path in sorted(skills_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8-sig")
            meta, body = _parse_frontmatter(text)
            skills.append(Skill(
                name=meta.get("name", path.stem),
                description=meta.get("description", ""),
                keywords=meta.get("keywords", []),
                content=body,
            ))
        except Exception:
            pass
    return skills


def select_relevant_skills(skills, user_message, max_skills=3):
    msg_lower = user_message.lower()
    scored = []
    for skill in skills:
        score = sum(1 for kw in skill.keywords if kw.lower() in msg_lower)
        if score > 0:
            scored.append((score, skill))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:max_skills]]


def build_skill_context(skills):
    if not skills:
        return ""
    return "\n\n".join(f"## {s.name}\n{s.content}" for s in skills)
