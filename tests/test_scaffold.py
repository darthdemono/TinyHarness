"""`tinyharness new`: the project template that makes TinyHarness a dependency of the event project."""
import datetime
import os
import re
import subprocess
import sys
import tomllib

import pytest

from tinyharness import cli, scaffold

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_slug_makes_a_valid_package_name_and_rejects_empty_names():
    assert scaffold.slug("My Cool_App!") == "my-cool-app"
    with pytest.raises(ValueError, match="letter or digit"):
        scaffold.slug("!!!")


def test_default_author_uses_git_config_and_falls_back(monkeypatch):
    class Out:
        stdout = "Ada Lovelace\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Out())
    assert scaffold.default_author() == "Ada Lovelace"
    Out.stdout = "\n"
    assert scaffold.default_author() == "the project authors"

    def broken(*a, **k):
        raise OSError("no git")

    monkeypatch.setattr(subprocess, "run", broken)
    assert scaffold.default_author() == "the project authors"


def test_create_writes_every_file_filled_in_and_initialises_git(tmp_path):
    dest = scaffold.create("Event Thing", parent=str(tmp_path), author="Ada")
    for _, rel in scaffold.FILES:
        assert os.path.isfile(os.path.join(dest, rel)), rel
        text = open(os.path.join(dest, rel), encoding="utf-8").read()
        assert not re.search(r"@(NAME|SLUG|YEAR|AUTHOR)@", text), rel
    assert "Copyright" in open(os.path.join(dest, "NOTICE")).read() and "Ada" in open(os.path.join(dest, "NOTICE")).read()
    assert os.path.isdir(os.path.join(dest, ".git"))
    meta = tomllib.loads(open(os.path.join(dest, "pyproject.toml")).read())
    assert meta["project"]["name"] == "event-thing" and meta["project"]["dependencies"][0].startswith("tinyharness @ git+https://github.com/")
    assert meta["project"]["license"] == "Apache-2.0"


def test_licence_text_matches_the_one_in_this_repository_except_the_copyright_line(tmp_path):
    dest = scaffold.create("p", parent=str(tmp_path), author="Ada Lovelace", git=False)
    made = open(os.path.join(dest, "LICENSE")).read()
    ours = open(os.path.join(ROOT, "LICENSE")).read()
    line = re.compile(r"^   Copyright \d{4} .*$", re.MULTILINE)
    assert len(line.findall(made)) == 1 and "Copyright %d Ada Lovelace" % datetime.date.today().year in made
    assert line.sub("", made) == line.sub("", ours)
    assert "Local working files" in open(os.path.join(dest, ".gitignore")).read()


def test_this_repository_licence_names_the_owner_and_year():
    assert "Copyright 2026 Jubair Hasan" in open(os.path.join(ROOT, "LICENSE")).read()
    assert "[yyyy]" not in open(os.path.join(ROOT, "LICENSE")).read()


def test_git_is_skipped_on_request_or_when_not_installed(tmp_path, monkeypatch):
    assert not os.path.exists(os.path.join(scaffold.create("a", parent=str(tmp_path), author="A", git=False), ".git"))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert not os.path.exists(os.path.join(scaffold.create("b", parent=str(tmp_path), author="A"), ".git"))


def test_an_existing_folder_is_never_overwritten(tmp_path):
    (tmp_path / "taken").mkdir()
    with pytest.raises(FileExistsError):
        scaffold.create("taken", parent=str(tmp_path), author="A")


def test_the_generated_project_passes_its_own_tests(tmp_path):
    dest = scaffold.create("demo", parent=str(tmp_path), author="A", git=False)
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=dest, capture_output=True, text=True)
    assert run.returncode == 0 and "1 passed" in run.stdout, run.stdout + run.stderr


def test_the_new_command_creates_the_project_and_says_what_to_do_next(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["new", "hack", "--author", "Ada", "--no-git"]) == 0
    out = capsys.readouterr().out
    assert "created" in out and "python app.py serve" in out and os.path.isfile(tmp_path / "hack" / "app.py")
