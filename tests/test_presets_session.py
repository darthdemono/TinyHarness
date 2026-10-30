import json

import pytest

from fake_server import start
from hackbase import cli, presets
from hackbase.agent import Agent
from hackbase.client import Client


def test_preset_fills_language_and_rejects_unknown():
    assert "in Hungarian" in presets.get("tutor", "Hungarian")
    with pytest.raises(KeyError):
        presets.get("nope")


def test_agent_save_and_load_keeps_current_system_prompt(tmp_path):
    _, url = start(lambda b: {"role": "assistant", "content": "A"})
    a = Agent(Client(model="m", base_url=url), system="old")
    a.run("Q1")
    a.save(str(tmp_path / "s.json"))
    b = Agent(Client(model="m", base_url=url), system="new")
    b.load(str(tmp_path / "s.json"))
    assert [m["content"] for m in b.messages] == ["new", "Q1", "A"]


def test_cli_session_persists_across_runs_and_preset_is_sent(tmp_path, capsys):
    srv, url = start(lambda b: {"role": "assistant", "content": "ok"})
    f = str(tmp_path / "s.json")
    base = ["--url", url, "--skills", str(tmp_path), "--session", f, "--preset", "coach", "--lang", "German"]
    assert cli.main(base + ["run", "Hallo"]) == 0
    assert cli.main(base + ["run", "Wie geht"]) == 0
    sent = srv.seen[1][1]["messages"]
    assert "German" in sent[0]["content"] and [m["content"] for m in sent[1:]] == ["Hallo", "ok", "Wie geht"]
    assert len(json.load(open(f))) == 5
