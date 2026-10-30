"""@file skills.py
@brief Load and validate Agent Skills: folders containing a SKILL.md with name and description.

Format (from https://agentskills.io/specification, read 2026-10-30):

- name: 1 to 64 characters, lowercase letters, digits and single hyphens, no leading or trailing hyphen, equal to the folder name.
- description: 1 to 1024 characters saying what the skill does and when to use it.
- Body: free Markdown instructions.

Progressive disclosure: only name and description go into the agent's prompt
(catalog); the body is read on demand through the `use_skill` tool.

The frontmatter parser is intentionally minimal (flat `key: value` lines).
Nested YAML such as `metadata:` maps is not parsed.
"""
import os
import re


DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")  # shipped with the package


def parse(text):
    """@brief Split a SKILL.md into frontmatter fields and body.

    @param text File contents.
    @return `(meta dict, body text)`; `({}, text)` if there is no frontmatter.
    """
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
    """@brief Read every skill folder directly under root.

    @param root Folder containing one subfolder per skill.
    @return Mapping name -> `{description, body, path}`; empty if root does not exist.
    """
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
    """@brief One `- name: description` line per skill, for the system prompt.

    @param skills Mapping from load.
    """
    return "\n".join("- %s: %s" % (n, s["description"]) for n, s in skills.items())


def validate(root):
    """@brief Check skill folders against the specification.

    @param root Folder containing skill folders. Folders without SKILL.md are ignored.
    @return List of `"dir: problem"` strings; empty when everything is valid.
    """
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
