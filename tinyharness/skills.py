"""Load Agent Skill folders: <dir>/<name>/SKILL.md with name and description frontmatter."""
import os
import re


DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")  # shipped with the package


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


def validate(root):
    """Check every skill folder against the Agent Skills spec; return a list of 'dir: problem' strings."""
    bad = []
    for d in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        p = os.path.join(root, d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            meta, body = parse(f.read())
        n, desc = meta.get("name", ""), meta.get("description", "")
        if not 1 <= len(n) <= 64 or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n):
            bad.append("%s: name must be 1-64 lowercase letters, digits and single hyphens" % d)
        if n != d:
            bad.append("%s: name '%s' must match the directory name" % (d, n))
        if not 1 <= len(desc) <= 1024:
            bad.append("%s: description must be 1-1024 characters" % d)
        if not body.strip():
            bad.append("%s: body is empty" % d)
    return bad
