"""Fill existing private Draft gaps from retained, exact-project rendered evidence.

This boundary has no create, approve or publish operation. Browser capture is
kept outside the web applications, and the existing private source/audit stores
remain authoritative.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlsplit
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.contracts import FetchResult
from app.acquisition.parser import AMENITIES
from app.acquisition.reconciliation import reconcile_candidate_quality
from app.acquisition.tanami import AMENITY_AR, _store_snapshot
from app.acquisition.tanami_context import (
    ContextTable,
    floor_unit_facts,
    payment_variants,
    select_unambiguous_plan,
    summary_facts,
)
from app.audit import write_audit
from app.config import Settings
from app.import_review import sync_linked_draft_from_candidate
from app.models import (
    Project,
    ProjectImportCandidate,
    ProjectMediaCategory,
    ProjectPaymentPlan,
    ProjectSourceType,
    PublicationStatus,
)
from app.storage import PrivateStorage

VERSION = "tanami-rendered-context-v1"
SUFFIXES = {"", "-Amenities", "-PaymentPlan", "-FloorPlans", "-MasterPlan", "-Location"}
FACT_KEYS = {
    "property_types",
    "unit_types",
    "bedrooms",
    "size_min",
    "size_max",
    "size_unit",
    "handover_quarter",
    "handover_year",
    "original_handover_value",
    "down_payment_percentage",
    "amenities",
    "localized_amenities",
}
PLACEHOLDERS = {"will be updated soon", "announcing soon", "various sizes available", "-"}


def rendered_media(
    documents: list[dict[str, Any]], primary: str
) -> list[tuple[str, ProjectMediaCategory]]:
    """Observed raster URLs only, scoped the same way as the Project's own banner ID."""
    base = next((d for d in documents if d.get("url") == primary), {})
    ids = {
        match.group(1)
        for image in base.get("images", [])
        if image.get("context") == "Summary"
        for match in [re.search(r"/Banner/(\d+)/", image.get("src", ""))]
        if match
    }
    if len(ids) != 1:
        return []
    project_id = next(iter(ids))
    found: dict[str, ProjectMediaCategory] = {}
    paths = {
        f"/Banner/{project_id}/": ProjectMediaCategory.EXTERIOR,
        f"/Gallery/{project_id}/": ProjectMediaCategory.GALLERY,
        f"/Project/Floor_Image/{project_id}/": ProjectMediaCategory.FLOOR_PLAN,
        f"/Project/LayoutPlan/{project_id}/": ProjectMediaCategory.MASTER_PLAN,
        f"/Project/Location_Map/{project_id}/": ProjectMediaCategory.LOCATION_MAP,
    }
    for document in documents:
        if document.get("url") not in {primary + s for s in SUFFIXES}:
            continue
        for image in document.get("images", []):
            if re.search(
                r"other projects|related projects|more projects", image.get("context", ""), re.I
            ):
                continue
            for key in ("href", "lazy", "src"):
                url = urljoin(primary, image.get(key) or "")
                parts = urlsplit(url)
                if parts.scheme != "https" or parts.netloc != "manage.tanamiproperties.com":
                    continue
                if not re.search(r"\.(?:jpg|jpeg|png|webp|avif)$", parts.path, re.I):
                    continue
                for prefix, category in paths.items():
                    if parts.path.startswith(prefix):
                        found[url] = category
    return list(found.items())


def reconcile_payment_context(
    candidate: ProjectImportCandidate, primary: str, variants: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Reclassify proven alternative offers, not genuine cross-source disagreements."""
    if len(variants) < 2 or not all(plan["is_complete"] for plan in variants):
        return []
    bookings = {
        float(m["percentage"])
        for plan in variants
        for m in plan["milestones"]
        if m["stage"] == "booking"
    }
    entries = (candidate.acquisition_summary or {}).get("official_fact_evidence", [])
    comparisons = [entry for entry in entries if entry.get("field") == "down_payment_percentage"]
    if len(comparisons) != 1:
        return []
    observations = comparisons[0].get("sources", [])
    if not observations or {s.get("source_url") for s in observations} != {
        primary,
        primary + "-PaymentPlan",
    }:
        return []
    if not all(s.get("value") in bookings for s in observations):
        return []
    removed = [
        r
        for r in candidate.conflict_reasons
        if r.startswith("Source disagreement for down_payment_percentage:")
    ]
    candidate.conflict_reasons = [r for r in candidate.conflict_reasons if r not in removed]
    return [
        {
            "previous_reason": reason,
            "observations": observations,
            "reason": "Separate complete payment offers; applicability still requires review",
            "requires_human_review": True,
        }
        for reason in removed
    ]


def fill_gaps(
    existing: dict[str, Any], facts: dict[str, Any], protected: set[str]
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    updated = dict(existing)
    changed: list[str] = []
    retained: dict[str, Any] = {}
    for key in sorted(FACT_KEYS | {"payment_plan"}):
        incoming = facts.get(key)
        if incoming in (None, "", [], {}) or key in protected:
            continue
        old = existing.get(key)
        missing = old in (None, "", [], {}, "not-confirmed")
        if isinstance(old, list) and old:
            missing = all(isinstance(x, str) and x.casefold() in PLACEHOLDERS for x in old)
        if key == "payment_plan" and isinstance(old, dict):
            missing = not old.get("milestones")
        if missing:
            updated[key] = incoming
            changed.append(key)
        elif old != incoming:
            retained[key] = {"retained_value": old, "rendered_value": incoming}
    return updated, changed, retained


async def apply_rendered_review(
    db: AsyncSession,
    settings: Settings,
    candidate_id: UUID,
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == candidate_id)
        .with_for_update()
    )
    if not candidate or not candidate.linked_project_id:
        raise ValueError("An existing linked candidate is required; no records will be created.")
    record = await db.get(
        Project,
        candidate.linked_project_id,
        populate_existing=True,
        options=[
            selectinload(Project.property_types),
            selectinload(Project.bedroom_options),
            selectinload(Project.unit_types),
            selectinload(Project.amenities),
            selectinload(Project.payment_plan).selectinload(ProjectPaymentPlan.milestones),
        ],
    )
    if not record or record.status != PublicationStatus.DRAFT:
        raise ValueError("Only an existing private Draft can receive rendered evidence.")
    primary = next(
        (
            url
            for url in candidate.source_urls
            if url.startswith("https://www.tanamiproperties.com/Projects/")
        ),
        None,
    )
    if not primary:
        raise ValueError("An existing exact Tanami Project source is required.")
    allowed = {primary + suffix for suffix in SUFFIXES}
    valid = []
    for document in documents:
        if document.get("candidate_id") != str(candidate_id):
            raise ValueError("Rendered evidence belongs to another candidate.")
        if document.get("requested_url") not in allowed:
            raise ValueError("Rendered evidence is outside the exact Project sections.")
        if document.get("error"):
            continue
        if document.get("url") != document["requested_url"] or not document.get("h1"):
            raise ValueError("Redirected or unidentified rendered evidence cannot update a Draft.")
        valid.append(document)
    base = next((d for d in valid if d["url"] == primary), None)
    if not base:
        raise ValueError("The exact rendered Project overview is required.")
    documents = sorted(documents, key=lambda value: str(value.get("requested_url")))
    digest = hashlib.sha256(json.dumps(documents, sort_keys=True).encode()).hexdigest()
    summary = dict(candidate.acquisition_summary or {})
    previous = summary.get("rendered_tanami_review", {})
    if previous.get("capture_hash") == digest:
        return {"candidate_id": str(candidate_id), "changed": [], "idempotent": True}
    facts = summary_facts([ContextTable(**table) for table in base.get("tables", [])])
    unit_facts = floor_unit_facts(
        [
            ContextTable(**table)
            for document in valid
            if document["url"] == primary + "-FloorPlans"
            for table in document.get("tables", [])
        ]
    )
    for key, value in unit_facts.items():
        if facts.get(key) in (None, "", [], {}):
            facts[key] = value
    facilities = [
        item["text"]
        for document in valid
        if document["url"] == primary + "-Amenities"
        for item in document.get("prose", [])
        if item.get("tag") == "li"
        and re.search(r"facilit|amenit", item.get("heading", ""), re.I)
        and not re.search(
            r"other projects|related projects|more projects", item.get("heading", ""), re.I
        )
    ]
    amenities = [
        label
        for label, aliases in AMENITIES.items()
        if any(value.casefold() in aliases for value in facilities)
    ]
    if amenities:
        facts["amenities"] = amenities
        facts["localized_amenities"] = [
            {"label_en": label, "label_ar": AMENITY_AR[label]} for label in amenities
        ]
    variants = []
    for document in valid:
        if document["url"] == primary + "-PaymentPlan":
            variants = payment_variants([ContextTable(**t) for t in document.get("tables", [])])
    selected = select_unambiguous_plan(variants)
    if selected:
        selected["source_url"] = primary + "-PaymentPlan"
        selected["requires_review"] = True
        facts["payment_plan"] = selected
    protected = set(candidate.human_edited_fields or [])
    protected.update((summary.get("contextual_fact_review") or {}).get("verified_fields", []))
    # Canonical owner edits may be newer than the retained candidate payload.
    for field in FACT_KEYS - {
        "amenities",
        "localized_amenities",
        "property_types",
        "bedrooms",
        "unit_types",
    }:
        if getattr(record, field, None) not in (None, "", [], {}):
            protected.add(field)
    for field, relationship in {
        "property_types": "property_types",
        "bedrooms": "bedroom_options",
        "localized_amenities": "amenities",
        "unit_types": "unit_types",
    }.items():
        if getattr(record, relationship, []):
            protected.add(field)
    if record.payment_plan and record.payment_plan.milestones:
        protected.add("payment_plan")
    before = dict(candidate.normalized_payload or {})
    updated, changed, retained = fill_gaps(before, facts, protected)
    resolutions = reconcile_payment_context(candidate, primary, variants)
    # Different populated values remain unchanged, with both observations private.
    # Alternative plan applicability is a review requirement, not a flattened conflict.
    # A scalar retained without its original unit/phase context is not proof of
    # disagreement. Preserve it for review; existing sourced conflicts stay intact.
    storage = PrivateStorage(settings)
    for document in valid:
        await _store_snapshot(
            db,
            storage,
            candidate,
            FetchResult(
                url=document["url"],
                status=None,
                retrieved_at=datetime.fromisoformat(document["captured_at"]),
                content_type="application/json",
                body=json.dumps(document, sort_keys=True).encode(),
            ),
            ProjectSourceType.APPROVED_SECONDARY_SOURCE,
            rendered=True,
        )
    review = {
        "version": VERSION,
        "capture_hash": digest,
        "checked_at": datetime.now(UTC).isoformat(),
        "sources": [d["url"] for d in valid],
        "facts": facts,
        "payment_variants": variants,
        "changed_fields": changed,
        "retained_observations": retained,
        "payment_context_resolutions": resolutions,
        "amenity_list_evidence": facilities,
        "unit_tables": [
            {
                "source_url": d["url"],
                "tables": [
                    t
                    for t in d.get("tables", [])
                    if any("Unit Type" in row for row in t.get("rows", []))
                ],
            }
            for d in valid
        ],
        "overview_evidence": [p for p in base.get("prose", []) if p.get("heading") == "Overview"],
        "payment_reason": "Complete table captured; current terms require human verification"
        if selected
        else "Alternative/unit-specific or incomplete payment terms; no universal plan assumed",
        "automatic_approval": False,
    }
    summary["rendered_tanami_review"] = review
    candidate.normalized_payload = updated
    candidate.acquisition_summary = summary
    reconcile_candidate_quality(candidate)
    if changed:
        await db.flush()
        await db.refresh(candidate, ["evidence"])
        await sync_linked_draft_from_candidate(db, candidate, fields=set(changed))
    await write_audit(
        db,
        action="project_import.rendered_evidence_reviewed",
        entity_type="project_import_candidate",
        entity_id=candidate.id,
        correlation_id="rendered-" + digest[:24],
        before={"changed_fields": {key: before.get(key) for key in changed}},
        after={"changed_fields": {key: updated[key] for key in changed}},
        metadata={"version": VERSION, "source_urls": review["sources"]},
    )
    await db.flush()
    return {"candidate_id": str(candidate_id), "changed": changed, "idempotent": False}
