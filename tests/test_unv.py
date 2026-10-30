import os
import stat
import sys

import pytest

from fake_server import start
from tinyharness import cli

pytestmark = pytest.mark.skipif(os.name == "nt", reason="the stand-in unv is a shell-style script")

FAKE_UNV = """#!{py}
import os, sys
a = sys.argv[1:]
assert a[0] == "exec"
env = dict(os.environ)
i = 1
log = []
while a[i] != "--":
    flag, spec = a[i], a[i + 1]
    log.append(flag + " " + spec)
    var = spec.split("=", 1)[1].split(":")[0]
    env[var] = "SECRET-VALUE-123"
    i += 2
open(os.environ["UNV_LOG"], "w").write("\\n".join(log))
os.execvpe(a[i + 1], a[i + 1:], env)
"""


@pytest.fixture
def fake_unv(tmp_path, monkeypatch):
    exe = tmp_path / "unv"
    exe.write_text(FAKE_UNV.format(py=sys.executable))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("UNV_LOG", str(tmp_path / "log.txt"))
    return tmp_path / "log.txt"


def test_strip_flags_handles_both_forms():
    argv = ["--unv", "Groq", "--unv=Other", "--local", "run", "hi", "--unv-pool", "p"]
    assert cli.strip_flags(argv, ("--unv", "--unv-pool")) == ["--local", "run", "hi"]


def test_key_reaches_the_server_as_a_bearer_token_and_never_in_argv(fake_unv, tmp_path, capsys):
    srv, url = start(lambda b: {"role": "assistant", "content": "ok"})
    # the fake server records bodies only; capture the header through a patched handler class
    seen = []
    orig = srv.RequestHandlerClass.do_POST

    def spy(self):
        seen.append(self.headers.get("Authorization"))
        orig(self)

    srv.RequestHandlerClass.do_POST = spy
    code = cli.main(["--backend", "openai", "--url", url, "--skills", str(tmp_path), "--unv", "Groq", "run", "hi"])
    assert code == 0 and seen == ["Bearer SECRET-VALUE-123"]
    assert fake_unv.read_text() == "--entry Groq=TINYHARNESS_API_KEY:key"
    assert "SECRET-VALUE" not in capsys.readouterr().out


def test_explicit_mapping_and_pool_are_passed_through(fake_unv, tmp_path):
    _, url = start(lambda b: {"role": "assistant", "content": "ok"})
    cli.main(["--url", url, "--skills", str(tmp_path), "--unv", "Hugging Face=HF_TOKEN:key", "--unv-pool", "free", "run", "hi"])
    assert fake_unv.read_text().splitlines() == ["--entry Hugging Face=HF_TOKEN:key", "--pool free=TINYHARNESS_API_KEY"]


def test_missing_unv_command_is_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(SystemExit, match="unv command"):
        cli.main(["--unv", "Groq", "run", "hi"])
