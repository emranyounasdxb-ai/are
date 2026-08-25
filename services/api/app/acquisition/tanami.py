"""Reusable, explicit-list Tanami Project acquisition boundary.

Only owner-approved exact Project URLs enter this adapter. It may follow a small
set of same-project document links, but it never enumerates the Tanami catalogue
or follows related-project cards.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.adapters import adapter_for
from app.acquisition.contracts import (
    FetchResult,
    ManifestCandidate,
    NormalizedEvidence,
    SourceFetcher,
)
from app.acquisition.parser import clean, normalize_evidence, normalize_name, parse_html
from app.acquisition.security import BatchCachingFetcher, SecureFetcher, host_is_allowed
from app.config import Settings
from app.models import (
    AreaAlias,
    AreaCommunity,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMediaCategory,
    ProjectProcessingStatus,
    ProjectSourceSnapshot,
    ProjectSourceType,
)
from app.storage import PrivateStorage

TANAMI_ADAPTER_KEY = "tanami-explicit-project-list"
TANAMI_ADAPTER_VERSION = "2.0"
TANAMI_DOCUMENT_DOMAINS = ("tanamiproperties.com",)
TANAMI_MEDIA_DOMAINS = ("tanamiproperties.com", "manage.tanamiproperties.com")
PROJECT_PATH = re.compile(r"^/Projects/([A-Za-z0-9][A-Za-z0-9-]*)$")
SAME_PROJECT_SECTIONS = frozenset(
    {
        "amenities",
        "features",
        "floor-plan",
        "floor-plans",
        "gallery",
        "location",
        "master-plan",
        "overview",
        "payment-plan",
    }
)
REJECTED_CONTENT_TOKENS = frozenset(
    {
        "agent",
        "avatar",
        "contact",
        "currency",
        "favicon",
        "facebook",
        "icon",
        "instagram",
        "linkedin",
        "logo",
        "placeholder",
        "qr",
        "related",
        "snapchat",
        "social",
        "spinner",
        "tiktok",
        "tracking",
        "twitter",
        "whatsapp",
        "/x.",
        "youtube",
    }
)


@dataclass(frozen=True)
class TanamiIdentity:
    project_name: str
    developer_name: str | None
    area_name: str | None


@dataclass(frozen=True)
class TanamiDocumentSet:
    primary_url: str
    results: tuple[FetchResult, ...]
    normalized: NormalizedEvidence
    identity: TanamiIdentity
    media: tuple[tuple[str, ProjectMediaCategory], ...]


def normalize_project_urls(urls: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Validate and deterministically deduplicate explicit Tanami Project URLs."""
    if not urls:
        raise ValueError("At least one owner-approved Tanami Project URL is required.")
    normalized: dict[str, None] = {}
    for value in urls:
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or parsed.query
            or parsed.fragment
            or not host_is_allowed(parsed.hostname, TANAMI_DOCUMENT_DOMAINS)
            or not PROJECT_PATH.fullmatch(parsed.path.rstrip("/"))
        ):
            raise ValueError(
                "Every input must be an exact credential-free HTTPS Tanami Project URL."
            )
        canonical = urlunsplit(
            ("https", "www.tanamiproperties.com", parsed.path.rstrip("/"), "", "")
        )
        normalized[canonical] = None
    return tuple(sorted(normalized))


def same_project_urls(primary_url: str, body: bytes) -> tuple[str, ...]:
    """Return only bounded same-project documents linked by the exact Project page."""
    primary = normalize_project_urls([primary_url])[0]
    primary_path = urlsplit(primary).path
    parsed = parse_html(body, primary)
    accepted: set[str] = set()
    for value in parsed.links:
        split = urlsplit(value)
        path = split.path.rstrip("/")
        if (
            split.scheme != "https"
            or not split.hostname
            or not host_is_allowed(split.hostname, TANAMI_DOCUMENT_DOMAINS)
            or split.query
            or path == primary_path
            or not path.startswith(f"{primary_path}/")
        ):
            continue
        remainder = path[len(primary_path) + 1 :].casefold()
        if remainder in SAME_PROJECT_SECTIONS:
            accepted.add(urlunsplit(("https", "www.tanamiproperties.com", path, "", "")))
    return tuple(sorted(accepted))


async def acquire_project_documents(
    url: str,
    *,
    fetcher: SourceFetcher | None = None,
) -> TanamiDocumentSet:
    """Fetch one exact Project and its explicitly linked same-project documents."""
    primary_url = normalize_project_urls([url])[0]
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    primary = await asyncio.to_thread(source_fetcher.fetch, primary_url, TANAMI_DOCUMENT_DOMAINS)
    if not primary.ok or primary.content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError(primary.error_message or "The exact Tanami Project page was unavailable.")
    results = [primary]
    for linked_url in same_project_urls(primary_url, primary.body):
        result = await asyncio.to_thread(source_fetcher.fetch, linked_url, TANAMI_DOCUMENT_DOMAINS)
        if result.ok and result.content_type in {"text/html", "application/xhtml+xml"}:
            results.append(result)
    identity = extract_identity(primary)
    manifest = ManifestCandidate(
        row_id=1,
        project_name=identity.project_name,
        developer=identity.developer_name or "Developer not confirmed",
        area=identity.area_name or "Area not confirmed",
    )
    combined = _combined_normalized(results, manifest)
    media = exact_project_media(primary_url, tuple(results))
    return TanamiDocumentSet(primary_url, tuple(results), combined, identity, media)


def extract_identity(result: FetchResult) -> TanamiIdentity:
    page = parse_html(result.body, result.url)
    project_name = next((value for value in page.headings if value), page.title)
    if not project_name:
        raise ValueError("The exact Tanami page did not expose a Project identity.")
    project_name = re.split(r"\s+[|–—]\s+", project_name, maxsplit=1)[0].strip()
    developer = _label_value(page.text, ("developer", "developed by"))
    area = _label_value(page.text, ("area", "location", "community"))
    return TanamiIdentity(project_name, developer, area)


def _label_value(text: str, labels: tuple[str, ...]) -> str | None:
    next_label = (
        "Developer|Developed by|Area|Location|Community|Property Type|Bedrooms|Handover|"
        "Payment Plan"
    )
    for label in labels:
        match = re.search(
            rf"\b{re.escape(label)}\s*[:\-]\s*([^|•\n]{{2,100}}?)"
            rf"(?=\s+(?:{next_label})\s*[:\-]|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            return clean(match.group(1)).rstrip(".,")
    return None


def _combined_normalized(
    results: list[FetchResult], manifest: ManifestCandidate
) -> NormalizedEvidence:
    normalized = [normalize_evidence(parse_html(item.body, item.url), manifest) for item in results]
    extracted: dict[str, object] = {}
    proposal: dict[str, object] = {}
    conflicts: list[str] = []
    media: set[str] = set()
    for item in normalized:
        for key, value in item.source_extracted.items():
            if value not in (None, [], {}, "") and key not in extracted:
                extracted[key] = value
                proposal[key] = value
        conflicts.extend(item.conflicts)
        media.update(item.media_urls)
    extracted.setdefault("project_name", manifest.project_name)
    proposal.setdefault("project_name", manifest.project_name)
    missing = tuple(
        key
        for key in (
            "developer",
            "area",
            "property_types",
            "bedrooms",
            "handover_quarter",
            "handover_year",
            "payment_plan",
            "availability_status",
            "construction_status",
        )
        if proposal.get(key) in (None, [], {}, "")
    )
    return NormalizedEvidence(
        source_extracted=extracted,
        normalized_proposal=proposal,
        missing_fields=missing,
        conflicts=tuple(dict.fromkeys(conflicts)),
        media_urls=tuple(sorted(media)),
    )


class _ContextualMediaParser(HTMLParser):
    def __init__(self, base_url: str, primary_path: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.primary_path = primary_path
        self.anchor_stack: list[str | None] = []
        self.media: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a":
            href = values.get("href")
            self.anchor_stack.append(urljoin(self.base_url, href) if href else None)
        if tag not in {"img", "source"}:
            return
        source = values.get("src") or values.get("data-src") or values.get("data-lazy-src")
        if not source:
            return
        linked = next((item for item in reversed(self.anchor_stack) if item), None)
        if linked:
            linked_path = urlsplit(linked).path.rstrip("/")
            if linked_path.startswith("/Projects/") and linked_path != self.primary_path:
                return
        self.media.add(urljoin(self.base_url, source))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchor_stack:
            self.anchor_stack.pop()


def exact_project_media(
    primary_url: str, results: tuple[FetchResult, ...]
) -> tuple[tuple[str, ProjectMediaCategory], ...]:
    """Collect media embedded in exact-project documents, excluding related-card assets."""
    primary_path = urlsplit(primary_url).path.rstrip("/")
    selected: dict[str, ProjectMediaCategory] = {}
    for result in results:
        parser = _ContextualMediaParser(result.url, primary_path)
        parser.feed(result.body.decode("utf-8", errors="replace"))
        section = urlsplit(result.url).path.rstrip("/").rsplit("/", 1)[-1].casefold()
        for url in parser.media:
            split = urlsplit(url)
            path = split.path.casefold()
            if (
                split.scheme != "https"
                or not split.hostname
                or not host_is_allowed(split.hostname, TANAMI_MEDIA_DOMAINS)
                or not path.endswith((".jpg", ".jpeg", ".png", ".webp", ".avif"))
                or any(token in path for token in REJECTED_CONTENT_TOKENS)
            ):
                continue
            selected[url] = _media_category(path, section)
    return tuple(sorted(selected.items()))


def _media_category(path: str, section: str) -> ProjectMediaCategory:
    value = f"{path} {section}"
    if "floor" in value:
        return ProjectMediaCategory.FLOOR_PLAN
    if "master" in value:
        return ProjectMediaCategory.MASTER_PLAN
    if "location" in value or "map" in value:
        return ProjectMediaCategory.LOCATION_MAP
    if "amenit" in value or "feature" in value:
        return ProjectMediaCategory.AMENITIES
    if "interior" in value:
        return ProjectMediaCategory.INTERIOR
    if "exterior" in value or "facade" in value:
        return ProjectMediaCategory.EXTERIOR
    if "cover" in value or "hero" in value or "banner" in value:
        return ProjectMediaCategory.COVER
    return ProjectMediaCategory.GALLERY


async def acquire_explicit_batch(
    db: AsyncSession,
    settings: Settings,
    urls: list[str] | tuple[str, ...],
    *,
    fetcher: SourceFetcher | None = None,
    batch_name: str | None = None,
) -> ProjectImportBatch:
    """Acquire an idempotent review batch from an explicit approved URL list."""
    approved_urls = normalize_project_urls(urls)
    digest = hashlib.sha256(json.dumps(approved_urls, separators=(",", ":")).encode()).hexdigest()
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.manifest_hash == digest)
        .execution_options(populate_existing=True)
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.evidence
            ),
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            ),
        )
    )
    if batch is None:
        batch = ProjectImportBatch(
            name=batch_name or f"Tanami explicit Project batch {digest[:12]}",
            source_reference="explicit-owner-approved-url-list",
            manifest_hash=digest,
            adapter_version=TANAMI_ADAPTER_VERSION,
            total_count=len(approved_urls),
            started_at=datetime.now(UTC),
            candidates=[],
        )
        db.add(batch)
        await db.flush()
    existing = {item.manifest_row_id: item for item in batch.candidates}
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    storage = PrivateStorage(settings)
    for row_id, url in enumerate(approved_urls, start=1):
        documents = await acquire_project_documents(url, fetcher=source_fetcher)
        candidate = existing.get(row_id)
        if candidate is None:
            candidate = ProjectImportCandidate(
                batch_id=batch.id,
                manifest_row_id=row_id,
                raw_source_payload={},
                owner_manifest_values={"approved_project_url": url},
                normalized_project_name=documents.identity.project_name,
                content_hash=hashlib.sha256(url.encode()).hexdigest(),
                review_status=ImportReviewStatus.DISCOVERED,
                processing_status=ProjectProcessingStatus.RAW,
                evidence=[],
                staged_media=[],
                changes=[],
            )
            batch.candidates.append(candidate)
            await db.flush()
            existing[row_id] = candidate
        elif candidate.owner_manifest_values.get("approved_project_url") != url:
            raise ValueError("An existing explicit batch row has a different approved URL.")
        await _update_candidate(db, storage, candidate, documents, source_fetcher)
        await db.commit()
    batch.completed_at = datetime.now(UTC)
    batch.clean_count = 0
    batch.needs_review_count = len(approved_urls)
    batch.failed_count = 0
    await db.commit()
    return batch


async def _update_candidate(
    db: AsyncSession,
    storage: PrivateStorage,
    candidate: ProjectImportCandidate,
    documents: TanamiDocumentSet,
    fetcher: SourceFetcher,
) -> None:
    previous = candidate.normalized_payload or {}
    for result in documents.results:
        await _store_snapshot(
            db, storage, candidate, result, ProjectSourceType.APPROVED_SECONDARY_SOURCE
        )
    identity = documents.identity
    proposal = dict(documents.normalized.normalized_proposal)
    human_conflicts: list[str] = []
    for field_name in candidate.human_edited_fields:
        if field_name in previous and previous.get(field_name) != proposal.get(field_name):
            proposal[field_name] = previous[field_name]
            human_conflicts.append(f"Human-edited field preserved during refresh: {field_name}.")
    candidate.owner_manifest_values = {
        "approved_project_url": documents.primary_url,
        "source_project_name": identity.project_name,
        "source_developer": identity.developer_name,
        "source_area": identity.area_name,
    }
    candidate.adapter_key = TANAMI_ADAPTER_KEY
    candidate.adapter_version = TANAMI_ADAPTER_VERSION
    candidate.normalized_project_name = identity.project_name
    candidate.normalized_payload = proposal
    candidate.raw_source_payload = {
        "source_extracted": documents.normalized.source_extracted,
        "document_count": len(documents.results),
    }
    candidate.source_urls = [item.url for item in documents.results]
    candidate.extracted_at = max(item.retrieved_at for item in documents.results)
    candidate.last_verified_at = candidate.extracted_at
    candidate.content_hash = hashlib.sha256(
        "".join(hashlib.sha256(item.body).hexdigest() for item in documents.results).encode()
    ).hexdigest()
    conflicts = [*documents.normalized.conflicts, *human_conflicts]
    official_status = "not-resolved"
    if identity.developer_name:
        official = adapter_for(identity.developer_name)
        if official:
            manifest = ManifestCandidate(
                candidate.manifest_row_id,
                identity.project_name,
                identity.developer_name,
                identity.area_name or "Area not confirmed",
            )
            discovery = await asyncio.to_thread(official.discover, manifest, fetcher)
            if discovery.source_url:
                result, evidence = await asyncio.to_thread(
                    official.acquire,
                    manifest,
                    discovery,
                    fetcher,
                )
                if result.ok and evidence:
                    await _store_snapshot(
                        db,
                        storage,
                        candidate,
                        result,
                        ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
                    )
                    candidate.official_source_url = result.url
                    candidate.source_urls = list(
                        dict.fromkeys([*candidate.source_urls, result.url])
                    )
                    for localized_url in discovery.localized_urls:
                        if localized_url == result.url:
                            continue
                        localized = await asyncio.to_thread(
                            fetcher.fetch, localized_url, official.allowed_domains
                        )
                        if localized.ok:
                            await _store_snapshot(
                                db,
                                storage,
                                candidate,
                                localized,
                                ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
                            )
                            candidate.source_urls = list(
                                dict.fromkeys([*candidate.source_urls, localized.url])
                            )
                    official_status = "corroborated"
                else:
                    official_status = "source-unavailable"
            else:
                official_status = "source-not-found"
            if official.canonical_developer_slug:
                from app.acquisition.service import match_developer_identity

                candidate.proposed_developer_id = await match_developer_identity(
                    db, official.canonical_developer_slug
                )
        else:
            official_status = "alias-not-registered"
    if identity.area_name:
        candidate.proposed_area_id = await _match_area(db, identity.area_name)
    if not candidate.proposed_developer_id:
        conflicts.append("Canonical Developer requires exact human resolution.")
    if not candidate.proposed_area_id:
        conflicts.append("Canonical Area/Community requires exact human resolution.")
    media_warning = None
    if len(documents.media) < 2:
        media_warning = (
            "Insufficient exact-project media was discovered; retain the candidate for review."
        )
        conflicts.append(media_warning)
    candidate.validation_errors = [
        {"field": field, "code": "missing_source_evidence"}
        for field in documents.normalized.missing_fields
    ]
    if official_status != "corroborated":
        candidate.validation_errors.append(
            {
                "field": "official_developer_source",
                "code": "official_source_not_found",
                "message": "Official Developer corroboration requires review or recovery.",
            }
        )
    candidate.conflict_reasons = list(dict.fromkeys(conflicts))
    candidate.acquisition_summary = {
        "source_status": "acquired",
        "official_developer_status": official_status,
        "document_count": len(documents.results),
        "media_discovered": len(documents.media),
        "media_warning": media_warning,
        "publication": "not-permitted",
    }
    candidate.review_status = ImportReviewStatus.NEEDS_REVIEW
    candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
    await _stage_media(db, candidate, documents.media)


async def refresh_explicit_candidate(
    db: AsyncSession,
    settings: Settings,
    candidate_id: UUID,
    *,
    fetcher: SourceFetcher | None = None,
) -> ProjectImportCandidate:
    """Refresh one existing explicit-list candidate without changing its identity."""
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == candidate_id)
        .options(
            selectinload(ProjectImportCandidate.evidence),
            selectinload(ProjectImportCandidate.staged_media),
        )
    )
    if not candidate or candidate.adapter_key != TANAMI_ADAPTER_KEY:
        raise ValueError("Only an existing reusable Tanami candidate may use this refresh.")
    value = candidate.owner_manifest_values.get("approved_project_url")
    if not isinstance(value, str):
        raise ValueError("The candidate has no retained owner-approved Project URL.")
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    documents = await acquire_project_documents(value, fetcher=source_fetcher)
    await _update_candidate(db, PrivateStorage(settings), candidate, documents, source_fetcher)
    candidate.human_review_completed = False
    candidate.review_version += 1
    await db.commit()
    return candidate


async def _store_snapshot(
    db: AsyncSession,
    storage: PrivateStorage,
    candidate: ProjectImportCandidate,
    result: FetchResult,
    source_type: ProjectSourceType,
) -> None:
    digest = hashlib.sha256(result.body).hexdigest()
    existing = await db.scalar(
        select(ProjectSourceSnapshot).where(
            ProjectSourceSnapshot.candidate_id == candidate.id,
            ProjectSourceSnapshot.source_url == result.url,
            ProjectSourceSnapshot.content_hash == digest,
        )
    )
    if existing:
        return
    stored = await storage.save_acquisition_snapshot(result.body, result.content_type)
    db.add(
        ProjectSourceSnapshot(
            candidate_id=candidate.id,
            source_url=result.url,
            source_type=source_type,
            http_status=result.status,
            retrieved_at=result.retrieved_at,
            adapter_key=TANAMI_ADAPTER_KEY,
            adapter_version=TANAMI_ADAPTER_VERSION,
            content_type=result.content_type,
            size_bytes=len(result.body),
            etag=result.etag,
            last_modified=result.last_modified,
            content_hash=digest,
            storage_key=stored.storage_key,
            outcome="extracted",
        )
    )


async def _stage_media(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    media: tuple[tuple[str, ProjectMediaCategory], ...],
) -> None:
    existing = {item.source_url: item for item in candidate.staged_media}
    for order, (url, category) in enumerate(media[:24]):
        item = existing.get(url)
        if item:
            item.category = category
            item.last_seen_at = datetime.now(UTC)
            continue
        db.add(
            ProjectImportMedia(
                candidate_id=candidate.id,
                category=category,
                source_url=url,
                rights_status=MediaRightsStatus.PENDING,
                stage_status="reference-only",
                display_order=order,
                last_seen_at=datetime.now(UTC),
            )
        )


async def _match_area(db: AsyncSession, name: str) -> UUID | None:
    direct = await db.scalar(
        select(AreaCommunity.id).where(func.lower(AreaCommunity.name_en) == name.casefold())
    )
    if direct:
        return direct if isinstance(direct, UUID) else None
    result = await db.scalar(
        select(AreaAlias.area_id).where(AreaAlias.normalized_alias == normalize_name(name))
    )
    return result if isinstance(result, UUID) else None
