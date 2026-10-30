"""Find, download and run llama.cpp's llama-server, the fast CPU/GPU inference engine behind GGUF models.

Works on Linux, macOS and Windows, on x64 and arm64. Standard library only.
"""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request
import zipfile

RELEASES = "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10"
EXE = "llama-server.exe" if os.name == "nt" else "llama-server"


def home():
    return os.environ.get("TINYHARNESS_HOME") or os.path.join(os.path.expanduser("~"), ".tinyharness")


def platform_key(system=None, machine=None):
    """Return (os, arch) with os in linux/macos/windows and arch in x64/arm64; raise on anything else."""
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    os_ = {"linux": "linux", "darwin": "macos", "windows": "windows"}.get(system)
    arch = {"x86_64": "x64", "amd64": "x64", "x64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(machine)
    if not os_ or not arch:
        raise RuntimeError("no prebuilt llama.cpp for %s %s; install llama-server yourself and set TINYHARNESS_LLAMA_SERVER" % (system, machine))
    return os_, arch


def asset_pattern(os_, arch, variant="cpu"):
    """Regex for the release asset name. variant is 'cpu' or 'vulkan' (any GPU with a Vulkan driver)."""
    v = "vulkan-" if variant == "vulkan" else ""
    if os_ == "linux":
        return r"llama-.+-bin-ubuntu-%s%s\.tar\.gz" % (v, arch)
    if os_ == "macos":
        if variant == "vulkan":
            raise RuntimeError("the vulkan build does not exist for macOS; the default build already uses Metal")
        return r"llama-.+-bin-macos-%s\.tar\.gz" % arch
    return r"llama-.+-bin-win-%s-%s\.zip" % ("vulkan" if variant == "vulkan" else "cpu", arch)


def pick_asset(releases, pattern):
    """First (tag, asset) in the newest-first release list whose asset name matches pattern."""
    rx = re.compile(pattern)
    for rel in releases:
        for a in rel.get("assets", []):
            if rx.fullmatch(a["name"]):
                return rel["tag_name"], a
    raise RuntimeError("no release asset matches " + pattern)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tinyharness"})
    if os.environ.get("GITHUB_TOKEN") and "api.github.com" in url:
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    return urllib.request.urlopen(req, timeout=60)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def safe_extract(archive, dest):
    """Extract a .zip or .tar.gz refusing any member that would land outside dest."""
    root = os.path.realpath(dest)
    opener = zipfile.ZipFile if archive.endswith(".zip") else tarfile.open
    with opener(archive) as z:
        names = z.namelist() if archive.endswith(".zip") else z.getnames()
        for n in names:
            target = os.path.realpath(os.path.join(root, n))
            if target != root and not target.startswith(root + os.sep):
                raise RuntimeError("unsafe path in archive: " + n)
        if archive.endswith(".zip"):
            z.extractall(root)
        else:
            z.extractall(root, filter="data")


def find_binary(root):
    """Return the path of llama-server under root, or None."""
    for d, _, files in os.walk(root):
        if EXE in files:
            return os.path.join(d, EXE)
    return None


def installed(variant="cpu"):
    """Newest llama-server of this variant previously installed under the tinyharness home, or None."""
    base = os.path.join(home(), "llama.cpp")
    if not os.path.isdir(base):
        return None
    for tag in sorted((d for d in os.listdir(base) if d.endswith("-" + variant)), reverse=True):
        p = find_binary(os.path.join(base, tag))
        if p:
            return p
    return None


def find_server(variant="cpu"):
    """Resolve llama-server: TINYHARNESS_LLAMA_SERVER, then a previous install, then PATH (cpu only)."""
    env = os.environ.get("TINYHARNESS_LLAMA_SERVER")
    if env:
        return env
    return installed(variant) or (shutil.which("llama-server") if variant == "cpu" else None)


def make_executable(path):
    """Mark the unpacked binary runnable. Windows has no execute bit, so it is left alone there."""
    if os.name != "nt":
        os.chmod(path, 0o755)


def install(variant="cpu", log=print):
    """Download the newest matching llama.cpp release, verify its sha256, unpack it, return the binary path."""
    pattern = asset_pattern(*platform_key(), variant=variant)
    with _get(RELEASES) as r:
        tag, asset = pick_asset(json.load(r), pattern)
    dest = os.path.join(home(), "llama.cpp", "%s-%s" % (tag, variant))
    got = find_binary(dest) if os.path.isdir(dest) else None
    if got:
        return got
    log("downloading %s (%d MB)" % (asset["name"], asset["size"] // 1048576))
    os.makedirs(dest, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=home()) as tmp:  # not /tmp, which is often a small RAM disk
        arc = os.path.join(tmp, asset["name"])
        with _get(asset["browser_download_url"]) as r, open(arc, "wb") as f:
            shutil.copyfileobj(r, f)
        want = (asset.get("digest") or "").removeprefix("sha256:")
        if want and sha256_file(arc) != want:
            raise RuntimeError("checksum mismatch for " + asset["name"])
        safe_extract(arc, dest)
    got = find_binary(dest)
    if not got:
        raise RuntimeError("llama-server not found in " + asset["name"])
    make_executable(got)
    return got


def free_port():
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def command(binary, model, port, ctx=4096, threads=None, kv="q8_0", gpu_layers=None, offline=False):
    """llama-server argv tuned for small machines: one slot, quantised KV cache, no built-in web UI.

    model is a path to a .gguf file, or a Hugging Face spec 'user/repo[:quant]' that llama-server downloads itself.
    """
    cmd = [binary, "--host", "127.0.0.1", "--port", str(port), "-c", str(ctx), "-np", "1", "--no-webui"]
    cmd += ["-m", model] if os.path.isfile(model) else ["-hf", model]
    if threads:
        cmd += ["-t", str(threads)]
    if gpu_layers is not None:
        cmd += ["-ngl", str(gpu_layers)]
    if offline:
        cmd.append("--offline")  # use the model cache only, never touch the network
    if kv:
        cmd += ["-ctk", kv, "-ctv", kv]
    return cmd


class Server:
    """Run llama-server as a child process for the length of a with block."""

    def __init__(self, model, binary=None, ctx=4096, threads=None, kv="q8_0", timeout=1800, log=print, gpu=False, offline=False):
        variant = "vulkan" if gpu else "cpu"
        self.binary = binary or find_server(variant) or install(variant, log=log)
        self.port = free_port()
        self.cmd = command(self.binary, model, self.port, ctx, threads, kv, gpu_layers=99 if gpu else None, offline=offline)
        self.timeout = timeout
        self.log = log
        self.proc = None
        self.logfile = os.path.join(home(), "logs", "llama-server.log")

    @property
    def url(self):
        return "http://127.0.0.1:%d/v1" % self.port

    def _tail(self, n=15):
        try:
            with open(self.logfile, encoding="utf-8", errors="replace") as f:
                return "".join(f.readlines()[-n:])
        except OSError:
            return ""

    def start(self):
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        out = open(self.logfile, "w", encoding="utf-8")
        self.proc = subprocess.Popen(self.cmd, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        out.close()
        self.log("starting llama-server (first run may download the model; log: %s)" % self.logfile)
        deadline = time.monotonic() + self.timeout
        health = "http://127.0.0.1:%d/health" % self.port
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("llama-server exited with code %s:\n%s" % (self.proc.returncode, self._tail()))
            try:
                with urllib.request.urlopen(health, timeout=2) as r:
                    if r.status == 200:
                        return self
            except OSError:  # 503 while loading, connection refused while binding
                pass
            time.sleep(0.5)
        self.stop()
        raise RuntimeError("llama-server not ready after %ds:\n%s" % (self.timeout, self._tail()))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
