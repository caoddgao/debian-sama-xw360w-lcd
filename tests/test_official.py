import unittest
from datetime import datetime

from PIL import Image, ImageDraw

from unittest.mock import patch

from sama_lcd.official import _draw_arch_bar, _draw_chart, _metric_text, sample_values


class OfficialThemeTest(unittest.TestCase):
    def test_temperature_uses_theme_unit_and_live_value(self):
        layer = {"metric": "CPUTEMP", "sample": "47°", "show_unit": True}
        self.assertEqual(_metric_text(layer, {"CPUTEMP": 41.4}, datetime(2026, 10, 22)), "41°")
        self.assertEqual(_metric_text(layer, {}, datetime(2026, 10, 22)), "--")

    def test_split_date_and_short_day_follow_theme_layout(self):
        now = datetime(2026, 10, 22, 20, 10)
        self.assertEqual(_metric_text({"metric": "DATE", "date_part": "month", "sample": "09"}, {}, now), "10")
        self.assertEqual(_metric_text({"metric": "DATE", "date_part": "day", "sample": "28"}, {}, now), "22")
        self.assertEqual(_metric_text({"metric": "DAY", "sample": "Thu"}, {}, now), "Thu")

    def test_theme04_pump_uses_live_rpm_and_theme_suffix(self):
        with patch("sama_lcd.official.cpu_opt_rpm", return_value=2510):
            values = sample_values("theme04", 40.0, 10.0)
        self.assertEqual(values["WATERPUMP"], 2510)
        layer = {"metric": "WATERPUMP", "sample": "1406R", "show_unit": True}
        self.assertEqual(_metric_text(layer, values, datetime(2026, 10, 22)), "2510R")
        self.assertEqual(_metric_text(layer, {"WATERPUMP": None}, datetime(2026, 10, 22)), "--")

    def test_arch_bar_track_remains_visible_at_zero_usage(self):
        layer = {"kind": "ArchBar", "x": 10, "y": 10, "diameter": 80,
                 "archWidth": 4, "startPer": 25, "totalAngel": 180,
                 "metric": "CPULOAD", "FrontColor": "#c193fc", "BackColor": "#ffffff"}
        canvas = Image.new("RGB", (100, 100), "black")
        draw = ImageDraw.Draw(canvas)
        _draw_arch_bar(draw, layer, {"CPULOAD": 0})
        self.assertEqual(canvas.getpixel((50, 89)), (193, 147, 252))
        _draw_arch_bar(draw, layer, {"CPULOAD": 50})
        self.assertEqual(canvas.getpixel((22, 78)), (255, 255, 255))
        self.assertEqual(canvas.getpixel((78, 78)), (193, 147, 252))

    def test_chart_has_border_at_zero_and_fills_usage_history(self):
        layer = {"x": 10, "y": 10, "width": 80, "height": 40, "metric": "CPULOAD",
                 "maxValue": 100, "FillColor": "#c0c0c0", "LineColor": "#800080",
                 "BorderColor": "#800080"}
        canvas = Image.new("RGB", (100, 60), "black")
        draw = ImageDraw.Draw(canvas)
        _draw_chart(draw, layer, {"CPULOAD": 0}, {"CPULOAD": [0]})
        self.assertEqual(canvas.getpixel((50, 10)), (128, 0, 128))
        self.assertEqual(canvas.getpixel((50, 25)), (0, 0, 0))
        _draw_chart(draw, layer, {"CPULOAD": 50}, {"CPULOAD": [50]})
        self.assertEqual(canvas.getpixel((50, 35)), (192, 192, 192))


if __name__ == "__main__":
    unittest.main()
