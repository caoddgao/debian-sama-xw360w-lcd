"""Simple replaceable background and high contrast square layout."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = (480, 480)  # Candidate Turing 2.1-inch resolution; hardware trial pending.


def _font(size: int):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def frame(temp: float | None, usage: float | None, background: Path | None = None,
          trial: bool = False) -> Image.Image:
    if background:
        with Image.open(background) as source:
            image = source.convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)
    else:
        image = Image.new("RGB", SIZE, "#101922")
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 472, 472), outline="#3f7894", width=5)
    draw.text((93, 66), "CPU", font=_font(44), fill="#75d6e6")
    if trial:
        draw.text((88, 190), "TEST", font=_font(68), fill="white")
        draw.text((184, 390), "UP", font=_font(22), fill="#75d6e6")
    else:
        t = "--" if temp is None else f"{temp:.1f}"
        u = "--" if usage is None else f"{usage:.0f}"
        draw.text((90, 147), f"{t}°C", font=_font(59), fill="white")
        draw.text((89, 285), "LOAD", font=_font(32), fill="#75d6e6")
        draw.text((215, 280), f"{u}%", font=_font(55), fill="white")
    return image

