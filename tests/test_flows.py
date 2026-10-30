from fake_server import start
from hackbase.client import Client
from hackbase.flows import REFUSAL, chunks, digest, grounded


def test_chunks_respect_size_and_cut_long_lines():
    got = chunks("aa\nbb\ncc\n" + "x" * 25, size=8)
    assert all(len(c) <= 9 for c in got) and "".join(got).replace("\n", "") == "aabbcc" + "x" * 25


def test_digest_maps_then_reduces():
    calls = []

    def reply(b):
        calls.append(b["messages"][-1]["content"])
        return {"role": "assistant", "content": "S%d" % len(calls)}

    _, url = start(reply)
    out = digest(Client(model="m", base_url=url), "l1\nl2\nl3\nl4\n", size=6)
    assert out.startswith("S") and len(calls) == 3
    assert any("Combine" in c for c in calls)


def test_digest_single_chunk_is_one_call_and_empty_is_empty():
    srv, url = start(lambda b: {"role": "assistant", "content": "ok"})
    c = Client(model="m", base_url=url)
    assert digest(c, "short") == "ok" and len(srv.seen) == 1
    assert digest(c, "") == ""


def test_grounded_cites_and_refuses_without_calling_model(tmp_path):
    (tmp_path / "book.md").write_text("intro\nPhotosynthesis makes sugar from light.\nend\n")
    srv, url = start(lambda b: {"role": "assistant", "content": "Sugar [book.md:2]"})
    c = Client(model="m", base_url=url)
    ans, srcs = grounded(c, "what does photosynthesis make", str(tmp_path))
    assert srcs == ["book.md:2"] and "Photosynthesis makes sugar" in srv.seen[0][1]["messages"][-1]["content"]
    n = len(srv.seen)
    assert grounded(c, "quantum gravity", str(tmp_path)) == (REFUSAL, []) and len(srv.seen) == n
