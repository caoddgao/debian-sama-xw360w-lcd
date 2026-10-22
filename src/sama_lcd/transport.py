"""Bounded rev C probe and guarded access to the upstream display library."""

from pathlib import Path
import os
import re
import sys

import serial
from PIL import Image

from .discovery import DEVICE_LINK, DeviceMismatch, inspect

VENDOR = Path(__file__).resolve().parents[2] / "vendor" / "turing_rev_c"
sys.path.insert(0, str(VENDOR))
from library.lcd.lcd_comm import Orientation  # noqa: E402
from library.lcd.lcd_comm_rev_c import LcdCommRevC, SubRevision, Command  # noqa: E402


class ProtocolMismatch(RuntimeError):
    pass


class NoHelloResponse(ProtocolMismatch):
    """The verified device opened, but did not answer before the read timeout."""


def safe_open() -> serial.Serial:
    device = inspect()
    if not (device.readable and device.writable):
        raise PermissionError(f"无目标串口读写权限：{DEVICE_LINK} -> {device.target}")
    port = serial.Serial(str(DEVICE_LINK), 115200, timeout=1, write_timeout=3, rtscts=True)
    try:
        reopened = inspect()
        if (reopened.target != device.target or
                os.fstat(port.fileno()).st_rdev != device.target.stat().st_rdev):
            raise DeviceMismatch("打开期间目标串口发生变化")
        return port
    except Exception:
        port.close()
        raise


def probe_serial(port: serial.Serial) -> tuple[str, int]:
    """Send upstream's rev C HELLO once, never retry on mismatch."""
    port.reset_input_buffer()
    hello = bytes(Command.HELLO.value).ljust(250, b"\x00")
    count = port.write(hello)
    if count != len(hello):
        raise ProtocolMismatch(f"HELLO 只写入 {count}/{len(hello)} 字节")
    response = port.read(23).decode("ascii", errors="replace").strip("\x00\r\n ")
    inspect()  # Distinguish a disconnect from an invalid protocol reply.
    if not response:
        raise NoHelloResponse("已确认的屏幕未应答 HELLO")
    match = re.fullmatch(r"chs_[\w]+\.dev\d+_rom\d+\.(\d+)", response)
    if not match:
        raise ProtocolMismatch(f"HELLO 应答不符合 rev C 格式：{response!r}")
    rom = int(match.group(1))
    if not 80 <= rom <= 100:
        raise ProtocolMismatch(f"ROM 版本异常：{rom}")
    return response, rom


def probe() -> tuple[str, int]:
    with safe_open() as port:
        return probe_serial(port)


class GuardedRevC(LcdCommRevC):
    def openSerial(self):
        self.lcd_serial = safe_open()


class ScreenSession:
    def __enter__(self):
        self.lcd = GuardedRevC(com_port=str(DEVICE_LINK), display_width=480, display_height=480)
        try:
            self.response, rom = probe_serial(self.lcd.lcd_serial)
            self.lcd.sub_revision = SubRevision.REV_2INCH
            self.lcd.rom_version = rom
            self.lcd.SetOrientation(Orientation.LANDSCAPE)
            return self
        except Exception:
            self.lcd.closeSerial()
            raise

    def __exit__(self, *_):
        self.lcd.closeSerial()

    def show(self, image: Image.Image):
        if image.size != (480, 480):
            raise ValueError("当前候选协议仅允许 480×480 图像")
        device = inspect()  # Recheck the stable link before every frame.
        if os.fstat(self.lcd.lcd_serial.fileno()).st_rdev != device.target.stat().st_rdev:
            raise DeviceMismatch("打开的串口与当前稳定链接不一致")
        self.lcd.DisplayPILImage(image)

