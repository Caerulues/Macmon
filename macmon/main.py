from __future__ import annotations

import argparse
import time

from rich.console import Console
from rich.live import Live

from macmon.collectors.cpu import get_cpu_summary
from macmon.collectors.gpu import get_ane_info, get_gpu_info
from macmon.collectors.hardware import get_hardware_summary
from macmon.collectors.memory import get_memory_info
from macmon.collectors.network import get_network_info
from macmon.collectors.power import get_power_info
from macmon.ui.dashboard import build_dashboard
from macmon.collectors.powermetrics import get_powermetrics_output, parse_powermetrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal hardware monitor for macOS")
    parser.add_argument("--interval", type=float, default=1.0, help="refresh interval in seconds")
    parser.add_argument("--no-screen", action="store_true", help="do not use alternate screen")
    parser.add_argument("--debug-powermetrics", action="store_true", help="print raw powermetrics lines used for parsing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    console = Console()
    if args.debug_powermetrics:
        output = get_powermetrics_output()
        snap = parse_powermetrics(output)
        console.print("Parsed powermetrics:", style="bold")
        console.print(f"P freq: {snap.p_freq_mhz} MHz | E freq: {snap.e_freq_mhz} MHz | GPU freq: {snap.gpu_freq_mhz} MHz")
        console.print(f"CPU power: {snap.cpu_power_w} W | GPU power: {snap.gpu_power_w} W | ANE power: {snap.ane_power_w} W | Total: {snap.system_total_w} W")
        console.print("\nRaw related lines:", style="bold")
        for line in output.splitlines():
            if any(key.lower() in line.lower() for key in ("frequency", "freq", "residency", "power", "CPU ", "GPU", "ANE")):
                console.print(line)
        return

    chip = get_hardware_summary()
    # Warm up psutil rate counters.
    get_cpu_summary()
    get_network_info()
    try:
        with Live(console=console, refresh_per_second=10, screen=not args.no_screen) as live:
            while True:
                cpu = get_cpu_summary()
                gpu = get_gpu_info()
                ane = get_ane_info()
                memory = get_memory_info()
                net = get_network_info()
                power = get_power_info()
                live.update(
                    build_dashboard(
                        cpu=cpu,
                        gpu=gpu,
                        ane=ane,
                        memory=memory,
                        net=net,
                        power=power,
                        chip=chip,
                        console_width=console.width
                    )
                )
                time.sleep(args.interval)
                
    except KeyboardInterrupt:
        console.clear()
        console.print("Macmon exited.", style="dim")




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMacmon exited.")
