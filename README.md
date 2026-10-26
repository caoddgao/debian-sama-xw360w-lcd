# Debian SAMA XW360W LCD / 先马 CPU 水冷屏应用

[中文说明](#中文说明) · [English](#english) · [本地运行 / Local run](#本地运行)

## 中文说明

**用于在 Debian Linux 下使用先马 SAMA XW360W CPU 水冷液晶屏的应用程序。**
以 Python 实现，已在 Debian 13.7 上验证 480×480 屏幕显示、CPU 温度与占用率、
本机主题选择以及图形登录后的用户服务启动。其他主题还可显示 Linux 能读取的
GPU、内存、CPU 封装功率及水泵转速等指标，缺失数据使用 `--`。

这是社区项目。目前的设备匹配和权限示例针对已验证的 XW360W 机器；
不代表所有先马水冷型号或 USB 固件均兼容。

## English

**A Debian Linux application for the LCD on SAMA XW360W CPU liquid coolers.**
This community Python project has been tested on Debian 13.7 with a 480×480 display.
It displays CPU temperature and usage, supports local theme selection, and includes
an example systemd user service for graphical login. Themes can also display GPU,
memory, CPU package power, and pump speed readings when Linux exposes them.
Unavailable sensor values are shown as `--`.

Device matching and permission examples target the verified XW360W setup. Support
for every SAMA cooler model or USB firmware has not been established. Vendor theme
images and fonts are not distributed; users may import locally available themes.
The default simple display works without those vendor assets.

## 来源与许可证 / Upstream and licenses

- USB rev C 通信代码 / USB rev C transport: [mathoudebine/turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python), commit `2b33ab4f00a096916dd6a1174441a53a7ec33b03`. [保留文件及修改说明 / Vendored files and changes](vendor/turing_rev_c/README.md).
- 主题离线解析 / Offline theme parsing: [netfleece](https://pypi.org/project/netfleece/), MIT license. [来源与兼容性修改 / Provenance and compatibility changes](vendor/netfleece/README.md).
- 本项目采用 GPL-3.0-or-later / This project uses GPL-3.0-or-later: [LICENSE](LICENSE). Third-party license notices are retained alongside their source.

## 首次克隆 / First checkout

```sh
git clone https://github.com/caoddgao/debian-sama-xw360w-lcd.git
cd debian-sama-xw360w-lcd
cp config.example.json config.json
```

随后按下方“本地运行”准备依赖，再执行 `./run.sh detect` 和 `./run.sh preview`。
个人 `config.json` 不提交；示例配置使用简洁画面，不依赖本机官方主题。
Debian 需要 Python 3、venv 和 DejaVu 字体；GTK 主题选择器另外需要系统
`python3-gi` 与 `gir1.2-gtk-4.0`。依赖包版本见 [依赖记录](docs/DEPENDENCIES.md)。

Prepare the local dependencies described under “Local run” below, then use
`./run.sh detect` and `./run.sh preview`. Copy the example configuration before
running the service. Personal configuration, virtual environments, downloaded
packages, logs, and imported vendor assets are excluded from Git. Debian needs
Python 3, venv, and DejaVu fonts; the optional GTK theme picker also needs system
packages `python3-gi` and `gir1.2-gtk-4.0`.

The files in `packaging/` are examples from the validated machine. Adapt their
project paths and local group name before installing them on another machine.
Device checks, setup evidence, and known limitations are documented below and in
[HARDWARE](docs/HARDWARE.md) and [PROTOCOL](docs/PROTOCOL.md).

## 本机运行记录 / Local status

在 Debian 13.7 上显示 `k10temp/Tctl` 和 `/proc/stat` 的总 CPU 占用率。
只读识别、离线渲染、协议审查、静态画面与前台连续显示已验收。
用户服务已启用并正在运行；不得把 LG 的 `/dev/ttyACM0` 当作目标。

On Debian 13.7 the display shows `k10temp/Tctl` and total CPU usage from `/proc/stat`.
Read-only detection, offline rendering, protocol review, a static frame, and continuous
foreground display have been accepted. The user service is enabled and running. The LG
device at `/dev/ttyACM0` must never be used as the target.

## 选择官方主题 / Choosing an official theme

Windows 已安装的先马程序中找到 21 个 480×480 圆屏内置主题。它们已经
转换到本机 `assets/themes/official/`，可运行 `./choose-theme.sh` 打开
带预览的主题选择器。点击主题会立即切换，并在下次登录沿用。
选择器也可切回原来的简洁画面。运行 `./run.sh themes` 列出主题；
`./run.sh preview --theme theme15` 生成离线预览。

The SAMA software installed on Windows contains 21 built-in 480×480 round-screen themes.
They were converted locally to `assets/themes/official/`; run `./choose-theme.sh` to open
a theme picker with previews. Clicking a theme switches immediately and is kept for the
next login. The picker can also switch back to the simple display. `./run.sh themes`
lists the themes; `./run.sh preview --theme theme15` renders an offline preview.

官方 `.turtheme` 含图片、字体和布局，不是单张背景图。当前实现显示静态
主题及实时 CPU/GPU/内存等 Debian 可读指标；动画暂以静态首帧显示，
不可读的专有传感器不伪造数值。官方素材仅在本机保留，已排除 Git。
导入来源和细节见 [主题说明](assets/themes/README.md)。
主题 15 的 `USAGE` 弧条按官方预览显示完整底轨，并随 CPU 使用率填充。
主题 18 的 CPU 功率读取本机 RAPL CPU 封装能耗，以相邻读数换算平均瓦数；
首次读数会暂时显示 `--`，随后每秒更新。
主题 17 的 `CPU USE` 图形保留最近 64 次 CPU 使用率采样，绘制曲线、填充和边框；
空闲时曲线会贴近图框底部。
主题 04 的 `WATERPUMP` 读取 ASUS EC 的 `CPU_Opt` 转速；与主板约 2510 RPM 的读数核对后，
实机读到约 2510 RPM，离线预览显示为 `2514R`。本机已通过 DKMS 安装新版
`asus-ec-sensors` 并设置开机加载；安装后的再次重启仍待验证，详情见
[硬件记录](docs/HARDWARE.md)。传感器不可读时显示 `--`。

An official `.turtheme` contains images, fonts, and a layout, not a single background
image. The current implementation shows the theme statically with live readings that
Debian can provide, such as CPU, GPU, and memory. Animations are shown as their first
frame, and proprietary sensors that cannot be read are never faked. Official assets stay
on the local machine and are excluded from Git. See the [theme notes](assets/themes/README.md)
for import sources and details.
Theme 15's `USAGE` arc shows the full base track as in the official preview and fills
with CPU usage.
Theme 18's CPU power reads the local RAPL CPU package energy counter and converts
consecutive readings into average watts; the first reading shows `--`, then it updates
every second.
Theme 17's `CPU USE` graph keeps the last 64 CPU usage samples and draws the curve, fill,
and border; when idle the curve stays near the bottom of the frame.
Theme 04's `WATERPUMP` reads the `CPU_Opt` speed from the ASUS EC. Checked against the
motherboard's reading of about 2510 RPM, the live value is about 2510 RPM and the offline
preview shows `2514R`. A newer `asus-ec-sensors` was installed through DKMS and set to
load at boot; a reboot after installation is still to be verified, see
[HARDWARE](docs/HARDWARE.md). Unreadable sensors show `--`.

## 当前验证 / Current safeguards

- 唯一允许的路径：`/dev/serial/by-id/usb-Android_Android_20080411-if00`。
- 程序每次打开前验证链接、`1d6b:0121`、序列号 `20080411`、接口 00、`cdc_acm` 驱动；打开后核对设备号。
- `detect` 为只读；`probe` 只发送一次上游 rev C `HELLO` 并限时读取 23 字节；异常响应立即停止。
- `show-once` 仅在有效 `HELLO` 后发送候选 480×480 的单帧 `TEST`。本机 480×480 画面和方向已目视确认，其他机器仍需验证。
- `run` 每秒更新一次；短暂失联时等待原设备回来并重新核实身份，身份或协议不匹配时退出。
- 精确匹配目标 USB 身份的 udev 规则与图形登录用户服务已安装，状态和回退见下文。
- CPU 封装能耗计数器仅授权本机 `renping` 用户组读取，用于主题 18 的瓦数显示。

- The only allowed path is `/dev/serial/by-id/usb-Android_Android_20080411-if00`.
- Before every open the program checks the link, `1d6b:0121`, serial `20080411`, interface 00, and the `cdc_acm` driver; after opening it checks the device number.
- `detect` is read-only; `probe` sends a single upstream rev C `HELLO` and reads 23 bytes with a timeout; any unexpected response stops it immediately.
- `show-once` sends one candidate 480×480 `TEST` frame only after a valid `HELLO`. The 480×480 image and orientation were visually confirmed on this machine; other machines still need verification.
- `run` updates once per second. After a short disconnect it waits for the same device to return and re-verifies its identity; it exits on an identity or protocol mismatch.
- A udev rule that exactly matches the target USB identity and a graphical-login user service are installed; status and rollback are described below.
- Only the local `renping` group may read the CPU package energy counter, used for the wattage in theme 18.

<a id="本地运行"></a>
## 本地运行 / Local run

`run.sh` 使用项目里的 Python venv 与从 Debian 官方包离线提取的依赖，未执行第三方安装脚本。
源码留在项目内；系统外安装两条精确匹配的 udev 规则及指向项目内 unit 的用户服务链接。

`run.sh` uses the project's Python venv and dependencies extracted offline from official
Debian packages; no third-party install scripts are run. The source stays inside the
project; outside it, only two exactly matching udev rules and a user service link pointing
to the unit in the project are installed.

```sh
./run.sh detect                    # 只读 / read-only
./run.sh preview --output preview.png  # 只写本项目 PNG / writes a PNG in the project only
./run.sh probe                     # 需要临时串口授权；单次 HELLO / needs temporary serial access; single HELLO
./run.sh show-once                 # 仅在 HELLO 匹配后试屏 / test frame only after a matching HELLO
./run.sh run                       # 试屏目视确认后才运行 / run only after the test frame is visually confirmed
./run.sh run --background assets/themes/my-background.png
```

如需在同一 Debian 13.7 机器重新准备项目内依赖：

To prepare the in-project dependencies again on the same Debian 13.7 machine:

```sh
python3 -m venv --without-pip .venv
apt download python3-pil python3-serial python3-numpy libraqm0
mkdir -p vendor/debian-deps
for package in python3-*.deb libraqm0_*.deb; do dpkg-deb -x "$package" vendor/debian-deps; done
```

这些命令只在项目中创建文件，不安装系统包。当前实际包版本与校验值见
[依赖记录](docs/DEPENDENCIES.md)。

These commands only create files inside the project and do not install system packages.
The exact package versions and checksums are in [DEPENDENCIES](docs/DEPENDENCIES.md).

背景接受 PNG/JPEG 等 Pillow 可读文件，缩放到 480×480。默认背景为自绘纯色。
可先用 `./run.sh preview --background assets/themes/文件名.png` 离线预览。
登录服务从项目内的 `config.json` 读取 `background`，可填
`assets/themes/文件名.png`；修改后用
`systemctl --user restart sama-xw360w-lcd.service` 应用。
按 `Ctrl+C` 停止前台程序。若数值不可读，显示 `--`。

Backgrounds can be PNG/JPEG or any other file Pillow can read, scaled to 480×480. The
default background is a plain drawn color. Preview offline first with
`./run.sh preview --background assets/themes/<file>.png`. The login service reads
`background` from the project's `config.json`, e.g. `assets/themes/<file>.png`; apply
changes with `systemctl --user restart sama-xw360w-lcd.service`. Press `Ctrl+C` to stop
the foreground program. Unreadable values show `--`.

当前账户不在 `dialout` 组。验收期间曾对 `/dev/ttyACM1` 使用临时 ACL，
现已撤销。已安装的精确 udev 规则使目标节点为 `root:renping 0660`；
LG 的 `/dev/ttyACM0` 仍是 `root:dialout 0660`。

The current account is not in the `dialout` group. A temporary ACL on `/dev/ttyACM1` was
used during acceptance and has been revoked. The installed exact udev rule makes the target
node `root:renping 0660`; the LG device `/dev/ttyACM0` remains `root:dialout 0660`.

登录自启动状态：

Login autostart status:

```sh
systemctl --user status sama-xw360w-lcd.service
journalctl --user -u sama-xw360w-lcd.service -f
systemctl --user stop sama-xw360w-lcd.service
systemctl --user start sama-xw360w-lcd.service
```

## 回退 / Rollback

1. `systemctl --user disable --now sama-xw360w-lcd.service` 停止并禁用登录自启动。
2. 如果仍有 unit 链接，可用 `unlink ~/.config/systemd/user/sama-xw360w-lcd.service` 删除链接，再运行 `systemctl --user daemon-reload`。
3. `pkexec rm /etc/udev/rules.d/70-sama-xw360w-lcd.rules` 删除权限规则，
   `pkexec udevadm control --reload-rules` 重新加载；对目标节点重新插拔或触发 udev 以恢复默认权限。
   如需撤销 CPU 功率读取权限，同样删除 `/etc/udev/rules.d/71-sama-cpu-power.rules`，
   并将 `/sys/class/powercap/intel-rapl:0/energy_uj` 恢复为 `root:root 0400`。
4. 删除本项目目录中的 `.venv/`、`vendor/debian-deps/`、预览和日志即可移除本地运行依赖；程序不会改水泵、风扇、固件。

1. `systemctl --user disable --now sama-xw360w-lcd.service` stops and disables login autostart.
2. If a unit link remains, remove it with `unlink ~/.config/systemd/user/sama-xw360w-lcd.service`, then run `systemctl --user daemon-reload`.
3. Remove the permission rule with `pkexec rm /etc/udev/rules.d/70-sama-xw360w-lcd.rules` and reload with
   `pkexec udevadm control --reload-rules`; replug the target device or trigger udev to restore default permissions.
   To revoke CPU power access, likewise remove `/etc/udev/rules.d/71-sama-cpu-power.rules`
   and restore `/sys/class/powercap/intel-rapl:0/energy_uj` to `root:root 0400`.
4. Deleting `.venv/`, `vendor/debian-deps/`, previews, and logs from the project directory removes the local runtime dependencies. The program never changes pump, fan, or firmware settings.

2026-10-22 从 Windows 重启到 Debian 的首次实测：用户服务确实自动启动，
但目标屏幕第一次 `HELLO` 返回空应答，服务退出，屏幕未显示。稍后同一
设备身份和权限下手动 `probe` 成功；现对这种空应答每隔 2 秒最多重试
10 次，非空错误应答仍立即退出。修复后手动重启服务已连接并发送画面。
修复后的再次跨系统重启、真正注销/重新登录和 USB 短暂失联仍待实测。

First real test on 2026-10-22, rebooting from Windows into Debian: the user service did
start automatically, but the screen's first `HELLO` returned an empty reply, the service
exited, and nothing was displayed. A manual `probe` shortly afterwards with the same device
identity and permissions succeeded. Empty replies are now retried every 2 seconds, up to 10
times; non-empty error replies still exit immediately. After the fix, a manual service
restart connected and sent a frame. Another cross-OS reboot, a real logout/login, and a
brief USB disconnect after the fix are still to be tested.

离线测试 / Offline tests: `PYTHONPATH=src:vendor/debian-deps/usr/lib/python3/dist-packages LD_LIBRARY_PATH=vendor/debian-deps/usr/lib/x86_64-linux-gnu .venv/bin/python -m unittest discover -s tests -v`.

后续实机记录见 [HARDWARE](docs/HARDWARE.md) 和 [PROTOCOL](docs/PROTOCOL.md)。
上游传输代码与许可证见 [vendor/turing_rev_c](vendor/turing_rev_c/README.md)。

Further hardware notes are in [HARDWARE](docs/HARDWARE.md) and [PROTOCOL](docs/PROTOCOL.md).
The upstream transport code and its license are in [vendor/turing_rev_c](vendor/turing_rev_c/README.md).
