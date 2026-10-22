import tempfile
import unittest
from pathlib import Path

from sama_lcd.metrics import CpuTimes, cpu_percent, cpu_times, tctl_celsius


class MetricsTest(unittest.TestCase):
    def test_tctl_uses_label_and_millidegrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = Path(tmp) / "hwmon1"
            node.mkdir()
            (node / "name").write_text("k10temp\n")
            (node / "temp1_label").write_text("Tccd1\n")
            (node / "temp1_input").write_text("32000\n")
            (node / "temp2_label").write_text("Tctl\n")
            (node / "temp2_input").write_text("40900\n")
            self.assertEqual(tctl_celsius(Path(tmp)), 40.9)

    def test_no_sensor_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(tctl_celsius(Path(tmp)))

    def test_cpu_total_excludes_guest_double_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            stat = Path(tmp) / "stat"
            stat.write_text("cpu  10 1 3 20 2 1 1 0 5 0\n")
            self.assertEqual(cpu_times(stat), CpuTimes(38, 22))

    def test_cpu_delta(self):
        self.assertEqual(cpu_percent(CpuTimes(100, 40), CpuTimes(200, 65)), 75.0)
        self.assertIsNone(cpu_percent(None, CpuTimes(200, 65)))


if __name__ == "__main__":
    unittest.main()

