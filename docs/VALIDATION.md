# 发布检查 / Publication checks

日期 / Date: 2026-10-22

- 目标平台 / Target: Debian Linux; validated on Debian 13.7 with the SAMA XW360W 480×480 screen.
- 离线测试 / Offline tests: 15 tests passed (CPU metrics, package energy accounting, CPU_Opt sensor selection, theme text and charts, and bounded startup HELLO retries).
- 检查 / Checks: local documentation links, example JSON configuration, shell syntax, and `git diff --check` passed.
- 发布内容 / Public source: application, tests, documentation, installer examples, third-party transport/parser code, and their license notices.
- 本机内容 / Local files: `config.json`, `.venv/`, extracted Debian dependencies, downloaded `.deb` packages, logs, previews, captures, and imported official theme assets are excluded from the current Git tree.
- 默认配置 / Default: copy `config.example.json` to `config.json`; the example uses the simple display and requires no vendor theme assets.

## 复现测试 / Reproduce tests

After preparing the local dependencies as described in the README:

```sh
PYTHONPATH=src:vendor/debian-deps/usr/lib/python3/dist-packages \
LD_LIBRARY_PATH=vendor/debian-deps/usr/lib/x86_64-linux-gnu \
.venv/bin/python -m unittest discover -s tests -v
```

These are offline tests; they do not establish additional real-device compatibility.
Existing device observations and remaining boot/reconnect checks are recorded in
[HARDWARE](HARDWARE.md), [PROTOCOL](PROTOCOL.md), and [STAGES](STAGES.md).

## 保留运行目录 / Keep the runtime directory

本机的用户服务直接运行项目内的 `run.sh`，主题选择器也读取此目录的本机素材。
上传 GitHub 后仍需保留本地项目、虚拟环境、提取依赖和个人配置，才能继续使用
当前已配置的屏幕服务。

The installed user service executes `run.sh` from this project directory. The theme
picker reads local assets here as well. Keep the project, local environment,
extracted dependencies, and personal configuration to continue using the current
screen service after publishing the source to GitHub.
