"""Behaviour at the edges: bad model output, odd wire formats, limits and failure paths."""
import io
import json
import threading
import urllib.error
import urllib.request

import pytest

from fake_server import start, start_raw
from tinyharness import extras, flows, redteam, skills, structured, web
from tinyharness.agent import Agent
from tinyharness.client import Client


# --- agent -----------------------------------------------------------------

def test_agent_gives_up_after_max_steps_when_the_model_never_stops_calling_tools():
    _, url = start(lambda b: {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "t", "arguments": {}}}]})
    a = Agent(Client(model="m", base_url=url), max_steps=2)
    a.tool(lambda: "r")
    a.tools["t"] = a.tools.pop("<lambda>")
    assert a.run("go") == "stopped after 2 steps"


# --- client streaming wire format -----------------------------------------

def test_openai_stream_ignores_blank_lines_comments_and_stops_at_done():
    body = ": keepalive\n\ndata: " + json.dumps({"choices": [{"delta": {"content": "hi"}}]}) + "\n\ndata: [DONE]\ndata: ignored\n"
    _, url = start_raw(body)
    got = []
    msg = Client(model="m", backend="openai", base_url=url).chat([{"role": "user", "content": "x"}], on_token=got.append)
    assert got == ["hi"] and msg == {"role": "assistant", "content": "hi"}


def test_ollama_stream_skips_blank_lines():
    body = json.dumps({"message": {"content": "a"}}) + "\n\n" + json.dumps({"message": {"content": "b"}, "done": True}) + "\n"
    _, url = start_raw(body)
    msg = Client(model="m", backend="ollama", base_url=url).chat([{"role": "user", "content": "x"}], on_token=lambda t: None)
    assert msg["content"] == "ab"


def test_streaming_sends_the_bearer_key():
    srv, url = start_raw("data: [DONE]\n")
    Client(model="m", backend="openai", base_url=url, api_key="K").chat([{"role": "user", "content": "x"}], on_token=lambda t: None)
    assert srv.seen[0][1]["Authorization"] == "Bearer K"


# --- flows -----------------------------------------------------------------

def test_digest_stops_reducing_when_notes_do_not_shrink_and_still_answers():
    calls = []

    def reply(body):
        calls.append(body["messages"][-1]["content"])
        return {"role": "assistant", "content": "LONG-NOTE-%d" % len(calls)}

    _, url = start(reply)
    out = flows.digest(Client(model="m", base_url=url), "aaaa\nbbbb\ncccc\n", size=5)
    assert out == "LONG-NOTE-%d" % len(calls)
    assert calls[-1].startswith("Combine into one final answer.") and len(calls) == 4


# --- redteam ---------------------------------------------------------------

def test_a_crashing_agent_is_recorded_not_fatal():
    def broken(canary):
        raise RuntimeError("model offline")

    res = redteam.run(broken, redteam.PAYLOADS[:2])
    assert [r[1] for r in res] == [False, False] and res[0][2] == "error: model offline"


# --- skills ----------------------------------------------------------------

def test_validate_ignores_folders_without_a_skill_file(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "file.txt").write_text("x")
    assert skills.validate(str(tmp_path)) == [] and skills.validate(str(tmp_path / "missing")) == []


# --- structured ------------------------------------------------------------

def test_find_json_skips_a_broken_brace_and_finds_the_next_object():
    assert structured.find_json('{oops} then {"a": 1}') == {"a": 1}


def test_single_object_answer_must_be_an_object():
    with pytest.raises(ValueError, match="expected a JSON object, got list"):
        structured.check([1], {"a": "int"})


def test_many_rows_rejects_a_lone_object():
    _, url = start(lambda b: {"role": "assistant", "content": '{"a": 1}'})
    with pytest.raises(ValueError, match="expected a JSON array"):
        structured.ask_json(Client(model="m", base_url=url), "p", {"a": "int"}, many=True, retries=0)


# --- web -------------------------------------------------------------------

def _serve(factory):
    srv = web.make_server(factory, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_port


def test_web_unknown_paths_are_404():
    _, url = start(lambda b: {"role": "assistant", "content": "x"})
    srv, base = _serve(lambda: Agent(Client(model="m", base_url=url)))
    for method_path in ("/nope",):
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(base + method_path)
        assert e.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(urllib.request.Request(base + "/other", data=b"{}"))
    assert e.value.code == 404
    srv.shutdown()


def test_web_evicts_the_oldest_conversation_past_the_limit(monkeypatch):
    monkeypatch.setattr(web, "MAX_SESSIONS", 2)
    made = []
    _, url = start(lambda b: {"role": "assistant", "content": "x"})

    def factory():
        made.append(1)
        return Agent(Client(model="m", base_url=url))

    srv, base = _serve(factory)

    def post(sid):
        urllib.request.urlopen(urllib.request.Request(base + "/chat", data=json.dumps({"sid": sid, "message": "q"}).encode())).read()

    for sid in ("a", "b", "c", "a"):  # c evicts a, so the second a starts a fresh conversation
        post(sid)
    assert len(made) == 4
    srv.shutdown()


# --- extras ----------------------------------------------------------------

def test_fetch_url_returns_plain_text_untouched():
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"<b>raw</b> text")

        def log_message(self, *a):
            pass

    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    assert extras.fetch_url("http://127.0.0.1:%d/" % s.server_port) == "<b>raw</b> text"
    s.shutdown()


def test_stdout_without_reconfigure_still_works(monkeypatch):
    from tinyharness import cli

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    assert cli.main(["skills"]) == 0 and "summarize" in buf.getvalue()


def test_digest_reduces_in_rounds_until_one_note_remains():
    calls = []

    def reply(body):
        calls.append(body["messages"][-1]["content"])
        return {"role": "assistant", "content": "A"}

    _, url = start(reply)
    out = flows.digest(Client(model="m", base_url=url), "l1\nl2\nl3\nl4\nl5\nl6\nl7\nl8\n", size=6)
    assert out == "A" and len(calls) == 7
    assert calls[4].startswith("Combine these notes.") and calls[6].startswith("Combine these notes.")
