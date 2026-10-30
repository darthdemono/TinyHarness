"""Load Agent Skill folders: <dir>/<name>/SKILL.md with name and description frontmatter."""
import os


def parse(text):
    """Return (meta dict, body). Frontmatter is flat 'key: value' lines between --- fences."""
    if not text.startswith("---"):
        return {}, text
    head, _, body = text[3:].partition("\n---")
    meta = {}
    for line in head.strip().splitlines():
        k, _, v = line.partition(":")
        if v:
            meta[k.strip()] = v.strip().strip("\"'")
    return meta, body.lstrip("\n")


def load(root):
    """Map skill name -> {'description','body','path'} for every SKILL.md directly under root."""
    skills = {}
    if not os.path.isdir(root):
        return skills
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "SKILL.md")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                meta, body = parse(f.read())
            skills[meta.get("name", d)] = {
                "description": meta.get("description", ""),
                "body": body,
                "path": p,
            }
    return skills


def catalog(skills):
    """One line per skill for the system prompt."""
    return "\n".join("- %s: %s" % (n, s["description"]) for n, s in skills.items())
