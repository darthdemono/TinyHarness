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
