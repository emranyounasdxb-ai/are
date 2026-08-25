from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.adapters import adapter_for
from app.acquisition.media import SecureRasterFetcher, thumbnail, validate_raster
from app.config import Settings
from app.models import ProjectImportBatch, ProjectImportCandidate, ProjectImportMedia
from app.storage import PrivateStorage

REJECTED_URL_TOKENS = (
    "favicon",
    "icon",
    "logo",
    "placeholder",
    "spinner",
    "social",
    "app-store",
    "google-play",
)


async def intake_private_media(
    db: AsyncSession,
    settings: Settings,
    batch_id: uuid.UUID,
    *,
    candidate_ids: list[uuid.UUID] | None = None,
    fetcher: SecureRasterFetcher | None = None,
) -> dict[str, int]:
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.id == batch_id)
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            )
        )
    )
    if not batch:
        raise ValueError("Import batch not found.")
    selected = [
        candidate
        for candidate in batch.candidates
        if candidate_ids is None or candidate.id in candidate_ids
    ]
    if candidate_ids and len(selected) != len(set(candidate_ids)):
        raise ValueError("Every media candidate must belong to the selected batch.")
    storage = PrivateStorage(settings)
    source_fetcher = fetcher or SecureRasterFetcher()
    existing_hashes = set(
        await db.scalars(
            select(ProjectImportMedia.sha256).where(ProjectImportMedia.sha256.is_not(None))
        )
    )
    stats = {
        "references": 0,
        "downloaded": 0,
        "deduplicated": 0,
        "failed": 0,
        "skipped_video": 0,
    }
    for candidate in sorted(selected, key=lambda value: value.manifest_row_id):
        adapter = adapter_for(str(candidate.owner_manifest_values.get("owner_developer", "")))
        for media in sorted(candidate.staged_media, key=lambda value: value.source_url)[:12]:
            stats["references"] += 1
            if media.category.value == "video-reference":
                stats["skipped_video"] += 1
                continue
            if media.storage_key or media.duplicate_of_id:
                continue
            if adapter is None or any(
                token in media.source_url.casefold() for token in REJECTED_URL_TOKENS
            ):
                media.stage_status = "failed"
                media.failure_reason = "Media URL is outside the bounded official raster policy."
                stats["failed"] += 1
                continue
            result = await asyncio.to_thread(
                source_fetcher.fetch, media.source_url, adapter.allowed_domains
            )
            media.retrieved_at = datetime.now(UTC)
            if not result.ok or not result.content_type:
                media.stage_status = "failed"
                media.failure_reason = (
                    result.error_message or result.error_code or "Fetch failed."
                )[:500]
                stats["failed"] += 1
                continue
            try:
                raster = await asyncio.to_thread(validate_raster, result.body, result.content_type)
            except ValueError as exc:
                media.stage_status = "failed"
                media.failure_reason = str(exc)[:500]
                stats["failed"] += 1
                continue
            duplicate = await db.scalar(
                select(ProjectImportMedia).where(
                    ProjectImportMedia.sha256 == raster.sha256,
                    ProjectImportMedia.id != media.id,
                )
            )
            if duplicate or raster.sha256 in existing_hashes:
                media.sha256 = raster.sha256
                media.mime_type = raster.mime_type
                media.size_bytes = len(raster.content)
                media.width = raster.width
                media.height = raster.height
                media.duplicate_of_id = duplicate.id if duplicate else None
                media.stage_status = "duplicate"
                stats["deduplicated"] += 1
                continue
            storage_key = await storage.save_acquisition_media(raster.content, raster.extension)
            try:
                thumbnail_content = await asyncio.to_thread(thumbnail, raster)
                thumbnail_key = await storage.save_acquisition_media(
                    thumbnail_content, "webp", thumbnail=True
                )
            except Exception:
                storage.delete(storage_key)
                raise
            media.storage_key = storage_key
            media.thumbnail_storage_key = thumbnail_key
            media.mime_type = raster.mime_type
            media.size_bytes = len(raster.content)
            media.sha256 = raster.sha256
            media.width = raster.width
            media.height = raster.height
            media.failure_reason = None
            media.stage_status = "downloaded"
            existing_hashes.add(raster.sha256)
            stats["downloaded"] += 1
        await db.commit()
    return stats
