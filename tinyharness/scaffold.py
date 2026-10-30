"""@file scaffold.py
@brief Start a new project that depends on TinyHarness: `tinyharness new NAME`.

The intended way to use TinyHarness at an event is as a dependency. The event
project lives in its own repository with its own idea, code, tests and history,
and imports `tinyharness` like any other library. This module writes that
repository in one second: licence, notice, ignore file, a working `app.py`
(assistant plus web page), a test, a CI workflow, a README that has the model
and licence sections the event asks for, and a submission checklist.

Templates are plain text files in `tinyharness/templates/project/` ending in
`.tmpl`; the suffix keeps test runners and linters from treating them as code.
Placeholders look like `@NAME@` so Python and TOML braces need no escaping.
"""
import datetime
import os
import re
import shutil
import subprocess

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "project")

## Template file -> path inside the new project.
FILES = [
    ("README.md.tmpl", "README.md"),
    ("SUBMISSION.md.tmpl", "SUBMISSION.md"),
    ("pyproject.toml.tmpl", "pyproject.toml"),
    ("app.py.tmpl", "app.py"),
    ("test_app.py.tmpl", "tests/test_app.py"),
    ("gitignore.tmpl", ".gitignore"),
    ("check.yml.tmpl", ".github/workflows/check.yml"),
    ("LICENSE.tmpl", "LICENSE"),
    ("NOTICE.tmpl", "NOTICE"),
]


def slug(name):
    """@brief Turn a project name into a valid package name (lowercase, hyphens).

    @param name Project name as typed.
    @return The slug.
    @throws ValueError If nothing usable is left.
    """
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not s:
        raise ValueError("the project name needs at least one letter or digit")
    return s


def default_author():
    """@brief The author for the notice: `git config user.name`, else a neutral phrase.

    @return Name text.
    """
    try:
        out = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        out = ""
    return out or "the project authors"


def create(name, parent=".", author=None, git=True):
    """@brief Write a new project folder.

    Nothing is overwritten: an existing folder is an error. If `git` is true and git is installed,
    the folder is initialised with `git init -b main` (no commit is made).

    @param name Project name; the folder is named exactly this.
    @param parent Folder to create it in.
    @param author Name for the notice and package metadata; defaults to default_author().
    @param git Whether to run `git init`.
    @return Path of the new folder.
    @throws ValueError For an unusable name.
    @throws FileExistsError If the folder already exists.
    """
    values = {"@NAME@": name, "@SLUG@": slug(name), "@YEAR@": str(datetime.date.today().year), "@AUTHOR@": author or default_author()}
    dest = os.path.join(parent, name)
    if os.path.exists(dest):
        raise FileExistsError(dest)
    for src, rel in FILES:
        with open(os.path.join(TEMPLATES, src), encoding="utf-8") as f:
            text = f.read()
        for key, val in values.items():
            text = text.replace(key, val)
        out = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    if git and shutil.which("git"):
        subprocess.run(["git", "init", "-b", "main", "-q", dest], check=True)
    return dest
