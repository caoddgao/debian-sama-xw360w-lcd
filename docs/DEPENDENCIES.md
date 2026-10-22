# 项目内依赖来源

没有执行第三方安装脚本，也没有安装系统 Python 包。
`python3 -m venv --without-pip .venv` 创建本地 Python 3.13 环境；
以下 Debian 13.7 官方二进制包由 `apt download` 下载到项目根目录，
经 `dpkg-deb -x` 提取到 `vendor/debian-deps/`。包和提取目录在 `.gitignore` 中，
应用源码没有依赖外部用户目录。

| 包 | 版本 | SHA-256 |
| --- | --- | --- |
| python3-serial | 3.5-2 | `55adf00b96ef91b1d8ad935d134c341f7c3dd021a5666cd53e75f37144006a51` |
| python3-pil | 11.1.0-5+deb13u4 | `df0b2a77d6e4486a656dfadc89ab9d0a8a77bc4cc7242b26fba7217dc9b02870` |
| python3-numpy | 1:2.2.4+ds-1 | `eacb51b412e4621e4b6d631a479f6f0589522416e494d8da0e680f1863b5cb44` |
| libraqm0 | 0.10.2-1 | `417415530d831b044f75212676944de1fc5a87838d1cf28b318294450a1353b3` |

`run.sh` 仅把项目内提取的 Python 包路径与 `libraqm.so.0` 路径加入该进程环境。
依赖包各自的版权文件保留在提取目录的 `usr/share/doc/`。

