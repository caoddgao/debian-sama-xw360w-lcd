import tempfile
import unittest
from pathlib import Path

from sama_lcd.metrics import CpuPackagePower, CpuTimes, cpu_opt_rpm, cpu_percent, cpu_times, tctl_celsius


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

    def test_cpu_opt_uses_asusec_and_exact_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / "hwmon1"
            wrong.mkdir()
            (wrong / "name").write_text("nct6799\n")
            (wrong / "fan1_label").write_text("CPU_Opt\n")
            (wrong / "fan1_input").write_text("600\n")
            ec = root / "hwmon11"
            ec.mkdir()
            (ec / "name").write_text("asusec\n")
            (ec / "fan1_label").write_text("CPU_Fan\n")
            (ec / "fan1_input").write_text("600\n")
            (ec / "fan2_label").write_text("CPU_Opt\n")
            (ec / "fan2_input").write_text("2510\n")
            self.assertEqual(cpu_opt_rpm(root), 2510)
            (ec / "fan2_input").unlink()
            self.assertIsNone(cpu_opt_rpm(root))

    def test_cpu_total_excludes_guest_double_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            stat = Path(tmp) / "stat"
            stat.write_text("cpu  10 1 3 20 2 1 1 0 5 0\n")
            self.assertEqual(cpu_times(stat), CpuTimes(38, 22))

    def test_cpu_delta(self):
        self.assertEqual(cpu_percent(CpuTimes(100, 40), CpuTimes(200, 65)), 75.0)
        self.assertIsNone(cpu_percent(None, CpuTimes(200, 65)))

    def test_package_power_uses_energy_delta_and_wraps_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            zone = Path(tmp) / "intel-rapl:0"
            zone.mkdir()
            (zone / "name").write_text("package-0\n")
            (zone / "max_energy_range_uj").write_text("100000000\n")
            energy = zone / "energy_uj"
            energy.write_text("90000000\n")
            sampler = CpuPackagePower(Path(tmp))
            self.assertIsNone(sampler.sample(now=1.0))
            energy.write_text("20000000\n")
            self.assertAlmostEqual(sampler.sample(now=2.0), 30.0)
            energy.write_text("45000000\n")
            self.assertAlmostEqual(sampler.sample(now=3.0), 25.0)

    def test_package_power_missing_sensor_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(CpuPackagePower(Path(tmp)).sample(now=1.0))


if __name__ == "__main__":
    unittest.main()

