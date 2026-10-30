from hackbase import skills


def test_parse_and_load(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: x\ndescription: does x\n---\nBody\n")
    s = skills.load(str(tmp_path))
    assert s["x"]["description"] == "does x" and s["x"]["body"] == "Body\n"
    assert skills.catalog(s) == "- x: does x"


def test_missing_root_and_no_frontmatter(tmp_path):
    assert skills.load(str(tmp_path / "nope")) == {}
    assert skills.parse("plain") == ({}, "plain")


def test_bundled_skill_loads():
    assert "summarize" in skills.load("skills")


def test_validate_flags_each_spec_rule(tmp_path):
    def mk(d, text):
        (tmp_path / d).mkdir()
        (tmp_path / d / "SKILL.md").write_text(text)

    mk("good", "---\nname: good\ndescription: d\n---\nbody\n")
    mk("Bad_Name", "---\nname: Bad_Name\ndescription: d\n---\nbody\n")
    mk("other", "---\nname: not-other\ndescription:\n---\n\n")
    out = skills.validate(str(tmp_path))
    assert not any(p.startswith("good") for p in out)
    assert any("Bad_Name: name must be" in p for p in out)
    assert any("other: name 'not-other' must match" in p for p in out)
    assert any("other: description" in p for p in out) and any("other: body" in p for p in out)


def test_bundled_skills_pass_validation_and_cli(capsys):
    from hackbase import cli

    assert skills.validate("skills") == []
    assert cli.main(["skills", "--validate"]) == 0 and "valid" in capsys.readouterr().out
