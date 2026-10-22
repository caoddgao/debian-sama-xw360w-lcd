"""Foreground one-second monitoring loop. No service is installed here."""

import logging
import time
from collections import deque
from pathlib import Path
import serial

from .discovery import DeviceMismatch, DeviceUnavailable
from .metrics import CpuPackagePower, cpu_percent, cpu_times, tctl_celsius
from .official import render as official_render, sample_values
from .render import frame
from .transport import NoHelloResponse, ProtocolMismatch, ScreenSession

LOG = logging.getLogger(__name__)
HELLO_ATTEMPTS = 10


def run(background: Path | None = None, theme_id: str | None = None):
    power_sampler = CpuPackagePower()
    cpu_history = deque(maxlen=64)
    previous = None
    last_log = 0.0
    unanswered_hello = 0
    while True:
        try:
            with ScreenSession() as screen:
                unanswered_hello = 0
                LOG.info("屏幕已连接：%s", screen.response)
                while True:
                    started = time.monotonic()
                    current = cpu_times()
                    load = cpu_percent(previous, current)
                    previous = current
                    if load is not None:
                        cpu_history.append(load)
                    temp = tctl_celsius()
                    values = sample_values(theme_id, temp, load, power_sampler) if theme_id else None
                    if started - last_log >= 10:
                        power = values.get("CPUPWR") if values else None
                        power_note = (f" CPU package={power:.1f}W" if power is not None else
                                      " CPU package=--W" if values and "CPUPWR" in values else "")
                        LOG.info("Tctl=%s°C CPU=%s%%%s", "--" if temp is None else f"{temp:.1f}",
                                 "--" if load is None else f"{load:.1f}", power_note)
                        last_log = started
                    if theme_id:
                        screen.show(official_render(theme_id, values, history={"CPULOAD": cpu_history}))
                    else:
                        screen.show(frame(temp, load, background))
                    time.sleep(max(0, 1 - (time.monotonic() - started)))
        except NoHelloResponse as exc:
            unanswered_hello += 1
            if unanswered_hello >= HELLO_ATTEMPTS:
                raise ProtocolMismatch(f"屏幕连续 {HELLO_ATTEMPTS} 次未应答 HELLO") from exc
            LOG.warning("%s；2 秒后重试（%d/%d）", exc, unanswered_hello, HELLO_ATTEMPTS)
        except DeviceUnavailable as exc:
            LOG.warning("等待原屏幕设备恢复：%s", exc)
        except (DeviceMismatch, ProtocolMismatch, PermissionError):
            raise
        except (serial.SerialException, OSError) as exc:
            LOG.warning("串口暂时失联，2 秒后重新核对原设备：%s", exc)
        time.sleep(2)

