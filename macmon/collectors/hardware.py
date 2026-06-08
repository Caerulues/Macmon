from __future__ import annotations

import platform

from macmon.utils.command import run


def _sysctl_int(name: str) -> int | None:
    raw = run(["sysctl", "-n", name])
    try:
        return int(raw)
    except Exception:
        return None


def get_chip_name() -> str:
    output = run(["system_profiler", "SPHardwareDataType"], timeout=6)
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Chip:"):
            chip = line.split(":", 1)[1].strip()
            return chip if chip.startswith("Apple ") else f"Apple {chip}"
        if line.startswith("Processor Name:"):
            return line.split(":", 1)[1].strip()
    return platform.processor() or "Unknown"


def get_core_counts() -> tuple[int | None, int | None, int | None]:
    p = _sysctl_int("hw.perflevel0.physicalcpu")
    e = _sysctl_int("hw.perflevel1.physicalcpu")
    gpu = _sysctl_int("hw.optional.gpu_core_count")
    return p, e, gpu


def get_hardware_summary() -> str:
    chip = get_chip_name()
    p, e, gpu = get_core_counts()
    parts: list[str] = []
    if e is not None:
        parts.append(f"{e}E")
    if p is not None:
        parts.append(f"{p}P")
    if gpu is not None:
        parts.append(f"{gpu}GPU")
    return f"{chip} (cores: {'+'.join(parts)})" if parts else chip
