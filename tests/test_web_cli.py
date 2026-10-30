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
    web = make_server(Agent(Client(model="m", base_url=url)), port=0)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % web.server_port
    assert b"hackbase" in urllib.request.urlopen(base + "/").read()
    req = urllib.request.Request(base + "/chat", data=json.dumps({"message": "ping"}).encode())
    assert json.load(urllib.request.urlopen(req))["reply"] == "pong"
    web.shutdown()


def test_cli_run_and_skills(capsys):
    srv, url = start(lambda b: {"role": "assistant", "content": "yo"})
    assert cli.main(["--url", url, "run", "hi"]) == 0
    assert "yo" in capsys.readouterr().out
    assert cli.main(["skills"]) == 0
    assert "summarize" in capsys.readouterr().out
