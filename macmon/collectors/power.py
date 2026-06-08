from __future__ import annotations

from macmon.collectors.powermetrics import parse_powermetrics


def get_power_info() -> dict:
    snap = parse_powermetrics()
    return {
        "cpu": snap.cpu_power_w,
        "gpu": snap.gpu_power_w,
        "ane": snap.ane_power_w,
        "system_total": snap.system_total_w,
    }
