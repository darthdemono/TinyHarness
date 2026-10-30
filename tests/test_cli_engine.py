"""The command line around the local engine: doctor, setup, --local, serve, chat and python -m."""
import builtins
import json
import runpy
import sys

import pytest

from fake_server import start
from tinyharness import cli, hw, llamacpp


def test_doctor_reports_machine_and_a_missing_engine(monkeypatch, capsys):
    monkeypatch.setattr(hw, "report", lambda: {"system": "Testix x1"})
    monkeypatch.setattr(llamacpp, "find_server", lambda variant="cpu": None)
    assert cli.main(["doctor"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["system"] == "Testix x1" and "tinyharness setup" in info["llama_server"]


def test_setup_installs_the_requested_variant_and_prints_the_binary_path(monkeypatch, capsys):
    got = []
    monkeypatch.setattr(llamacpp, "install", lambda variant="cpu", log=print: got.append(variant) or "/x/llama-server")
    assert cli.main(["setup", "--variant", "vulkan"]) == 0
    assert got == ["vulkan"] and capsys.readouterr().out.strip() == "/x/llama-server"


class FakeEngine:
    """Stands in for llamacpp.Server: records its settings and points the client at a fake model server."""
    made = []

    def __init__(self, spec, **kw):
        self.spec, self.kw = spec, kw
        FakeEngine.made.append(self)
        _, self.url = start(lambda b: {"role": "assistant", "content": "engine says hi"})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stopped = True


@pytest.fixture
def engine(monkeypatch):
    FakeEngine.made = []
    monkeypatch.setattr(llamacpp, "Server", FakeEngine)
    return FakeEngine


def test_local_uses_the_given_model_and_talks_to_the_engine(engine, tmp_path, capsys):
    argv = ["--local", "org/m-GGUF:Q4_0", "--gpu", "--offline", "--ctx", "2048", "--threads", "3", "--skills", str(tmp_path), "run", "hi"]
    assert cli.main(argv) == 0
    e = engine.made[0]
    assert e.spec == "org/m-GGUF:Q4_0" and e.kw == {"ctx": 2048, "threads": 3, "gpu": True, "offline": True}
    assert "engine says hi" in capsys.readouterr().out and e.stopped


def test_local_auto_picks_the_model_that_fits_this_machine(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(hw, "ram_gb", lambda: 2.0)
    cli.main(["--local", "--skills", str(tmp_path), "run", "hi"])
    assert engine.made[0].spec == hw.TIERS[0][1]


def test_local_trims_history_to_the_context_size(engine, tmp_path):
    seen = {}
    real = cli.Agent

    def spy(*a, **kw):
        seen.update(kw)
        return real(*a, **kw)

    cli.Agent = spy
    try:
        cli.main(["--local", "x", "--ctx", "1000", "--skills", str(tmp_path), "run", "hi"])
    finally:
        cli.Agent = real
    assert seen["max_chars"] == 2500


def test_serve_prints_the_address_and_serves_until_stopped(monkeypatch, capsys, tmp_path):
    class Stub:
        def serve_forever(self):
            Stub.ran = True

    monkeypatch.setattr(cli, "make_server", lambda build, port: Stub())
    assert cli.main(["--skills", str(tmp_path), "serve", "--port", "1234"]) == 0
    assert Stub.ran and capsys.readouterr().out.strip() == "http://127.0.0.1:1234"


def test_chat_answers_each_line_saves_the_session_and_ends_on_eof(monkeypatch, capsys, tmp_path):
    _, url = start(lambda b: {"role": "assistant", "content": "pong"})
    lines = iter(["ping", "ping again"])

    def fake_input(prompt):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr(builtins, "input", fake_input)
    session = tmp_path / "s.json"
    assert cli.main(["--url", url, "--skills", str(tmp_path), "--session", str(session), "chat"]) == 0
    assert capsys.readouterr().out.count("pong") == 2
    assert [m["content"] for m in json.loads(session.read_text())] == ["ping", "pong", "ping again", "pong"]


@pytest.mark.filterwarnings("ignore:.*found in sys.modules:RuntimeWarning")
def test_python_dash_m_runs_the_command_line(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tinyharness", "skills"])
    with pytest.raises(SystemExit) as e:
        runpy.run_module("tinyharness.cli", run_name="__main__")
    assert e.value.code == 0 and "summarize" in capsys.readouterr().out


def test_chat_without_a_session_file_ends_cleanly_on_ctrl_c(monkeypatch, capsys, tmp_path):
    _, url = start(lambda b: {"role": "assistant", "content": "pong"})
    lines = iter(["ping"])

    def fake_input(prompt):
        try:
            return next(lines)
        except StopIteration:
            raise KeyboardInterrupt from None

    monkeypatch.setattr(builtins, "input", fake_input)
    assert cli.main(["--url", url, "--skills", str(tmp_path), "chat"]) == 0
    assert "pong" in capsys.readouterr().out
