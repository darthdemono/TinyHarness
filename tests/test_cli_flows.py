import json

from fake_server import start
from hackbase import cli


def test_extract_csv_from_image(tmp_path, capsys):
    img = tmp_path / "r.jpg"
    img.write_bytes(b"ABC")
    srv, url = start(lambda b: {"role": "assistant", "content": '[{"item": "tea", "price": 2.5}]'})
    args = ["--url", url, "extract", "--fields", "item:str,price:float", "--many", "--csv", "-i", str(img)]
    assert cli.main(args) == 0
    assert capsys.readouterr().out == "item,price\ntea,2.5\n"
    assert srv.seen[0][1]["messages"][-1]["images"] == ["QUJD"]


def test_extract_single_json(capsys):
    _, url = start(lambda b: {"role": "assistant", "content": '{"n": 3}'})
    assert cli.main(["--url", url, "extract", "--fields", "n:int"]) == 0
    assert json.loads(capsys.readouterr().out) == {"n": 3}


def test_digest_and_ask(tmp_path, capsys):
    (tmp_path / "t.txt").write_text("Photosynthesis makes sugar.\n")
    _, url = start(lambda b: {"role": "assistant", "content": "answer"})
    assert cli.main(["--url", url, "digest", str(tmp_path / "t.txt")]) == 0
    assert capsys.readouterr().out.strip() == "answer"
    assert cli.main(["--url", url, "ask", str(tmp_path), "what is photosynthesis"]) == 0
    assert capsys.readouterr().out.strip().endswith("Sources: t.txt:1")
    assert cli.main(["--url", url, "ask", str(tmp_path), "zebra"]) == 0
    assert "not covered" in capsys.readouterr().out
