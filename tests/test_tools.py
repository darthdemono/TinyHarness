import pytest

from tinyharness.tools import folder_tools


def make(tmp_path):
    (tmp_path / "a.md").write_text("Residence permit renewal needs a passport.\nOther line\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("Bus tickets cost 450 forint.\n")
    (tmp_path / "img.png").write_bytes(b"\x00")
    return {f.__name__: f for f in folder_tools(str(tmp_path))}


def test_list_read_search(tmp_path):
    t = make(tmp_path)
    assert t["list_files"]().splitlines() == ["a.md", "sub/b.txt"]
    assert "passport" in t["read_file"]("a.md")
    assert t["search_docs"]("residence permit").startswith("a.md:1: Residence permit")
    assert t["search_docs"]("zebra") == "no matches"


def test_read_cannot_escape_folder(tmp_path):
    (tmp_path.parent / "secret.txt").write_text("x")
    t = make(tmp_path)
    with pytest.raises(ValueError):
        t["read_file"]("../secret.txt")


def test_cli_docs_flag_registers_tools(tmp_path, capsys):
    from fake_server import start
    from tinyharness import cli

    make(tmp_path)
    _, url = start(lambda b: {"role": "assistant", "content": str(len(b.get("tools", [])))})
    assert cli.main(["--url", url, "--skills", str(tmp_path / "none"), "--docs", str(tmp_path), "run", "hi"]) == 0
    assert capsys.readouterr().out.strip() == "3"


def test_skips_vendor_dirs_and_search_returns_hits(tmp_path):
    from tinyharness.tools import search

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "x.txt").write_text("permit")
    (tmp_path / "a.md").write_text("one\npermit permit\n")
    assert search(str(tmp_path), "permit") == [(2, "a.md", 2, "permit permit")]


def test_paths_use_forward_slashes_on_every_os(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c.md").write_text("x")
    assert {f.__name__: f for f in folder_tools(str(tmp_path))}["list_files"]() == "a/b/c.md"
