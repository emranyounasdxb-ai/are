from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

MAX_RASTER_BYTES = 10 * 1024 * 1024
MAX_RASTER_PIXELS = 40_000_000


@dataclass(frozen=True)
class ValidatedRaster:
    content: bytes
    mime_type: str
    extension: str
    width: int
    height: int
    sha256: str


def validate_raster(content: bytes, declared_mime: str) -> ValidatedRaster:
    if not content or len(content) > MAX_RASTER_BYTES:
        raise ValueError("Raster media is empty or exceeds the acquisition limit.")
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.verify()
        with Image.open(io.BytesIO(content)) as source:
            width, height = source.size
            if width < 320 or height < 180 or width * height > MAX_RASTER_PIXELS:
                raise ValueError("Raster media dimensions are outside the accepted range.")
            output = io.BytesIO()
            if source.format == "JPEG" and declared_mime == "image/jpeg":
                source.convert("RGB").save(output, "JPEG", quality=90, optimize=True)
                mime, extension = "image/jpeg", "jpg"
            elif source.format == "PNG" and declared_mime == "image/png":
                source.save(output, "PNG", optimize=True)
                mime, extension = "image/png", "png"
            elif source.format == "WEBP" and declared_mime == "image/webp":
                source.save(output, "WEBP", quality=90, method=6)
                mime, extension = "image/webp", "webp"
            else:
                raise ValueError("Raster extension, MIME and decoded format do not match.")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Raster media is not a decodable JPEG, PNG or WebP image.") from exc
    sanitized = output.getvalue()
    return ValidatedRaster(
        content=sanitized,
        mime_type=mime,
        extension=extension,
        width=width,
        height=height,
        sha256=hashlib.sha256(sanitized).hexdigest(),
    )


def duplicate_hash(existing_hashes: set[str], raster: ValidatedRaster) -> bool:
    return raster.sha256 in existing_hashes
