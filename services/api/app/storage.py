from __future__ import annotations

import asyncio
import hashlib
import io
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import Settings

MAX_CV_BYTES = 5 * 1024 * 1024
MAX_PROPERTY_IMAGE_BYTES = 10 * 1024 * 1024
MAX_ACQUISITION_SNAPSHOT_BYTES = 8 * 1024 * 1024
IMAGE_MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}
MIME_TYPES = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass(frozen=True)
class StoredFile:
    storage_key: str
    original_filename: str
    declared_mime_type: str
    verified_format: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class StoredImage(StoredFile):
    width: int
    height: int


class PrivateStorage:
    def __init__(self, settings: Settings) -> None:
        if settings.private_storage_backend != "local":
            raise RuntimeError(
                "The configured private object-storage adapter is not available locally."
            )
        self.root = Path(settings.private_storage_path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        if candidate.parent != self.root:
            raise RuntimeError("Unsafe private storage key")
        return candidate

    async def save_cv(self, upload: UploadFile) -> StoredFile:
        filename = upload.filename or ""
        if (
            not filename
            or Path(filename).name != filename
            or "/" in filename
            or "\\" in filename
            or "\x00" in filename
        ):
            raise _invalid_file("Use a valid filename.")
        extension = Path(filename).suffix.lower().removeprefix(".")
        if extension not in MIME_TYPES or upload.content_type != MIME_TYPES[extension]:
            raise _invalid_file("CV must be a PDF, DOC or DOCX with a matching content type.")
        content = await upload.read(MAX_CV_BYTES + 1)
        await upload.close()
        if not content or len(content) > MAX_CV_BYTES:
            raise _invalid_file(
                "CV must be no larger than 5 MB.", too_large=len(content) > MAX_CV_BYTES
            )
        _verify_content(extension, content)
        storage_key = f"{uuid.uuid4().hex}.{extension}"
        self._path(storage_key).write_bytes(content)
        return StoredFile(
            storage_key=storage_key,
            original_filename=filename[:255],
            declared_mime_type=upload.content_type,
            verified_format=extension,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    async def save_property_image(self, upload: UploadFile) -> StoredImage:
        return await self._save_image(upload, "property")

    async def save_project_image(self, upload: UploadFile) -> StoredImage:
        return await self._save_image(upload, "project")

    async def save_acquisition_snapshot(
        self, content: bytes, content_type: str | None
    ) -> StoredFile:
        if not content or len(content) > MAX_ACQUISITION_SNAPSHOT_BYTES:
            raise ValueError("Acquisition snapshot is empty or exceeds the private-storage limit.")
        extensions = {
            "application/json": "json",
            "application/ld+json": "json",
            "application/pdf": "pdf",
            "application/xhtml+xml": "html",
            "application/xml": "xml",
            "text/html": "html",
            "text/xml": "xml",
        }
        extension = extensions.get(content_type or "")
        if not extension:
            raise ValueError("Acquisition snapshot content type is not supported.")
        storage_key = f"acquisition-{uuid.uuid4().hex}.{extension}"
        await asyncio.to_thread(self._path(storage_key).write_bytes, content)
        return StoredFile(
            storage_key=storage_key,
            original_filename=f"official-source.{extension}",
            declared_mime_type=content_type or "application/octet-stream",
            verified_format=extension,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    async def _save_image(self, upload: UploadFile, prefix: str) -> StoredImage:
        filename = upload.filename or ""
        if (
            not filename
            or Path(filename).name != filename
            or any(value in filename for value in ("/", "\\", "\x00"))
        ):
            raise _invalid_image("Use a valid image filename.")
        extension = Path(filename).suffix.lower().removeprefix(".")
        if extension not in IMAGE_MIME_TYPES or upload.content_type != IMAGE_MIME_TYPES[extension]:
            raise _invalid_image(
                "Cover image must be a JPEG, PNG or WebP with a matching content type."
            )
        content = await upload.read(MAX_PROPERTY_IMAGE_BYTES + 1)
        await upload.close()
        if not content or len(content) > MAX_PROPERTY_IMAGE_BYTES:
            raise _invalid_image("Cover image must be no larger than 10 MB.", too_large=True)
        try:
            with Image.open(io.BytesIO(content)) as source:
                source.verify()
            with Image.open(io.BytesIO(content)) as source:
                width, height = source.size
                if width < 320 or height < 180 or width * height > 40_000_000:
                    raise _invalid_image("Cover image dimensions are outside the accepted range.")
                output = io.BytesIO()
                if extension in {"jpg", "jpeg"}:
                    source.convert("RGB").save(output, format="JPEG", quality=90, optimize=True)
                    stored_extension = "jpg"
                elif extension == "png":
                    source.save(output, format="PNG", optimize=True)
                    stored_extension = "png"
                else:
                    source.save(output, format="WEBP", quality=90, method=6)
                    stored_extension = "webp"
                sanitized = output.getvalue()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise _invalid_image(
                "The uploaded file is not a decodable JPEG, PNG or WebP image."
            ) from exc
        storage_key = f"{prefix}-{uuid.uuid4().hex}.{stored_extension}"
        await asyncio.to_thread(self._path(storage_key).write_bytes, sanitized)
        return StoredImage(
            storage_key,
            filename[:255],
            IMAGE_MIME_TYPES[stored_extension],
            stored_extension,
            len(sanitized),
            hashlib.sha256(sanitized).hexdigest(),
            width,
            height,
        )

    def read(self, storage_key: str) -> bytes:
        path = self._path(storage_key)
        if not path.is_file():
            raise FileNotFoundError(storage_key)
        return path.read_bytes()

    def delete(self, storage_key: str) -> None:
        path = self._path(storage_key)
        if path.is_file():
            path.unlink()


def _verify_content(extension: str, content: bytes) -> None:
    if extension == "pdf" and not content.startswith(b"%PDF-"):
        raise _invalid_file("The uploaded file is not a valid PDF.")
    if extension == "doc" and not content.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        raise _invalid_file("The uploaded file is not a valid legacy Word document.")
    if extension == "docx":
        if not content.startswith(b"PK\x03\x04"):
            raise _invalid_file("The uploaded file is not a valid DOCX document.")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise _invalid_file("The uploaded file is not a valid DOCX document.")
        except zipfile.BadZipFile as exc:
            raise _invalid_file("The uploaded file is not a valid DOCX document.") from exc


def _invalid_file(message: str, *, too_large: bool = False) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE
        if too_large
        else status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_cv", "message": message},
    )


def _invalid_image(message: str, *, too_large: bool = False) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE
        if too_large
        else status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_property_image", "message": message},
    )
