"""Read-only validation of the one allowed USB serial interface."""

from dataclasses import dataclass
import os
from pathlib import Path

DEVICE_LINK = Path("/dev/serial/by-id/usb-Android_Android_20080411-if00")
EXPECTED = {"idVendor": "1d6b", "idProduct": "0121", "serial": "20080411"}


class DeviceMismatch(RuntimeError):
    pass


class DeviceUnavailable(DeviceMismatch):
    """The exact by-id link is temporarily absent, e.g. during replug."""


@dataclass(frozen=True)
class Device:
    link: Path
    target: Path
    usb_path: Path
    readable: bool
    writable: bool


def inspect() -> Device:
    if not DEVICE_LINK.is_symlink():
        raise DeviceUnavailable(f"指定设备链接不存在：{DEVICE_LINK}")
    try:
        target = DEVICE_LINK.resolve(strict=True)
    except OSError as exc:
        raise DeviceUnavailable(f"目标设备暂不可用：{exc}") from exc
    if not target.name.startswith("ttyACM") or target.name == "ttyACM0":
        raise DeviceMismatch(f"链接目标异常：{target}")
    sys_tty = Path("/sys/class/tty") / target.name / "device"
    try:
        interface = sys_tty.resolve(strict=True)
        if (interface / "bInterfaceNumber").read_text().strip().lower() != "00":
            raise DeviceMismatch("目标不是 USB 接口 00")
        driver = (interface / "driver").resolve(strict=True)
        if driver.name != "cdc_acm":
            raise DeviceMismatch(f"驱动不匹配：{driver.name}")
        usb = next(p for p in interface.parents if (p / "idVendor").exists())
        found = {key: (usb / key).read_text().strip().lower() for key in EXPECTED}
    except (OSError, StopIteration) as exc:
        raise DeviceMismatch(f"无法从 sysfs 核实目标设备：{exc}") from exc
    if found != EXPECTED:
        raise DeviceMismatch(f"USB 身份不匹配：{found}")
    return Device(DEVICE_LINK, target, usb, os.access(target, os.R_OK), os.access(target, os.W_OK))

