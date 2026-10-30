import json
import threading
import urllib.request

from fake_server import start
from hackbase import cli
from hackbase.agent import Agent
from hackbase.client import Client
from hackbase.web import make_server


def test_web_chat_roundtrip():
    srv, url = start(lambda b: {"role": "assistant", "content": "pong"})
    web = make_server(lambda: Agent(Client(model="m", base_url=url)), port=0)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % web.server_port
    assert b"hackbase" in urllib.request.urlopen(base + "/").read()
    req = urllib.request.Request(base + "/chat", data=json.dumps({"message": "ping"}).encode())
    lines = [json.loads(x) for x in urllib.request.urlopen(req).read().decode().splitlines()]
    assert "".join(x["t"] for x in lines) == "pong"
    web.shutdown()


def test_cli_run_and_skills(capsys):
    srv, url = start(lambda b: {"role": "assistant", "content": "yo"})
    assert cli.main(["--url", url, "run", "hi"]) == 0
    assert "yo" in capsys.readouterr().out
    assert cli.main(["skills"]) == 0
    assert "summarize" in capsys.readouterr().out


def test_web_sessions_are_separate():
    seen = []

    def reply(b):
        seen.append(len(b["messages"]))
        return {"role": "assistant", "content": "r"}

    _, url = start(reply)
    web = make_server(lambda: Agent(Client(model="m", base_url=url)), port=0)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/chat" % web.server_port

    def post(sid):
        req = urllib.request.Request(base, data=json.dumps({"sid": sid, "message": "x"}).encode())
        return urllib.request.urlopen(req).read()

    post("a")
    post("a")
    post("b")
    assert seen == [1, 3, 1]
    web.shutdown()


def test_web_reports_backend_failure_as_error_line():
    web = make_server(lambda: Agent(Client(model="m", base_url="http://127.0.0.1:1")), port=0)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    req = urllib.request.Request("http://127.0.0.1:%d/chat" % web.server_port, data=json.dumps({"message": "x"}).encode())
    line = json.loads(urllib.request.urlopen(req).read().decode().splitlines()[0])
    assert "error" in line
    web.shutdown()
