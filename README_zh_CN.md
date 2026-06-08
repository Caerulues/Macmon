Macmon

<p align="center">
  <strong>一个面向 Apple Silicon Mac 的终端硬件监控工具</strong>
</p>
<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-macOS-lightgrey">
  <img alt="Apple Silicon" src="https://img.shields.io/badge/Apple%20Silicon-M%20Series-black">
  <img alt="Terminal" src="https://img.shields.io/badge/UI-Terminal-green">
  <img alt="PowerMetrics" src="https://img.shields.io/badge/Data-powermetrics-orange">
</p>

---

项目简介

Macmon 是一个运行在 macOS 终端中的 Apple Silicon 硬件监控工具，主要用于实时查看 M 系列芯片的 CPU、GPU、ANE、内存、网络、功耗和运行频率等状态。

项目参考了 asitop、Stats 等工具的数据采集思路，使用 powermetrics、psutil、vm_stat、ioreg 等 macOS 原生接口获取系统数据，并通过终端仪表盘进行可视化展示。

本项目的定位是一个偏向 Apple Silicon 性能监控 + 终端可视化面板 的轻量级工具。

---

功能特性

CPU 监控

* 实时显示 CPU 总占用率
* 显示每个 CPU 核心的占用情况
* 区分 P-Core 与 E-Core
* 分别显示 P-Core 运行频率
* 分别显示 E-Core 运行频率
* 显示 CPU 实时功耗
* 支持横向条形统计图展示核心负载

GPU 与 ANE 监控

* 显示 GPU 使用率
* 显示 GPU 运行频率
* 显示 GPU 实时功耗
* 显示 ANE 实时功耗
* 使用条形统计图展示 GPU / ANE 状态

内存监控

* 显示当前 RAM 使用量
* 显示总内存容量
* 显示 Swap 使用状态
* 显示内存历史变化曲线
* 小窗口下自动压缩展示区域

网络监控

* 实时显示上传速率
* 实时显示下载速率
* 显示网络流量历史变化
* 支持窗口缩放下的自适应显示

功耗与频率监控

* 使用 powermetrics -f plist 读取结构化数据
* 支持 CPU Package Power
* 支持 GPU Power
* 支持 ANE Power
* 支持 Combined Power
* 支持 P-Core / E-Core 分离频率显示

---

技术栈

模块	技术
编程语言	Python
终端 UI	Rich / Textual 风格终端布局
CPU 使用率	psutil
内存统计	psutil / vm_stat
网络速率	psutil
功耗采集	powermetrics
频率采集	powermetrics plist
硬件信息	ioreg
系统平台	macOS Apple Silicon

---

项目结构

```
.
├── main.py                     # 程序启动入口
├── requirements.txt            # Python 依赖列表
├── README.md                   # 中文说明文档
├── README_EN.md                # 英文说明文档
│
├── core/                       # 核心数据采集逻辑
│   ├── collectors/             # 各硬件模块采集器
│   │   ├── cpu.py              # CPU 占用率、P/E 核频率与功耗
│   │   ├── gpu.py              # GPU 使用率、频率与功耗
│   │   ├── memory.py           # RAM 与 Swap 统计
│   │   ├── network.py          # 上传 / 下载速率统计
│   │   └── temperature.py      # 温度数据采集
│   │
│   ├── powermetrics.py         # powermetrics plist 解析
│   └── state.py                # 运行时状态缓存
│
├── ui/                         # 终端界面
│   ├── dashboard.py            # 主仪表盘布局
│   ├── widgets.py              # 条形图、曲线图等组件
│   └── theme.py                # 颜色与显示样式
│
└── scripts/                    # 辅助脚本
    └── run.sh                  # 启动脚本
```

---

运行环境

建议环境：

* macOS 13+
* Apple Silicon Mac，包含 M1 / M2 / M3 / M4 系列
* Python 3.10+
* 终端支持 Unicode 字符显示
* 当前用户具有 sudo 权限

由于功耗和频率数据依赖 Apple 的 powermetrics，本项目主要面向 Apple Silicon Mac。Intel Mac、Windows 或 Linux 无法完整使用本项目的功耗与频率监控功能。

---

安装依赖

建议先创建虚拟环境：

python3 -m venv .venv
source .venv/bin/activate

安装依赖：

pip install -r requirements.txt

---

启动项目

由于 powermetrics 需要管理员权限，启动前建议先执行：

sudo -v

然后运行：

python main.py

也可以使用启动脚本：

./scripts/run.sh

如果脚本没有执行权限，可以先运行：

chmod +x scripts/run.sh

---

刷新频率设置

项目中通常存在两类刷新频率。

UI 刷新间隔

用于控制终端界面多久刷新一次。

通常可以在配置或主循环中找到：

REFRESH_INTERVAL = 1.0

单位为秒。

例如改为：

REFRESH_INTERVAL = 0.5

表示每 0.5 秒刷新一次界面。

powermetrics 采样间隔

用于控制系统功耗和频率数据多久采样一次。

通常可以找到：

powermetrics -i 1000

单位为毫秒。

例如：

powermetrics -i 500

表示每 500 毫秒采样一次。

不建议设置得过低，否则 powermetrics 本身可能产生较高 CPU 占用。

---

数据来源说明

powermetrics

主要用于获取：

* CPU Power
* GPU Power
* ANE Power
* Combined Power
* P-Core Frequency
* E-Core Frequency
* GPU Frequency

项目优先使用：

powermetrics -f plist

相比普通文本输出，plist 结构更稳定，更适合在不同 macOS 版本和不同 M 系列芯片上解析。

psutil

主要用于获取：

* CPU 使用率
* 每核心占用率
* 内存使用量
* 网络上传 / 下载字节数
* 系统运行时间

vm_stat

用于补充 macOS 内存分页与 Swap 信息。

ioreg

用于读取部分 Apple Silicon 硬件、电池和传感器相关信息。

---

常见问题

为什么功耗或频率显示 N/A？

常见原因包括：

1. 没有管理员权限
2. powermetrics 被系统拒绝执行
3. 当前 macOS 版本输出字段发生变化
4. 设备不是 Apple Silicon Mac
5. 采样间隔太短导致数据还没有返回

可以先测试：

sudo powermetrics -n 1 -f plist

如果该命令本身无法正常输出，Macmon 也无法获取功耗和频率数据。

为什么 CPU 分成 P-Core 和 E-Core？

Apple Silicon 使用性能核心和能效核心的混合架构。P-Core 更偏向高性能任务，E-Core 更偏向低功耗后台任务。分开显示可以更清楚地观察系统当前负载分布。

为什么需要 sudo？

powermetrics 读取的是系统底层性能与功耗计数器，macOS 要求管理员权限才能访问。

Control+C 退出是否正常？

正常。项目会捕获 KeyboardInterrupt，将其视为正常退出，不应输出 Python Traceback。

---

开发路线图

计划支持：

* 更完整的温度传感器解析
* 风扇转速显示
* 电池功耗显示
* 电池循环次数显示
* 监控数据导出为 CSV
* 长时间功耗曲线记录
* Web Dashboard
* 配置文件自定义布局
* 更多 Apple Silicon 型号适配

---

参考项目

本项目实现思路参考：

* asitop
* Stats
* Apple powermetrics
* macOS system utilities

---

许可

MIT License © 2026 Caerulues
