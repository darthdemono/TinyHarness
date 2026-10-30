"""Tiny hardware probe and model recommendation. Standard library only, no psutil."""
import os
import platform
import subprocess

# (max total RAM in GB, Hugging Face GGUF spec, note). Sizes checked on Hugging Face, 2026-10-30.
TIERS = [
    (3, "ggml-org/gemma-3-270m-it-GGUF", "Gemma 3 270M, text only, about 0.3 GB"),
    (6, "ggml-org/gemma-3-1b-it-GGUF:Q4_K_M", "Gemma 3 1B, text only, about 0.8 GB"),
    (12, "ggml-org/gemma-4-E2B-it-GGUF:Q4_0", "Gemma 4 E2B, text and images, about 2.8 GB plus 0.6 GB projector"),
    (10**6, "ggml-org/gemma-4-E4B-it-GGUF:Q4_0", "Gemma 4 E4B, text and images, about 4.6 GB plus 0.6 GB projector"),
]


def parse_meminfo(text):
    """Return total RAM in GB from /proc/meminfo text."""
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1048576
    raise ValueError("no MemTotal line")


def ram_gb():
    """Total physical RAM in GB, or None when it cannot be read."""
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong)] + [
                    (n, ctypes.c_ulonglong) for n in ("avail", "tpf", "apf", "tv", "av", "ae")
                ]

            ms = MS()
            ms.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))  # type: ignore[attr-defined]
            return ms.total / 2**30
        if platform.system() == "Darwin":
            return int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)) / 2**30
        with open("/proc/meminfo", encoding="utf-8") as f:
            return parse_meminfo(f.read())
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return None


def recommend(gb):
    """(spec, note) of the largest tier that fits gb of RAM; the smallest tier when unknown."""
    if gb is None:
        return TIERS[1][1], TIERS[1][2]
    for cap, spec, note in TIERS:
        if gb < cap:
            return spec, note
    return TIERS[-1][1], TIERS[-1][2]


def report():
    gb = ram_gb()
    spec, note = recommend(gb)
    return {
        "system": "%s %s" % (platform.system(), platform.machine()),
        "cpus": os.cpu_count(),
        "ram_gb": round(gb, 1) if gb else None,
        "recommended_model": spec,
        "note": note,
    }
