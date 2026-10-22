"""CPU Tctl and aggregate utilization from kernel interfaces."""

from dataclasses import dataclass
from pathlib import Path

HWMON = Path("/sys/class/hwmon")
PROC_STAT = Path("/proc/stat")


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

