from __future__ import annotations

import plistlib
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from macmon.utils.command import run

_CACHE_TTL = 0.75
_cache_time = 0.0
_cache_output = ""
_cache_plist: dict[str, Any] | None = None


@dataclass
class PowerMetricsSnapshot:
    output: str = ""
    cpu_power_w: float | None = None
    gpu_power_w: float | None = None
    ane_power_w: float | None = None
    system_total_w: float | None = None
    cpu_avg_temp_c: float | None = None
    p_freq_mhz: int | None = None
    e_freq_mhz: int | None = None
    gpu_freq_mhz: int | None = None
    ane_usage: float = 0.0
    gpu_usage: float = 0.0
    throttle: str = "no"
    cpu_temps: list[float] = field(default_factory=list)


def _run_bytes(cmd: list[str], timeout: float = 4.0) -> bytes:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout)
    except Exception:
        return b""


def _load_last_plist(blob: bytes) -> dict[str, Any] | None:
    """powermetrics -f plist may emit one plist or NUL-separated plist records."""
    if not blob:
        return None
    for part in reversed([p for p in blob.split(b"\x00") if p.strip()]):
        try:
            data = plistlib.loads(part)
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return None


def _plist_to_debug_text(data: dict[str, Any] | None) -> str:
    if not data:
        return ""
    lines: list[str] = ["powermetrics plist snapshot"]
    processor = data.get("processor", {}) if isinstance(data.get("processor"), dict) else {}
    for cluster in processor.get("clusters", []) or []:
        name = str(cluster.get("name", "Cluster"))
        freq = _hz_to_mhz(cluster.get("freq_hz"))
        idle = _ratio_to_active(cluster.get("idle_ratio"))
        if freq is not None:
            lines.append(f"{name} active frequency: {freq} MHz")
        if idle is not None:
            lines.append(f"{name} active residency: {idle:.1f}%")
    gpu = data.get("gpu", {}) if isinstance(data.get("gpu"), dict) else {}
    if gpu:
        freq = _hz_to_mhz(gpu.get("freq_hz"))
        active = _ratio_to_active(gpu.get("idle_ratio"))
        if freq is not None:
            lines.append(f"GPU active frequency: {freq} MHz")
        if active is not None:
            lines.append(f"GPU active residency: {active:.1f}%")
    for key, label in (
        ("cpu_energy", "CPU Power"),
        ("gpu_energy", "GPU Power"),
        ("ane_energy", "ANE Power"),
        ("combined_power", "System Total"),
    ):
        value = _mw_to_w(processor.get(key))
        if value is not None:
            lines.append(f"{label}: {value:.2f} W")
    pressure = data.get("thermal_pressure")
    if pressure is not None:
        lines.append(f"thermal pressure: {pressure}")
    return "\n".join(lines)


def _fetch_powermetrics() -> tuple[str, dict[str, Any] | None]:
    plist_cmds = [
        ["sudo", "-n", "powermetrics", "--samplers", "cpu_power,gpu_power,thermal", "-i", "2", "-n", "1", "-f", "plist"],
        ["sudo", "-n", "powermetrics", "--samplers", "cpu_power,gpu_power", "-i", "2", "-n", "1", "-f", "plist"],
    ]
    for cmd in plist_cmds:
        blob = _run_bytes(cmd, timeout=5)
        data = _load_last_plist(blob)
        if data:
            return _plist_to_debug_text(data), data

    # Text fallback for older or restricted powermetrics builds.
    text_cmds = [
        ["sudo", "-n", "powermetrics", "--samplers", "smc,cpu_power,gpu_power,thermal", "-i", "2", "-n", "1"],
        ["sudo", "-n", "powermetrics", "--samplers", "cpu_power,gpu_power,thermal", "-i", "2", "-n", "1"],
        ["sudo", "-n", "powermetrics", "--samplers", "smc", "-i", "2", "-n", "1"],
    ]
    for cmd in text_cmds:
        out = run(cmd, timeout=5)
        if out:
            return out, None
    return "", None


def get_powermetrics_output() -> str:
    """Return cached powermetrics output/debug text.

    Run `sudo -v` before starting Macmon. Without cached sudo credentials,
    `sudo -n powermetrics` cannot collect privileged counters and this returns empty output.
    """
    global _cache_time, _cache_output, _cache_plist
    now = time.monotonic()
    if (_cache_output or _cache_plist) and now - _cache_time < _CACHE_TTL:
        return _cache_output
    _cache_output, _cache_plist = _fetch_powermetrics()
    _cache_time = now
    return _cache_output


def get_powermetrics_plist() -> dict[str, Any] | None:
    get_powermetrics_output()
    return _cache_plist


def _to_w(value: str, unit: str | None) -> float:
    number = float(value.replace(",", ""))
    unit_l = (unit or "W").lower()
    if unit_l == "mw":
        number /= 1000
    elif unit_l in {"uw", "µw"}:
        number /= 1_000_000
    return round(number, 2)


def _mw_to_w(value: Any) -> float | None:
    try:
        return round(float(value) / 1000.0, 2)
    except Exception:
        return None


def _hz_to_mhz(value: Any) -> int | None:
    try:
        v = float(value)
    except Exception:
        return None
    if v <= 0:
        return None
    return int(round(v / 1_000_000)) if v > 100_000 else int(round(v))


def _ratio_to_active(value: Any) -> float | None:
    try:
        return max(0.0, min(100.0, (1.0 - float(value)) * 100.0))
    except Exception:
        return None


def _first_power(output: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, output, re.I)
        if match:
            unit = match.group(2) if len(match.groups()) >= 2 else "W"
            return _to_w(match.group(1), unit)
    return None


def _first_int(output: str, patterns: list[str]) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, output, re.I)
        if match:
            return int(float(match.group(1).replace(",", "")))
    return None


def _first_percent(output: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, output, re.I)
        if match:
            return float(match.group(1))
    return None


def _cluster_kind(name: str) -> str:
    n = name.strip().upper()
    if n.startswith("E") or "EFFICIENCY" in n or "E-CLUSTER" in n or "E_CLUSTER" in n:
        return "E"
    if n.startswith("P") or "PERFORMANCE" in n or "P-CLUSTER" in n or "P_CLUSTER" in n:
        return "P"
    return "U"


def _classify_clusters(clusters: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Classify powermetrics CPU clusters as P/E.

    Apple Silicon plist output is not perfectly stable across macOS versions.
    Some builds name clusters clearly as E-Cluster/P-Cluster, while others only
    expose generic cluster names. In the generic case, use the same practical
    assumption used by tools such as asitop: efficiency clusters have lower
    active/max frequency than performance clusters.
    """
    typed: list[tuple[str, dict[str, Any]]] = []
    unknown: list[dict[str, Any]] = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue
        kind = _cluster_kind(str(cluster.get("name", "")))
        if kind == "U":
            unknown.append(cluster)
        else:
            typed.append((kind, cluster))

    if not unknown:
        return typed

    if not any(kind == "P" for kind, _ in typed) and not any(kind == "E" for kind, _ in typed):
        # All cluster names are generic. Sort by available frequency; lower half = E, upper half = P.
        ranked = sorted(
            unknown,
            key=lambda c: _hz_to_mhz(c.get("freq_hz"))
            or _hz_to_mhz(c.get("max_freq_hz"))
            or _hz_to_mhz(c.get("hw_residency_max_freq_hz"))
            or 0,
        )
        split = max(1, len(ranked) // 2)
        return [("E", c) for c in ranked[:split]] + [("P", c) for c in ranked[split:]]

    # If one type was identified and the other was not, assign unknown clusters to the missing type.
    missing = "E" if any(kind == "P" for kind, _ in typed) and not any(kind == "E" for kind, _ in typed) else "P"
    typed.extend((missing, c) for c in unknown)
    return typed


def _parse_plist_snapshot(data: dict[str, Any]) -> PowerMetricsSnapshot:
    snap = PowerMetricsSnapshot(output=_plist_to_debug_text(data))
    processor = data.get("processor", {}) if isinstance(data.get("processor"), dict) else {}
    gpu = data.get("gpu", {}) if isinstance(data.get("gpu"), dict) else {}

    snap.cpu_power_w = _mw_to_w(processor.get("cpu_energy"))
    snap.gpu_power_w = _mw_to_w(processor.get("gpu_energy"))
    snap.ane_power_w = _mw_to_w(processor.get("ane_energy"))
    snap.system_total_w = _mw_to_w(processor.get("combined_power"))
    if snap.system_total_w is None:
        parts = [v for v in (snap.cpu_power_w, snap.gpu_power_w, snap.ane_power_w) if v is not None]
        snap.system_total_w = round(sum(parts), 2) if parts else None

    p_freqs: list[int] = []
    e_freqs: list[int] = []
    p_active: list[float] = []
    e_active: list[float] = []
    clusters = [c for c in (processor.get("clusters", []) or []) if isinstance(c, dict)]
    for kind, cluster in _classify_clusters(clusters):
        freq = _hz_to_mhz(cluster.get("freq_hz"))
        active = _ratio_to_active(cluster.get("idle_ratio"))
        if kind == "P":
            if freq is not None:
                p_freqs.append(freq)
            if active is not None:
                p_active.append(active)
        elif kind == "E":
            if freq is not None:
                e_freqs.append(freq)
            if active is not None:
                e_active.append(active)
    snap.p_freq_mhz = max(p_freqs) if p_freqs else None
    snap.e_freq_mhz = max(e_freqs) if e_freqs else None

    snap.gpu_freq_mhz = _hz_to_mhz(gpu.get("freq_hz"))
    gpu_active = _ratio_to_active(gpu.get("idle_ratio"))
    if gpu_active is not None:
        snap.gpu_usage = gpu_active

    # powermetrics does not provide reliable ANE utilization on all SoCs; asitop treats ANE mainly by power.
    if snap.ane_power_w is not None:
        snap.ane_usage = min(100.0, max(0.0, snap.ane_power_w / 8.0 * 100.0))

    pressure = str(data.get("thermal_pressure", "")).lower()
    if pressure and pressure not in {"nominal", "normal", "0"}:
        snap.throttle = "yes"
    return snap


def _weighted_frequency_from_residency(line: str) -> int | None:
    pairs = re.findall(r"([\d.,]+)\s*(MHz|GHz)\s*:\s*([\d.]+)%", line, re.I)
    if not pairs:
        return None
    weighted = 0.0
    total = 0.0
    for freq_s, unit, pct_s in pairs:
        freq = float(freq_s.replace(",", ""))
        if unit.lower() == "ghz":
            freq *= 1000
        pct = float(pct_s)
        weighted += freq * pct
        total += pct
    return int(round(weighted / total)) if total > 0 else None


def estimate_cpu_freqs_from_core_residency(output: str, layout: list[str]) -> tuple[int | None, int | None]:
    p_freqs: list[int] = []
    e_freqs: list[int] = []
    for line in output.splitlines():
        m = re.search(r"CPU\s+(\d+)\s+active\s+residency", line, re.I)
        if not m:
            continue
        idx = int(m.group(1))
        freq = _weighted_frequency_from_residency(line)
        if freq is None or idx >= len(layout):
            continue
        typ = layout[idx]
        if typ == "P":
            p_freqs.append(freq)
        elif typ == "E":
            e_freqs.append(freq)
    p = int(round(sum(p_freqs) / len(p_freqs))) if p_freqs else None
    e = int(round(sum(e_freqs) / len(e_freqs))) if e_freqs else None
    return p, e


def parse_powermetrics(output: str | None = None) -> PowerMetricsSnapshot:
    if output is None:
        output = get_powermetrics_output()
        plist = get_powermetrics_plist()
        if plist:
            return _parse_plist_snapshot(plist)
    snap = PowerMetricsSnapshot(output=output or "")
    if not output:
        return snap

    snap.cpu_power_w = _first_power(output, [
        r"CPU\s+Power:\s*([\d.,]+)\s*(uW|µW|mW|W)",
        r"CPU\s*:\s*([\d.,]+)\s*(uW|µW|mW|W)",
    ])
    snap.gpu_power_w = _first_power(output, [
        r"GPU\s+Power:\s*([\d.,]+)\s*(uW|µW|mW|W)",
        r"GPU\s*:\s*([\d.,]+)\s*(uW|µW|mW|W)",
    ])
    snap.ane_power_w = _first_power(output, [
        r"ANE\s+Power:\s*([\d.,]+)\s*(uW|µW|mW|W)",
        r"ANE\s*:\s*([\d.,]+)\s*(uW|µW|mW|W)",
    ])
    snap.system_total_w = _first_power(output, [
        r"System\s+Total:\s*([\d.,]+)\s*(uW|µW|mW|W)",
        r"Average\s+System\s+Total:\s*([\d.,]+)\s*(uW|µW|mW|W)",
        r"Combined\s+Power.*?:\s*([\d.,]+)\s*(uW|µW|mW|W)",
        r"CPU\+GPU\+ANE\s+Power:\s*([\d.,]+)\s*(uW|µW|mW|W)",
    ])
    if snap.system_total_w is None:
        parts = [v for v in (snap.cpu_power_w, snap.gpu_power_w, snap.ane_power_w) if v is not None]
        if parts:
            snap.system_total_w = round(sum(parts), 2)

    snap.p_freq_mhz = _first_int(output, [
        r"P[- ]?Cluster\s+HW\s+active\s+frequency:\s*([\d.,]+)\s*MHz",
        r"P[- ]?Cluster.*?active.*?frequency:\s*([\d.,]+)\s*MHz",
        r"Performance.*?active.*?frequency:\s*([\d.,]+)\s*MHz",
    ])
    snap.e_freq_mhz = _first_int(output, [
        r"E[- ]?Cluster\s+HW\s+active\s+frequency:\s*([\d.,]+)\s*MHz",
        r"E[- ]?Cluster.*?active.*?frequency:\s*([\d.,]+)\s*MHz",
        r"Efficiency.*?active.*?frequency:\s*([\d.,]+)\s*MHz",
    ])
    snap.gpu_freq_mhz = _first_int(output, [
        r"GPU\s+HW\s+active\s+frequency:\s*([\d.,]+)\s*MHz",
        r"GPU.*?active.*?frequency:\s*([\d.,]+)\s*MHz",
        r"GPU.*?frequency:\s*([\d.,]+)\s*MHz",
    ])

    gpu_usage = _first_percent(output, [r"GPU\s+active\s+residency:\s*([\d.]+)%", r"GPU\s+Busy:\s*([\d.]+)%"])
    if gpu_usage is not None:
        snap.gpu_usage = gpu_usage
    ane_usage = _first_percent(output, [r"ANE\s+active\s+residency:\s*([\d.]+)%", r"ANE\s+Busy:\s*([\d.]+)%"])
    if ane_usage is not None:
        snap.ane_usage = ane_usage

    temps: list[float] = []
    for line in output.splitlines():
        if not re.search(r"CPU|core|P-core|E-core|cluster", line, re.I):
            continue
        for match in re.finditer(r"([\d.]+)\s*°?C", line):
            temps.append(float(match.group(1)))
    snap.cpu_temps = temps
    if temps:
        snap.cpu_avg_temp_c = round(sum(temps) / len(temps), 1)

    if re.search(r"thermal pressure:\s*(heavy|serious|critical|yes|true)", output, re.I):
        snap.throttle = "yes"
    elif re.search(r"throttle.*?(yes|true|active)", output, re.I):
        snap.throttle = "yes"
    return snap
