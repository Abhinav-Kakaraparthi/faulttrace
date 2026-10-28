"""Offline synthetic fixture generation; Pillow 13.0.0 and portable PNG writer.

Pillow is a development-only generator/viewer dependency, never imported by
the probe. No system fonts, external assets, PNG text, or alpha channels.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
try:
    from tools.canonical_png import encode
except ModuleNotFoundError:  # Direct invocation: python tools/generate_image_fixtures.py.
    from canonical_png import encode

ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "image-evidence"
DISPLAY = (65, 105, 415, 230)


def generate(directory=ROOT):
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (480, 300), (224, 229, 233))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((25, 25, 455, 275), radius=18, fill=(57, 67, 76))
    label = ImageFont.load_default(size=21)
    small = ImageFont.load_default(size=16)
    draw.text((67, 55), "DIFFERENTIAL PRESSURE", font=label, fill=(240, 244, 248))
    draw.text((67, 245), "SYNTHETIC TEST INSTRUMENT", font=small, fill=(211, 218, 224))
    for x, y in ((43, 43), (437, 43), (43, 257), (437, 257)):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(175, 184, 193))
        draw.line((x - 3, y, x + 3, y), fill=(75, 82, 89))
    draw.rectangle(DISPLAY, fill=(12, 25, 22))
    # Seven-segment digits; expected value belongs only to this offline generator/tests.
    segments = ((8, 0, 42, 7), (43, 8, 50, 39), (43, 48, 50, 79),
                (8, 80, 42, 87), (0, 48, 7, 79), (0, 8, 7, 39), (8, 40, 42, 47))
    for x, active in zip((92, 160, 228), ((1, 2), tuple(range(7)), (0, 1, 2, 3, 4, 5))):
        for index in active:
            a, b, c, d = segments[index]
            draw.rectangle((x + a, 123 + b, x + c, 123 + d), fill=(104, 250, 171))
    draw.text((310, 174), "kPa", font=ImageFont.load_default(size=28), fill=(104, 250, 171))
    obscured = image.copy()
    # Opaque pixel replacement: no blur, transparency, hidden layer, or surviving digit.
    ImageDraw.Draw(obscured).rectangle(DISPLAY, fill=(87, 91, 96))
    manifest = {}
    for fixture_id, frame, ref in (("panel-a", image, "image-001"),
                                   ("panel-b", obscured, "image-002")):
        path = directory / (fixture_id + ".png")
        path.write_bytes(encode(frame))
        manifest[fixture_id] = {"evidence_ref": ref, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()
