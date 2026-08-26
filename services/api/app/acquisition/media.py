from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from email.message import Message
from typing import Any, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from PIL import Image, UnidentifiedImageError

from app.acquisition.security import (
    USER_AGENT,
    AcquisitionSecurityError,
    validate_public_url,
)

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


@dataclass(frozen=True)
class RasterFetchResult:
    url: str
    body: bytes = b""
    content_type: str | None = None
    status: int | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == 200 and bool(self.body) and not self.error_code


@dataclass(frozen=True)
class ResponsiveDerivative:
    content: bytes
    format: Literal["webp", "avif"]
    mime_type: str
    width: int
    height: int
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class MediaQuality:
    status: str
    public_eligible: bool
    cover_eligible: bool
    rejection_reason: str | None


def classify_media_quality(raster: ValidatedRaster, category: str) -> MediaQuality:
    """Apply public-readiness dimensions without ever upscaling a source master."""
    return classify_media_dimensions(raster.width, raster.height, category)


def classify_media_dimensions(width: int, height: int, category: str) -> MediaQuality:
    """Classify already-decoded dimensions for API and operator display."""
    if category == "cover":
        eligible = width >= 1600 and height >= 900 and width > height
        return MediaQuality(
            "cover-ready" if eligible else "low-resolution",
            eligible,
            eligible,
            None if eligible else "High-resolution Cover image required",
        )
    minimum_long_edge = 1000 if category in {"floor-plan", "master-plan"} else 1200
    eligible = max(width, height) >= minimum_long_edge
    return MediaQuality(
        "public-ready" if eligible else "low-resolution",
        eligible,
        False,
        None if eligible else "Image does not meet the minimum public-readiness dimensions.",
    )


def normalized_media_filename(
    project_slug: str, category: str, display_order: int, digest: str, extension: str
) -> str:
    safe_slug = re.sub(r"[^a-z0-9]+", "-", project_slug.casefold()).strip("-")[:80]
    safe_category = re.sub(r"[^a-z0-9]+", "-", category.casefold()).strip("-")[:24]
    if not safe_slug or not safe_category or extension not in {"jpg", "png", "webp", "avif"}:
        raise ValueError("A safe project media filename could not be generated.")
    return f"{safe_slug}-{safe_category}-{display_order:02d}-{digest[:12]}.{extension}"


def responsive_derivatives(
    raster: ValidatedRaster, widths: tuple[int, ...] = (480, 960, 1600)
) -> tuple[ResponsiveDerivative, ...]:
    outputs: list[ResponsiveDerivative] = []
    with Image.open(io.BytesIO(raster.content)) as source:
        base = source.convert("RGB")
        for width in sorted({value for value in widths if 0 < value <= raster.width}):
            height = max(1, round(raster.height * width / raster.width))
            resized = base.resize((width, height), Image.Resampling.LANCZOS)
            for image_format, extension, mime_type, options in (
                ("WEBP", "webp", "image/webp", {"quality": 84, "method": 6}),
                ("AVIF", "avif", "image/avif", {"quality": 72}),
            ):
                buffer = io.BytesIO()
                resized.save(buffer, image_format, **options)
                content = buffer.getvalue()
                outputs.append(
                    ResponsiveDerivative(
                        content=content,
                        format=cast(Literal["webp", "avif"], extension),
                        mime_type=mime_type,
                        width=width,
                        height=height,
                        size_bytes=len(content),
                        sha256=hashlib.sha256(content).hexdigest(),
                    )
                )
    return tuple(outputs)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> None:
        return None


class SecureRasterFetcher:
    """Bounded HTTPS fetcher that revalidates every redirect destination."""

    def __init__(self, *, timeout_seconds: float = 12) -> None:
        self.timeout_seconds = timeout_seconds
        self._opener = build_opener(_NoRedirect())

    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> RasterFetchResult:
        current = _encode_raster_url(url)
        try:
            for _ in range(4):
                current = validate_public_url(current, allowed_domains)
                request = Request(  # noqa: S310 -- strict URL validation is performed above.
                    current,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "image/avif,image/webp,image/png,image/jpeg",
                    },
                )
                try:
                    with self._opener.open(request, timeout=self.timeout_seconds) as response:
                        content_type = response.headers.get_content_type().lower()
                        if content_type not in {
                            "image/jpeg",
                            "image/png",
                            "image/webp",
                            "image/avif",
                        }:
                            return RasterFetchResult(
                                current,
                                status=response.status,
                                error_code="unsupported_media_type",
                                error_message="Only JPEG, PNG and WebP raster media is accepted.",
                            )
                        body = response.read(MAX_RASTER_BYTES + 1)
                        if len(body) > MAX_RASTER_BYTES:
                            return RasterFetchResult(
                                current,
                                status=response.status,
                                error_code="media_too_large",
                                error_message="The image exceeds the private intake limit.",
                            )
                        return RasterFetchResult(current, body, content_type, response.status)
                except HTTPError as exc:
                    if exc.code in {301, 302, 303, 307, 308} and exc.headers.get("Location"):
                        current = _encode_raster_url(urljoin(current, str(exc.headers["Location"])))
                        continue
                    return RasterFetchResult(
                        current,
                        status=exc.code,
                        error_code=f"http_{exc.code}",
                        error_message="The media source returned an error.",
                    )
            return RasterFetchResult(
                current,
                error_code="redirect_limit",
                error_message="The media redirect limit was exceeded.",
            )
        except AcquisitionSecurityError as exc:
            return RasterFetchResult(
                current, error_code="security_rejected", error_message=str(exc)
            )
        except (TimeoutError, URLError, OSError) as exc:
            return RasterFetchResult(
                current, error_code="network_error", error_message=type(exc).__name__
            )


def _encode_raster_url(url: str) -> str:
    """Encode unsafe path/query characters without changing the destination host."""
    parsed = urlsplit(url)
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            quote(parsed.path, safe="/%:@+"),
            quote(parsed.query, safe="=&?/:@%+,;"),
            "",
        )
    )


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
            elif source.format == "AVIF" and declared_mime == "image/avif":
                source.convert("RGB").save(output, "AVIF", quality=90)
                mime, extension = "image/avif", "avif"
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


def thumbnail(raster: ValidatedRaster) -> bytes:
    with Image.open(io.BytesIO(raster.content)) as source:
        source.thumbnail((480, 320))
        output = io.BytesIO()
        source.convert("RGB").save(output, "WEBP", quality=82, method=6)
        return output.getvalue()
