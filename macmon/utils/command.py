from __future__ import annotations

import subprocess


def run(cmd: list[str], timeout: float = 3.0) -> str:
    try:
        return subprocess.check_output(
            cmd,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        ).strip()
    except Exception:
        return ""
