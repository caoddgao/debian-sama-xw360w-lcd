把自制背景 PNG/JPEG 放到此目录，再将项目根目录 `config.json` 的
`background` 设置为相对路径，例如 `assets/themes/my-background.png`。
运行 `systemctl --user restart sama-xw360w-lcd.service` 应用新背景。
默认 `null` 使用程序绘制的深色纯色背景。
Windows 官方软件截图到位后再调整版式和素材；不要直接复制无授权主题。

## 本机官方主题

Windows 系统盘的先马程序自带 `theme/480480r` 目录。已从该目录将 21 个
`theme01`–`theme21` 文件转换为本机 `official/` 中的 PNG 图层和布局 JSON。
该目录被 Git 忽略，只供这台机器个人使用；项目不分发官方素材。

运行 `./choose-theme.sh` 打开带预览的 GTK 主题选择器。点击主题后会保存
`config.json` 并重启已安装的用户服务；下次登录仍使用所选主题。
`./run.sh themes` 可以列出主题，`./run.sh preview --theme theme15` 可离线预览。

离线导入命令：

```sh
PYTHONPATH=vendor/debian-deps/usr/lib/python3/dist-packages \
LD_LIBRARY_PATH=vendor/debian-deps/usr/lib/x86_64-linux-gnu \
.venv/bin/python tools/import_official_themes.py '/Windows安装目录/SAMA_Multi_Chn/theme/480480r'
```

主题背景、图层、文字和多数仪表可显示。动画主题目前使用静态首帧；
Windows 专有指标或 Debian 无法读取的传感器显示 `--` 或空仪表。
主题 18 的 `CPUPWR` 来自 Linux RAPL `package-0` 能耗计数器的时间差，
单位为瓦，表示 CPU 封装平均功率。需要安装项目中的
`packaging/71-sama-cpu-power.rules` 赋予本机用户组只读权限。

