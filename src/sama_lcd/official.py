"""Render locally imported official SAMA themes without executing Windows code."""

import json
import shutil
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .metrics import cpu_opt_rpm

ROOT = Path(__file__).resolve().parents[2] / "assets/themes/official"
SIZE = (480, 480)


@lru_cache
def catalogue():
    path = ROOT / "catalogue.json"
    return json.loads(path.read_text()) if path.exists() else []


@lru_cache
def load_theme(theme_id):
    if theme_id not in {theme["id"] for theme in catalogue()}:
        raise ValueError(f"未知官方主题：{theme_id}")
    base = ROOT / theme_id
    return base, json.loads((base / "theme.json").read_text())


@lru_cache(maxsize=64)
def _font(name, size):
    # Windows theme sizes are points; Pillow expects pixels (96 dpi / 72 dpi).
    pixels = max(6, round(float(size) * 4 / 3))
    names = {
        "Kumbh Sans": "KumbhSans-Regular.ttf",
        "Kumbh Sans Light": "KumbhSans-Light.ttf",
        "Kumbh Sans Medium": "KumbhSans-Medium.ttf",
        "Kumbh Sans SemiBold": "KumbhSans-SemiBold.ttf",
        "Kumbh Sans Bold": "KumbhSans-Bold.ttf",
        "LiquidCrystal-Normal": "LiquidCrystal-Normal.otf",
        "LiquidCrystal-Light": "LiquidCrystal-Light.otf",
    }
    candidate = ROOT / "fonts" / names.get(name, name.replace(" ", "") + ".ttf")
    if candidate.exists():
        return ImageFont.truetype(str(candidate), pixels)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", pixels)


def _metric_text(layer, values, now):
    key = layer.get("metric")
    sample = layer.get("sample", "")
    if key == "StaticText":
        return layer.get("value") or sample
    if key == "TIME":
        if ":" not in sample and len(sample) <= 2:
            return now.strftime("%S")
        return now.strftime("%H:%M:%S" if sample.count(":") > 1 else "%H:%M")
    if key == "DATE":
        part = layer.get("date_part")
        if part:
            return now.strftime({"year": "%Y", "month": "%m", "day": "%d"}[part])
        if "-" in sample:
            return now.strftime("%Y-%m-%d")
        if "/" in sample:
            return now.strftime("%Y/%m/%d")
        return now.strftime("%m.%d")
    if key == "DAY":
        return now.strftime("%a" if len(sample) <= 3 else "%A")
    value = values.get(key)
    if value is None:
        return "--"
    if isinstance(value, str):
        return value
    if key in ("CPUTEMP", "GPUTEMP"):
        number = f"{value:.0f}"
        suffix = "°C" if "°C" in sample else "℃" if "℃" in sample else "°" if "°" in sample else ""
    elif key in ("CPUCLOCK", "CPUCLOCK_G", "GPUCLOCK"):
        number = f"{value / 1000:.1f}" if key.endswith("_G") else f"{value:.0f}"
        suffix = "G" if key.endswith("_G") else "M" if sample.endswith("M") else ""
    elif key in ("CPUPWR", "GPUPWR"):
        number, suffix = f"{value:.0f}", "W" if "W" in sample else ""
    elif key == "WATERPUMP":
        number, suffix = f"{value:.0f}", "R" if sample.endswith("R") else ""
    else:
        number = f"{value:.0f}"
        suffix = "%" if "%" in sample or key.endswith("LOAD") else ""
    return number + (suffix if layer.get("show_unit", True) else "")


def _percent(layer, values):
    value = values.get(layer.get("metric"))
    if isinstance(value, (int, float)):
        return max(0, min(100, value)) / 100
    return 0


def _draw_arch_bar(draw, layer, values):
    diameter = layer.get("diameter", 0)
    if not diameter:
        return
    x, y = int(layer["x"]), int(layer["y"])
    box = (x, y, x + diameter, y + diameter)
    # SAMA measures startPer clockwise from 12 o'clock; Pillow uses 3 o'clock.
    start = layer.get("startPer", 0) * 3.6 - 90
    end = start + layer.get("totalAngel", 180)
    width = max(1, layer.get("archWidth", 10))
    # The official theme 15 preview has a full purple track and a white fill
    # growing from the left as CPU usage rises.
    draw.arc(box, start, end, fill=layer.get("FrontColor", "white"), width=width)
    progress = _percent(layer, values)
    if progress:
        draw.arc(box, end - (end - start) * progress, end,
                 fill=layer.get("BackColor", "white"), width=width)


def _draw_chart(draw, layer, values, history=None):
    x, y = int(layer["x"]), int(layer["y"])
    width, height = int(layer.get("width", 0)), int(layer.get("height", 0))
    if width < 2 or height < 2:
        return
    right, bottom = x + width - 1, y + height - 1
    metric = layer.get("metric")
    samples = list(history.get(metric, ())) if history else []
    if not samples and isinstance(values.get(metric), (int, float)):
        samples = [values[metric]]
    if samples:
        # Fill unused history with the earliest sample so the chart is visible
        # immediately, then scroll left as one-second readings arrive.
        samples = ([samples[0]] * (max(0, 64 - len(samples))) + samples)[-64:]
        maximum = max(1, float(layer.get("maxValue", 100)))
        points = [(x + round(i * (width - 1) / (len(samples) - 1)),
                   bottom - round((height - 2) * max(0, min(maximum, value)) / maximum))
                  for i, value in enumerate(samples)]
        draw.polygon([(x, bottom), *points, (right, bottom)], fill=layer.get("FillColor", "#c0c0c0"))
        draw.line(points, fill=layer.get("LineColor", "white"), width=max(1, layer.get("lineWidth", 1)))
    draw.rectangle((x, y, right, bottom), outline=layer.get("BorderColor", "white"),
                   width=max(1, layer.get("borderWidth", 1)))


@lru_cache(maxsize=128)
def _image(path):
    with Image.open(path) as source:
        return source.convert("RGBA")


def _cpu_mhz():
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("cpu MHz"):
                return float(line.split(":", 1)[1])
    except (OSError, ValueError):
        pass
    return None


def _memory_load():
    try:
        lines = Path("/proc/meminfo").read_text().splitlines()
        fields = {line.split(":", 1)[0]: int(line.split()[1]) for line in lines}
        return 100 * (1 - fields["MemAvailable"] / fields["MemTotal"])
    except (OSError, ValueError, KeyError, ZeroDivisionError):
        return None


def _gpu_values():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,clocks.gr,power.draw,memory.used,memory.total",
             "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=0.8, check=True)
        name, temp, load, clock, power, used, total = [part.strip() for part in result.stdout.splitlines()[0].split(",")]
        return {"GPUMODEL": name, "GPUTEMP": float(temp), "GPULOAD": float(load),
                "GPUCLOCK": float(clock), "GPUPWR": float(power),
                "GPURAMLOAD": 100 * float(used) / float(total)}
    except (OSError, ValueError, IndexError, subprocess.SubprocessError, ZeroDivisionError):
        return {}


def sample_values(theme_id, temp, usage, power_sampler=None):
    _, theme = load_theme(theme_id)
    required = {layer.get("metric") for layer in theme["layers"]}
    values = {"CPUTEMP": temp, "CPULOAD": usage}
    if "CPUPWR" in required and power_sampler is not None:
        values["CPUPWR"] = power_sampler.sample()
    if "WATERPUMP" in required:
        values["WATERPUMP"] = cpu_opt_rpm()
    if "CPUCLOCK" in required or "CPUCLOCK_G" in required:
        values["CPUCLOCK"] = values["CPUCLOCK_G"] = _cpu_mhz()
    if "RAMLOAD" in required:
        values["RAMLOAD"] = _memory_load()
    if "DRVLOAD" in required:
        try:
            disk = shutil.disk_usage("/")
            values["DRVLOAD"] = 100 * disk.used / disk.total
        except (OSError, ZeroDivisionError):
            pass
    if "CPUMODEL" in required:
        try:
            values["CPUMODEL"] = next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                                      if line.startswith("model name"))
        except (OSError, StopIteration):
            pass
    if any(key and key.startswith("GPU") for key in required):
        values.update(_gpu_values())
    return values


def render(theme_id, values, now=None, history=None):
    base, theme = load_theme(theme_id)
    now = now or datetime.now()
    canvas = Image.new("RGBA", SIZE, "black")
    draw = ImageDraw.Draw(canvas)
    for layer in theme["layers"]:
        kind = layer["kind"]
        x, y = int(layer["x"]), int(layer["y"])
        if kind in ("Image", "Animation") and layer.get("image"):
            canvas.alpha_composite(_image(base / layer["image"]), (x, y))
            draw = ImageDraw.Draw(canvas)
        elif kind in ("Data", "Text"):
            label = _metric_text(layer, values, now)
            if theme_id == "theme21":
                if layer.get("metric") != "DATE":
                    y += 10
                if label == "CPU：":
                    label = "CPU:"
            font = _font(layer.get("font", ""), layer.get("size", 20))
            align = layer.get("align", 0)
            anchor = "ra" if align == 2 else "ma" if align == 1 else "la"
            text_x = x - round(font.size * 0.2) if align == 2 else x
            draw.text((text_x, y), label, font=font, fill=layer.get("color", "white"), anchor=anchor)
        elif kind == "StatuBar":
            width, height = layer.get("width", 0), layer.get("height", 0)
            pct = _percent(layer, values)
            if layer.get("BackColor") and layer.get("BackColor") != "#ffffff":
                draw.rectangle((x, y, x + width, y + height), fill=layer["BackColor"])
            if pct:
                draw.rectangle((x, y, x + width * pct, y + height), fill=layer.get("FrontColor", "white"))
        elif kind == "ArchBar":
            _draw_arch_bar(draw, layer, values)
        elif kind == "Chart":
            _draw_chart(draw, layer, values, history)
        elif kind == "Clock" and layer.get("image"):
            hand = _image(base / layer["image"])
            metric = layer.get("metric")
            angle = (now.second * 6 if "S" in str(metric) else
                     now.minute * 6 if "M" in str(metric) else
                     (now.hour % 12 + now.minute / 60) * 30)
            hand = hand.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=False)
            canvas.alpha_composite(hand, (x, y))
            draw = ImageDraw.Draw(canvas)
    return canvas.convert("RGB")
