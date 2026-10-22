"""Convert this machine's installed SAMA 480x480 themes to local, untracked assets.

The .turtheme files are NRBF object graphs. Parsing them as data avoids executing
the Windows application or deserializing arbitrary .NET objects.
"""

import argparse
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "vendor" / "netfleece"))
import netfleece  # noqa: E402


def pick(obj, name, default=None):
    if not isinstance(obj, dict):
        return default
    for key in (f"<{name}>k__BackingField", f"GraphItem+<{name}>k__BackingField",
                f"GraphImage+<{name}>k__BackingField", name,
                f"GraphItem+_{name}", f"_{name}"):
        if key in obj:
            return obj[key]
    return default


def color(value):
    if not isinstance(value, dict):
        return "#ffffff"
    argb = value.get("value", 0)
    if value.get("state") == 1:
        # System.Drawing.KnownColor entries used by the bundled themes.
        known = {164: "#ffffff", 140: "#ff0000", 95: "#808080",
                 150: "#800080", 66: "#ffff00"}
        return known.get(value.get("knownColor"), "#ffffff")
    return f"#{argb & 0xffffff:06x}"


def save_bitmap(obj, target):
    if not isinstance(obj, dict) or not isinstance(obj.get("Data"), list):
        return None
    raw = bytes(obj["Data"])
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        if image.width > 1920 or image.height > 1920:
            raise ValueError("Unexpected theme bitmap size")
        image.save(target, "PNG")
    return target.name


def convert_item(item, number, target):
    kind = pick(item, "TypeName")
    if not kind or pick(item, "hide", False):
        return None
    result = {"kind": kind, "x": pick(item, "posX", 0), "y": pick(item, "posY", 0)}
    if kind in ("Image", "Animation", "Clock"):
        bitmap = pick(item, "bitmap")
        image = save_bitmap(bitmap, target / f"layer{number:02}.png")
        if image:
            result["image"] = image
    metric = pick(item, "m_data")
    if isinstance(metric, dict):
        result["metric"] = pick(metric, "DataName")
        result["show_unit"] = bool(pick(metric, "ShowUnit", True))
        result["sample"] = pick(metric, "ValueWithUnit", "")
        result["value"] = metric.get("_Value", "")
    font = pick(item, "fontConfig")
    if isinstance(font, dict):
        result["font"] = pick(font, "name", "")
        result["size"] = pick(font, "size", 20)
        result["color"] = color(pick(font, "color"))
        result["align"] = pick(pick(font, "alignment"), "index", 0)
    for name in ("width", "height", "radius", "diameter", "archWidth",
                 "startPer", "totalAngel", "centerX", "centerY", "angle",
                 "endAngle", "maxValue", "lineWidth", "borderWidth"):
        value = pick(item, name)
        if value is not None:
            result[name] = value
    for name in ("FrontColor", "BackColor", "LineColor", "FillColor", "BorderColor"):
        value = pick(item, name)
        if value is not None:
            result[name] = color(value)
    return result


def import_themes(source, output):
    output.mkdir(parents=True, exist_ok=True)
    catalogue = []
    for path in sorted(source.glob("theme[0-9][0-9].turtheme")):
        with path.open("rb") as stream:
            data = netfleece.parse(stream, backfill=True, crunch=True)
        if (pick(data, "width"), pick(data, "height")) != (480, 480):
            continue
        target = output / path.stem
        target.mkdir(parents=True, exist_ok=True)
        preview = save_bitmap(pick(data, "themePic"), target / "preview.png")
        graph = pick(data, "GraphList").get("Collection`1+items")
        items = graph["_items"][:graph["_size"]]
        layers = [converted for n, item in enumerate(items)
                  if isinstance(item, dict)
                  if (converted := convert_item(item, n, target))]
        date_layers = [layer for layer in layers if layer.get("metric") == "DATE"]
        if len(date_layers) in (2, 3):
            parts = ("month", "day") if len(date_layers) == 2 else ("year", "month", "day")
            for layer, part in zip(date_layers, parts):
                layer["date_part"] = part
        meta = {"id": path.stem, "name": f"官方主题 {int(path.stem[5:]):02}",
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "preview": preview, "layers": layers}
        (target / "theme.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        catalogue.append({"id": meta["id"], "name": meta["name"]})
    fonts = source.parents[1] / "fonts"
    if fonts.exists():
        destination = output / "fonts"
        destination.mkdir(exist_ok=True)
        for font in fonts.iterdir():
            if font.suffix.lower() in (".ttf", ".otf"):
                shutil.copy2(font, destination / font.name)
    (output / "catalogue.json").write_text(json.dumps(catalogue, ensure_ascii=False, indent=2))
    print(f"Imported {len(catalogue)} official themes into {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="installed SAMA theme/480480r directory")
    parser.add_argument("--output", type=Path, default=PROJECT / "assets/themes/official")
    args = parser.parse_args()
    import_themes(args.source, args.output)
