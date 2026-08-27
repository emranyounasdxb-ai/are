"""Price-free, field-scoped evidence review; fetching is never factual approval.

The caller supplies an exact, reviewed Project/developer/area/phase context.
Only dated current observations can fill gaps. Historical observations remain
private, and competing values never overwrite the existing proposal.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.acquisition.parser import parse_html
from app.acquisition.reconciliation import _missing
from app.acquisition.research import exact_document_identity
from app.acquisition.tanami_context import (
    ContextTable,
    contextual_tables,
    payment_variants,
    summary_facts,
)
from app.audit import write_audit
from app.models import Project, ProjectImportCandidate, PublicationStatus

FIELDS = frozenset(
    {
        "project_identity",
        "developer",
        "area",
        "property_types",
        "unit_types",
        "bedrooms",
        "size_min",
        "size_max",
        "size_unit",
        "amenities",
        "construction_status",
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "availability_status",
        "down_payment_percentage",
        "payment_plan",
    }
)
FORBIDDEN = re.compile(
    r"\b(?:AED|USD|GBP|EUR|dirhams?|price|prices|pricing|whatsapp|telephone|email)\b"
    r"|[€£$]|درهم|[\w.+-]+@[\w.-]+\.[a-z]{2,}|\+971[\s\d-]{7,}",
    re.I,
)
PLACEHOLDER = re.compile(
    r"not confirmed|to be announced|coming soon details|will be updated|"
    r"available shortly|#\w+#|^q\s*$|^q1 2000$",
    re.I,
)


def safe_fact(value: Any) -> bool:
    """Reject whole unsafe values, rather than salvaging amounts without context."""
    return not FORBIDDEN.search(json.dumps(value, ensure_ascii=False))


def project_fact_projection(
    body: bytes, source_url: str, exact_names: tuple[str, ...]
) -> dict[str, Any]:
    """Discard page bodies, prices, leads and non-factual rows before persistence.

    Table extraction is provisional: exact heading matching alone never verifies
    developer/area/phase, freshness, source independence or commercial applicability.
    """
    parsed = parse_html(body, source_url)
    heading = parsed.headings[0] if parsed.headings else parsed.title or ""
    matches = any(exact_document_identity(name, heading) for name in exact_names)
    allowed_labels = {"property type", "unit type", "size", "handover", "down payment"}
    tables = contextual_tables(body) if matches else []
    safe_tables = [
        ContextTable(
            table.heading if safe_fact(table.heading) else "",
            [
                row
                for row in table.rows
                if safe_fact(row) and len(row) == 2 and row[0].lower().rstrip(":") in allowed_labels
            ],
        )
        for table in tables
    ]
    facts = {
        key: value
        for key, value in summary_facts(safe_tables).items()
        if key in FIELDS and safe_fact(value)
    }
    plans = payment_variants(
        [
            ContextTable(table.heading, [row for row in table.rows if safe_fact(row)])
            for table in tables
            if safe_fact(table.heading)
        ]
    )
    return {
        "source_url": source_url,
        "content_hash": hashlib.sha256(body).hexdigest(),
        "heading": heading if safe_fact(heading) else None,
        "heading_match_only": matches,
        "provisional_fields": facts,
        "provisional_payment_variants": [plan for plan in plans if safe_fact(plan)],
        "verification": "unconfirmed: exact context, source date and applicability require review",
    }


class FactObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    value: Any
    source_url: str
    publisher: str = Field(min_length=2, max_length=150)
    # Identical syndicated feeds must share a group, even on different domains.
    independence_group: str = Field(min_length=2, max_length=150)
    source_kind: Literal["official", "supporting"]
    source_date: date | None
    temporal_status: Literal["current", "last-known", "undated"]
    exact_context: str = Field(min_length=8, max_length=500)
    excerpt: str = Field(min_length=4, max_length=1500)
    evidence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_evidence(self) -> FactObservation:
        if self.field not in FIELDS or not safe_fact(self.model_dump(mode="json")):
            raise ValueError("Only permitted price-free Project facts may be retained")
        url = urlsplit(self.source_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.port not in (None, 443)
        ):
            raise ValueError("Evidence requires a credential-free HTTPS source URL")
        if _missing(self.value) or PLACEHOLDER.search(str(self.value)):
            raise ValueError("Placeholder values are not factual observations")
        if self.temporal_status != "undated" and self.source_date is None:
            raise ValueError("Current and last-known facts require an explicit source date")
        if self.source_date and self.source_date > date.today():
            raise ValueError("A future source date is not verification")
        return self


def review_observations(
    observations: list[FactObservation],
    existing: dict[str, Any],
    *,
    exact_context: str,
    requested_fields: set[str],
    protected_fields: set[str] | None = None,
) -> dict[str, Any]:
    """Pure deterministic preview, suitable for comparing again under a DB lock."""
    if not requested_fields <= FIELDS:
        raise ValueError("Unexpected requested field")
    protected = protected_fields or set()
    unique = {
        json.dumps(item.model_dump(mode="json"), sort_keys=True): item
        for item in observations
        if item.field in requested_fields
    }
    retained = [unique[key] for key in sorted(unique)]
    if any(item.exact_context != exact_context for item in retained):
        raise ValueError("Evidence belongs to a different Project/developer/area/phase")
    updates: dict[str, Any] = {}
    states: dict[str, str] = {}
    conflicts: dict[str, list[dict[str, Any]]] = {}
    for field in sorted(requested_fields):
        current = [
            item for item in retained if item.field == field and item.temporal_status == "current"
        ]
        values = {json.dumps(item.value, sort_keys=True) for item in current}
        prior = existing.get(field)
        # Keep the baseline as well as both source observations. No silent overwrite.
        disagrees = not _missing(prior) and any(item.value != prior for item in current)
        if len(values) > 1 or disagrees:
            states[field] = "conflict"
            conflicts[field] = [item.model_dump(mode="json") for item in current]
            continue
        confirmed = (
            any(item.source_kind == "official" for item in current)
            or len(
                {item.independence_group for item in current if item.source_kind == "supporting"}
            )
            >= 2
        )
        if not confirmed:
            states[field] = "unconfirmed"
            continue
        states[field] = (
            "verified" if any(item.source_kind == "official" for item in current) else "supported"
        )
        if (
            _missing(prior)
            and field not in protected
            and field not in {"project_identity", "developer", "area"}
        ):
            updates[field] = current[0].value
    result = {
        "version": "targeted-field-evidence-v1",
        "context": exact_context,
        "states": states,
        "updates": updates,
        "conflicts": conflicts,
        "observations": [item.model_dump(mode="json") for item in retained],
        "baseline": {
            field: existing.get(field)
            if safe_fact(existing.get(field))
            else {
                "retained_value_hash": hashlib.sha256(
                    json.dumps(existing.get(field), sort_keys=True).encode()
                ).hexdigest(),
                "not_copied": True,
            }
            for field in sorted(requested_fields)
        },
    }
    result["review_hash"] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


async def persist_targeted_review(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    review: dict[str, Any],
    *,
    expected_version: int,
) -> bool:
    """Apply an inspected private review to this exact existing Draft only.

    The caller locks the candidate row. This function never creates identities,
    Projects, media, approvals or publications, and does not commit the transaction.
    """
    if candidate.review_version != expected_version or not candidate.linked_project_id:
        raise ValueError("Candidate changed or has no existing Draft")
    publication_status = await db.scalar(
        select(Project.status).where(Project.id == candidate.linked_project_id).with_for_update()
    )
    if publication_status != PublicationStatus.DRAFT:
        raise ValueError("Targeted research can update an existing Draft only")
    if not safe_fact(review):
        raise ValueError("Private review contains prohibited data")
    summary = dict(candidate.acquisition_summary or {})
    if summary.get("targeted_field_review") == review:
        return False
    # Observations must still reproduce the exact preview against locked state.
    expected = review_observations(
        [FactObservation.model_validate(item) for item in review.get("observations", [])],
        candidate.normalized_payload or {},
        exact_context=review["context"],
        requested_fields=set(review["states"]),
        protected_fields=set(candidate.human_edited_fields or []),
    )
    if any(review.get(key) != value for key, value in expected.items()):
        raise ValueError("Evidence preview is stale or has been altered")
    if expected["updates"]:
        # Identity/translation edits still belong to the existing bilingual editor.
        from app.import_review import sync_linked_draft_from_candidate

        candidate.normalized_payload = {
            **(candidate.normalized_payload or {}),
            **expected["updates"],
        }
        await sync_linked_draft_from_candidate(db, candidate, fields=set(expected["updates"]))
    summary["targeted_field_review"] = review
    candidate.acquisition_summary = summary
    candidate.review_version += 1
    await write_audit(
        db,
        action="project_import.targeted_evidence_review",
        entity_type="project_import_candidate",
        entity_id=candidate.id,
        correlation_id=f"targeted-{review['review_hash'][:24]}",
        metadata={
            "review_hash": review["review_hash"],
            "fields": sorted(review["states"]),
            "automatic_approval": False,
        },
    )
    await db.flush()
    return True
