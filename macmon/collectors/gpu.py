from __future__ import annotations

from macmon.collectors.powermetrics import parse_powermetrics
from macmon.utils.command import run


def _sysctl_int(name: str) -> int | None:
    raw = run(["sysctl", "-n", name])
    try:
        return int(raw)
    except Exception:
        return None


def get_gpu_info() -> dict:
    core_count = _sysctl_int("hw.optional.gpu_core_count") or 1
    snap = parse_powermetrics()
    usage = snap.gpu_usage
    freq = snap.gpu_freq_mhz
    cores = [{"index": i, "type": "G", "usage": usage} for i in range(core_count)]
    return {"usage": usage, "freq": freq, "core_count": core_count, "cores": cores}


def get_ane_info() -> dict:
    snap = parse_powermetrics()
    return {
        "usage": snap.ane_usage,
        "power": snap.ane_power_w,
        "cores": [{"index": 0, "type": "ANE", "usage": snap.ane_usage}],
    }
