"""Foreground one-second monitoring loop. No service is installed here."""

import logging
import time
from pathlib import Path
import serial

from .discovery import DeviceMismatch, DeviceUnavailable
from .metrics import cpu_percent, cpu_times, tctl_celsius
from .render import frame
from .transport import ProtocolMismatch, ScreenSession

LOG = logging.getLogger(__name__)


def run(background: Path | None = None):
    previous = None
    last_log = 0.0
    while True:
        try:
            with ScreenSession() as screen:
                LOG.info("屏幕已连接：%s", screen.response)
                while True:
                    started = time.monotonic()
                    current = cpu_times()
                    load = cpu_percent(previous, current)
                    previous = current
                    temp = tctl_celsius()
                    if started - last_log >= 10:
                        LOG.info("Tctl=%s°C CPU=%s%%", "--" if temp is None else f"{temp:.1f}",
                                 "--" if load is None else f"{load:.1f}")
                        last_log = started
                    screen.show(frame(temp, load, background))
                    time.sleep(max(0, 1 - (time.monotonic() - started)))
        except DeviceUnavailable as exc:
            LOG.warning("等待原屏幕设备恢复：%s", exc)
        except (DeviceMismatch, ProtocolMismatch, PermissionError):
            raise
        except (serial.SerialException, OSError) as exc:
            LOG.warning("串口暂时失联，2 秒后重新核对原设备：%s", exc)
        time.sleep(2)

