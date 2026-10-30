"""@file llamacpp.py
@brief Find, download, verify and run llama.cpp's `llama-server`, the fast inference engine behind GGUF models.

Why llama.cpp: it runs quantised models on a plain CPU or any GPU with a Vulkan
driver, which is what makes low-end laptops and small boards usable. TinyHarness
does not reimplement inference; it manages the engine and talks to it over its
OpenAI-compatible HTTP API (see client.py).

Lifecycle:

1. find_server: environment override, then a previous install, then PATH.
2. install: ask the GitHub releases API for the newest build with an asset for
   this OS and CPU, download it, check the published SHA-256, unpack it under
   the TinyHarness home (default ~/.tinyharness), return the binary path.
3. Server: start the binary on a free local port with settings tuned for small
   machines, wait until /health answers 200, stop it when the with-block ends.

Supported targets: Linux, macOS and Windows on x64 and arm64 (platform_key).
Release asset names were read from the live release list; CI downloads and
runs the binary on every target to catch a renamed asset.
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
    """@brief Directory where TinyHarness keeps downloaded engines and logs.

    @return TINYHARNESS_HOME if set, otherwise `~/.tinyharness`.
    """
    return os.environ.get("TINYHARNESS_HOME") or os.path.join(os.path.expanduser("~"), ".tinyharness")


def platform_key(system=None, machine=None):
    """@brief Map this machine to the (os, arch) names used by llama.cpp release assets.

    @param system Override for platform.system(), used by tests.
    @param machine Override for platform.machine(), used by tests.
    @return A tuple such as `("linux", "x64")` or `("macos", "arm64")`.
    @throws RuntimeError For any other system or CPU, with a hint to supply llama-server manually.
    """
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    os_ = {"linux": "linux", "darwin": "macos", "windows": "windows"}.get(system)
    arch = {"x86_64": "x64", "amd64": "x64", "x64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(machine)
    if not os_ or not arch:
        raise RuntimeError("no prebuilt llama.cpp for %s %s; install llama-server yourself and set TINYHARNESS_LLAMA_SERVER" % (system, machine))
    return os_, arch


def asset_pattern(os_, arch, variant="cpu"):
    """@brief Regular expression matching the release asset for one target.

    Asset names in a release are of the form `llama-<tag>-bin-<platform>.<ext>`,
    for example `llama-b12015-bin-ubuntu-x64.tar.gz` or `llama-b12015-bin-win-cpu-arm64.zip`.

    @param os_ One of linux, macos, windows.
    @param arch One of x64, arm64.
    @param variant `"cpu"` (default) or `"vulkan"` (GPU offload through any Vulkan driver, including NVIDIA).
    @return A pattern to use with re.fullmatch.
    @throws RuntimeError If a Vulkan build is requested for macOS (the default macOS build uses Metal).
    """
    v = "vulkan-" if variant == "vulkan" else ""
    if os_ == "linux":
        return r"llama-.+-bin-ubuntu-%s%s\.tar\.gz" % (v, arch)
    if os_ == "macos":
        if variant == "vulkan":
            raise RuntimeError("the vulkan build does not exist for macOS; the default build already uses Metal")
        return r"llama-.+-bin-macos-%s\.tar\.gz" % arch
    return r"llama-.+-bin-win-%s-%s\.zip" % ("vulkan" if variant == "vulkan" else "cpu", arch)


def pick_asset(releases, pattern):
    """@brief Choose the newest release that has a matching asset.

    Releases are listed newest first. A release with no matching asset (for example one still being built) is skipped.

    @param releases Parsed JSON from the GitHub releases API.
    @param pattern Regular expression from asset_pattern.
    @return `(tag, asset)` where asset is the API object with name, size, digest and download URL.
    @throws RuntimeError If no release matches.
    """
    rx = re.compile(pattern)
    for rel in releases:
        for a in rel.get("assets", []):
            if rx.fullmatch(a["name"]):
                return rel["tag_name"], a
    raise RuntimeError("no release asset matches " + pattern)


def _get(url):
    """@brief Open a URL with a User-Agent, adding GITHUB_TOKEN only for api.github.com requests.

    The token (optional) raises the unauthenticated API rate limit. It is never sent to other hosts.

    @param url Address to open.
    @return A response object usable as a context manager.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "tinyharness"})
    if os.environ.get("GITHUB_TOKEN") and "api.github.com" in url:
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    return urllib.request.urlopen(req, timeout=60)


def sha256_file(path):
    """@brief Hash a file in 1 MiB blocks (large archives are not read into memory).

    @param path File to hash.
    @return Lowercase hexadecimal SHA-256.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def safe_extract(archive, dest):
    """@brief Unpack a .zip or .tar.gz while refusing any entry that would land outside the destination.

    Every member name is resolved first, so a crafted archive containing `../` paths
    extracts nothing at all. For tar files, the `data` extraction filter further blocks links and special files.

    @param archive Path of the archive; the extension picks the format.
    @param dest Folder to extract into.
    @throws RuntimeError On the first unsafe entry.
    """
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
    """@brief Locate llama-server (or llama-server.exe on Windows) anywhere below a folder.

    @param root Folder to search.
    @return Path of the binary, or None.
    """
    for d, _, files in os.walk(root):
        if EXE in files:
            return os.path.join(d, EXE)
    return None


def installed(variant="cpu"):
    """@brief Newest llama-server of one variant that install() has already unpacked.

    @param variant `"cpu"` or `"vulkan"`; install folders are named `<tag>-<variant>`.
    @return Binary path, or None if nothing is installed.
    """
    base = os.path.join(home(), "llama.cpp")
    if not os.path.isdir(base):
        return None
    for tag in sorted((d for d in os.listdir(base) if d.endswith("-" + variant)), reverse=True):
        p = find_binary(os.path.join(base, tag))
        if p:
            return p
    return None


def find_server(variant="cpu"):
    """@brief Decide which llama-server to run, without downloading anything.

    Order: TINYHARNESS_LLAMA_SERVER, then a previous install of this variant, then a
    `llama-server` on PATH (CPU variant only, because a PATH binary's GPU support is unknown).

    @param variant `"cpu"` or `"vulkan"`.
    @return Path or command name, or None.
    """
    env = os.environ.get("TINYHARNESS_LLAMA_SERVER")
    if env:
        return env
    return installed(variant) or (shutil.which("llama-server") if variant == "cpu" else None)


def make_executable(path):
    """@brief Mark the unpacked binary runnable. Windows has no execute bit, so nothing is done there.

    @param path Binary to mark.
    """
    if os.name != "nt":
        os.chmod(path, 0o755)


def install(variant="cpu", log=print):
    """@brief Download the newest matching llama.cpp build, verify it and unpack it.

    If the newest tag is already unpacked the existing binary is returned and nothing
    is downloaded. The archive goes into a temporary folder inside the TinyHarness
    home, not the system temp folder, because /tmp is often a small RAM disk (this
    broke a download on the development machine). GitHub publishes a SHA-256 digest
    per asset; when present, a mismatch aborts before anything is unpacked.

    @param variant `"cpu"` or `"vulkan"`.
    @param log Callable receiving progress messages (default print).
    @return Path of the llama-server binary.
    @throws RuntimeError On checksum mismatch, a missing asset, or an archive with no server in it.
    """
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
    """@brief Ask the operating system for an unused TCP port on localhost.

    There is a small window before llama-server binds it; acceptable for a local tool.

    @return Port number.
    """
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def command(binary, model, port, ctx=4096, threads=None, kv="q8_0", gpu_layers=None, offline=False):
    """@brief Build the llama-server command line, tuned for small machines.

    Choices and why:

    - `-np 1`: one request slot. The default (auto) allocates several slots and multiplies KV-cache memory.
    - `-ctk/-ctv q8_0`: 8-bit KV cache roughly halves its memory at little quality cost.
    - `--no-webui`: llama-server's own page is not needed; TinyHarness has its own.
    - `--host 127.0.0.1`: never listen on the network.
    - `-hf` vs `-m`: an existing file path is loaded directly, anything else is a Hugging Face spec `user/repo[:quant]` that llama-server downloads and caches.

    @param binary Path of llama-server.
    @param model A .gguf file path or a Hugging Face spec.
    @param port Local port to listen on.
    @param ctx Context window in tokens.
    @param threads CPU threads, or None to let llama.cpp choose.
    @param kv KV-cache type, or None for the default (f16, larger).
    @param gpu_layers Layers to offload (99 means all), or None for CPU only.
    @param offline True adds `--offline`: use the cache, never the network.
    @return Argument list for subprocess.
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
    """@brief A llama-server child process that lives for the length of a `with` block.

    @code{.py}
    with Server("ggml-org/gemma-4-E2B-it-GGUF:Q4_0", gpu=True) as srv:
        client = Client(backend="openai", base_url=srv.url)
    @endcode

    Output goes to `<home>/logs/llama-server.log`; the tail of that file is included
    in error messages so a failed start explains itself.
    """

    def __init__(self, model, binary=None, ctx=4096, threads=None, kv="q8_0", timeout=1800, log=print, gpu=False, offline=False):
        """@brief Prepare (but do not start) a server.

        If no binary is given, find_server is tried and install is the fallback, so
        the first use downloads the engine automatically.

        @param model .gguf path or Hugging Face spec, see command().
        @param binary Explicit llama-server path (tests use a stand-in).
        @param ctx Context window in tokens.
        @param threads CPU threads or None.
        @param kv KV-cache type or None.
        @param timeout Seconds to wait for the model to load. Long by default (30 min) because the first run may download gigabytes.
        @param log Callable for progress messages.
        @param gpu True selects the Vulkan build and offloads all layers.
        @param offline True forbids network access.
        """
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
        """@brief Base URL for an OpenAI-style client, including the `/v1` prefix."""
        return "http://127.0.0.1:%d/v1" % self.port

    def _tail(self, n=15):
        """@brief The last lines of the server log, or an empty string if there is no log.

        @param n Number of lines.
        """
        try:
            with open(self.logfile, encoding="utf-8", errors="replace") as f:
                return "".join(f.readlines()[-n:])
        except OSError:
            return ""

    def start(self):
        """@brief Launch the process and block until it reports healthy.

        llama-server answers /health with 503 while loading and 200 when ready; only
        200 counts. If the process exits early the log tail is raised as the error.
        On timeout the process is stopped first.

        @return self, so it can be used as a context manager.
        @throws RuntimeError If the process exits or does not become ready in time.
        """
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
        """@brief Stop the process: ask politely, wait 10 seconds, then kill. Safe to call twice or before start."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

    def __enter__(self):
        """@brief Start the server (see start)."""
        return self.start()

    def __exit__(self, *exc):
        """@brief Stop the server, also when the block raised."""
        self.stop()
