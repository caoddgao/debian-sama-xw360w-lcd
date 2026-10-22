"""Small GTK theme chooser for the local 480x480 SAMA catalogue."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

PROJECT = Path(__file__).resolve().parents[2]
THEMES = PROJECT / "assets/themes/official"
CONFIG = PROJECT / "config.json"


class ThemePicker(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.renping.SamaThemePicker")

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self, title="先马水冷屏主题")
        window.set_default_size(850, 650)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(16)
        outer.set_margin_bottom(16)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        window.set_child(outer)

        title = Gtk.Label(label="选择官方内置主题")
        title.add_css_class("title-2")
        title.set_xalign(0)
        outer.append(title)
        self.status = Gtk.Label(label="点击预览图即可应用到水冷屏。动画主题目前显示静态首帧。")
        self.status.set_xalign(0)
        self.status.set_wrap(True)
        outer.append(self.status)

        simple = Gtk.Button(label="使用原来的简洁画面")
        simple.connect("clicked", self.select, None)
        outer.append(simple)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        outer.append(scroller)
        flow = Gtk.FlowBox()
        flow.set_max_children_per_line(4)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_row_spacing(12)
        flow.set_column_spacing(12)
        scroller.set_child(flow)

        catalogue_path = THEMES / "catalogue.json"
        catalogue = json.loads(catalogue_path.read_text()) if catalogue_path.exists() else []
        for theme in catalogue:
            preview = THEMES / theme["id"] / "preview.png"
            button = Gtk.Button()
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            image = Gtk.Picture.new_for_filename(str(preview))
            image.set_size_request(170, 170)
            image.set_content_fit(Gtk.ContentFit.CONTAIN)
            card.append(image)
            card.append(Gtk.Label(label=theme["name"]))
            button.set_child(card)
            button.connect("clicked", self.select, theme["id"])
            flow.insert(button, -1)
        if not catalogue:
            self.status.set_text("未找到本机官方主题，请先运行导入程序。")
        window.present()

    def select(self, _button, theme_id):
        try:
            settings = json.loads(CONFIG.read_text())
            settings["theme"] = theme_id
            with tempfile.NamedTemporaryFile("w", dir=PROJECT, prefix=".config-", suffix=".json",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(settings, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, CONFIG)
            result = subprocess.run(["systemctl", "--user", "restart", "sama-xw360w-lcd.service"],
                                    capture_output=True, text=True, timeout=12)
            if result.returncode:
                self.status.set_text(f"配置已保存，服务启动失败：{result.stderr.strip()}")
            else:
                name = "原来的简洁画面" if theme_id is None else f"官方主题 {int(theme_id[5:]):02}"
                self.status.set_text(f"已选择{name}，正在水冷屏上显示。")
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            self.status.set_text(f"应用主题失败：{exc}")


if __name__ == "__main__":
    ThemePicker().run()
