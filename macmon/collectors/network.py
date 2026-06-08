from __future__ import annotations

import time
from collections import deque

import psutil

_LAST_BYTES: tuple[float, int, int] | None = None
_UP_HISTORY: deque[float] = deque(maxlen=600)
_DOWN_HISTORY: deque[float] = deque(maxlen=600)


def _format_rate(bytes_per_sec: float) -> str:
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    value = float(bytes_per_sec)
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1
    if idx == 0:
        return f"{value:.0f} {units[idx]}"
    return f"{value:.2f} {units[idx]}"


def get_network_info() -> dict:
    global _LAST_BYTES
    counters = psutil.net_io_counters()
    now = time.time()
    if _LAST_BYTES is None:
        _LAST_BYTES = (now, counters.bytes_sent, counters.bytes_recv)
        up = down = 0.0
    else:
        last_t, last_sent, last_recv = _LAST_BYTES
        dt = max(now - last_t, 1e-6)
        up = max(0.0, (counters.bytes_sent - last_sent) / dt)
        down = max(0.0, (counters.bytes_recv - last_recv) / dt)
        _LAST_BYTES = (now, counters.bytes_sent, counters.bytes_recv)
    _UP_HISTORY.append(up)
    _DOWN_HISTORY.append(down)
    return {
        "upload_bps": up,
        "download_bps": down,
        "upload": _format_rate(up),
        "download": _format_rate(down),
        "upload_history": list(_UP_HISTORY),
        "download_history": list(_DOWN_HISTORY),
    }
