from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import UTC, datetime
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.adapters import OFFICIAL_ADAPTERS
from app.acquisition.media import (
    SecureRasterFetcher,
    classify_media_quality,
    normalized_media_filename,
    responsive_derivatives,
    thumbnail,
    validate_raster,
)
from app.acquisition.reconciliation import reconcile_candidate_quality
from app.acquisition.security import host_is_allowed
from app.acquisition.sobha_siniya_pilot import media_domains_for_candidate
from app.acquisition.tanami import TANAMI_ADAPTER_KEY, TANAMI_MEDIA_DOMAINS
from app.config import Settings
from app.models import (
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMediaCategory,
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
    "agent",
    "avatar",
    "contact",
    "tracking",
    "pixel",
    "whatsapp",
    "app-store",
    "google-play",
)
MEDIA_PROCESSING_VERSION = "project-media-v3"
AUTOMATIC_EXACT_PROJECT_RIGHTS_BASIS = (
    "Automatically approved exact-Project image from a validated candidate source."
)
TANAMI_OWNER_AUTHORIZED_RIGHTS_BASIS = (
    "Owner-authorized exact-Project Tanami media use; Tanami source provenance "
    "retained and ALIYAS is not recorded as the original copyright owner."
)

MEDIA_CATEGORY_LABELS = {
    "cover": ("Cover image", "الصورة الرئيسية"),
    "gallery": ("Gallery image", "صورة من المعرض"),
    "exterior": ("Exterior view", "صورة خارجية"),
    "interior": ("Interior view", "صورة داخلية"),
    "amenities": ("Amenities", "المرافق"),
    "floor-plan": ("Floor plan", "مخطط الطابق"),
    "master-plan": ("Master plan", "المخطط الرئيسي"),
    "location-map": ("Location map", "خريطة الموقع"),
    "construction": ("Construction image", "صورة الإنشاءات"),
}


async def intake_private_media(
    db: AsyncSession,
    settings: Settings,
    batch_id: uuid.UUID,
    *,
    candidate_ids: list[uuid.UUID] | None = None,
    media_ids: set[uuid.UUID] | None = None,
    fetcher: SecureRasterFetcher | None = None,
    preserve_review_state: bool = False,
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
    if media_ids is not None and not media_ids <= {
        media.id for candidate in selected for media in candidate.staged_media
    }:
        raise ValueError("Every selected image must belong to the selected candidates.")
    if media_ids is not None:
        selected = [
            candidate
            for candidate in selected
            if any(media.id in media_ids for media in candidate.staged_media)
        ]
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
        "classification_uncertain": 0,
        "skipped_video": 0,
    }
    for candidate in sorted(selected, key=lambda value: value.manifest_row_id):
        prior_review_status = candidate.review_status
        prior_processing_status = candidate.processing_status
        candidate_stats = {key: 0 for key in stats}
        ordered_media = sorted(
            candidate.staged_media,
            key=lambda value: (
                int((value.discovery_manifest or {}).get("source_order", value.display_order)),
                value.display_order,
            ),
        )
        for media in ordered_media:
            if media_ids is not None and media.id not in media_ids:
                continue
            candidate_stats["references"] += 1
            if media.category.value == "floor-plan":
                candidate_stats["floor_plan_candidates"] += 1
            if media.category.value == "master-plan":
                candidate_stats["master_plan_candidates"] += 1
            if media.category.value == "video-reference":
                candidate_stats["skipped_video"] += 1
                continue
            disposition = str((media.discovery_manifest or {}).get("disposition") or "accepted")
            if disposition in {"reject", "uncertain"}:
                reason = (
                    "DOM-aware classification requires human review."
                    if disposition == "uncertain"
                    else "DOM-aware classification rejected this non-Project asset."
                )
                _remove_media_output(storage, media, reason)
                media.stage_status = (
                    "classification-uncertain"
                    if disposition == "uncertain"
                    else "rejected-unrelated"
                )
                if disposition == "uncertain":
                    candidate_stats["classification_uncertain"] += 1
                else:
                    candidate_stats["unrelated_rejected"] += 1
                continue
            if media.stage_status == "rejected-unrelated" or (
                media.processing_version == MEDIA_PROCESSING_VERSION
                and media.stage_status
                in {
                    "downloaded",
                    "duplicate",
                    "rejected-low-resolution",
                }
            ):
                if media.stage_status == "downloaded":
                    _apply_category_metadata(candidate, media)
                    _synchronize_owner_authorized_tanami_rights(candidate, media)
                _count_terminal_media(candidate_stats, media)
                continue
            allowed_domains = _allowed_domains_for_media(candidate, media.source_url)
            if allowed_domains is None or any(
                token in media.source_url.casefold() for token in REJECTED_URL_TOKENS
            ):
                _remove_media_output(
                    storage,
                    media,
                    "Media URL is outside the bounded official raster policy.",
                )
                media.stage_status = "rejected-unrelated"
                media.failure_reason = "Media URL is outside the bounded official raster policy."
                candidate_stats["unrelated_rejected"] += 1
                continue
            candidate_stats["attempted"] += 1
            result = await asyncio.to_thread(
                source_fetcher.fetch, media.source_url, allowed_domains
            )
            media.retrieved_at = datetime.now(UTC)
            if not result.ok or not result.content_type:
                reason = result.error_message or result.error_code or "Fetch failed."
                _remove_media_output(storage, media, reason)
                media.stage_status = "failed"
                media.failure_reason = reason[:500]
                candidate_stats["failed"] += 1
                continue
            try:
                raster = await asyncio.to_thread(validate_raster, result.body, result.content_type)
            except ValueError as exc:
                _remove_media_output(storage, media, str(exc))
                media.stage_status = "failed"
                media.failure_reason = str(exc)[:500]
                candidate_stats["failed"] += 1
                continue
            quality = classify_media_quality(raster, media.category.value)
            media.display_order = int(
                (media.discovery_manifest or {}).get("category_order", media.display_order)
            )
            media.last_seen_at = media.retrieved_at
            media.original_sha256 = hashlib.sha256(result.body).hexdigest()
            media.processed_sha256 = raster.sha256
            media.processing_version = MEDIA_PROCESSING_VERSION
            media.mime_type = raster.mime_type
            media.size_bytes = len(raster.content)
            media.sha256 = raster.sha256
            media.width = raster.width
            media.height = raster.height
            if not quality.public_eligible:
                _remove_media_output(
                    storage,
                    media,
                    quality.rejection_reason or "Image failed the existing resolution requirement.",
                )
                media.stage_status = "rejected-low-resolution"
                media.failure_reason = quality.rejection_reason
                candidate_stats["low_resolution_rejected"] += 1
                continue
            project_name = str(
                candidate.normalized_project_name
                or candidate.owner_manifest_values.get("owner_project_name")
                or f"Project {candidate.manifest_row_id}"
            )
            project_slug = project_name
            private_master_filename = normalized_media_filename(
                project_slug,
                media.category.value,
                media.display_order,
                raster.sha256,
                raster.extension,
            )
            public_filename = descriptive_media_filename(
                project_slug,
                media.category.value,
                media.display_order + 1,
            )
            media.normalized_filename = public_filename
            category_en, category_ar = MEDIA_CATEGORY_LABELS[media.category.value]
            project_name_ar = str(
                (candidate.normalized_payload or {}).get("project_name_ar")
                or candidate.owner_manifest_values.get("owner_project_name_ar")
                or project_name
            )
            media.title_en = f"{project_name} — {category_en}"
            media.title_ar = f"{project_name_ar} — {category_ar}"
            media.description_en = f"{category_en} for {project_name}."
            media.description_ar = f"{category_ar} — {project_name_ar}."
            media.alt_en_draft = f"{category_en} for {project_name}"
            media.alt_ar_draft = f"{category_ar} — {project_name_ar}"
            media.tags = [project_name, category_en]
            media.public_metadata = public_media_metadata(
                project_name=project_name,
                category=category_en,
                title=media.title_en,
                description=media.description_en,
                website="https://aliyasrealestate.ae",
            )
            duplicate = await db.scalar(
                select(ProjectImportMedia).where(
                    ProjectImportMedia.candidate_id == candidate.id,
                    ProjectImportMedia.sha256 == raster.sha256,
                    ProjectImportMedia.id != media.id,
                )
            )
            if duplicate:
                _remove_media_output(
                    storage,
                    media,
                    "Duplicate of another image for the same Project candidate.",
                )
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
            if candidate.adapter_key == TANAMI_ADAPTER_KEY:
                _synchronize_owner_authorized_tanami_rights(candidate, media)
            elif media.rights_status != MediaRightsStatus.APPROVED:
                media.rights_status = MediaRightsStatus.APPROVED
                media.rights_basis = AUTOMATIC_EXACT_PROJECT_RIGHTS_BASIS
                media.rights_confirmed_by = None
                media.rights_confirmed_at = datetime.now(UTC)
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
        _select_best_cover(candidate)
        candidate_stats["accepted_cover_candidates"] = sum(
            item.stage_status == "downloaded" and item.category == ProjectMediaCategory.COVER
            for item in candidate.staged_media
        )
        candidate_stats["accepted_gallery_candidates"] = sum(
            item.stage_status == "downloaded" and item.category == ProjectMediaCategory.GALLERY
            for item in candidate.staged_media
        )
        _apply_media_diagnostics(
            candidate,
            candidate_stats,
            preserve_review_state=preserve_review_state,
        )
        if preserve_review_state:
            candidate.review_status = prior_review_status
            candidate.processing_status = prior_processing_status
        for key, value in candidate_stats.items():
            stats[key] += value
        await db.commit()
    return stats


def _synchronize_owner_authorized_tanami_rights(
    candidate: ProjectImportCandidate, media: ProjectImportMedia
) -> None:
    """Apply the owner's source-specific authorization without weakening other sources."""
    if candidate.adapter_key != TANAMI_ADAPTER_KEY:
        return
    manifest = media.discovery_manifest or {}
    project_url = str(manifest.get("project_url") or "")
    manifest_source_url = str(manifest.get("source_url") or "")
    dom_discovered_tanami_media = bool(
        project_url.startswith("https://www.tanamiproperties.com/Projects/")
        and manifest_source_url == media.source_url
        and manifest.get("disposition") == "accepted"
    )
    if not dom_discovered_tanami_media:
        if media.rights_basis == TANAMI_OWNER_AUTHORIZED_RIGHTS_BASIS or (
            media.rights_basis == AUTOMATIC_EXACT_PROJECT_RIGHTS_BASIS
            and media.rights_status == MediaRightsStatus.APPROVED
        ):
            media.rights_status = MediaRightsStatus.PENDING
            media.rights_basis = AUTOMATIC_EXACT_PROJECT_RIGHTS_BASIS
            media.rights_confirmed_by = None
            media.rights_confirmed_at = datetime.now(UTC)
        return
    if (
        media.rights_status == MediaRightsStatus.APPROVED
        and media.rights_basis == TANAMI_OWNER_AUTHORIZED_RIGHTS_BASIS
    ):
        return
    media.rights_status = MediaRightsStatus.APPROVED
    media.rights_basis = TANAMI_OWNER_AUTHORIZED_RIGHTS_BASIS
    media.rights_confirmed_by = None
    media.rights_confirmed_at = datetime.now(UTC)


def _allowed_domains_for_media(
    candidate: ProjectImportCandidate, source_url: str
) -> tuple[str, ...] | None:
    """Resolve the narrow allowlist for each retained source, not the whole candidate."""
    hostname = urlsplit(source_url).hostname or ""
    pilot_domains = media_domains_for_candidate(candidate)
    if pilot_domains and host_is_allowed(hostname, pilot_domains):
        return pilot_domains
    if candidate.adapter_key == TANAMI_ADAPTER_KEY and host_is_allowed(
        hostname, TANAMI_MEDIA_DOMAINS
    ):
        return TANAMI_MEDIA_DOMAINS
    for adapter in OFFICIAL_ADAPTERS:
        if host_is_allowed(hostname, adapter.allowed_domains):
            return adapter.allowed_domains
    return None


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
    elif media.stage_status == "rejected-unrelated":
        stats["unrelated_rejected"] += 1


def _select_best_cover(candidate: ProjectImportCandidate) -> None:
    """Select one real high-resolution landscape master without using plans or maps."""
    eligible_categories = {
        ProjectMediaCategory.COVER,
        ProjectMediaCategory.GALLERY,
        ProjectMediaCategory.EXTERIOR,
        ProjectMediaCategory.INTERIOR,
        ProjectMediaCategory.AMENITIES,
    }
    eligible = [
        item
        for item in candidate.staged_media
        if item.stage_status == "downloaded"
        and item.rights_status == MediaRightsStatus.APPROVED
        and not (item.rights_basis or "").startswith("Automatically approved exact-Project")
        and item.storage_key
        and item.category in eligible_categories
        and isinstance(item.width, int)
        and isinstance(item.height, int)
        and item.width >= 1600
        and item.height >= 900
        and item.width > item.height
    ]
    selected = max(
        eligible,
        key=lambda item: ((item.width or 0) * (item.height or 0), item.width or 0),
        default=None,
    )
    for item in candidate.staged_media:
        if item.category == ProjectMediaCategory.COVER and item is not selected:
            item.category = ProjectMediaCategory.GALLERY
            _apply_category_metadata(candidate, item)
    if selected and selected.category != ProjectMediaCategory.COVER:
        selected.category = ProjectMediaCategory.COVER
        selected.display_order = 0
        _apply_category_metadata(candidate, selected)


def _apply_category_metadata(candidate: ProjectImportCandidate, media: ProjectImportMedia) -> None:
    project_name = str(
        candidate.normalized_project_name
        or candidate.owner_manifest_values.get("owner_project_name")
        or f"project-{candidate.manifest_row_id}"
    )
    project_name_ar = str(
        (candidate.normalized_payload or {}).get("project_name_ar")
        or candidate.owner_manifest_values.get("owner_project_name_ar")
        or project_name
    )
    category_en, category_ar = MEDIA_CATEGORY_LABELS[media.category.value]
    media.normalized_filename = descriptive_media_filename(
        project_name, media.category.value, media.display_order + 1
    )
    media.title_en = f"{project_name} — {category_en}"
    media.title_ar = f"{project_name_ar} — {category_ar}"
    media.description_en = f"{category_en} for {project_name}."
    media.description_ar = f"{category_ar} — {project_name_ar}."
    media.alt_en_draft = f"{category_en} for {project_name}"
    media.alt_ar_draft = f"{category_ar} — {project_name_ar}"
    media.tags = [project_name, category_en]
    media.public_metadata = public_media_metadata(
        project_name=project_name,
        category=category_en,
        title=media.title_en,
        description=media.description_en,
        website="https://aliyasrealestate.ae",
    )


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


def _remove_media_output(storage: PrivateStorage, media: ProjectImportMedia, reason: str) -> None:
    _delete_existing_media_files(storage, media)
    media.duplicate_of_id = None
    media.normalized_filename = None
    media.alt_en_draft = None
    media.alt_ar_draft = None
    media.title_en = None
    media.title_ar = None
    media.description_en = None
    media.description_ar = None
    media.tags = []
    media.public_metadata = {}
    media.derivative_manifest = []
    media.rights_status = MediaRightsStatus.REJECTED
    media.rights_basis = f"Automatically removed: {reason}"[:500]
    media.rights_confirmed_by = None
    media.rights_confirmed_at = datetime.now(UTC)
    media.processing_version = MEDIA_PROCESSING_VERSION


def _apply_media_diagnostics(
    candidate: ProjectImportCandidate,
    stats: dict[str, int],
    *,
    preserve_review_state: bool = False,
) -> None:
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
            "media_classification_uncertain": stats["classification_uncertain"],
            "media_coverage_incomplete": coverage_incomplete,
            "cover_quality_warning": (
                None
                if stats["accepted_cover_candidates"]
                else "High-resolution Cover image required"
            ),
        }
    )
    candidate.acquisition_summary = summary
    if preserve_review_state:
        return
    reconcile_candidate_quality(candidate)
    candidate.review_status = ImportReviewStatus.NEEDS_REVIEW
    candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
