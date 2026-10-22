# 先马 XW360W 屏幕项目（实机试屏待完成）

在 Debian 13.7 上显示 `k10temp/Tctl` 和 `/proc/stat` 的总 CPU 占用率。
只读识别、离线渲染、协议审查、静态画面与前台连续显示已验收。
用户服务已启用并正在运行；不得把 LG 的 `/dev/ttyACM0` 当作目标。

## 当前验证

- 唯一允许的路径：`/dev/serial/by-id/usb-Android_Android_20080411-if00`。
- 程序每次打开前验证链接、`1d6b:0121`、序列号 `20080411`、接口 00、`cdc_acm` 驱动；打开后核对设备号。
- `detect` 为只读；`probe` 只发送一次上游 rev C `HELLO` 并限时读取 23 字节；异常响应立即停止。
- `show-once` 仅在有效 `HELLO` 后发送候选 480×480 的单帧 `TEST`。480×480 和方向尚需目视验收。
- `run` 每秒更新一次；短暂失联时等待原设备回来并重新核实身份，身份或协议不匹配时退出。
- 精确匹配目标 USB 身份的 udev 规则与图形登录用户服务已安装，状态和回退见下文。

## 本地运行

`run.sh` 使用项目里的 Python venv 与从 Debian 官方包离线提取的依赖，未执行第三方安装脚本。
源码留在项目内；系统外只安装一条 udev 规则及指向项目内 unit 的用户服务链接。

```sh
./run.sh detect                    # 只读
./run.sh preview --output preview.png  # 只写本项目 PNG
./run.sh probe                     # 需要临时串口授权；单次 HELLO
./run.sh show-once                 # 仅在 HELLO 匹配后试屏
./run.sh run                       # 试屏目视确认后才运行
./run.sh run --background assets/themes/my-background.png
```

如需在同一 Debian 13.7 机器重新准备项目内依赖：

```sh
python3 -m venv --without-pip .venv
apt download python3-pil python3-serial python3-numpy libraqm0
mkdir -p vendor/debian-deps
for package in python3-*.deb libraqm0_*.deb; do dpkg-deb -x "$package" vendor/debian-deps; done
```

这些命令只在项目中创建文件，不安装系统包。当前实际包版本与校验值见
[依赖记录](docs/DEPENDENCIES.md)。

背景接受 PNG/JPEG 等 Pillow 可读文件，缩放到 480×480。默认背景为自绘纯色。
可先用 `./run.sh preview --background assets/themes/文件名.png` 离线预览。
登录服务从项目内的 `config.json` 读取 `background`，可填
`assets/themes/文件名.png`；修改后用
`systemctl --user restart sama-xw360w-lcd.service` 应用。
按 `Ctrl+C` 停止前台程序。若数值不可读，显示 `--`。

当前账户不在 `dialout` 组。验收期间曾对 `/dev/ttyACM1` 使用临时 ACL，
现已撤销。已安装的精确 udev 规则使目标节点为 `root:renping 0660`；
LG 的 `/dev/ttyACM0` 仍是 `root:dialout 0660`。

登录自启动状态：

```sh
systemctl --user status sama-xw360w-lcd.service
journalctl --user -u sama-xw360w-lcd.service -f
systemctl --user stop sama-xw360w-lcd.service
systemctl --user start sama-xw360w-lcd.service
```

## 回退

1. `systemctl --user disable --now sama-xw360w-lcd.service` 停止并禁用登录自启动。
2. 如果仍有 unit 链接，可用 `unlink ~/.config/systemd/user/sama-xw360w-lcd.service` 删除链接，再运行 `systemctl --user daemon-reload`。
3. `pkexec rm /etc/udev/rules.d/70-sama-xw360w-lcd.rules` 删除权限规则，
   `pkexec udevadm control --reload-rules` 重新加载；对目标节点重新插拔或触发 udev 以恢复默认权限。
4. 删除本项目目录中的 `.venv/`、`vendor/debian-deps/`、预览和日志即可移除本地运行依赖；程序不会改水泵、风扇、固件。

真正注销登录、重启和 USB 短暂失联后的恢复尚未实测，需在方便中断屏幕显示时验证。

离线测试：`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`。

后续实机记录见 [HARDWARE](docs/HARDWARE.md) 和 [PROTOCOL](docs/PROTOCOL.md)。
上游传输代码与许可证见 [vendor/turing_rev_c](vendor/turing_rev_c/README.md)。

