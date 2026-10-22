# 安装示例 / Installation examples

本目录文件记录已验证机器的安装方式。`sama-xw360w-lcd.service` 和桌面入口
使用本机绝对路径，udev 规则使用本机 `renping` 用户组。其他机器必须先调整
项目路径、组名，并核对目标 USB 身份。不要直接照搬本机的用户和路径。

These files are examples from the validated machine. The service and desktop
entry contain local absolute paths; the udev rules use the local `renping` group.
Adapt the project paths and group name and verify the target USB identity before
installing on another system. The service executes directly from the project
directory, so keep that directory and its local dependencies while using it.

前台静态画面和连续数值已于 2026-10-22 目视验收。

`70-sama-xw360w-lcd.rules` 只匹配 `1d6b:0121`、序列号 `20080411`
的 `ttyACM*` 节点，授予 `renping` 组读写，不匹配 LG 监视器。
安装前后用 `udevadm info`、`getfacl` 和 `./run.sh detect` 核对。

`sama-xw360w-lcd.service` 是登录图形会话启动的用户服务，
无 root 运行和固件/泵/风扇控制。已链接并启用。协议不匹配时不会
由 systemd 自动重启；程序内部仅在原设备失联时重连。停止与禁用命令为：

```sh
systemctl --user disable --now sama-xw360w-lcd.service
unlink ~/.config/systemd/user/sama-xw360w-lcd.service
systemctl --user daemon-reload
```

持久权限规则的回退：删除已安装的
`/etc/udev/rules.d/70-sama-xw360w-lcd.rules`，重新加载 udev 规则，
然后针对已确认的目标设备重新触发规则或重新插拔屏幕 USB。

