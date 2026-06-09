from __future__ import annotations

import math
from typing import Iterable

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

CPU_P_STYLE = "bright_blue"
CPU_E_STYLE = "cyan"
GPU_STYLE = "blue"
ANE_STYLE = "magenta"
MEM_STYLE = "orange3"
UPLOAD_STYLE = "blue"
DOWNLOAD_STYLE = "red"
TEXT_STYLE = "white"
DIM_STYLE = "grey37"
TEMP_STYLE = "yellow"


def fmt_w(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f} W"


def fmt_temp(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1f}°C"


def fmt_freq(value: int | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1000:
        return f"{value / 1000:.2f} GHz"
    return f"{value} MHz"


def usage_bar(percent: float, width: int, style: str) -> Text:
    percent = max(0.0, min(100.0, percent))
    filled = int(round(width * percent / 100))
    t = Text()
    t.append("█" * filled, style=style)
    t.append("░" * max(0, width - filled), style=DIM_STYLE)
    return t


def _chunked(items: list[dict], max_rows: int = 5) -> list[list[dict]]:
    return [items[i : i + max_rows] for i in range(0, len(items), max_rows)] or [[]]


def horizontal_usage_columns(items: list[dict], max_rows: int = 5, bar_width: int = 12, column_gap: int = 2) -> Table:
    chunks = _chunked(items, max_rows)
    table = Table.grid(expand=True, padding=(0, column_gap))
    for _ in chunks:
        table.add_column(ratio=1, no_wrap=True)

    rows = []
    for row_idx in range(max_rows):
        row_cells = []
        for chunk in chunks:
            if row_idx >= len(chunk):
                row_cells.append(Text(""))
                continue
            item = chunk[row_idx]
            typ = item.get("type", "U")
            idx = item.get("index", 0)
            usage = float(item.get("usage", 0.0))
            if typ == "P":
                style = CPU_P_STYLE
                label = f"P{idx}"
            elif typ == "E":
                style = CPU_E_STYLE
                label = f"E{idx}"
            elif typ == "ANE":
                style = ANE_STYLE
                label = "ANE"
            else:
                style = GPU_STYLE
                label = f"G{idx}"
            cell = Text()
            cell.append(f"{label:<4}", style="bold " + style)
            cell.append(usage_bar(usage, bar_width, style))
            cell.append(f" {usage:>3.0f}%", style=TEXT_STYLE)
            row_cells.append(cell)
        rows.append(row_cells)

    for row in rows:
        table.add_row(*row)
    return table


def cpu_panel(cpu: dict) -> Panel:
    cores = cpu.get("cores", [])
    header = Text()
    header.append(f"Total {cpu.get('total', 0):.0f}%  ", style=TEXT_STYLE)
    header.append(f"E {cpu.get('e_avg', 0):.0f}% @ {fmt_freq(cpu.get('e_freq'))}  ", style=CPU_E_STYLE)
    header.append(f"P {cpu.get('p_avg', 0):.0f}% @ {fmt_freq(cpu.get('p_freq'))}", style=CPU_P_STYLE)

    grid = Table.grid(expand=True)
    grid.add_row(header)
    grid.add_row(horizontal_usage_columns(cores, max_rows=5, bar_width=20, column_gap=5))
    return Panel(grid, title="CPU", border_style=DIM_STYLE, expand=True)


def gpu_ane_panel(gpu: dict, ane: dict) -> Panel:
    items = list(gpu.get("cores", [])) + list(ane.get("cores", []))
    header = Text()
    header.append(f"GPU {gpu.get('usage', 0):.0f}% @ {fmt_freq(gpu.get('freq'))}  ", style=GPU_STYLE)
    header.append(f"ANE {ane.get('usage', 0):.0f}%", style=ANE_STYLE)

    grid = Table.grid(expand=True)
    grid.add_row(header)
    grid.add_row(horizontal_usage_columns(items, max_rows=5, bar_width=20, column_gap=5))
    return Panel(grid, title="GPU + ANE", border_style=DIM_STYLE, expand=True)


def memory_history_chart(values: list[float], width: int, height: int = 8) -> Text:
    if width <= 0:
        width = 20
    values = values[-width:] or [0.0]
    max_width_values = values + [values[-1]] * max(0, width - len(values))
    lines: list[Text] = []
    for row in reversed(range(height)):
        threshold = row / height * 100
        line = Text()
        for value in max_width_values:
            if value >= threshold:
                line.append("█", style=MEM_STYLE)
            else:
                line.append(" ")
        lines.append(line)
    out = Text()
    for line in lines:
        out.append_text(line)
        out.append("\n")
    out.append("─" * width, style=DIM_STYLE)
    return out


def memory_panel(memory: dict, console_width: int) -> Panel:
    width = max(30, console_width - 8)
    text = Text()
    text.append(
        f"RAM Usage: {memory.get('used_gb', 0):.1f}/{memory.get('total_gb', 0):.1f} GB - swap {memory.get('swap', 'inactive')}\n",
        style=TEXT_STYLE,
    )
    text.append_text(memory_history_chart(memory.get("history", []), width=width, height=6))
    return Panel(text, title="Memory", border_style=DIM_STYLE)


def internet_chart(up_values: list[float], down_values: list[float], width: int, height: int = 9) -> Text:
    width = max(30, width)
    up_values = (up_values[-width:] or [0.0])
    down_values = (down_values[-width:] or [0.0])
    if len(up_values) < width:
        up_values = [0.0] * (width - len(up_values)) + up_values
    if len(down_values) < width:
        down_values = [0.0] * (width - len(down_values)) + down_values
    max_abs = max(max(up_values, default=0.0), max(down_values, default=0.0), 1.0)
    top_rows = height // 2
    bottom_rows = height // 2
    rows = [[(" ", None) for _ in range(width)] for _ in range(top_rows + 1 + bottom_rows)]
    baseline = top_rows
    for x, value in enumerate(up_values):
        h = int(round(value / max_abs * top_rows))
        for y in range(baseline - h, baseline):
            if 0 <= y < len(rows):
                rows[y][x] = ("█", UPLOAD_STYLE)
    for x, value in enumerate(down_values):
        h = int(round(value / max_abs * bottom_rows))
        for y in range(baseline + 1, baseline + 1 + h):
            if 0 <= y < len(rows):
                rows[y][x] = ("█", DOWNLOAD_STYLE)
    for x in range(width):
        rows[baseline][x] = ("─", DIM_STYLE)
    out = Text()
    for row in rows:
        for ch, style in row:
            out.append(ch, style=style) if style else out.append(ch)
        out.append("\n")
    return out


def internet_panel(net: dict, console_width: int) -> Panel:
    width = max(30, console_width - 8)
    text = Text()
    text.append(f"↑ {net.get('upload', 'N/A')}\n", style=UPLOAD_STYLE)
    text.append_text(internet_chart(net.get("upload_history", []), net.get("download_history", []), width=width, height=6))
    text.append(f"↓ {net.get('download', 'N/A')}", style=DOWNLOAD_STYLE)
    return Panel(text, title="Internet", border_style=DIM_STYLE)


def power_panel(power: dict, cpu: dict, gpu: dict) -> Panel:
    table = Table.grid(expand=True)
    table.add_column(ratio=1)
    table.add_column(ratio=2)
    rows = [
        ("Power", f"CPU {fmt_w(power.get('cpu'))} | P {fmt_freq(cpu.get('p_freq'))} | E {fmt_freq(cpu.get('e_freq'))}", TEXT_STYLE),
        ("", f"GPU {fmt_w(power.get('gpu'))} @ {fmt_freq(gpu.get('freq'))}", TEXT_STYLE),
        ("", f"ANE {fmt_w(power.get('ane'))}", TEXT_STYLE),
        ("", f"System Total {fmt_w(power.get('system_total'))}", TEXT_STYLE),
    ]
    for left, right, style in rows:
        table.add_row(Text(left, style="bold " + style if left else style), Text(right, style=style))
    return Panel(table, title="Power", border_style=DIM_STYLE)
