"""Read-only discovery/preview, bounded protocol probe, and foreground display."""

import argparse
import json
import logging
from pathlib import Path

from . import app
from .discovery import inspect
from .metrics import cpu_times, tctl_celsius
from .render import frame
from .transport import ScreenSession, probe


def main():
    parser = argparse.ArgumentParser(prog="sama-lcd")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("detect", help="只读核对 USB 身份和权限")
    preview = commands.add_parser("preview", help="离线生成 PNG，无设备写入")
    preview.add_argument("--output", type=Path, default=Path("preview.png"))
    preview.add_argument("--background", type=Path)
    commands.add_parser("probe", help="向已核实设备发送一次 rev C HELLO")
    commands.add_parser("show-once", help="在 480×480 候选屏上显示单帧 TEST")
    monitor = commands.add_parser("run", help="前台每秒更新 CPU 温度和占用率")
    monitor.add_argument("--background", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger().setLevel(logging.INFO)  # Upstream configured handlers at import time.
    try:
        if args.command == "detect":
            device = inspect()
            print(f"link={device.link} target={device.target} usb={device.usb_path}")
            print(f"readable={device.readable} writable={device.writable}")
            print(f"Tctl={tctl_celsius()}°C cpu_stat_available={cpu_times() is not None}")
        elif args.command == "preview":
            image = frame(tctl_celsius(), None, args.background)
            image.save(args.output)
            print(args.output)
        elif args.command == "probe":
            response, rom = probe()
            print(f"rev C HELLO: {response!r}; ROM={rom}; resolution unverified")
        elif args.command == "show-once":
            with ScreenSession() as screen:
                print(f"rev C HELLO: {screen.response!r}")
                screen.show(frame(None, None, trial=True))
            print("单帧已发送；需目视确认方向、裁切、色彩")
        elif args.command == "run":
            background = args.background
            if background is None:
                config = Path(__file__).resolve().parents[2] / "config.json"
                setting = json.loads(config.read_text()).get("background")
                background = Path(setting) if setting else None
            app.run(background)
    except KeyboardInterrupt:
        print("已停止")
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"错误：{exc}\n")


if __name__ == "__main__":
    main()

