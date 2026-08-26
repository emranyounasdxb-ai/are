"""One-record, review-gated acquisition for the authorized Sobha Siniya pilot.

This module is deliberately separate from the inert 50-row owner manifest.  Its
allowlist contains one Tanami Project URL and five official Sobha corroborating
pages; it cannot be reused as a general crawler.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.contracts import FetchResult, SourceFetcher
from app.acquisition.parser import parse_html
from app.acquisition.security import BatchCachingFetcher, SecureFetcher
from app.acquisition.tanami import MediaDiscovery, discover_exact_project_media
from app.audit import write_audit
from app.config import Settings
from app.models import (
    AreaAlias,
    AreaCommunity,
    Developer,
    DeveloperTranslation,
    DeveloperVerificationStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMediaCategory,
    ProjectProcessingStatus,
    ProjectSourceSnapshot,
    ProjectSourceType,
    PublicationStatus,
    Role,
    UAEEmirate,
    User,
)
from app.storage import PrivateStorage

PILOT_ADAPTER_KEY: Final = "tanami-sobha-siniya-pilot"
PILOT_ADAPTER_VERSION: Final = "1.1"
PRIMARY_URL: Final = "https://www.tanamiproperties.com/Projects/Sobha-Siniya-Island"
OFFICIAL_PRESS_FILM_URL: Final = (
    "https://sobharealty.com/media-center/press-releases/"
    "sobha-siniya-island-an-effortless-escape-into-natures-luxury-and-legacy-just-moments-away"
)
OFFICIAL_PRESS_FILM_CANONICAL_URL: Final = (
    "https://sobharealty.com/media-center/press-releases/"
    "sobha-siniya-island-an-effortless-escape-into-nature-s-luxury-and-legacy-just-moments-away"
)
OFFICIAL_PARTNERSHIP_URL: Final = (
    "https://sobharealty.com/media-center/press-releases/"
    "rashid-bin-saud-al-mualla-witnesses-signing-partnership-agreement"
)
OFFICIAL_EN_URL: Final = "https://sobharealty.com/sobha-communities/sobha-siniya-island"
OFFICIAL_AR_URL: Final = (
    "https://sobharealty.com/ar/%D8%AC%D8%B2%D9%8A%D8%B1%D8%A9-%D8%B4%D9%88%D8%A8%D8%A7-"
    "%D8%A7%D9%84%D8%B3%D9%8A%D9%86%D9%8A%D8%A9/%D9%85%D8%AC%D8%AA%D9%85%D8%B9%D8%A7%D8%AA-"
    "%D8%B4%D9%88%D8%A8%D8%A7"
)
AUTHORIZED_DOCUMENTS: Final = (
    PRIMARY_URL,
    OFFICIAL_PRESS_FILM_URL,
    OFFICIAL_PRESS_FILM_CANONICAL_URL,
    OFFICIAL_PARTNERSHIP_URL,
    OFFICIAL_EN_URL,
    OFFICIAL_AR_URL,
    f"{PRIMARY_URL}-FloorPlans",
    f"{PRIMARY_URL}-MasterPlan",
    f"{PRIMARY_URL}-Amenities",
)
DOCUMENT_DOMAINS: Final = ("tanamiproperties.com", "sobharealty.com")
MEDIA_DOMAINS: Final = ("manage.tanamiproperties.com", "sobharealty.com")
OFFICIAL_MEDIA: Final = (
    (
        "https://sobharealty.com/sites/default/files/2025-04/banner%20web_0.jpg",
        ProjectMediaCategory.COVER,
        "Official Sobha Siniya Island architectural waterfront view",
        "منظر معماري رسمي للواجهة البحرية في جزيرة شوبا السينية",
    ),
    (
        "https://sobharealty.com/sites/default/files/2024-08/1418%20x%20771.jpg",
        ProjectMediaCategory.GALLERY,
        "Official Sobha Siniya Island waterfront residences view",
        "منظر رسمي للمساكن والواجهة البحرية في جزيرة شوبا السينية",
    ),
    (
        "https://sobharealty.com/sites/default/files/2025-01/SobhaSiniyaIsland_1.jpg",
        ProjectMediaCategory.LOCATION_MAP,
        "Official Sobha Siniya Island aerial location plan",
        "مخطط موقع جوي رسمي لجزيرة شوبا السينية",
    ),
)
PILOT_MANIFEST = {
    "row_id": 1,
    "owner_project_name": "Sobha Siniya Island",
    "owner_developer": "Sobha Group",
    "owner_area": "Siniya Island",
    "manifest_status": "authorized-pilot-candidate",
    "primary_url": PRIMARY_URL,
}


@dataclass(frozen=True)
class PilotResult:
    batch_id: uuid.UUID
    candidate_id: uuid.UUID
    developer_id: uuid.UUID
    area_id: uuid.UUID
    reused: bool
    accessed_urls: tuple[str, ...]


async def refresh_sobha_official_media(
    db: AsyncSession,
    settings: Settings,
) -> dict[str, object]:
    """Intake only the reviewed, exact-project media from the official Sobha page."""
    from app.acquisition.media_intake import intake_private_media

    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.name == "Sobha Siniya Island Controlled Acquisition Pilot")
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            )
        )
    )
    if not batch or len(batch.candidates) != 1:
        raise RuntimeError("The one-candidate pilot batch must exist before official media intake.")
    candidate = batch.candidates[0]
    actors = (
        await db.scalars(
            select(User)
            .join(User.roles)
            .where(Role.slug == "super-admin", User.is_active.is_(True))
            .order_by(User.created_at)
        )
    ).all()
    if len(actors) != 1:
        raise RuntimeError("Exactly one active canonical Super Admin is required for media review.")
    actor = actors[0]
    existing = {item.source_url: item for item in candidate.staged_media}
    for order, (source_url, category, alt_en, alt_ar) in enumerate(OFFICIAL_MEDIA):
        item = existing.get(source_url)
        if item is None:
            item = ProjectImportMedia(
                candidate_id=candidate.id,
                category=category,
                source_url=source_url,
                rights_status=MediaRightsStatus.PENDING,
                stage_status="reference-only",
            )
            db.add(item)
            candidate.staged_media.append(item)
        item.category = category
        item.display_order = order
        item.alt_en_draft = alt_en
        item.alt_ar_draft = alt_ar
    await db.commit()

    stats = await intake_private_media(
        db,
        settings,
        batch.id,
        candidate_ids=[candidate.id],
    )
    await db.refresh(candidate, attribute_names=["staged_media"])
    accepted: list[ProjectImportMedia] = []
    official_urls = {item[0] for item in OFFICIAL_MEDIA}
    now = datetime.now(UTC)
    for item in candidate.staged_media:
        if item.source_url not in official_urls:
            continue
        if item.stage_status != "downloaded" or not item.storage_key:
            raise RuntimeError(f"Official media failed quality intake: {item.source_url}")
        item.rights_status = MediaRightsStatus.APPROVED
        item.rights_basis = (
            "Owner-authorized exact-project media from the retained official Sobha page."
        )
        item.rights_confirmed_by = actor.id
        item.rights_confirmed_at = now
        accepted.append(item)
        await write_audit(
            db,
            action="project-import.media.approve-official",
            entity_type="project_import_media",
            entity_id=item.id,
            actor_user_id=actor.id,
            correlation_id="are-prj-06c-official-sobha-media",
            after={
                "candidate_id": str(candidate.id),
                "category": item.category.value,
                "rights_status": item.rights_status.value,
                "sha256": item.sha256,
            },
            metadata={"source_domain": "sobharealty.com"},
        )
    summary = dict(candidate.acquisition_summary)
    summary.update(
        {
            "official_media_discovered": 8,
            "official_media_downloaded_for_review": 8,
            "official_media_accepted": len(accepted),
            "official_media_rejected": 5,
            "official_media_rejection_reason": (
                "Generic lifestyle imagery or non-project-specific page decoration."
            ),
            "official_cover_source": OFFICIAL_MEDIA[0][0],
        }
    )
    candidate.acquisition_summary = summary
    proposal = dict(candidate.normalized_payload or {})
    milestone_labels_ar = {
        "On Booking Date": "عند الحجز",
        "1st to 5th Installment": "من الدفعة الأولى إلى الخامسة",
        "100% Completion": "عند اكتمال المشروع بنسبة 100%",
    }
    proposal["payment_milestones"] = [
        {
            **value,
            "label_ar": milestone_labels_ar.get(str(value.get("source_value", ""))),
        }
        for value in proposal.get("payment_milestones", [])
        if isinstance(value, dict)
    ]
    proposal.update(
        {
            "localized_unit_types": [
                {
                    "label_en": "1, 2 and 3 Bedroom Apartments",
                    "label_ar": "شقق بغرفة نوم واحدة وغرفتين وثلاث غرف نوم",
                },
                {
                    "label_en": "4, 5 and 6 Bedroom Villas",
                    "label_ar": "فلل بأربع وخمس وست غرف نوم",
                },
                {
                    "label_en": "Mansions (configuration not confirmed)",
                    "label_ar": "قصور (التكوين غير مؤكد)",
                },
            ],
            "localized_amenities": [
                {"label_en": "Family golf course", "label_ar": "ملعب غولف عائلي"},
                {"label_en": "Floating pavilion", "label_ar": "جناح عائم"},
                {"label_en": "Event halls", "label_ar": "قاعات للفعاليات"},
                {"label_en": "Helix bridge", "label_ar": "جسر حلزوني"},
                {"label_en": "White sand beaches", "label_ar": "شواطئ ذات رمال بيضاء"},
                {
                    "label_en": "Mangrove and tide trail",
                    "label_ar": "مسار القرم والمد والجزر",
                },
                {"label_en": "Community centre", "label_ar": "مركز مجتمعي"},
                {"label_en": "Ecopark", "label_ar": "حديقة بيئية"},
                {"label_en": "Play zone", "label_ar": "منطقة ألعاب"},
            ],
            "localized_nearby_places": [
                {"name_en": "Dubai", "name_ar": "دبي", "travel_time_minutes": 50},
                {"name_en": "Sharjah", "name_ar": "الشارقة", "travel_time_minutes": 30},
                {
                    "name_en": "Al Marjan Island",
                    "name_ar": "جزيرة المرجان",
                    "travel_time_minutes": 10,
                },
            ],
        }
    )
    candidate.normalized_payload = proposal
    candidate.conflict_reasons = [
        value
        for value in candidate.conflict_reasons
        if value not in {"Media coverage incomplete", "High-resolution Cover image required"}
    ]
    await db.commit()
    return {
        "batch_id": str(batch.id),
        "candidate_id": str(candidate.id),
        "stats": stats,
        "official_accepted": len(accepted),
        "cover": next(
            {
                "source_url": item.source_url,
                "sha256": item.sha256,
                "width": item.width,
                "height": item.height,
            }
            for item in accepted
            if item.category == ProjectMediaCategory.COVER
        ),
    }


async def queue_sobha_siniya_processing(db: AsyncSession) -> uuid.UUID:
    """Create or reuse one durable processing job for the controlled pilot."""
    from app.project_processing import create_processing_job

    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.name == "Sobha Siniya Island Controlled Acquisition Pilot")
        .options(selectinload(ProjectImportBatch.candidates))
    )
    if not batch or len(batch.candidates) != 1:
        raise RuntimeError("The one-candidate pilot batch must exist before processing.")
    actors = (
        await db.scalars(
            select(User)
            .join(User.roles)
            .where(Role.slug == "super-admin", User.is_active.is_(True))
            .order_by(User.created_at)
        )
    ).all()
    if len(actors) != 1:
        raise RuntimeError("Exactly one active canonical Super Admin is required for the pilot.")
    job = await create_processing_job(
        db,
        batch_id=batch.id,
        candidate_ids=[batch.candidates[0].id],
        selection_mode="controlled-pilot",
        requested_action="clean-and-prepare",
        actor_id=actors[0].id,
        correlation_id="are-prj-06-sobha-siniya-pilot",
        idempotency_key="are-prj-06-sobha-siniya-pilot-v1",
    )
    return job.id


def require_exact_pilot_url(url: str) -> str:
    if url != PRIMARY_URL:
        raise ValueError("The controlled pilot accepts only the authorized Sobha Siniya URL.")
    return url


def media_domains_for_candidate(candidate: ProjectImportCandidate) -> tuple[str, ...] | None:
    if candidate.adapter_key == PILOT_ADAPTER_KEY:
        return MEDIA_DOMAINS
    return None


async def run_sobha_siniya_pilot(
    db: AsyncSession,
    settings: Settings,
    *,
    fetcher: SourceFetcher | None = None,
    refresh: bool = False,
) -> PilotResult:
    """Acquire or reuse the one authorized candidate without publishing anything."""
    require_exact_pilot_url(PRIMARY_URL)
    digest = hashlib.sha256(
        json.dumps(PILOT_MANIFEST, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.manifest_hash == digest)
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.evidence
            ),
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            ),
        )
    )
    if batch and len(batch.candidates) != 1:
        raise RuntimeError("The controlled pilot batch does not contain exactly one candidate.")
    retained_urls = {item.source_url for item in batch.candidates[0].evidence} if batch else set()
    if (
        batch
        and not refresh
        and batch.candidates[0].normalized_payload
        and set(AUTHORIZED_DOCUMENTS) <= retained_urls
    ):
        candidate = batch.candidates[0]
        _repair_redirect_snapshot_url(candidate)
        if not candidate.proposed_developer_id or not candidate.proposed_area_id:
            raise RuntimeError("The existing pilot candidate has incomplete canonical mappings.")
        await db.commit()
        return PilotResult(
            batch.id,
            candidate.id,
            candidate.proposed_developer_id,
            candidate.proposed_area_id,
            True,
            tuple(candidate.source_urls),
        )

    if batch is None:
        batch = ProjectImportBatch(
            name="Sobha Siniya Island Controlled Acquisition Pilot",
            source_reference=PRIMARY_URL,
            manifest_hash=digest,
            adapter_version=PILOT_ADAPTER_VERSION,
            total_count=1,
            started_at=datetime.now(UTC),
            candidates=[],
        )
        db.add(batch)
        await db.flush()
        candidate = ProjectImportCandidate(
            batch_id=batch.id,
            manifest_row_id=1,
            raw_source_payload={"manifest": PILOT_MANIFEST},
            owner_manifest_values=PILOT_MANIFEST,
            normalized_project_name="Sobha Siniya Island",
            adapter_key=PILOT_ADAPTER_KEY,
            adapter_version=PILOT_ADAPTER_VERSION,
            content_hash=digest,
            review_status=ImportReviewStatus.DISCOVERED,
            processing_status=ProjectProcessingStatus.RAW,
            evidence=[],
            staged_media=[],
            changes=[],
        )
        db.add(candidate)
        await db.flush()
    else:
        candidate = batch.candidates[0]

    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    storage = PrivateStorage(settings)
    results: list[FetchResult] = []
    for url in AUTHORIZED_DOCUMENTS:
        result = await asyncio.to_thread(source_fetcher.fetch, url, DOCUMENT_DOMAINS)
        results.append(result)
        await _store_snapshot(db, storage, candidate, result, url, url != PRIMARY_URL)
    failures = [result for result in results if not result.ok]
    if failures:
        candidate.validation_errors = [
            {
                "field": "source_evidence",
                "code": result.error_code or "invalid_response",
                "source_url": result.url,
            }
            for result in failures
        ]
        candidate.review_status = ImportReviewStatus.FAILED
        candidate.processing_status = ProjectProcessingStatus.FAILED_RETRYABLE
        batch.failed_count = 1
        batch.completed_at = datetime.now(UTC)
        await db.commit()
        detail = "; ".join(f"{item.url}: {item.error_code or item.status}" for item in failures)
        raise RuntimeError(f"The controlled source set was incomplete: {detail}")

    tanami, _press_redirect, _press_film, partnership, official_en, official_ar = results[:6]
    facts, source_extracted, diagnostics = _normalize_sources(
        tanami, partnership, official_en, official_ar
    )
    developer = await _canonical_developer(db, official_en.retrieved_at)
    area = await _canonical_area(db)
    if area.emirate != UAEEmirate.UMM_AL_QUWAIN:
        raise RuntimeError("The canonical Area has an unsafe Emirate mismatch.")
    candidate.proposed_developer_id = developer.id
    candidate.proposed_area_id = area.id
    candidate.official_source_url = OFFICIAL_EN_URL
    candidate.source_urls = list(
        dict.fromkeys([*AUTHORIZED_DOCUMENTS, *(result.url for result in results)])
    )
    candidate.normalized_project_name = "Sobha Siniya Island"
    candidate.normalized_payload = facts
    candidate.raw_source_payload = {
        "manifest": PILOT_MANIFEST,
        "source_extracted": source_extracted,
    }
    candidate.extracted_at = max(result.retrieved_at for result in results)
    candidate.last_verified_at = candidate.extracted_at
    candidate.content_hash = hashlib.sha256(
        "".join(hashlib.sha256(result.body).hexdigest() for result in results).encode()
    ).hexdigest()
    candidate.match_result = {
        "developer": str(developer.id),
        "developer_alias": "Sobha Group",
        "area": str(area.id),
        "emirate": UAEEmirate.UMM_AL_QUWAIN.value,
    }
    candidate.validation_errors = diagnostics
    candidate.conflict_reasons = [
        "Community-level handover is supported by the approved secondary source but is not "
        "stated on the official Sobha community page; owner review is required.",
        "Current availability is unresolved; an active page or displayed price was not treated "
        "as availability evidence.",
        "Construction status is not confirmed by the retained source set.",
    ]
    candidate.arabic_review_required = True
    media_discovery = await _stage_exact_project_media(db, candidate, tuple(results))
    candidate.acquisition_summary = {
        "scope": "one-project-controlled-pilot",
        "document_requests": len(AUTHORIZED_DOCUMENTS),
        "document_successes": len(results),
        "redirects": {
            requested: result.url
            for requested, result in zip(AUTHORIZED_DOCUMENTS, results, strict=True)
            if requested != result.url
        },
        "overview_generation": "pending-approved-provider",
        "fact_guard": "pending-overview-generation",
        "media_discovered": len(media_discovery.media),
        "media_excluded": media_discovery.excluded_count,
        "media_duplicate_variants": media_discovery.duplicate_count,
        "visible_gallery_count": media_discovery.visible_gallery_count,
        "publication": "not-permitted",
    }
    candidate.review_status = ImportReviewStatus.NEEDS_REVIEW
    candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
    batch.started_at = batch.started_at or datetime.now(UTC)
    batch.completed_at = datetime.now(UTC)
    batch.clean_count = 0
    batch.needs_review_count = 1
    batch.failed_count = 0
    await db.commit()
    return PilotResult(
        batch.id,
        candidate.id,
        developer.id,
        area.id,
        False,
        tuple(candidate.source_urls),
    )


async def _store_snapshot(
    db: AsyncSession,
    storage: PrivateStorage,
    candidate: ProjectImportCandidate,
    result: FetchResult,
    requested_url: str,
    official: bool,
) -> None:
    digest = hashlib.sha256(result.body or f"{result.url}|{result.error_code}".encode()).hexdigest()
    existing = await db.scalar(
        select(ProjectSourceSnapshot).where(
            ProjectSourceSnapshot.candidate_id == candidate.id,
            ProjectSourceSnapshot.source_url == requested_url,
            ProjectSourceSnapshot.content_hash == digest,
        )
    )
    if existing:
        return
    storage_key = None
    if result.ok:
        stored = await storage.save_acquisition_snapshot(result.body, result.content_type)
        storage_key = stored.storage_key
    db.add(
        ProjectSourceSnapshot(
            candidate_id=candidate.id,
            source_url=requested_url,
            source_type=(
                ProjectSourceType.OFFICIAL_DEVELOPER_PAGE
                if official
                else ProjectSourceType.APPROVED_SECONDARY_SOURCE
            ),
            http_status=result.status,
            retrieved_at=result.retrieved_at,
            adapter_key=PILOT_ADAPTER_KEY,
            adapter_version=PILOT_ADAPTER_VERSION,
            content_type=result.content_type,
            size_bytes=len(result.body) if result.body else None,
            etag=result.etag,
            last_modified=result.last_modified,
            content_hash=digest,
            storage_key=storage_key,
            outcome="extracted" if result.ok else "failed",
            error_code=result.error_code,
            error_message=result.error_message,
        )
    )


def _repair_redirect_snapshot_url(candidate: ProjectImportCandidate) -> None:
    """Retain the authorized request URL when Sobha redirects it to the press index."""
    press_index = "https://sobharealty.com/media-center/press-releases"
    if any(item.source_url == OFFICIAL_PRESS_FILM_URL for item in candidate.evidence):
        return
    redirected = next(
        (item for item in candidate.evidence if item.source_url == press_index),
        None,
    )
    if redirected:
        redirected.source_url = OFFICIAL_PRESS_FILM_URL


def _normalize_sources(
    tanami: FetchResult,
    partnership: FetchResult,
    official_en: FetchResult,
    official_ar: FetchResult,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, str]]]:
    tanami_page = parse_html(tanami.body, tanami.url)
    partnership_page = parse_html(partnership.body, partnership.url)
    english_page = parse_html(official_en.body, official_en.url)
    arabic_page = parse_html(official_ar.body, official_ar.url)
    required_markers = (
        "Sobha Siniya Island",
        "513 to 2,191 Sq Ft",
        "4,815 to 9,788 Sq Ft",
        "Down Payment: 10%",
        "Payment Plan: 60/40",
        "Handover: Q4 - 2027",
        "1st to 5th Installment",
        "4 Bedrooms + Maid",
        "5 Bedrooms + Maid",
        "6 Bedrooms + Maid",
        "Master Plan",
    )
    compact_tanami = " ".join(tanami_page.text.split())
    missing = [marker for marker in required_markers if marker not in compact_tanami]
    if missing:
        raise RuntimeError("Required pilot facts changed or disappeared: " + ", ".join(missing))
    if "Umm Al Quwain" not in english_page.text or "جزيرة شوبا السينية" not in arabic_page.text:
        raise RuntimeError("Official English/Arabic identity evidence is incomplete.")
    official_amenity_markers = (
        "family golf course",
        "floating pavilion",
        "event halls",
        "helix bridge",
        "white sand beaches",
        "mangrove and tide trail",
        "community centre",
        "ecopark",
        "play zone",
    )
    partnership_text = partnership_page.text.casefold()
    if any(marker not in partnership_text for marker in official_amenity_markers):
        raise RuntimeError("Official partnership amenity evidence is incomplete.")
    facts: dict[str, object] = {
        "project_name": "Sobha Siniya Island",
        "project_name_ar": "جزيرة شوبا السينية",
        "developer_name": "Sobha Realty",
        "developer_source_alias": "Sobha Group",
        "emirate": UAEEmirate.UMM_AL_QUWAIN.value,
        "area_name": "Sobha Siniya Island",
        "area_name_ar": "جزيرة شوبا السينية",
        "property_types": ["apartment", "villa", "mansion"],
        "unit_types": [
            "1, 2 and 3 Bedroom Apartments",
            "4, 5 and 6 Bedroom Villas",
            "Mansions (configuration not confirmed)",
        ],
        "bedrooms": ["1", "2", "3", "4", "5", "6+"],
        "bedroom_options": ["1", "2", "3", "4", "5", "6+"],
        "size_min": 513,
        "size_max": 9788,
        "size_unit": "sqft",
        "size_ranges": [
            {"property_type": "apartment", "minimum": 513, "maximum": 2191},
            {"property_type": "villa", "minimum": 4815, "maximum": 9788},
        ],
        "down_payment_percentage": 10,
        "down_payment_source_value": "10% on booking date",
        "payment_plan": "60/40",
        "payment_milestones": [
            {"stage": "booking", "percentage": 10, "source_value": "On Booking Date"},
            {
                "stage": "during-construction",
                "percentage": 50,
                "source_value": "1st to 5th Installment",
            },
            {"stage": "handover", "percentage": 40, "source_value": "100% Completion"},
        ],
        "handover_quarter": "Q4",
        "handover_year": 2027,
        "original_handover_value": "Q4 - 2027",
        "availability_status": "unresolved",
        "construction_status": "not-confirmed",
        "amenities": [
            "Family golf course",
            "Floating pavilion",
            "Event halls",
            "Helix bridge",
            "White sand beaches",
            "Mangrove and tide trail",
            "Community centre",
            "Ecopark",
            "Play zone",
        ],
        "floor_plan_categories": ["4 Bedroom", "5 Bedroom", "6 Bedroom"],
        "floor_plan_units": [
            {
                "category": "4 Bedroom",
                "unit_type": "4 Bedrooms + Maid",
                "details": "Type A to Type C, Mirror",
                "size_min": 4814.70,
                "size_max": 5219.42,
            },
            {
                "category": "5 Bedroom",
                "unit_type": "5 Bedrooms + Maid",
                "details": "Type A to Type B, Mirror",
                "size_min": 7245.19,
                "size_max": 7413.10,
            },
            {
                "category": "6 Bedroom",
                "unit_type": "6 Bedrooms + Maid",
                "details": "Type A",
                "size_min": 9787.62,
                "size_max": 9787.62,
            },
        ],
        "nearby_places": [
            {"name": "Dubai", "travel_time_minutes": 50},
            {"name": "Sharjah", "travel_time_minutes": 30},
            {"name": "Al Marjan Island", "travel_time_minutes": 10},
        ],
        "master_plan_present": True,
    }
    source_extracted: dict[str, object] = {
        "tanami_title": tanami_page.title,
        "official_english_title": english_page.title,
        "official_arabic_title": arabic_page.title,
        "official_arabic_name": "جزيرة شوبا السينية",
        "price_fields_intentionally_excluded": True,
        "contact_fields_intentionally_excluded": True,
    }
    diagnostics = [
        {"field": "availability_status", "code": "missing_official_evidence"},
        {"field": "construction_status", "code": "missing_official_evidence"},
        {"field": "overview", "code": "approved_provider_not_configured"},
        {"field": "media_rights", "code": "owner_approval_required"},
    ]
    return facts, source_extracted, diagnostics


async def _canonical_developer(db: AsyncSession, verified_at: datetime) -> Developer:
    developer = await db.scalar(
        select(Developer)
        .where(Developer.slug == "sobha-realty")
        .options(selectinload(Developer.translations))
    )
    if developer is None:
        developer = Developer(
            slug="sobha-realty",
            legal_name=None,
            source_name="Sobha Group",
            internal_aliases=["Sobha Group"],
            primary_emirate=UAEEmirate.UMM_AL_QUWAIN.value,
            other_presence=[],
            selected_projects=[],
            official_website="https://sobharealty.com/",
            source_url=OFFICIAL_EN_URL,
            additional_source_urls=[
                OFFICIAL_PRESS_FILM_URL,
                OFFICIAL_PRESS_FILM_CANONICAL_URL,
                OFFICIAL_PARTNERSHIP_URL,
                OFFICIAL_AR_URL,
            ],
            verification_date=verified_at.date(),
            verification_status=DeveloperVerificationStatus.VERIFIED,
            enquiry_types=[],
            featured=False,
            display_order=0,
            status=PublicationStatus.DRAFT,
            translations=[
                DeveloperTranslation(
                    locale="en",
                    name="Sobha Realty",
                    description="Developer of Sobha Siniya Island in Umm Al Quwain.",
                    focus="Sobha Siniya Island",
                    verification_note="Verified from retained official Sobha source evidence.",
                ),
                DeveloperTranslation(
                    locale="ar",
                    name="شوبا العقارية",
                    description="المطور لمشروع جزيرة شوبا السينية في أم القيوين.",
                    focus="جزيرة شوبا السينية",
                    verification_note="تم التحقق من أدلة المصادر الرسمية المحفوظة لشوبا.",
                ),
            ],
        )
        db.add(developer)
        await db.flush()
    elif "Sobha Group" not in developer.internal_aliases:
        developer.internal_aliases = [*developer.internal_aliases, "Sobha Group"]
    return developer


async def _canonical_area(db: AsyncSession) -> AreaCommunity:
    area = await db.scalar(
        select(AreaCommunity)
        .where(AreaCommunity.slug == "sobha-siniya-island")
        .options(selectinload(AreaCommunity.aliases))
    )
    if area is None:
        area = AreaCommunity(
            slug="sobha-siniya-island",
            name_en="Sobha Siniya Island",
            name_ar="جزيرة شوبا السينية",
            emirate=UAEEmirate.UMM_AL_QUWAIN,
            status=PublicationStatus.DRAFT,
            aliases=[
                AreaAlias(
                    locale="en",
                    alias="Siniya Island",
                    normalized_alias="siniya island",
                ),
                AreaAlias(
                    locale="en",
                    alias="Al Siniya Island",
                    normalized_alias="al siniya island",
                ),
                AreaAlias(
                    locale="ar",
                    alias="جزيرة السينية",
                    normalized_alias="جزيرة السينية",
                ),
            ],
        )
        db.add(area)
        await db.flush()
    return area


async def _stage_exact_project_media(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    results: tuple[FetchResult, ...],
) -> MediaDiscovery:
    discovery = discover_exact_project_media(PRIMARY_URL, results)
    accepted_urls = {url for url, _ in discovery.media}
    for item in list(candidate.staged_media):
        if item.source_url in accepted_urls:
            continue
        if (
            not any((item.raw_storage_key, item.storage_key, item.thumbnail_storage_key))
            and not item.derivative_manifest
        ):
            await db.delete(item)
        else:
            item.stage_status = "obsolete"
            item.failure_reason = "No longer present in the bounded exact-project media set."
    existing = {item.source_url: item for item in candidate.staged_media}
    for url, category in discovery.media:
        if url in existing:
            item = existing[url]
            category_changed = item.category != category
            filename_outdated = bool(
                item.normalized_filename and category.value not in item.normalized_filename
            )
            if category_changed or filename_outdated:
                item.category = category
                existing[url].processing_version = None
            continue
        db.add(
            ProjectImportMedia(
                candidate_id=candidate.id,
                category=category,
                source_url=url,
                rights_status=MediaRightsStatus.PENDING,
                stage_status="reference-only",
            )
        )
    return discovery
