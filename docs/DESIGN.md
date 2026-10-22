# 先马 XW360W 水冷屏幕：Debian 设计与施工方案

日期：2026-10-22；目标机器：Debian 13.7、Ryzen 7 7700X、先马 XW360W 水冷、Windows 11 双系统。

## 1. 目标、依据与待确认事项

目标：在 Debian 启动并进入桌面后，让水冷头的 LCD 显示实时 CPU 温度、总占用率；在设备能力确认后，可选增加频率、时钟及背景主题。先做清晰稳定的原型，显示样式参考先马官网和现有 Windows 控制程序。

先马官网将 **XW360W（无风扇版）**描述为带可自定义 IPS 屏的水冷，并提供适用于 XW 等系列的屏幕控制软件。但官网页面没有给出这台水冷的 USB 设备 ID、显示分辨率、通信协议、Linux 驱动接口和屏幕断电后的行为。用户手中的产品是否为官网这个具体版本，也需用外观、包装型号或软件信息确认。不能把其他型号（包括 XW360W-P、二代或其他品牌）的协议、尺寸或主题直接当成本机规格。

官方参考：

- [XW360W 产品页](https://www.sama.cn/archives/6829)
- [先马屏幕软件下载页](https://www.sama.cn/sanre/download)
- [XW 等系列屏幕软件说明页](https://www.sama.cn/archives/8935)

## 2. 项目位置与目录分工

**Debian 机器的建议仓库根目录：`/home/renping/projects/sama-xw360w-lcd/`。** 这是未来在用户电脑上运行 Codex 时使用的绝对路径；这份设计文件本身不会自动在该机器创建该目录。不要在 `/usr`、`/etc`、`/boot`、EFI 分区或 Windows 分区里写开发文件。

```text
/home/renping/projects/sama-xw360w-lcd/
├── README.md                 # 状态、用法、已验证的硬件信息
├── docs/
│   ├── DESIGN.md             # 本方案的本机副本及调整记录
│   ├── HARDWARE.md           # Linux/Windows 设备标识与接口证据
│   └── PROTOCOL.md           # 已验证的数据包、屏幕行为与未知项
├── captures/
│   └── README.md             # 采集记录；原始包默认不入 Git
├── assets/
│   └── themes/               # 自制或获准使用的背景素材
├── src/sama_lcd/
│   ├── discovery.py          # 识别设备、接口与权限
│   ├── metrics.py            # CPU 温度、占用率等采样
│   ├── render.py             # 在确认屏幕格式后渲染画面
│   ├── transport.py          # HID/串口/其他实际接口的发送层
│   ├── app.py                # 主循环、重连、日志、优雅退出
│   └── cli.py                # 检测、单帧试验、运行命令
├── tests/                    # 协议编码及渲染的离线测试
├── packaging/                # 经验证后使用的 udev/systemd 示例
├── pyproject.toml            # Python 依赖和命令入口
└── .gitignore                # 排除抓包、虚拟环境和个人素材
```

由 Codex 在 Debian 本机创建上述目录并初始化 Git；首次建仓时将当前方案复制为 `docs/DESIGN.md`。如果用户已有统一的编程项目目录，只改仓库根目录，内部结构保持一致。

## 3. 阶段与验收门槛

### A. 只读识别（先做）

1. 核对包装型号、屏幕形状、Windows 程序名与当前显示效果；记录 Windows **Device Manager → 设备属性 → Details → Hardware Ids**（设备可能归在 USB、HID、Ports 或显示设备）。
2. Debian 记录 `lsusb`、USB 树、冷头对应接口、内核绑定驱动以及 `/dev/hidraw*`、`/dev/tty*` 等映射；用 VID:PID、设备路径和插拔前后变化确认归属。避免看到某个 HID 就断定它是冷头。
3. 核实温度来源（Ryzen 7 7700X 优先核对 `k10temp` 的标注读数）及 CPU 总占用率；比较 GNOME 监控/传感器输出，记录单位和刷新率。

**门槛 A：** `docs/HARDWARE.md` 有证据支持设备归属、接口类型和指标来源。如果 Debian 看不到对应 USB 设备，先核对线缆和 Windows 设备枚举；不进入发送阶段。

### B. 协议确认（只处理屏幕）

1. 先查是否有**相同 VID:PID 且同一控制程序/固件族**的现成开源实现，检查许可证与实测范围。型号相似不能证明协议兼容。
2. 若无公开协议，在 Windows 官方程序正常显示时，用 Wireshark + USBPcap 采集 **只属于已核对设备** 的 USB 通信；依次记录静止画面、切换官方主题、替换背景、CPU 负载变化和退出程序的差异。或者在法律与许可范围内分析官方程序的数据格式；记录观察结果和自己的实现，不复制专有素材或代码。
3. 写出传输类别（HID report、USB bulk/control、串口，或其他）、端点、包长度、初始化顺序、像素/压缩格式、坐标、频率与断线处理。核实是否能实时传图，还是只能设置固件内主题并传递数值。

**门槛 B：** `docs/PROTOCOL.md` 有足以重放的一次已知安全画面/数据交互。未知时停在调查阶段，不能试探性地乱发数据包，更不能向风扇、泵或固件控制端点写入。

### C. 最小可用程序

1. Python 程序先实现 `detect`（只读）、`show-once`（已验证协议的单帧试验），然后 `run`（持续更新）；传输层隔离协议细节，测试时用虚拟设备替身。
2. 从 Linux `hwmon` 读取核对过的温度通道；总占用率采用两次 `/proc/stat` 采样的时间差计算。数据缺失显示 `--`，不能伪造 0°C。设置合理更新频率（初期约 1 秒一次，按实测传输能力调整），不让监控程序影响水冷工作。
3. 先以纯色背景、大字号的 `CPU  °C` 和 `LOAD  %` 试屏；核实方向、裁切、色彩、开机后首次显示和停止程序的画面行为。频率与动画属于下一步可选项。

**门槛 C：** 数值与 Debian 本机读数一致；持续运行、睡眠唤醒/重新登录和 USB 短暂失联时可恢复；退出时不影响水泵及散热控制。

### D. 样式与部署

1. 在确认真实屏幕尺寸和刷新/吞吐限制后制作适配布局；参考官网配色和信息层级。若官方主题/图像需要复制，先确认有权使用；默认采用自行绘制背景。
2. 用户确认具体版式后再加主题配置、静态背景、字体及可选时钟/频率。避免屏幕小而信息拥挤。
3. 先前台运行，验收后才创建针对**已确认 VID:PID** 的最小权限 udev 规则和 systemd 用户服务；设备尚未确认前，不预设通配 USB 权限，也不使用长期 root 进程。
4. 文档包含安装、停止、故障日志、卸载/回退步骤；独立的 Git 提交保留每个可工作的阶段。

**门槛 D：** Debian 登录后屏幕自动显示；重启、退出程序、Windows 回切的行为均实测；停止服务可撤销改动。

## 4. 第一轮需要用户提供的最少信息

在 Debian 的终端运行下列**只读**命令，把完整输出发给 Codex/本对话：

```bash
lsusb
lsusb -t
sensors
```

- `lsusb`：列出 USB 设备及厂商/产品 ID；无参数。
- `lsusb -t`：以树状结构列出 USB 连接及接口驱动；`-t` 表示 tree。
- `sensors`：列出可见的温度、风扇等传感器；无参数。若显示“command not found”，先反馈这一信息，不急着安装或扫描硬件。

另需 Windows 官方软件的界面截图（展示主题与读数）以及上述 Hardware Ids。截图尽量不含个人信息；抓包和程序安装放在 B 阶段。若 `lsusb` 有多个无法区分的候选，下一轮再按输出制定准确的只读定位命令。

## 5. 给 Debian 本机 Codex 的任务说明

> 工作目录 `/home/renping/projects/sama-xw360w-lcd/`。先阅读 `docs/DESIGN.md`；不要假定当前 USB 设备与其他 XW 型号或网上项目协议一致。第一轮仅创建项目结构、Git 仓库、只读检测与 `docs/HARDWARE.md`；核对 `lsusb`、USB 接口和 CPU 温度来源，列出仍需 Windows 侧提供的证据。设备和传输协议未证实之前，不写设备、不设置 udev 权限、不启用常驻服务，也不改动风扇、水泵、固件或 Windows 分区。证实协议后，按门槛 B–D 逐步提交和实机验收。

## 6. 资料来源和证据边界

- 先马官网产品页与软件下载页：确认该系列存在自定义屏与官方控制软件；**未给出本机协议**。
- [Linux 内核 hwmon 接口文档](https://docs.kernel.org/hwmon/sysfs-interface.html)：温度输入一般以毫摄氏度表示；实际通道仍要以本机标签核实。
- [Wireshark USB 抓取说明](https://wiki.wireshark.org/CaptureSetup/USB)：Windows 可借助 USBPcap 捕获 USB 传输；抓包本身不意味着已理解格式。
- 其他品牌基于特定 USB ID 的 Linux 工具只可作为逆向方法参考；未经设备匹配，不作为 XW360W 的现成驱动。

## 7. 2026-10-22 第一轮实机输出与计划调整

用户提供的 Debian 截图显示：

- `sensors` 中 `k10temp-pci-00c3` 的 `Tctl` 为 40.9°C、`Tccd1` 为 32.8°C。CPU 温度来源已经存在；本项目先以 `Tctl` 为显示候选，待和 BIOS/Windows 显示口径核对。`spd5118` 的约 40°C 是内存温度，不能误当 CPU 温度。
- `lsusb` 的 **Bus 003 Device 006** 为 `1d6b:0121 Linux Foundation Android`；在 `lsusb -t` 中对应 **Bus 003 Port 010**，接口由 `cdc_acm` 驱动绑定，属 USB 虚拟串口类别。尚未证明这个物理设备就是水冷屏。
- [AIDA64 LCD Guide 的 Turing 部分](https://download.aida64.com/resources/lcd/aida64_lcd_guide.pdf)列出 `1d6b:0121`，并将其列在使用虚拟串口/WinUSB 的 Turing 屏 ID 之中。[InfoPanel-linux 项目](https://github.com/emaspa/InfoPanel-linux)明确把 `1d6b:0121` 列为 Turing Smart Screen 2.1 英寸、480×480 的串口版本。**这些是匹配线索，不是 XW360W 屏幕型号或分辨率的证明。**

调查优先级因此改为：先获取 `3-10` 的设备描述、产品/序列号及对应的 `/dev/ttyACM*`，交叉核对 Windows Device Manager 的 Hardware Ids 和实际冷头外观；匹配后先评估同类开源串口协议/实现，再决定是否需要 Windows USBPcap 抓包。切勿在尚未确认的 `/dev/ttyACM*` 上写入试验数据。

**下一条只读命令**（在用户 Debian 终端执行）：

```bash
udevadm info --query=property --path=/sys/bus/usb/devices/3-10
```

`udevadm info` 查询设备资料；`--query=property` 仅列出该设备的属性；`--path=...` 指向截图中 Bus 003 Port 010 的内核设备路径。此命令不改动设备。若重启或重新插拔后 USB 端口变了，先重新核对 `lsusb -t`，不可继续使用旧路径。

## 8. 2026-10-22 第二轮设备属性与实现路线修订

用户的 `udevadm info` 截图确认 Bus 003 Port 010 的属性：`PRODUCT=1d6b/121/ffff`、`ID_MODEL=Android`、`ID_SERIAL_SHORT=20080411`、`ID_USB_INTERFACES=:020201:0a0000:`。结合前一张 USB 树截图中的 `cdc_acm`，这个设备作为 USB 虚拟串口出现。

[Lamiore/aio-lcd](https://github.com/Lamiore/aio-lcd) 的实机记录表明，某一款其他品牌 AIO 水冷屏在唤醒后同样是 `1d6b:0121`、序列号 `20080411`，且由 [mathoudebine/turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) 的 Turing 2.1 英寸驱动支持。两项同时吻合使“同一 Turing 兼容屏模组”成为高可信候选；但用户冷头尚未经屏幕实机命令验证，不能把其确认为某个具体分辨率或固件修订。

**路线调整：** 优先阅读、审查、试用上游成熟的 Linux 串口显示库及其设备探测方式。Codex 的独立工作应集中于本机设备确认、稳定的传感器采样、专用显示布局/背景与服务封装。如果上游协议实机可用，直接依赖其传输实现；若需复制或改动 GPL-3.0 代码，遵守其许可证，并在仓库记录来源与版本。原计划中的 Windows USBPcap 抓包只作为兼容性检查失败后的备选。

**下一步只读命令：**

```bash
ls -l /dev/serial/by-id/
```

`ls` 列出目录；`-l` 显示详细信息及符号链接目标。该目录通常把 USB 产品/序列号映射到如 `/dev/ttyACM0` 的实际串口。重点找包含 `20080411` 的那一行；`ttyACM` 编号可能变化，不能硬编码。若该目录不存在，下一步改用已识别的 USB 路径查询，无需安装软件。

## 9. 2026-10-22 串口映射确认与 Codex 实施任务

用户实机输出：

```text
usb-Android_Android_20080411-if00 -> ../../ttyACM1
usb-LG_Electronics_Inc._LG_Monitor_Controls_FEDF0400D486-if02 -> ../../ttyACM0
```

因此 `20080411` 当前映射到 `/dev/ttyACM1`，而 `/dev/ttyACM0` 属于 LG 显示器控制接口。后续代码选用 `/dev/serial/by-id/usb-Android_Android_20080411-if00` 作为稳定设备路径；不要把 `ttyACM1` 写死进程序或权限规则。

### 可直接交给 Debian 本机 Codex 的任务

> 在 `/home/renping/projects/sama-xw360w-lcd/` 建项目并实现先马 XW360W 的 Linux 水冷头屏幕应用。已知用户的 USB 串口路径为 `/dev/serial/by-id/usb-Android_Android_20080411-if00`，指向 `/dev/ttyACM1`；`ttyACM0` 是 LG 显示器，严禁写入。USB ID `1d6b:0121`、序列号 `20080411` 与其他水冷品牌使用的 Turing 2.1 英寸屏匹配，但 XW360W 尚未实机试屏。CPU 温度参考 `k10temp` 的 `Tctl`。先审查 `mathoudebine/turing-smart-screen-python` 的协议实现、许可证、硬件修订探测与安装说明，作为独立上游依赖或参考；不要直接运行未知第三方安装脚本。第一阶段仅在用户目录中完成虚拟环境、配置与最小前台试屏；确认只打开上述设备路径，先显示纯色或静态 `CPU`，核对分辨率、方向、颜色和权限。如设备报告不匹配或需要系统级变更，请记录证据与建议，不向别的串口、泵或风扇发送数据。成功后实现独立的简洁界面：CPU `Tctl` 摄氏温度、CPU 总占用率，每秒更新；传感器缺失显示 `--`。随后依据用户提供的官网/Windows 主题截图制作自有背景。最后再处理最小 udev 权限和登录自动启动，提供禁用/回退步骤及实机验收结果。代码、测试、设备识别证据、上游版本与许可证记录放在项目仓库里。

推荐先验收上游的前台显示，再决定是否另写传输层：上游项目[明确支持 Linux、Turing 2.1 英寸屏和作为 Python 库集成](https://github.com/mathoudebine/turing-smart-screen-python)，其[安装说明](https://github.com/mathoudebine/turing-smart-screen-python/wiki/System-monitor-%3A-how-to-start)提醒在用户家目录运行服务时需调整附带的 systemd 权限设置。用户需求的价值主要在定制内容和稳定集成，协议重造只在上游不兼容时进行。
