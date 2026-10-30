import importlib.util
import os

from fake_server import start
from hackbase.client import Client


def load(name):
    path = os.path.join(os.path.dirname(__file__), "..", "examples", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_alt_text_sends_the_image(tmp_path):
    img = tmp_path / "p.jpg"
    img.write_bytes(b"ABC")
    srv, url = start(lambda b: {"role": "assistant", "content": "a cat"})
    assert load("alt_text").describe(str(img), Client(model="m", base_url=url)) == "a cat"
    assert srv.seen[0][1]["messages"][-1]["images"] == ["QUJD"]


def test_letter_explainer_exposes_folder_tools(tmp_path):
    (tmp_path / "rules.md").write_text("Permit renewal: 30 days before expiry.\n")
    letter = tmp_path / "letter.txt"
    letter.write_text("Your permit expires soon.")
    srv, url = start(lambda b: {"role": "assistant", "content": "plain"})
    out = load("letter_explainer").explain(str(letter), str(tmp_path), Client(model="m", base_url=url))
    assert out == "plain"
    names = [t["function"]["name"] for t in srv.seen[0][1]["tools"]]
    assert names == ["list_files", "read_file", "search_docs"]
