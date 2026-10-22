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
也尚未从设备收到 rev C `HELLO` 应答。

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

