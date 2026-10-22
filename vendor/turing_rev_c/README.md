# 上游 rev C 通信库

本目录保留 [mathoudebine/turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python)
提交 `2b33ab4f00a096916dd6a1174441a53a7ec33b03` 中运行 rev C 所需的原始文件：
`library/log.py`、`library/lcd/{color,lcd_comm,lcd_comm_rev_c,serialize}.py`。
原文件保留 SPDX 与版权标头，许可证见 `LICENSE`（GPL-3.0-or-later）。
本项目代码也按 GPL-3.0-or-later 发布。项目入口只使用显式串口路径，
不调用上游自动探测、重置、亮度或灯光函数。唯一的上游文件改动是
`library/log.py`：把日志位置固定到项目根目录，避免在其他目录写文件。

