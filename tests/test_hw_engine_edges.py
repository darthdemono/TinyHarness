"""Hardware probe and llama.cpp manager: other operating systems, failures and the full install flow."""
import ctypes
import io
import json
import os
import subprocess
import tarfile
import types
import urllib.request
import zipfile

import pytest

from tinyharness import hw, llamacpp


# --- hw --------------------------------------------------------------------

def test_ram_on_macos_comes_from_sysctl(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr(subprocess, "check_output", lambda cmd, text: str(8 * 2**30))
    assert hw.ram_gb() == 8.0


def test_ram_on_windows_comes_from_the_memory_status_call(monkeypatch):
    def status(ref):
        ref._obj.total = 4 * 2**30

    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(ctypes, "windll", types.SimpleNamespace(kernel32=types.SimpleNamespace(GlobalMemoryStatusEx=status)), raising=False)
    assert hw.ram_gb() == 4.0


def test_ram_is_unknown_when_the_system_gives_no_answer(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")  # no windll on this machine, or no API on a stripped one
    monkeypatch.delattr(ctypes, "windll", raising=False)
    assert hw.ram_gb() is None
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(OSError("no /proc")))
    assert hw.ram_gb() is None


def test_a_machine_beyond_every_tier_gets_the_largest_model():
    assert hw.recommend(10**7) == (hw.TIERS[-1][1], hw.TIERS[-1][2])


# --- llamacpp helpers ------------------------------------------------------

class Resp(io.BytesIO):
    pass


def test_github_token_is_sent_to_the_github_api_only(monkeypatch):
    sent = []
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: sent.append(req) or Resp(b""))
    monkeypatch.setenv("GITHUB_TOKEN", "T0K")
    llamacpp._get("https://api.github.com/x")
    llamacpp._get("https://example.com/asset")
    assert sent[0].get_header("Authorization") == "Bearer T0K" and sent[1].get_header("Authorization") is None


def test_safe_extract_unpacks_a_valid_zip(tmp_path):
    z = tmp_path / "a.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("dir/llama-server.exe", "x")
    llamacpp.safe_extract(str(z), str(tmp_path / "out"))
    assert (tmp_path / "out" / "dir" / "llama-server.exe").read_text() == "x"


def test_lookup_without_an_install_finds_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    monkeypatch.delenv("TINYHARNESS_LLAMA_SERVER", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert llamacpp.find_binary(str(tmp_path)) is None
    assert llamacpp.installed() is None
    (tmp_path / "llama.cpp" / "b1-cpu").mkdir(parents=True)  # an install folder that holds no binary
    assert llamacpp.installed() is None and llamacpp.find_server("cpu") is None


def test_path_binary_serves_the_cpu_variant_only(tmp_path, monkeypatch):
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    monkeypatch.delenv("TINYHARNESS_LLAMA_SERVER", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/llama-server")
    assert llamacpp.find_server("cpu") == "/usr/bin/llama-server" and llamacpp.find_server("vulkan") is None


def test_command_can_turn_off_kv_cache_quantisation():
    assert "-ctk" not in llamacpp.command("srv", "x/y", 1, kv=None)


# --- install flow ----------------------------------------------------------

def _archive(tmp_path, with_binary=True):
    name = "llama-b9-bin-ubuntu-x64.tar.gz"
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / (llamacpp.EXE if with_binary else "readme.txt")).write_text("bin")
    path = tmp_path / name
    with tarfile.open(path, "w:gz") as f:
        f.add(src / (llamacpp.EXE if with_binary else "readme.txt"), arcname="llama-b9/" + (llamacpp.EXE if with_binary else "readme.txt"))
    return name, path.read_bytes()


@pytest.fixture
def release(tmp_path, monkeypatch):
    """A fake GitHub release; returns a function to build the asset and a download counter."""
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    monkeypatch.setattr(llamacpp, "platform_key", lambda: ("linux", "x64"))
    state = {"downloads": 0}

    def setup(with_binary=True, digest="auto"):
        name, data = _archive(tmp_path, with_binary)
        import hashlib

        asset = {"name": name, "size": len(data), "browser_download_url": "https://dl/" + name,
                 "digest": "sha256:" + hashlib.sha256(data).hexdigest() if digest == "auto" else digest}
        releases = json.dumps([{"tag_name": "b9", "assets": [asset]}]).encode()

        def fake_get(url):
            if url == llamacpp.RELEASES:
                return Resp(releases)
            state["downloads"] += 1
            return Resp(data)

        monkeypatch.setattr(llamacpp, "_get", fake_get)

    return setup, state


def test_install_downloads_verifies_unpacks_and_reuses_the_install(release):
    setup, state = release
    setup()
    logs = []
    exe = llamacpp.install(log=logs.append)
    assert exe.endswith(llamacpp.EXE) and os.path.isfile(exe) and "downloading llama-b9" in logs[0]
    if os.name != "nt":
        assert os.stat(exe).st_mode & 0o111
    assert llamacpp.install(log=logs.append) == exe and state["downloads"] == 1 and len(logs) == 1


def test_install_rejects_a_download_that_does_not_match_its_checksum(release):
    setup, _ = release
    setup(digest="sha256:" + "0" * 64)
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        llamacpp.install(log=lambda m: None)


def test_install_accepts_a_release_with_no_published_checksum(release):
    setup, _ = release
    setup(digest="")
    assert llamacpp.install(log=lambda m: None).endswith(llamacpp.EXE)


def test_install_fails_clearly_when_the_archive_holds_no_server(release):
    setup, _ = release
    setup(with_binary=False)
    with pytest.raises(RuntimeError, match="llama-server not found"):
        llamacpp.install(log=lambda m: None)


# --- Server ----------------------------------------------------------------

def test_server_without_a_log_has_an_empty_tail_and_stop_before_start_is_harmless(tmp_path, monkeypatch):
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    s = llamacpp.Server("x/y", binary="srv", log=lambda m: None)
    assert s._tail() == ""
    s.stop()


def test_server_that_never_gets_healthy_is_stopped_and_reported(tmp_path, monkeypatch):
    import sys

    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    s = llamacpp.Server("x/y", binary=sys.executable, log=lambda m: None, timeout=1)
    s.cmd = [sys.executable, "-c", "import time; print('loading...', flush=True); time.sleep(60)"]
    with pytest.raises(RuntimeError, match="not ready after 1s"):
        s.start()
    assert s.proc.poll() is not None


def test_stop_kills_a_server_that_ignores_the_polite_request(tmp_path, monkeypatch):
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    s = llamacpp.Server("x/y", binary="srv", log=lambda m: None)
    events = []

    class Stubborn:
        def poll(self):
            return None

        def terminate(self):
            events.append("terminate")

        def wait(self, timeout=None):
            events.append("wait")
            if events.count("wait") == 1:
                raise subprocess.TimeoutExpired("srv", timeout)

        def kill(self):
            events.append("kill")

    s.proc = Stubborn()
    s.stop()
    assert events == ["terminate", "wait", "kill", "wait"]


def test_make_executable_sets_the_bit_on_unix_and_leaves_windows_alone(tmp_path, monkeypatch):
    f = tmp_path / "srv"
    f.write_text("x")
    f.chmod(0o600)
    if os.name != "nt":
        llamacpp.make_executable(str(f))
        assert os.stat(f).st_mode & 0o111
    monkeypatch.setattr(os, "name", "nt")
    llamacpp.make_executable(str(tmp_path / "does-not-exist"))  # would raise if it tried to chmod


def test_only_an_http_200_health_answer_means_ready(tmp_path, monkeypatch):
    import sys

    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    script = tmp_path / "fake.py"
    script.write_text(
        "import sys\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "port = int(sys.argv[sys.argv.index('--port') + 1])\nn = [0]\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n        n[0] += 1\n        self.send_response(204 if n[0] < 3 else 200); self.end_headers()\n"
        "    def log_message(self, *a): pass\n"
        "HTTPServer(('127.0.0.1', port), H).serve_forever()\n"
    )
    s = llamacpp.Server("x/y", binary=sys.executable, log=lambda m: None, timeout=30)
    s.cmd = [sys.executable, str(script)] + s.cmd[1:]
    with s:
        assert s.proc.poll() is None
