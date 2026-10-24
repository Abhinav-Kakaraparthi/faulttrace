"""Bounded image decoding; discard metadata and never accept file paths."""
import hashlib
from io import BytesIO
import json
import warnings

from PIL import Image

from .storage import ROOT, WorkflowError

MAX_UPLOAD = 2 * 1024 * 1024
MAX_PIXELS = 1024 * 1024
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def validate_upload(data, mime, fixture_id=None):
    if not data or len(data) > MAX_UPLOAD:
        raise WorkflowError("image_size_invalid", 413)
    if mime not in ("image/png", "image/jpeg"):
        raise WorkflowError("image_type_invalid", 415)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data), formats=("PNG", "JPEG")) as image:
                expected = "PNG" if mime == "image/png" else "JPEG"
                if image.format != expected or getattr(image, "n_frames", 1) != 1:
                    raise ValueError()
                width, height = image.size
                if not (16 <= width <= 2048 and 16 <= height <= 2048 and width * height <= MAX_PIXELS):
                    raise ValueError()
                image.verify()
            with Image.open(BytesIO(data), formats=("PNG", "JPEG")) as image:
                image.load()
                rgba = image.convert("RGBA")
                clean = Image.new("RGBA", rgba.size, "white")
                clean.alpha_composite(rgba)
                output = BytesIO()
                clean.convert("RGB").save(output, format="PNG")
                normalized = output.getvalue()
                if len(normalized) > MAX_UPLOAD:
                    raise ValueError()
    except Exception:
        raise WorkflowError("image_bytes_or_dimensions_invalid", 400) from None
    digest = hashlib.sha256(data).hexdigest()
    if fixture_id is not None:
        manifest = json.loads((ROOT / "fixtures/image-evidence/manifest.json").read_text())
        if fixture_id not in ("panel-a", "panel-b") or manifest[fixture_id]["sha256"] != digest:
            raise WorkflowError("fixture_provenance_mismatch", 400)
    return {"bytes": normalized, "sha256": digest, "width": width, "height": height,
            "origin": "synthetic-fixture" if fixture_id else "user-upload", "fixture_id": fixture_id}
