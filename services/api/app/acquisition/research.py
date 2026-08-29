"""Bounded official-source reinspection of existing private import candidates.

Discovery and parsing are research evidence, never approval. No Projects,
canonical identities, media rights or publication transitions are created here.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.acquisition.adapters import (
    PROJECT_FORM_SUFFIXES,
    adapter_for,
    official_url_matches_project,
)
from app.acquisition.contracts import DiscoveryResult, ManifestCandidate, SourceFetcher
from app.acquisition.parser import normalize_evidence, normalize_name, parse_html
from app.acquisition.reconciliation import (
    reconcile_candidate_quality,
    source_disagreement,
)
from app.acquisition.security import BatchCachingFetcher, SecureFetcher, host_is_allowed
from app.acquisition.tanami import _store_snapshot
from app.audit import write_audit
from app.config import Settings
from app.models import (
    ImportReviewStatus,
    Project,
    ProjectImportCandidate,
    ProjectMediaCategory,
    ProjectProcessingStatus,
    ProjectSourceType,
    PublicationStatus,
)
from app.project_field_policy import (
    candidate_media_is_preview_eligible,
    candidate_readiness_blockers,
    candidate_readiness_missing_fields,
)
from app.storage import PrivateStorage

RESEARCH_VERSION = "official-readiness-v1"
EXPLICIT_REFERENCE_DOMAINS = ("linkedin.com", "sharjah24.ae", "wam.ae")


def discovery_inspection_urls(discovery: DiscoveryResult | None) -> list[str]:
    """Inspect one bounded fuzzy URL privately; document identity still decides acceptance."""
    if discovery is None:
        return []
    if discovery.match_kind == "deterministic":
        return [
            url for url in dict.fromkeys([discovery.source_url, *discovery.localized_urls]) if url
        ]
    if discovery.match_kind == "fuzzy-suggestion" and discovery.suggested_url:
        return [discovery.suggested_url]
    return []


def research_fingerprint(research: dict[str, Any]) -> str:
    """Compare evidence outcomes without treating observation timestamps as changes."""
    stable = json.loads(json.dumps(research))
    stable.pop("checked_at", None)
    for document in stable.get("documents", []):
        document.pop("retrieved_at", None)
    return json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def recalculate_stored_conflicts(
    candidate: ProjectImportCandidate, storage: PrivateStorage
) -> list[dict[str, Any]]:
    """Replay retained evidence for the reproduced size/CTA parser defects only.

    A missing/unreadable snapshot is not a resolution. Original observations
    remain in the private summary alongside the deterministic replay result.
    """
    summary = dict(candidate.acquisition_summary or {})
    latest = {
        item.source_url: item
        for item in sorted(candidate.evidence, key=lambda item: item.retrieved_at)
    }
    resolved: list[dict[str, Any]] = list(summary.get("parser_conflict_resolutions", []))
    manifest = ManifestCandidate(
        candidate.manifest_row_id, candidate.normalized_project_name or "", "", ""
    )
    for entry in summary.get("official_fact_evidence", []):
        field = entry.get("field")
        if field not in {"size_min", "size_max", "availability_status"}:
            continue
        if field in getattr(candidate, "human_edited_fields", []):
            continue
        if (
            sum(item.get("field") == field for item in summary.get("official_fact_evidence", []))
            > 1
        ):
            # A partial replay must not remove another disagreement for this field.
            continue
        sources = list(entry.get("sources") or [])
        if not sources and entry.get("source_url"):
            # Official-vs-retained comparisons keep the baseline value in the
            # conflict evidence; do not guess another URL for that baseline.
            sources = [{"source_url": entry["source_url"], "value": entry.get("official_value")}]
        observations: list[dict[str, Any]] = []
        for source in sources:
            snapshot = latest.get(source.get("source_url"))
            if not snapshot or not snapshot.storage_key or snapshot.content_type != "text/html":
                break
            try:
                body = storage.read(snapshot.storage_key)
            except OSError:
                # Missing private evidence must keep the disagreement unresolved.
                break
            parsed = parse_html(body, snapshot.source_url)
            value = normalize_evidence(parsed, manifest).normalized_proposal.get(field)
            if value is None and not (
                field == "availability_status"
                and (source.get("value") == "coming-soon")
                and re.search(r"\bregister (?:your )?interest\b", parsed.text, re.I)
            ):
                # Absence alone never disproves a prior factual observation.
                break
            observations.append(
                {
                    "source_url": snapshot.source_url,
                    "value": value,
                    "sha256": hashlib.sha256(body).hexdigest(),
                }
            )
        else:
            if not observations:
                continue
            values = [item["value"] for item in observations]
            if "retained_value" in entry:
                values.append(entry["retained_value"])
            replacement = source_disagreement(field, values)
            matches = [
                reason
                for reason in candidate.conflict_reasons
                if reason.startswith(f"Source disagreement for {field}:")
            ]
            if not replacement and matches:
                candidate.conflict_reasons = [
                    reason for reason in candidate.conflict_reasons if reason not in matches
                ]
                resolved.append(
                    {
                        "field": field,
                        "previous_reasons": matches,
                        "observations": observations,
                        "reason": "Replayed retained evidence with corrected range/CTA parser",
                        "parser_version": RESEARCH_VERSION,
                    }
                )
    summary["parser_conflict_resolutions"] = resolved
    candidate.acquisition_summary = summary
    reconcile_candidate_quality(candidate)
    return resolved


def exact_document_identity(project_name: str, heading: str) -> bool:
    """Exact normalized identities only; never equate numbered phases/units."""
    identity = re.split(r"\s+(?:at|by)\s+", project_name, maxsplit=1, flags=re.I)[0]
    heading = re.split(r"\s(?:\||-|–)\s", heading, maxsplit=1)[0]
    heading = re.split(r"\s+by\s+", heading, maxsplit=1, flags=re.I)[0]
    expected = normalize_name(identity).split()
    actual = normalize_name(heading).split()
    if actual[:1] == ["about"]:
        actual = actual[1:]
    while expected and expected[-1] in PROJECT_FORM_SUFFIXES:
        expected.pop()
    while actual and actual[-1] in PROJECT_FORM_SUFFIXES:
        actual.pop()
    if not expected:
        return False
    if sorted(expected) == sorted(actual):
        return True
    if "".join(expected) == "".join(actual):
        return True
    # Official announcements commonly wrap an exact multi-token Project name
    # in a longer headline. Accept only the contiguous identity phrase so phase
    # numbers remain mandatory, while excluding unit/configuration pages.
    if len(expected) < 2:
        return False
    unit_suffixes = {
        "apartment",
        "apartments",
        "bedroom",
        "bedrooms",
        "br",
        "duplex",
        "studio",
        "townhouse",
        "townhouses",
        "unit",
        "units",
        "villa",
        "villas",
    }
    if set(actual) & unit_suffixes:
        return False
    expected_numbers = {value for value in expected if value.isdigit()}
    if expected_numbers:
        for number in expected_numbers:
            positions = [index for index, value in enumerate(actual) if value == number]
            expected_index = expected.index(number)
            neighbours = {
                value
                for value in (
                    expected[expected_index - 1] if expected_index else None,
                    expected[expected_index + 1] if expected_index + 1 < len(expected) else None,
                )
                if value
            }
            if not any(
                (index and actual[index - 1] in neighbours)
                or (index + 1 < len(actual) and actual[index + 1] in neighbours)
                for index in positions
            ):
                return False
    else:
        expected_tail_positions = [
            index for index, value in enumerate(actual) if value == expected[-1]
        ]
        if any(
            index + 1 < len(actual) and actual[index + 1].isdigit()
            for index in expected_tail_positions
        ):
            return False
    return set(expected) <= set(actual)


def readiness_report(candidate: ProjectImportCandidate) -> dict[str, Any]:
    """Report evidence and editorial/rights gates separately from Draft existence."""
    reconcile_candidate_quality(candidate)
    proposal = candidate.normalized_payload or {}
    missing = candidate_readiness_missing_fields(candidate)
    media = [item for item in candidate.staged_media if item.stage_status == "downloaded"]
    rights_unclear = [item for item in media if not candidate_media_is_preview_eligible(item)]
    approved_media = [item for item in media if item not in rights_unclear]
    blockers = candidate_readiness_blockers(candidate, missing)
    draft = candidate.editorial_draft
    research = (candidate.acquisition_summary or {}).get("source_first_research", {})
    return {
        "candidate_id": str(candidate.id),
        "project_id": str(candidate.linked_project_id) if candidate.linked_project_id else None,
        "row": candidate.manifest_row_id,
        "project": candidate.normalized_project_name,
        "ready": not blockers,
        "status": "Publication-ready; owner publication approval required"
        if not blockers
        else "Draft / Needs Review",
        "missing": sorted(missing),
        "conflicts": list(candidate.conflict_reasons),
        "blockers": list(dict.fromkeys(blockers)),
        "media": dict(Counter(item.stage_status for item in candidate.staged_media)),
        "prepared_media": len(media),
        "rights_unclear_media": len(rights_unclear),
        "prepared_cover": sum(item.category == ProjectMediaCategory.COVER for item in media),
        "prepared_gallery": sum(item.category == ProjectMediaCategory.GALLERY for item in media),
        "media_failures": [
            {"source_url": item.source_url, "reason": item.failure_reason}
            for item in candidate.staged_media
            if item.stage_status == "failed"
        ],
        "rights_cleared_cover": sum(
            item.category == ProjectMediaCategory.COVER for item in approved_media
        ),
        "overview_en": bool(draft and draft.overview_en),
        "overview_ar": bool(draft and draft.overview_ar),
        "official_research": research,
        "contextual_fact_review": (candidate.acquisition_summary or {}).get(
            "contextual_fact_review"
        ),
        "stored_fields_not_automatically_verified": proposal,
        "conflict_evidence": (candidate.acquisition_summary or {}).get(
            "official_fact_evidence", []
        ),
        "parser_resolutions": (candidate.acquisition_summary or {}).get(
            "parser_conflict_resolutions", []
        ),
    }


async def research_existing_batch(
    db: AsyncSession,
    settings: Settings,
    batch_id: UUID,
    *,
    fetcher: SourceFetcher | None = None,
    extra_urls: dict[int, list[str]] | None = None,
    candidate_ids: list[UUID] | None = None,
    discover: bool = True,
) -> dict[str, Any]:
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    storage = PrivateStorage(settings)
    statement = select(ProjectImportCandidate).where(ProjectImportCandidate.batch_id == batch_id)
    if candidate_ids is not None:
        if not candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("Select existing unique candidate IDs.")
        statement = statement.where(ProjectImportCandidate.id.in_(candidate_ids))
    candidates = list(await db.scalars(statement.order_by(ProjectImportCandidate.manifest_row_id)))
    if not candidates:
        raise ValueError("Research requires an existing nonempty batch.")
    if candidate_ids is not None and len(candidates) != len(candidate_ids):
        raise ValueError("Every selected candidate must belong to the requested batch.")
    linked_ids = [item.linked_project_id for item in candidates if item.linked_project_id]
    locked_project = await db.scalar(
        select(Project.id).where(
            Project.id.in_(linked_ids), Project.status != PublicationStatus.DRAFT
        )
    )
    if locked_project:
        raise ValueError("Research may update candidates linked to Draft Projects only.")
    reports: list[dict[str, Any]] = []
    mutated = 0
    for candidate in candidates:
        before_state = json.dumps(
            {
                "official_source_url": candidate.official_source_url,
                "acquisition_summary": candidate.acquisition_summary,
                "validation_errors": candidate.validation_errors,
                "conflict_reasons": candidate.conflict_reasons,
                "processing_status": candidate.processing_status.value,
                "review_status": candidate.review_status.value,
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        name = candidate.normalized_project_name or ""
        owner = candidate.owner_manifest_values
        developer = str(owner.get("source_developer") or owner.get("listing_developer") or "")
        area = str(owner.get("source_area") or owner.get("listing_area") or "")
        adapter = adapter_for(developer)
        research: dict[str, Any] = {
            "version": RESEARCH_VERSION,
            "checked_at": datetime.now(UTC).isoformat(),
            "documents": [],
            "exact_documents": [],
            "candidate_scoped_documents": [],
            "failures": [],
            "automatic_approval": False,
        }
        if adapter:
            manifest = ManifestCandidate(candidate.manifest_row_id, name, developer, area)
            discovery = (
                await asyncio.to_thread(adapter.discover, manifest, source_fetcher)
                if discover
                else None
            )
            research["failures"] = list(discovery.failures) if discovery else []
            discovered_urls = discovery_inspection_urls(discovery)
            if discovery and discovery.match_kind == "fuzzy-suggestion":
                research["failures"].append(
                    "Fuzzy URL inspected privately; exact document identity remains required"
                )
            urls = list(
                dict.fromkeys(
                    url
                    for url in [
                        *(extra_urls or {}).get(candidate.manifest_row_id, []),
                        candidate.official_source_url if discover else None,
                        *discovered_urls,
                    ]
                    if url
                )
            )[:8]
            scoped_urls = set((extra_urls or {}).get(candidate.manifest_row_id, []))
            for url in urls:
                is_explicit = url in scoped_urls
                allowed_domains = adapter.allowed_domains
                if is_explicit:
                    allowed_domains = (*allowed_domains, *EXPLICIT_REFERENCE_DOMAINS)
                if not host_is_allowed(urlsplit(url).hostname or "", allowed_domains):
                    research["failures"].append(f"Unapproved source domain: {url}")
                    continue
                result = await asyncio.to_thread(source_fetcher.fetch, url, allowed_domains)
                document: dict[str, Any] = {
                    "requested_url": url,
                    "source_url": result.url,
                    "retrieved_at": result.retrieved_at.isoformat(),
                    "status": result.status,
                    "error": result.error_code,
                    "sha256": hashlib.sha256(result.body).hexdigest(),
                    "exact_identity": False,
                }
                if result.ok:
                    source_type = ProjectSourceType.OFFICIAL_DEVELOPER_PAGE
                    if not host_is_allowed(
                        urlsplit(result.url).hostname or "", adapter.allowed_domains
                    ):
                        source_type = ProjectSourceType.APPROVED_SECONDARY_SOURCE
                    elif result.content_type == "application/pdf":
                        source_type = ProjectSourceType.OFFICIAL_DEVELOPER_BROCHURE
                    await _store_snapshot(db, storage, candidate, result, source_type)
                    if url in scoped_urls:
                        research["candidate_scoped_documents"].append(result.url)
                    if result.content_type in {"text/html", "application/xhtml+xml"}:
                        parsed = parse_html(result.body, result.url)
                        document["title"] = parsed.title
                        document["headings"] = list(parsed.headings[:12])
                        url_identity = official_url_matches_project(name, result.url)
                        identity_headings = list(parsed.headings[:2])
                        if "/property_category/" in urlsplit(result.url).path and url_identity:
                            identity_headings = list(parsed.headings[:6])
                        document["exact_identity"] = any(
                            exact_document_identity(name, heading)
                            for heading in [parsed.title or "", *identity_headings]
                        )
                        document["url_identity"] = url_identity
                        if document["exact_identity"]:
                            research["exact_documents"].append(result.url)
                        # Parsed proposals are private research only. Whole-page facts can
                        # include related Projects and require contextual adjudication.
                        document["unreviewed_proposal"] = normalize_evidence(
                            parsed, manifest
                        ).normalized_proposal
                        document["brochure_urls"] = [
                            link
                            for link in parsed.links
                            if urlsplit(link).path.lower().endswith(".pdf")
                            and host_is_allowed(
                                urlsplit(link).hostname or "", adapter.allowed_domains
                            )
                        ]
                        document["media_reference_count"] = len(parsed.media_urls)
                research["documents"].append(document)
        else:
            research["failures"].append("Exact canonical Developer adapter unavailable")
        research["exact_documents"] = list(dict.fromkeys(research["exact_documents"]))
        research["candidate_scoped_documents"] = list(
            dict.fromkeys(research["candidate_scoped_documents"])
        )
        if (
            research["exact_documents"]
            and candidate.official_source_url not in research["exact_documents"]
        ):
            candidate.official_source_url = research["exact_documents"][0]
        elif research["candidate_scoped_documents"]:
            # Explicit row-to-URL research input is a reviewable official reference,
            # not automatic identity approval. The authenticated CMS context review
            # remains mandatory before this evidence can satisfy readiness.
            candidate.official_source_url = research["candidate_scoped_documents"][0]
        elif adapter and not research["exact_documents"]:
            research["failures"].append("Exact official Project document unavailable")
        previous = (candidate.acquisition_summary or {}).get("source_first_research", {})
        if not discover:
            # Bounded retries must not discard already successful private evidence.
            by_url = {item["requested_url"]: item for item in previous.get("documents", [])}
            for document in research["documents"]:
                old = by_url.get(document["requested_url"])
                if old and old.get("status") == 200 and document.get("error"):
                    research["failures"].append(
                        f"Retry failed: {document['requested_url']}:{document['error']}"
                    )
                else:
                    by_url[document["requested_url"]] = document
            research["documents"] = list(by_url.values())
            research["exact_documents"] = list(
                dict.fromkeys([*previous.get("exact_documents", []), *research["exact_documents"]])
            )
            research["candidate_scoped_documents"] = list(
                dict.fromkeys(
                    [
                        *previous.get("candidate_scoped_documents", []),
                        *research["candidate_scoped_documents"],
                    ]
                )
            )
            research["failures"] = list(
                dict.fromkeys([*previous.get("failures", []), *research["failures"]])
            )
        if research_fingerprint(previous) == research_fingerprint(research):
            research = previous
        else:
            candidate.acquisition_summary = {
                **(candidate.acquisition_summary or {}),
                "source_first_research": research,
            }
        await asyncio.to_thread(recalculate_stored_conflicts, candidate, storage)
        report = readiness_report(candidate)
        # Research must never convert a record into editorial approval/publication.
        if not report["ready"]:
            candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
            candidate.review_status = ImportReviewStatus.NEEDS_REVIEW
        after_state = json.dumps(
            {
                "official_source_url": candidate.official_source_url,
                "acquisition_summary": candidate.acquisition_summary,
                "validation_errors": candidate.validation_errors,
                "conflict_reasons": candidate.conflict_reasons,
                "processing_status": candidate.processing_status.value,
                "review_status": candidate.review_status.value,
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        if before_state != after_state:
            mutated += 1
            await write_audit(
                db,
                actor_user_id=None,
                action="project.import.official_research",
                entity_type="project_import_candidate",
                entity_id=candidate.id,
                correlation_id=f"research:{batch_id}",
                metadata={"ready": report["ready"], "version": RESEARCH_VERSION},
            )
            await db.commit()
        reports.append(report)
        print(
            json.dumps(
                {
                    "row": candidate.manifest_row_id,
                    "project": name,
                    "exact_documents": len(research["exact_documents"]),
                    "ready": report["ready"],
                }
            ),
            flush=True,
        )
    payload = {"batch_id": str(batch_id), "version": RESEARCH_VERSION, "projects": reports}
    stored = await storage.save_private_json(
        json.dumps(payload, ensure_ascii=False, indent=2).encode(), prefix="research-report"
    )
    return {
        "count": len(reports),
        "ready": sum(item["ready"] for item in reports),
        "mutated": mutated,
        "private_report_key": stored.storage_key,
    }
