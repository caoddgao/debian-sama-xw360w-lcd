# 本机硬件与权限证据

记录日期：2026-10-22，Debian 13.7。只读检查已在可见宿主设备的执行环境完成。

## 屏幕候选

`/dev/serial/by-id/usb-Android_Android_20080411-if00 -> ../../ttyACM1`。
`/dev/serial/by-id/usb-LG_Electronics_Inc._LG_Monitor_Controls_FEDF0400D486-if02 -> ../../ttyACM0`。
`ttyACM0` 属于 LG 显示器，程序显式拒绝它。

`udevadm info --query=property --name=...20080411-if00` 读到：

```text
DEVNAME=/dev/ttyACM1
ID_VENDOR_ID=1d6b
ID_MODEL_ID=0121
ID_SERIAL_SHORT=20080411
ID_USB_INTERFACE_NUM=00
ID_USB_DRIVER=cdc_acm
ID_USB_INTERFACES=:020201:0a0000:
ID_PATH=pci-0000:0f:00.0-usb-0:10:1.0
```

`lsusb` 对应 Bus 003 Device 006 `1d6b:0121 Linux Foundation Android`；
`lsusb -t` 对应 Bus 003 Port 010，接口 0/1 绑定 `cdc_acm`。
这些与方案第 7–9 节以及 rev C 上游的唤醒后识别条件一致。
尚未通过冷头外观/Windows Hardware Ids 进行独立物理归属验证，
设备后来已返回 rev C `HELLO` 应答；实测记录见 PROTOCOL。

## 权限门槛

当前用户 `renping` 不在 `dialout` 组。`/dev/ttyACM1` 原为 `root:dialout 0660`，
`getfacl` 原无额外用户 ACL。首次 `./run.sh detect` 报告
`readable=False writable=False`；首次 `./run.sh probe` 因此在发送前退出。
之后通过 `pkexec setfacl -m u:renping:rw /dev/ttyACM1` 添加临时 ACL，
再次 `detect` 报告 `readable=True writable=True`、同一路径和 USB 身份。
前台验收后安装精确匹配 `1d6b:0121`、`20080411` 的 udev 规则。
`udevadm test` 对 ttyACM1 得到 group `renping`、mode `0660`；
对 LG ttyACM0 保持 group `dialout`。仅触发 ttyACM1 后实测同样如此。
临时 ACL 随后已撤销，`detect` 仍报告可读写。

## CPU 温度与占用率

本机 `sensors`：`k10temp-pci-00c3` 的 `Tctl` 39.5°C、`Tccd1` 31.4°C
（2026-10-22 只读采样）。之后 `detect` 从 hwmon 标签 `Tctl` 读到 41.375°C，
温度会随负载变化。程序按标签定位 `temp*_input`，将毫摄氏度转成 °C；
不把内存 `spd5118` 或 `Tccd1` 当 Tctl。
总占用率由 `/proc/stat` 的连续两次 `cpu` 汇总行差值计算；初次采样未知。
与 GNOME 系统监视器的实机数值对照仍待前台验收。

## 2026-10-22 水泵转速：主题 04

- 官方主题 04 底部字段是 `WATERPUMP`，使用主板 `CPU_Opt` 接口上的水泵转速。用户在主板界面核对到端口 `OPT-CPU`、约 2510 RPM。
- 主板为 `ASUS TUF GAMING X670E-PLUS WIFI`，内核为 `6.12.113+deb13-amd64`。`lm-sensors` 已安装；此前没有转速读数是因为主板监控驱动未加载。
- 临时运行 `pkexec /usr/sbin/modprobe nct6775` 后，出现 `nct6799` 的 7 路转速，其中非零通道约 600 RPM，与用户记得的 CPU_OPT 水泵约 2000 RPM 不符，不能直接拿来填 `WATERPUMP`。
- 本机内核自带的 `asus_ec_sensors` 模块不含此主板的 DMI 匹配。驱动维护者的新版源码 <https://github.com/zeule/asus-ec-sensors> 含该匹配和 `CPU_Opt` 传感器；从其 `master.tar.gz` 下载到 `/tmp/asus-ec-sensors-main.tar.gz`（当时 SHA-256 `a4a1c5a95191031ebe8fc27af9b2df98b243ad78a8ddfc5a1c7770d7ca425716`），在 `/tmp/asus-ec-sensors-master` 用当前内核头文件 `make modules` 编译成功。
- 重启前临时加载时，`asusec` 的 `CPU_Opt` 为 2511、2505 RPM。重启后 `/tmp` 源码与模块均已消失，内核未加载该模块；重新下载的源码包 SHA-256 与上次相同，在当前内核下重新编译、临时加载后读到 2517 RPM，与主板读数吻合。
- 主题 04 现在逐次扫描 `/sys/class/hwmon/hwmon*/name=asusec` 和 `fan*_label=CPU_Opt`，读取对应 `fan*_input`，不固定 `hwmon` 或 `fan` 编号；读取失败显示 `--`，不拿约 600 RPM 的其他风扇代替。离线主题预览实测显示 `2514R`。
- 同一份源码按版本 `20261022` 安装到 `/usr/src/asus-ec-sensors-20261022` 并由 DKMS 注册、编译、安装；`modprobe --show-depends asus-ec-sensors` 指向当前内核的 `updates/dkms/asus-ec-sensors.ko.xz`。`/etc/modules-load.d/asus-ec-sensors.conf` 由项目内 `packaging/asus-ec-sensors.conf` 安装，负责开机加载。驱动仅提供 hwmon 传感器读数，不设置水泵控制值。
- 卸载临时模块再用 `modprobe asus-ec-sensors` 加载已安装版本后，`CPU_Opt` 仍读到 2508 RPM；屏幕用户服务重启后已连接并持续运行。**安装后的跨系统重启验证尚未进行。** 若未来更换内核，需要对应内核头文件供 DKMS 自动重建；若 `CPU_Opt` 消失，先检查 `dkms status -m asus-ec-sensors`、`modprobe --show-depends asus-ec-sensors` 和 `sensors asusec-*`。
- 回退驱动：`pkexec /usr/bin/rm /etc/modules-load.d/asus-ec-sensors.conf`，`pkexec /usr/sbin/dkms remove -m asus-ec-sensors -v 20261022 --all`，再按需要卸载当前模块；DKMS 会恢复原有内核模块。删除 `/usr/src/asus-ec-sensors-20261022` 前先确认 DKMS 已移除。

