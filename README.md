Macmon

<p align="center">
  <strong>A terminal-based hardware monitoring tool for Apple Silicon Macs</strong>
</p>
<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-macOS-lightgrey">
  <img alt="Apple Silicon" src="https://img.shields.io/badge/Apple%20Silicon-M%20Series-black">
  <img alt="Terminal" src="https://img.shields.io/badge/UI-Terminal-green">
  <img alt="PowerMetrics" src="https://img.shields.io/badge/Data-powermetrics-orange">
</p>

---

[简体中文](/.README_zh_CN.md)

---

Overview

Macmon is a terminal-based hardware monitoring tool designed for Apple Silicon Macs. It provides real-time information about CPU, GPU, ANE, memory, network traffic, power consumption, and operating frequencies.

The project is inspired by tools such as asitop and Stats. It collects system data through native macOS interfaces, including powermetrics, psutil, vm_stat, and ioreg, then presents the data in a compact terminal dashboard.

The goal of this project is to provide a lightweight Apple Silicon performance monitor with terminal-based visualization.

---

Features

CPU Monitoring

* Real-time total CPU usage
* Per-core CPU utilization
* P-Core and E-Core distinction
* Separate P-Core frequency display
* Separate E-Core frequency display
* Real-time CPU power consumption
* Horizontal bar chart visualization for CPU load

GPU and ANE Monitoring

* GPU utilization
* GPU operating frequency
* GPU power consumption
* ANE power consumption
* Bar chart visualization for GPU and ANE status

Memory Monitoring

* Current RAM usage
* Total memory capacity
* Swap usage
* Memory usage history graph
* Adaptive layout for small terminal windows

Network Monitoring

* Real-time download speed
* Real-time upload speed
* Historical network traffic graph
* Adaptive display under different terminal sizes

Power and Frequency Monitoring

* Structured data parsing through powermetrics -f plist
* CPU package power
* GPU power
* ANE power
* Combined system power
* Separate P-Core and E-Core frequency reporting

---

Tech Stack

Module	Technology
Language	Python
Terminal UI	Rich / Textual-style terminal layout
CPU Usage	psutil
Memory Statistics	psutil / vm_stat
Network Throughput	psutil
Power Monitoring	powermetrics
Frequency Monitoring	powermetrics plist
Hardware Information	ioreg
Platform	macOS Apple Silicon

---

Project Structure

```
.
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Chinese documentation
├── README_EN.md                # English documentation
│
├── core/                       # Core data collection logic
│   ├── collectors/             # Hardware collectors
│   │   ├── cpu.py              # CPU usage, P/E-core frequency and power
│   │   ├── gpu.py              # GPU usage, frequency and power
│   │   ├── memory.py           # RAM and swap statistics
│   │   ├── network.py          # Upload and download speed
│   │   └── temperature.py      # Temperature collection
│   │
│   ├── powermetrics.py         # powermetrics plist parser
│   └── state.py                # Runtime state cache
│
├── ui/                         # Terminal interface
│   ├── dashboard.py            # Main dashboard layout
│   ├── widgets.py              # Bars, graphs and display widgets
│   └── theme.py                # Colors and visual style
│
└── scripts/                    # Helper scripts
    └── run.sh                  # Launch script
```

---

Runtime Environment

Recommended environment:

* macOS 13+
* Apple Silicon Mac, including M1 / M2 / M3 / M4 series
* Python 3.10+
* Terminal with Unicode support
* User account with sudo permission

Since power and frequency data depend on Apple powermetrics, this project is mainly intended for Apple Silicon Macs. Intel Macs, Windows, and Linux cannot fully support the power and frequency monitoring features.

---

Installation

It is recommended to create a virtual environment first:

python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

---

Running the Project

Because powermetrics requires administrator privileges, run the following command before starting Macmon:

sudo -v

Then start the program:

python main.py

Alternatively, use the launch script:

./scripts/run.sh

If the script is not executable, run:

chmod +x scripts/run.sh

---

Refresh Rate Configuration

There are usually two types of refresh intervals in this project.

UI Refresh Interval

This controls how often the terminal dashboard is updated.

You can usually find a value similar to:

REFRESH_INTERVAL = 1.0

The unit is seconds.

For example:

REFRESH_INTERVAL = 0.5

means that the interface refreshes every 0.5 seconds.

powermetrics Sampling Interval

This controls how often power and frequency data are sampled.

You can usually find a command similar to:

powermetrics -i 1000

The unit is milliseconds.

For example:

powermetrics -i 500

means that powermetrics samples data every 500 milliseconds.

It is not recommended to set this value too low, as powermetrics itself may introduce noticeable CPU overhead.

---

Data Sources

powermetrics

Used for collecting:

* CPU Power
* GPU Power
* ANE Power
* Combined Power
* P-Core Frequency
* E-Core Frequency
* GPU Frequency

The project prefers:

powermetrics -f plist

Compared with plain-text output, plist output is more structured and more stable across different macOS versions and Apple Silicon chips.

psutil

Used for collecting:

* CPU utilization
* Per-core utilization
* Memory usage
* Network upload and download bytes
* System uptime

vm_stat

Used as a supplementary source for macOS memory paging and swap information.

ioreg

Used to read selected Apple Silicon hardware, battery, and sensor-related information.

---

FAQ

Why are power or frequency values displayed as N/A?

Common causes include:

1. Missing administrator permission
2. powermetrics is blocked by macOS
3. The current macOS version changed the output fields
4. The device is not an Apple Silicon Mac
5. The sampling interval is too short and no valid data has returned yet

You can test powermetrics directly:

sudo powermetrics -n 1 -f plist

If this command does not return valid data, Macmon cannot read power and frequency information either.

Why does Macmon separate P-Core and E-Core frequency?

Apple Silicon uses a hybrid CPU architecture with performance cores and efficiency cores. P-Cores are designed for high-performance workloads, while E-Cores handle lighter or background tasks with lower power consumption. Showing them separately makes the system load distribution clearer.

Why is sudo required?

powermetrics accesses low-level performance and power counters. macOS requires administrator permission for this operation.

Is Control+C a normal way to exit?

Yes. The project treats KeyboardInterrupt as a normal exit and should not print a Python traceback when the user presses Control+C.

---

References

This project is inspired by:

* asitop
* Stats
* Apple powermetrics
* macOS system utilities

---

License

MIT License © 2026 Caerulues
