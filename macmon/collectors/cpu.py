from __future__ import annotations

import psutil

from macmon.utils.command import run
from macmon.collectors.powermetrics import estimate_cpu_freqs_from_core_residency, parse_powermetrics


def _sysctl_int(name: str) -> int | None:
    raw = run(["sysctl", "-n", name])
    try:
        return int(raw)
    except Exception:
        return None


def _freq_mhz(level: int) -> int | None:
    raw = run(["sysctl", "-n", f"hw.perflevel{level}.frequency"])
    try:
        value = int(raw)
    except Exception:
        return None
    return value // 1_000_000 if value > 1_000_000 else value


def get_core_layout() -> list[str]:
    p = _sysctl_int("hw.perflevel0.physicalcpu") or 0
    e = _sysctl_int("hw.perflevel1.physicalcpu") or 0
    logical = psutil.cpu_count(logical=True) or 0
    layout = ["P"] * p + ["E"] * e
    if len(layout) < logical:
        layout += ["U"] * (logical - len(layout))
    return layout[:logical]


def get_cpu_summary() -> dict:
    usages = psutil.cpu_percent(interval=None, percpu=True)
    layout = get_core_layout()
    cores = []
    type_counters = {"P": 0, "E": 0, "U": 0}
    for i, usage in enumerate(usages[:len(layout)]):
        typ = layout[i]
        idx = type_counters.get(typ, 0)
        type_counters[typ] = idx + 1
        cores.append({"index": idx, "global_index": i, "type": typ, "usage": float(usage)})
    p_vals = [c["usage"] for c in cores if c["type"] == "P"]
    e_vals = [c["usage"] for c in cores if c["type"] == "E"]
    snap = parse_powermetrics()
    est_p_freq, est_e_freq = estimate_cpu_freqs_from_core_residency(snap.output, layout)
    return {
        "total": float(psutil.cpu_percent(interval=None)),
        "p_avg": sum(p_vals) / len(p_vals) if p_vals else 0.0,
        "e_avg": sum(e_vals) / len(e_vals) if e_vals else 0.0,
        "p_freq": snap.p_freq_mhz or est_p_freq or _freq_mhz(0),
        "e_freq": snap.e_freq_mhz or est_e_freq or _freq_mhz(1),
        "cores": cores,
    }
