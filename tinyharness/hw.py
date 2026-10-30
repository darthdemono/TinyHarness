"""@file hw.py
@brief A tiny hardware probe and a model recommendation, standard library only.

Used by `tinyharness doctor` and by `--local` with no model named. The model
tiers below were checked against Hugging Face on 2026-10-30; the thresholds are
a conservative rule of thumb (model file plus context plus runtime must fit in
RAM) and have not been timed on every class of device.
"""
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
    """@brief Read total RAM from the text of /proc/meminfo.

    @param text File contents.
    @return Gigabytes (GiB).
    @throws ValueError If there is no MemTotal line.
    """
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1048576
    raise ValueError("no MemTotal line")


def ram_gb():
    """@brief Total physical RAM in GiB.

    Linux reads /proc/meminfo, macOS asks `sysctl hw.memsize`, Windows calls
    GlobalMemoryStatusEx through ctypes. Any failure yields None rather than an
    exception, because a missing number should degrade the recommendation, not abort.

    @return GiB as a float, or None when it cannot be read.
    """
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
    """@brief Pick the largest model tier that fits in a given amount of RAM.

    @param gb Total RAM in GiB, or None if unknown (then the second tier, a safe small text model, is returned).
    @return `(huggingface_spec, human_note)`.
    """
    if gb is None:
        return TIERS[1][1], TIERS[1][2]
    for cap, spec, note in TIERS:
        if gb < cap:
            return spec, note
    return TIERS[-1][1], TIERS[-1][2]


def report():
    """@brief Describe this machine and the recommended model.

    @return A dict with system, cpus, ram_gb, recommended_model and note, printed as JSON by `doctor`.
    """
    gb = ram_gb()
    spec, note = recommend(gb)
    return {
        "system": "%s %s" % (platform.system(), platform.machine()),
        "cpus": os.cpu_count(),
        "ram_gb": round(gb, 1) if gb else None,
        "recommended_model": spec,
        "note": note,
    }
