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
import sys
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


def installed():
    """Newest llama-server previously installed under the tinyharness home, or None."""
    base = os.path.join(home(), "llama.cpp")
    if not os.path.isdir(base):
        return None
    for tag in sorted(os.listdir(base), reverse=True):
        p = find_binary(os.path.join(base, tag))
        if p:
            return p
    return None


def find_server():
    """Resolve llama-server: TINYHARNESS_LLAMA_SERVER, then PATH, then a previous install."""
    env = os.environ.get("TINYHARNESS_LLAMA_SERVER")
    if env:
        return env
    return shutil.which("llama-server") or installed()


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
    with tempfile.TemporaryDirectory() as tmp:
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
    if os.name != "nt":
        os.chmod(got, 0o755)
    return got
