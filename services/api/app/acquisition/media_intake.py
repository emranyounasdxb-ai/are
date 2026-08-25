from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.adapters import adapter_for
from app.acquisition.media import (
    SecureRasterFetcher,
    classify_media_quality,
    normalized_media_filename,
    responsive_derivatives,
    thumbnail,
    validate_raster,
)
from app.acquisition.sobha_siniya_pilot import media_domains_for_candidate
from app.acquisition.tanami import TANAMI_ADAPTER_KEY, TANAMI_MEDIA_DOMAINS
from app.config import Settings
from app.models import (
    ImportReviewStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectProcessingStatus,
)
from app.project_processing import descriptive_media_filename, public_media_metadata
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
MEDIA_PROCESSING_VERSION = "project-media-v2"


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
    stats: dict[str, int] = {
        "references": 0,
        "attempted": 0,
        "downloaded": 0,
        "accepted": 0,
        "deduplicated": 0,
        "failed": 0,
        "low_resolution_rejected": 0,
        "unrelated_rejected": 0,
        "accepted_cover_candidates": 0,
        "accepted_gallery_candidates": 0,
        "floor_plan_candidates": 0,
        "master_plan_candidates": 0,
        "skipped_video": 0,
    }
    for candidate in sorted(selected, key=lambda value: value.manifest_row_id):
        candidate_stats = {key: 0 for key in stats}
        adapter = adapter_for(str(candidate.owner_manifest_values.get("owner_developer", "")))
        allowed_domains = media_domains_for_candidate(candidate)
        if candidate.adapter_key == TANAMI_ADAPTER_KEY:
            allowed_domains = TANAMI_MEDIA_DOMAINS
        if allowed_domains is None and adapter is not None:
            allowed_domains = adapter.allowed_domains
        for order, media in enumerate(
            sorted(candidate.staged_media, key=lambda value: value.source_url)[:50]
        ):
            candidate_stats["references"] += 1
            if media.category.value == "floor-plan":
                candidate_stats["floor_plan_candidates"] += 1
            if media.category.value == "master-plan":
                candidate_stats["master_plan_candidates"] += 1
            if media.category.value == "video-reference":
                candidate_stats["skipped_video"] += 1
                continue
            if media.processing_version == MEDIA_PROCESSING_VERSION and media.stage_status in {
                "downloaded",
                "duplicate",
                "rejected-low-resolution",
            }:
                _count_terminal_media(candidate_stats, media)
                continue
            if allowed_domains is None or any(
                token in media.source_url.casefold() for token in REJECTED_URL_TOKENS
            ):
                media.stage_status = "failed"
                media.failure_reason = "Media URL is outside the bounded official raster policy."
                candidate_stats["failed"] += 1
                candidate_stats["unrelated_rejected"] += 1
                continue
            candidate_stats["attempted"] += 1
            result = await asyncio.to_thread(
                source_fetcher.fetch, media.source_url, allowed_domains
            )
            media.retrieved_at = datetime.now(UTC)
            if not result.ok or not result.content_type:
                media.stage_status = "failed"
                media.failure_reason = (
                    result.error_message or result.error_code or "Fetch failed."
                )[:500]
                candidate_stats["failed"] += 1
                continue
            try:
                raster = await asyncio.to_thread(validate_raster, result.body, result.content_type)
            except ValueError as exc:
                media.stage_status = "failed"
                media.failure_reason = str(exc)[:500]
                candidate_stats["failed"] += 1
                continue
            quality = classify_media_quality(raster, media.category.value)
            project_slug = (
                candidate.normalized_project_name or f"project-{candidate.manifest_row_id}"
            )
            private_master_filename = normalized_media_filename(
                project_slug, media.category.value, order, raster.sha256, raster.extension
            )
            public_filename = descriptive_media_filename(
                project_slug,
                media.category.value,
                order + 1,
            )
            media.normalized_filename = public_filename
            media.display_order = order
            media.last_seen_at = media.retrieved_at
            media.original_sha256 = hashlib.sha256(result.body).hexdigest()
            media.processed_sha256 = raster.sha256
            media.processing_version = MEDIA_PROCESSING_VERSION
            project_name = (
                candidate.normalized_project_name or f"Project {candidate.manifest_row_id}"
            )
            category_title = media.category.value.replace("-", " ").title()
            media.title_en = f"{project_name} {category_title}"
            project_name_ar = str(
                (candidate.normalized_payload or {}).get("project_name_ar") or project_name
            )
            media.title_ar = f"{project_name_ar} - {category_title}"
            media.description_en = f"{category_title} view for {project_name}."
            media.description_ar = f"صورة {category_title} لمشروع {project_name_ar}."
            media.alt_en_draft = f"{category_title} view of {project_name}"
            media.alt_ar_draft = f"صورة لمشروع {project_name_ar}"
            media.tags = [project_slug, media.category.value]
            media.public_metadata = public_media_metadata(
                project_name=project_name,
                category=category_title,
                title=media.title_en,
                description=media.description_en,
                website="https://aliyasrealestate.ae",
            )
            duplicate = await db.scalar(
                select(ProjectImportMedia).where(
                    ProjectImportMedia.sha256 == raster.sha256,
                    ProjectImportMedia.id != media.id,
                )
            )
            if duplicate:
                _delete_existing_media_files(storage, media)
                media.sha256 = raster.sha256
                media.mime_type = raster.mime_type
                media.size_bytes = len(raster.content)
                media.width = raster.width
                media.height = raster.height
                media.duplicate_of_id = duplicate.id if duplicate else None
                media.stage_status = "duplicate"
                media.failure_reason = "Duplicate of another exact-project media master."
                media.derivative_manifest = []
                candidate_stats["deduplicated"] += 1
                continue
            previous_keys = _media_storage_keys(media)
            raw_key: str | None = None
            storage_key: str | None = None
            thumbnail_key: str | None = None
            derivative_keys: list[str] = []
            try:
                raw_key = await storage.save_acquisition_media(
                    result.body,
                    raster.extension,
                    normalized_filename=private_master_filename.replace(
                        f".{raster.extension}", f"-raw.{raster.extension}"
                    ),
                )
                storage_key = await storage.save_acquisition_media(
                    raster.content,
                    raster.extension,
                    normalized_filename=private_master_filename,
                )
                thumbnail_content = await asyncio.to_thread(thumbnail, raster)
                thumbnail_key = await storage.save_acquisition_media(
                    thumbnail_content,
                    "webp",
                    normalized_filename=public_filename.rsplit(".", 1)[0] + "-thumb.webp",
                    thumbnail=True,
                )
                derivative_manifest: list[dict[str, object]] = []
                derivatives = (
                    await asyncio.to_thread(responsive_derivatives, raster)
                    if quality.public_eligible
                    else ()
                )
                for derivative in derivatives:
                    filename = public_filename.rsplit(".", 1)[0]
                    filename = f"{filename}-{derivative.width}w.{derivative.format}"
                    key = await storage.save_acquisition_media(
                        derivative.content,
                        derivative.format,
                        normalized_filename=filename,
                    )
                    derivative_keys.append(key)
                    derivative_manifest.append(
                        {
                            "storage_key": key,
                            "format": derivative.format,
                            "mime_type": derivative.mime_type,
                            "width": derivative.width,
                            "height": derivative.height,
                            "size_bytes": derivative.size_bytes,
                            "sha256": derivative.sha256,
                        }
                    )
            except Exception:
                if raw_key:
                    storage.delete(raw_key)
                if storage_key:
                    storage.delete(storage_key)
                if thumbnail_key:
                    storage.delete(thumbnail_key)
                for key in derivative_keys:
                    storage.delete(key)
                raise
            media.raw_storage_key = raw_key
            media.storage_key = storage_key
            media.thumbnail_storage_key = thumbnail_key
            media.mime_type = raster.mime_type
            media.size_bytes = len(raster.content)
            media.sha256 = raster.sha256
            media.width = raster.width
            media.height = raster.height
            media.failure_reason = quality.rejection_reason
            media.stage_status = (
                "downloaded" if quality.public_eligible else "rejected-low-resolution"
            )
            media.derivative_manifest = derivative_manifest
            media.change_status = "newly-added"
            for key in previous_keys - {raw_key, storage_key, thumbnail_key, *derivative_keys}:
                storage.delete(key)
            if quality.public_eligible:
                candidate_stats["downloaded"] += 1
                candidate_stats["accepted"] += 1
                if quality.cover_eligible:
                    candidate_stats["accepted_cover_candidates"] += 1
                if media.category.value == "gallery":
                    candidate_stats["accepted_gallery_candidates"] += 1
            else:
                candidate_stats["low_resolution_rejected"] += 1
        _apply_media_diagnostics(candidate, candidate_stats)
        for key, value in candidate_stats.items():
            stats[key] += value
        await db.commit()
    return stats


def _count_terminal_media(stats: dict[str, int], media: ProjectImportMedia) -> None:
    if media.stage_status == "downloaded":
        stats["downloaded"] += 1
        stats["accepted"] += 1
        if media.category.value == "cover":
            stats["accepted_cover_candidates"] += 1
        if media.category.value == "gallery":
            stats["accepted_gallery_candidates"] += 1
    elif media.stage_status == "duplicate":
        stats["deduplicated"] += 1
    elif media.stage_status == "rejected-low-resolution":
        stats["low_resolution_rejected"] += 1


def _media_storage_keys(media: ProjectImportMedia) -> set[str]:
    keys = {
        value
        for value in (media.raw_storage_key, media.storage_key, media.thumbnail_storage_key)
        if value
    }
    keys.update(
        str(value["storage_key"]) for value in media.derivative_manifest if value.get("storage_key")
    )
    return keys


def _delete_existing_media_files(storage: PrivateStorage, media: ProjectImportMedia) -> None:
    for key in _media_storage_keys(media):
        storage.delete(key)
    media.raw_storage_key = None
    media.storage_key = None
    media.thumbnail_storage_key = None


def _apply_media_diagnostics(candidate: ProjectImportCandidate, stats: dict[str, int]) -> None:
    summary = dict(candidate.acquisition_summary)
    visible_gallery_count = int(summary.get("visible_gallery_count") or 0)
    coverage_incomplete = (
        visible_gallery_count > 1 and stats["accepted_gallery_candidates"] < visible_gallery_count
    )
    summary.update(
        {
            "media_attempted": stats["attempted"],
            "media_accepted": stats["accepted"],
            "media_low_resolution_rejected": stats["low_resolution_rejected"],
            "media_unrelated_rejected": int(summary.get("media_excluded") or 0)
            + stats["unrelated_rejected"],
            "media_duplicate_rejected": stats["deduplicated"],
            "media_failed_downloads": stats["failed"],
            "accepted_cover_candidates": stats["accepted_cover_candidates"],
            "accepted_gallery_candidates": stats["accepted_gallery_candidates"],
            "floor_plan_candidates": stats["floor_plan_candidates"],
            "master_plan_candidates": stats["master_plan_candidates"],
            "media_coverage_incomplete": coverage_incomplete,
            "cover_quality_warning": (
                None
                if stats["accepted_cover_candidates"]
                else "High-resolution Cover image required"
            ),
        }
    )
    candidate.acquisition_summary = summary
    retained = [
        value
        for value in candidate.conflict_reasons
        if value not in {"Media coverage incomplete", "High-resolution Cover image required"}
    ]
    if coverage_incomplete:
        retained.append("Media coverage incomplete")
    if not stats["accepted_cover_candidates"]:
        retained.append("High-resolution Cover image required")
    candidate.conflict_reasons = list(dict.fromkeys(retained))
    candidate.review_status = ImportReviewStatus.NEEDS_REVIEW
    candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
