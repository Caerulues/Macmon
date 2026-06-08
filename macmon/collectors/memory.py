from __future__ import annotations

from collections import deque

import psutil

_HISTORY: deque[float] = deque(maxlen=600)


def get_memory_info() -> dict:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    used_gb = (mem.total - mem.available) / 1024**3
    total_gb = mem.total / 1024**3
    percent = used_gb / total_gb * 100 if total_gb else 0.0
    _HISTORY.append(percent)
    return {
        "used_gb": used_gb,
        "total_gb": total_gb,
        "percent": percent,
        "swap": "active" if swap.used > 0 else "inactive",
        "history": list(_HISTORY),
    }
