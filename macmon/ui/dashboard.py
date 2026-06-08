from __future__ import annotations

from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from macmon.ui.widgets import (
    cpu_panel,
    gpu_ane_panel,
    internet_panel,
    memory_panel,
    power_panel,
)


def build_dashboard(
    *,
    cpu: dict,
    gpu: dict,
    ane: dict,
    memory: dict,
    net: dict,
    power: dict,
    chip: str,
    console_width: int,
):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top", ratio=2, minimum_size=13),
        Layout(name="memory", ratio=2),
        Layout(name="internet", ratio=2),
        Layout(name="bottom", size=9),
    )
    layout["header"].update(Panel(Text(chip, style="bold white"), border_style="grey37"))
    layout["top"].split_row(
        Layout(cpu_panel(cpu), name="cpu", ratio=3, minimum_size=42),
        Layout(gpu_ane_panel(gpu, ane), name="gpu_ane", ratio=2, minimum_size=34),
    )
    layout["memory"].update(memory_panel(memory, console_width=console_width))
    layout["internet"].update(internet_panel(net, console_width=console_width))
    layout["bottom"].update(power_panel(power, cpu, gpu))
    return layout
