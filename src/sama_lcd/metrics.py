"""CPU Tctl and aggregate utilization from kernel interfaces."""

from dataclasses import dataclass
from pathlib import Path
import time

HWMON = Path("/sys/class/hwmon")
PROC_STAT = Path("/proc/stat")
POWERCAP = Path("/sys/class/powercap")


class CpuPackagePower:
    """Average package watts from successive RAPL energy counter readings."""

    def __init__(self, root: Path = POWERCAP):
        self.root = root
        self.zone = None
        self.maximum = None
        self.previous = None

    def sample(self, now: float | None = None) -> float | None:
        now = time.monotonic() if now is None else now
        try:
            if self.zone is None:
                for zone in sorted(self.root.glob("intel-rapl:*")):
                    if zone.name.count(":") == 1 and zone.joinpath("name").read_text().strip().startswith("package-"):
                        self.zone = zone
                        self.maximum = int(zone.joinpath("max_energy_range_uj").read_text())
                        break
            if self.zone is None or not self.maximum or self.maximum <= 0:
                return None
            energy = int(self.zone.joinpath("energy_uj").read_text())
        except (OSError, ValueError):
            self.previous = None
            return None

        previous, self.previous = self.previous, (now, energy)
        if previous is None:
            return None
        elapsed = now - previous[0]
        if not 0 < elapsed <= 60:
            return None
        delta = (energy - previous[1]) % self.maximum
        watts = delta / elapsed / 1_000_000
        return watts if watts <= 1000 else None


def tctl_celsius(hwmon_root: Path = HWMON) -> float | None:
    for node in sorted(hwmon_root.glob("hwmon*")):
        try:
            if (node / "name").read_text().strip() != "k10temp":
                continue
            for label in node.glob("temp*_label"):
                if label.read_text().strip() == "Tctl":
                    milli = int(label.with_name(label.name.replace("_label", "_input")).read_text())
                    return milli / 1000
        except (OSError, ValueError):
            continue
    return None


def cpu_opt_rpm(hwmon_root: Path = HWMON) -> int | None:
    """Read the ASUS EC CPU_Opt fan header used by the water pump."""
    for node in sorted(hwmon_root.glob("hwmon*")):
        try:
            if (node / "name").read_text().strip() != "asusec":
                continue
            for label in node.glob("fan*_label"):
                if label.read_text().strip() == "CPU_Opt":
                    rpm = int(label.with_name(label.name.replace("_label", "_input")).read_text())
                    if rpm >= 0:
                        return rpm
        except (OSError, ValueError):
            continue
    return None


@dataclass(frozen=True)
class CpuTimes:
    total: int
    idle: int


def cpu_times(proc_stat: Path = PROC_STAT) -> CpuTimes | None:
    try:
        with proc_stat.open() as source:
            first = source.readline().split()
        if first[0] != "cpu" or len(first) < 9:
            return None
        fields = [int(x) for x in first[1:]]
        # guest/guest_nice are already included in user/nice by the kernel.
        return CpuTimes(sum(fields[:8]), fields[3] + fields[4])
    except (OSError, ValueError, IndexError):
        return None


def cpu_percent(before: CpuTimes | None, after: CpuTimes | None) -> float | None:
    if before is None or after is None:
        return None
    delta_total = after.total - before.total
    delta_idle = after.idle - before.idle
    if delta_total <= 0 or not 0 <= delta_idle <= delta_total:
        return None
    return max(0.0, min(100.0, 100.0 * (delta_total - delta_idle) / delta_total))

