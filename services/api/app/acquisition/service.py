from __future__ import annotations

import asyncio
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.adapters import ADAPTER_VERSION, adapter_for
from app.acquisition.contracts import (
    FetchResult,
    ManifestCandidate,
    NormalizedEvidence,
    SourceFetcher,
)
from app.acquisition.parser import normalize_name
from app.acquisition.security import BatchCachingFetcher, SecureFetcher, host_is_allowed
from app.config import Settings
from app.models import (
    AreaAlias,
    AreaCommunity,
    Developer,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportChange,
    ProjectImportMedia,
    ProjectMediaCategory,
    ProjectSourceSnapshot,
    ProjectSourceType,
)
from app.storage import PrivateStorage

EXPECTED_HEADERS = (
    "row_id",
    "owner_project_name",
    "owner_developer",
    "owner_area",
    "manifest_status",
)
EXPECTED_ROWS = 50


async def read_manifest(path: Path) -> tuple[list[ManifestCandidate], str]:
    content = await asyncio.to_thread(path.read_bytes)
    digest = hashlib.sha256(content).hexdigest()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    if tuple(reader.fieldnames or ()) != EXPECTED_HEADERS:
        raise ValueError("The owner manifest header does not match the approved contract.")
    records: list[ManifestCandidate] = []
    for row in reader:
        if row["manifest_status"] != "candidate":
            raise ValueError("Every owner manifest row must remain an inert candidate.")
        records.append(
            ManifestCandidate(
                row_id=int(row["row_id"]),
                project_name=row["owner_project_name"].strip(),
                developer=row["owner_developer"].strip(),
                area=row["owner_area"].strip(),
            )
        )
    if len(records) != EXPECTED_ROWS or len({item.row_id for item in records}) != EXPECTED_ROWS:
        raise ValueError("The owner manifest must contain exactly 50 unique rows.")
    if (
        len({(item.developer.casefold(), item.project_name.casefold()) for item in records})
        != EXPECTED_ROWS
    ):
        raise ValueError("The owner manifest contains a duplicate developer/project candidate.")
    return records, digest


async def load_manifest(
    db: AsyncSession,
    path: Path,
    *,
    batch_name: str = "Owner Off-Plan Project Manifest",
    source_reference: str = "data-intake/offplan-projects-owner-manifest.csv",
) -> ProjectImportBatch:
    records, digest = await read_manifest(path)
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.manifest_hash == digest)
        .options(selectinload(ProjectImportBatch.candidates))
    )
    if batch is None:
        batch = ProjectImportBatch(
            name=batch_name,
            source_reference=source_reference,
            manifest_hash=digest,
            adapter_version=ADAPTER_VERSION,
            total_count=EXPECTED_ROWS,
            candidates=[],
        )
        db.add(batch)
        await db.flush()
    existing_rows = (
        await db.scalars(
            select(ProjectImportCandidate).where(ProjectImportCandidate.batch_id == batch.id)
        )
    ).all()
    existing = {item.manifest_row_id: item for item in existing_rows}
    for record in records:
        raw = {
            "row_id": record.row_id,
            "owner_project_name": record.project_name,
            "owner_developer": record.developer,
            "owner_area": record.area,
            "manifest_status": "candidate",
        }
        if record.row_id in existing:
            if existing[record.row_id].owner_manifest_values != raw:
                raise ValueError("An existing batch row differs from the immutable owner manifest.")
            continue
        row_hash = hashlib.sha256(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        db.add(
            ProjectImportCandidate(
                batch_id=batch.id,
                manifest_row_id=record.row_id,
                raw_source_payload={"manifest": raw},
                owner_manifest_values=raw,
                normalized_project_name=record.project_name,
                content_hash=row_hash,
                review_status=ImportReviewStatus.DISCOVERED,
            )
        )
    await db.commit()
    return await _batch(db, batch.id)


async def acquire_batch(
    db: AsyncSession,
    settings: Settings,
    batch_id: str | None = None,
    *,
    failed_only: bool = False,
    refresh: bool = False,
    fetcher: SourceFetcher | None = None,
) -> ProjectImportBatch:
    batch = await selected_batch(db, batch_id)
    batch.started_at = datetime.now(UTC)
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    storage = PrivateStorage(settings)
    for candidate in sorted(batch.candidates, key=lambda item: item.manifest_row_id):
        if failed_only and candidate.review_status != ImportReviewStatus.FAILED:
            continue
        await _acquire_candidate(db, candidate, source_fetcher, storage, refresh=refresh)
        await db.commit()
    await _update_counts(db, batch)
    batch.completed_at = datetime.now(UTC)
    await db.commit()
    return await _batch(db, batch.id)


async def _acquire_candidate(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    fetcher: SourceFetcher,
    storage: PrivateStorage,
    *,
    refresh: bool,
) -> None:
    manifest = ManifestCandidate(
        row_id=candidate.manifest_row_id,
        project_name=str(candidate.owner_manifest_values["owner_project_name"]),
        developer=str(candidate.owner_manifest_values["owner_developer"]),
        area=str(candidate.owner_manifest_values["owner_area"]),
    )
    adapter = adapter_for(manifest.developer)
    if adapter is None:
        _fail(candidate, "adapter_missing", "No bounded official-source adapter exists.")
        return
    candidate.adapter_key = adapter.key
    candidate.adapter_version = adapter.version
    discovery = await asyncio.to_thread(adapter.discover, manifest, fetcher)
    result, normalized = await asyncio.to_thread(adapter.acquire, manifest, discovery, fetcher)
    candidate.acquisition_summary = {
        "discovery": discovery.match_kind,
        "suggested_url": discovery.suggested_url,
        "discovery_failures": list(discovery.failures),
        "error_code": result.error_code,
        "error_message": result.error_message,
    }
    if not result.ok or normalized is None:
        await _record_failure_evidence(db, candidate, adapter.key, adapter.version, result)
        if candidate.normalized_payload is not None and candidate.official_source_url:
            candidate.review_status = _existing_evidence_status(candidate)
            if refresh:
                classification = (
                    "source-removed" if result.status in {404, 410} else "source-unavailable"
                )
                await _record_change(db, candidate, classification, None, result.url, None)
            return
        _fail(
            candidate,
            result.error_code or "extraction_failed",
            result.error_message or "No source-grounded fields were extracted.",
        )
        if refresh:
            classification = (
                "source-removed" if result.status in {404, 410} else "source-unavailable"
            )
            await _record_change(db, candidate, classification, None, result.url, None)
        return
    stored = await storage.save_acquisition_snapshot(result.body, result.content_type)
    previous = candidate.normalized_payload
    previous_hash = candidate.content_hash
    snapshot = await _evidence(
        db, candidate, adapter.key, adapter.version, result, stored.storage_key, storage
    )
    proposal = normalized.normalized_proposal
    developer_id = await _match_developer(db, adapter.canonical_developer_slug)
    area_id = await _match_area(db, manifest.area)
    conflicts = list(normalized.conflicts)
    if developer_id is None:
        conflicts.append(f"Canonical Developer unresolved: {manifest.developer}.")
    if area_id is None:
        conflicts.append(f"Canonical Area/Community unresolved: {manifest.area}.")
    candidate.proposed_developer_id = developer_id
    candidate.proposed_area_id = area_id
    candidate.official_source_url = result.url
    candidate.source_urls = list(dict.fromkeys([result.url]))
    candidate.normalized_project_name = _string_or_none(proposal.get("project_name"))
    candidate.normalized_payload = proposal
    candidate.raw_source_payload = {
        "manifest": candidate.owner_manifest_values,
        "source_extracted": normalized.source_extracted,
    }
    candidate.extracted_at = result.retrieved_at
    candidate.last_verified_at = result.retrieved_at
    candidate.content_hash = stored.sha256
    candidate.match_result = {
        "discovery": discovery.match_kind,
        "developer": str(developer_id) if developer_id else None,
        "area": str(area_id) if area_id else None,
    }
    candidate.validation_errors = [
        {"field": field, "code": "missing_official_evidence"} for field in normalized.missing_fields
    ]
    candidate.conflict_reasons = conflicts
    candidate.arabic_review_required = not bool(
        normalized.source_extracted.get("arabic_content_available")
    )
    candidate.review_status = (
        ImportReviewStatus.READY_FOR_APPROVAL
        if not candidate.validation_errors
        and not conflicts
        and not candidate.arabic_review_required
        and developer_id
        and area_id
        else ImportReviewStatus.NEEDS_REVIEW
    )
    await _stage_media(db, candidate, snapshot, normalized, adapter.allowed_domains)
    if refresh:
        classification = classify_change(
            previous,
            proposal,
            same_hash=previous is not None and previous_hash == stored.sha256,
        )
        await _record_change(
            db, candidate, classification, previous, result.url, stored.sha256, proposal
        )


def classify_change(
    previous: dict[str, object] | None,
    current: dict[str, object] | None,
    *,
    same_hash: bool = False,
) -> str:
    if current is None:
        return "source-unavailable"
    if previous is None:
        return "changed"
    if same_hash or previous == current:
        return "unchanged"
    if previous.get("project_name") != current.get("project_name"):
        return "conflict-detected"
    return "changed"


async def _stage_media(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    snapshot: ProjectSourceSnapshot,
    normalized: NormalizedEvidence,
    allowed_domains: tuple[str, ...],
) -> None:
    selected = {
        url: _media_category(url)
        for url in normalized.media_urls
        if _media_category(url) is not None
    }
    bounded = dict(list(sorted(selected.items()))[:12])
    for item in list(candidate.staged_media):
        if item.stage_status == "reference-only" and item.source_url not in bounded:
            await db.delete(item)
    await db.flush()
    existing = {item.source_url for item in candidate.staged_media if item.source_url in bounded}
    for url, category in bounded.items():
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not host_is_allowed(parsed.hostname, allowed_domains)
            or url in existing
        ):
            continue
        db.add(
            ProjectImportMedia(
                candidate_id=candidate.id,
                snapshot_id=snapshot.id,
                category=category,
                source_url=url,
                rights_status=MediaRightsStatus.PENDING,
                stage_status="reference-only",
            )
        )
        existing.add(url)


def _media_category(url: str) -> ProjectMediaCategory | None:
    path = urlsplit(url).path.casefold()
    if any(
        token in path
        for token in (
            "favicon",
            "icon",
            "logo",
            "placeholder",
            "spinner",
            "social",
            "app-store",
            "google-play",
        )
    ):
        return None
    if path.endswith((".mp4", ".mov", ".webm")):
        return ProjectMediaCategory.VIDEO_REFERENCE
    if not path.endswith((".jpg", ".jpeg", ".png", ".webp", ".avif")):
        return None
    for tokens, category in (
        (("floor-plan", "floorplan"), ProjectMediaCategory.FLOOR_PLAN),
        (("master-plan", "masterplan"), ProjectMediaCategory.MASTER_PLAN),
        (("location", "map"), ProjectMediaCategory.LOCATION_MAP),
        (("construction", "progress"), ProjectMediaCategory.CONSTRUCTION),
        (("interior",), ProjectMediaCategory.INTERIOR),
        (("exterior", "facade"), ProjectMediaCategory.EXTERIOR),
        (("amenit",), ProjectMediaCategory.AMENITIES),
        (("cover", "hero"), ProjectMediaCategory.COVER),
    ):
        if any(token in path for token in tokens):
            return category
    return ProjectMediaCategory.GALLERY


async def _evidence(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    adapter_key: str,
    adapter_version: str,
    result: FetchResult,
    storage_key: str,
    storage: PrivateStorage,
) -> ProjectSourceSnapshot:
    digest = hashlib.sha256(result.body).hexdigest()
    existing = await db.scalar(
        select(ProjectSourceSnapshot).where(
            ProjectSourceSnapshot.candidate_id == candidate.id,
            ProjectSourceSnapshot.source_url == result.url,
            ProjectSourceSnapshot.content_hash == digest,
        )
    )
    if existing:
        storage.delete(storage_key)
        return existing
    record = ProjectSourceSnapshot(
        candidate_id=candidate.id,
        source_url=result.url,
        source_type=ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
        http_status=result.status,
        retrieved_at=result.retrieved_at,
        adapter_key=adapter_key,
        adapter_version=adapter_version,
        content_type=result.content_type,
        etag=result.etag,
        last_modified=result.last_modified,
        content_hash=digest,
        storage_key=storage_key,
        outcome="extracted",
    )
    db.add(record)
    await db.flush()
    return record


async def _record_failure_evidence(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    adapter_key: str,
    adapter_version: str,
    result: FetchResult,
) -> None:
    digest = hashlib.sha256(
        f"{result.url}|{result.status}|{result.error_code}".encode()
    ).hexdigest()
    exists = await db.scalar(
        select(ProjectSourceSnapshot.id).where(
            ProjectSourceSnapshot.candidate_id == candidate.id,
            ProjectSourceSnapshot.source_url == result.url,
            ProjectSourceSnapshot.content_hash == digest,
        )
    )
    if exists:
        return
    db.add(
        ProjectSourceSnapshot(
            candidate_id=candidate.id,
            source_url=result.url,
            source_type=ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
            http_status=result.status,
            retrieved_at=result.retrieved_at,
            adapter_key=adapter_key,
            adapter_version=adapter_version,
            content_type=result.content_type,
            etag=result.etag,
            last_modified=result.last_modified,
            content_hash=digest,
            outcome="failed",
            error_code=result.error_code,
            error_message=result.error_message,
        )
    )


async def _record_change(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    classification: str,
    previous: dict[str, object] | None,
    source_url: str | None,
    content_hash: str | None,
    current: dict[str, object] | None = None,
) -> None:
    db.add(
        ProjectImportChange(
            candidate_id=candidate.id,
            classification=classification,
            existing_value=previous,
            new_value=current,
            source_url=source_url,
            detected_at=datetime.now(UTC),
            content_hash=content_hash,
        )
    )


async def _match_developer(db: AsyncSession, slug: str | None) -> UUID | None:
    if not slug:
        return None
    value = await db.scalar(select(Developer.id).where(Developer.slug == slug))
    return value if isinstance(value, UUID) else None


async def _match_area(db: AsyncSession, name: str) -> UUID | None:
    normalized = normalize_name(name)
    direct = await db.scalar(
        select(AreaCommunity.id).where(func.lower(AreaCommunity.name_en) == name.casefold())
    )
    if direct:
        return direct
    value = await db.scalar(
        select(AreaAlias.area_id).where(AreaAlias.normalized_alias == normalized)
    )
    return value if isinstance(value, UUID) else None


def _fail(candidate: ProjectImportCandidate, code: str, message: str) -> None:
    candidate.review_status = ImportReviewStatus.FAILED
    candidate.validation_errors = [{"field": "official_source", "code": code, "message": message}]


def _existing_evidence_status(candidate: ProjectImportCandidate) -> ImportReviewStatus:
    if (
        not candidate.validation_errors
        and not candidate.conflict_reasons
        and not candidate.arabic_review_required
        and candidate.proposed_developer_id
        and candidate.proposed_area_id
    ):
        return ImportReviewStatus.READY_FOR_APPROVAL
    return ImportReviewStatus.NEEDS_REVIEW


async def _update_counts(db: AsyncSession, batch: ProjectImportBatch) -> None:
    statuses = list(
        await db.scalars(
            select(ProjectImportCandidate.review_status).where(
                ProjectImportCandidate.batch_id == batch.id
            )
        )
    )
    batch.total_count = len(statuses)
    batch.clean_count = statuses.count(ImportReviewStatus.READY_FOR_APPROVAL)
    batch.needs_review_count = statuses.count(ImportReviewStatus.NEEDS_REVIEW)
    batch.failed_count = statuses.count(ImportReviewStatus.FAILED)


async def selected_batch(db: AsyncSession, batch_id: str | None) -> ProjectImportBatch:
    if batch_id:
        return await _batch(db, UUID(batch_id))
    record = await db.scalar(
        select(ProjectImportBatch).order_by(ProjectImportBatch.created_at.desc())
    )
    if record is None:
        raise ValueError("Load the owner manifest before running acquisition.")
    return await _batch(db, record.id)


async def _batch(db: AsyncSession, batch_id: UUID) -> ProjectImportBatch:
    record = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.id == batch_id)
        .execution_options(populate_existing=True)
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            )
        )
    )
    if record is None:
        raise ValueError("Import batch not found.")
    return record


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def status_summary(batch: ProjectImportBatch) -> dict[str, object]:
    return {
        "batch_id": str(batch.id),
        "manifest_hash": batch.manifest_hash,
        "total": batch.total_count,
        "ready_for_approval": batch.clean_count,
        "needs_review": batch.needs_review_count,
        "failed": batch.failed_count,
        "candidates": [
            {
                "row_id": item.manifest_row_id,
                "project": item.owner_manifest_values.get("owner_project_name"),
                "status": item.review_status.value,
                "source_found": bool(item.official_source_url),
                "missing_fields": [error.get("field") for error in item.validation_errors],
                "conflicts": item.conflict_reasons,
                "media_references": len(item.staged_media),
                "arabic_review_required": item.arabic_review_required,
            }
            for item in sorted(batch.candidates, key=lambda row: row.manifest_row_id)
        ],
    }
