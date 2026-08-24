from __future__ import annotations

import hashlib
import io
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import Settings

MAX_CV_BYTES = 5 * 1024 * 1024
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
