import hashlib
import os
import tarfile
import zipfile

import pytest

from tinyharness import hw, llamacpp


@pytest.mark.parametrize("system,machine,want", [
    ("Linux", "x86_64", ("linux", "x64")),
    ("Linux", "aarch64", ("linux", "arm64")),
    ("Darwin", "arm64", ("macos", "arm64")),
    ("Darwin", "x86_64", ("macos", "x64")),
    ("Windows", "AMD64", ("windows", "x64")),
    ("Windows", "ARM64", ("windows", "arm64")),
])
def test_platform_key_covers_every_target(system, machine, want):
    assert llamacpp.platform_key(system, machine) == want


def test_platform_key_rejects_unknown():
    with pytest.raises(RuntimeError, match="no prebuilt"):
        llamacpp.platform_key("Linux", "riscv64")


NAMES = [
    "llama-b1-bin-ubuntu-x64.tar.gz", "llama-b1-bin-ubuntu-vulkan-x64.tar.gz", "llama-b1-bin-ubuntu-cuda-12.8-x64.tar.gz",
    "llama-b1-bin-ubuntu-arm64.tar.gz", "llama-b1-bin-macos-arm64.tar.gz", "llama-b1-bin-macos-x64.tar.gz",
    "llama-b1-bin-win-cpu-x64.zip", "llama-b1-bin-win-cpu-arm64.zip", "llama-b1-bin-win-vulkan-x64.zip", "llama-b1-bin-win-cuda-12.4-x64.zip",
]


@pytest.mark.parametrize("os_,arch,variant,want", [
    ("linux", "x64", "cpu", "llama-b1-bin-ubuntu-x64.tar.gz"),
    ("linux", "x64", "vulkan", "llama-b1-bin-ubuntu-vulkan-x64.tar.gz"),
    ("linux", "arm64", "cpu", "llama-b1-bin-ubuntu-arm64.tar.gz"),
    ("macos", "arm64", "cpu", "llama-b1-bin-macos-arm64.tar.gz"),
    ("macos", "x64", "cpu", "llama-b1-bin-macos-x64.tar.gz"),
    ("windows", "x64", "cpu", "llama-b1-bin-win-cpu-x64.zip"),
    ("windows", "arm64", "cpu", "llama-b1-bin-win-cpu-arm64.zip"),
    ("windows", "x64", "vulkan", "llama-b1-bin-win-vulkan-x64.zip"),
])
def test_pattern_picks_exactly_one_asset_per_target(os_, arch, variant, want):
    rels = [{"tag_name": "b1", "assets": [{"name": n} for n in NAMES]}]
    assert llamacpp.pick_asset(rels, llamacpp.asset_pattern(os_, arch, variant))[1]["name"] == want


def test_macos_has_no_vulkan_and_empty_releases_skipped():
    with pytest.raises(RuntimeError, match="Metal"):
        llamacpp.asset_pattern("macos", "arm64", "vulkan")
    rels = [{"tag_name": "b2", "assets": []}, {"tag_name": "b1", "assets": [{"name": NAMES[0]}]}]
    assert llamacpp.pick_asset(rels, llamacpp.asset_pattern("linux", "x64"))[0] == "b1"
    with pytest.raises(RuntimeError):
        llamacpp.pick_asset([], "x")


def test_safe_extract_rejects_path_traversal_in_both_formats(tmp_path):
    z = tmp_path / "a.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("../evil.txt", "x")
    with pytest.raises(RuntimeError, match="unsafe"):
        llamacpp.safe_extract(str(z), str(tmp_path / "out"))
    t = tmp_path / "a.tar.gz"
    src = tmp_path / "f.txt"
    src.write_text("x")
    with tarfile.open(t, "w:gz") as f:
        f.add(src, arcname="../evil.txt")
    with pytest.raises(RuntimeError, match="unsafe"):
        llamacpp.safe_extract(str(t), str(tmp_path / "out2"))
    assert not (tmp_path / "evil.txt").exists()


def test_extract_find_and_sha256(tmp_path):
    t = tmp_path / "a.tar.gz"
    exe = tmp_path / llamacpp.EXE
    exe.write_text("bin")
    with tarfile.open(t, "w:gz") as f:
        f.add(exe, arcname="llama-b1/" + llamacpp.EXE)
    llamacpp.safe_extract(str(t), str(tmp_path / "out"))
    assert llamacpp.find_binary(str(tmp_path / "out")).endswith(llamacpp.EXE)
    assert llamacpp.sha256_file(str(exe)) == hashlib.sha256(b"bin").hexdigest()


def test_installed_prefers_matching_variant_and_env_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    for tag in ("b1-cpu", "b2-cpu", "b2-vulkan"):
        d = tmp_path / "llama.cpp" / tag
        d.mkdir(parents=True)
        (d / llamacpp.EXE).write_text(tag)
    assert "b2-cpu" in llamacpp.installed("cpu") and "b2-vulkan" in llamacpp.installed("vulkan")
    monkeypatch.setenv("TINYHARNESS_LLAMA_SERVER", "/x/llama-server")
    assert llamacpp.find_server("vulkan") == "/x/llama-server"


def test_command_uses_file_or_hf_and_small_machine_flags(tmp_path):
    gguf = tmp_path / "m.gguf"
    gguf.write_text("x")
    c = llamacpp.command("srv", str(gguf), 9000, ctx=2048, threads=2, gpu_layers=99)
    assert c[c.index("-m") + 1] == str(gguf) and "-hf" not in c
    assert c[c.index("-np") + 1] == "1" and "--no-webui" in c and c[c.index("-ngl") + 1] == "99"
    assert c[c.index("-ctk") + 1] == "q8_0" and c[c.index("-t") + 1] == "2"
    h = llamacpp.command("srv", "ggml-org/x-GGUF:Q4_0", 9000)
    assert h[h.index("-hf") + 1] == "ggml-org/x-GGUF:Q4_0" and "-ngl" not in h


def test_server_start_stop_with_a_fake_health_server(tmp_path, monkeypatch):
    """A stand-in 'llama-server' (a python script) proves spawn, health wait and shutdown."""
    import sys

    script = tmp_path / "fake.py"
    script.write_text(
        "import sys\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "port = int(sys.argv[sys.argv.index('--port') + 1])\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')\n"
        "    def log_message(self, *a): pass\n"
        "HTTPServer(('127.0.0.1', port), H).serve_forever()\n"
    )
    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    s = llamacpp.Server("ggml-org/x:Q4", binary=sys.executable, log=lambda m: None)
    s.cmd = [sys.executable, str(script)] + s.cmd[1:]  # swap the binary for the fake, keep llama-server's flags
    with s:
        assert s.proc.poll() is None and s.url.endswith("/v1")
    assert s.proc.poll() is not None


def test_server_reports_early_exit_with_log_tail(tmp_path, monkeypatch):
    import sys

    monkeypatch.setenv("TINYHARNESS_HOME", str(tmp_path))
    s = llamacpp.Server("x/y", binary=sys.executable, log=lambda m: None, timeout=20)
    s.cmd = [sys.executable, "-c", "print('boom: model missing'); raise SystemExit(3)"]
    with pytest.raises(RuntimeError, match="boom: model missing"):
        s.start()


def test_hw_recommend_tiers_and_meminfo():
    assert hw.recommend(1.5)[0].endswith("gemma-3-270m-it-GGUF")
    assert "gemma-3-1b" in hw.recommend(4)[0]
    assert "E2B" in hw.recommend(8)[0] and "E4B" in hw.recommend(16)[0]
    assert hw.recommend(None) == (hw.TIERS[1][1], hw.TIERS[1][2])
    assert hw.parse_meminfo("MemTotal:       16384000 kB\nMemFree: 1 kB\n") == pytest.approx(15.625, rel=1e-3)
    with pytest.raises(ValueError):
        hw.parse_meminfo("nothing")
    assert set(hw.report()) >= {"system", "cpus", "recommended_model"}
    assert os.path.basename(hw.report()["recommended_model"])
