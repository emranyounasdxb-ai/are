from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from typing import Any

from app.acquisition.parser import names_genuinely_disagree
from app.models import MediaRightsStatus, ProjectImportCandidate, ProjectMediaCategory

_NAME_CONFLICT = re.compile(
    r"^Official source name differs: manifest '(.+)' versus source '(.+)'.$"
)
_SOURCE_CONFLICT = re.compile(r"^Source disagreement for ([^:]+): (.+)\.$")
_NON_CONFLICT_MESSAGES = {
    "Canonical Developer requires exact human resolution.",
    "Canonical Area/Community requires exact human resolution.",
    "Media coverage incomplete",
    "High-resolution Cover image required",
    "Insufficient exact-project media was discovered; retain the candidate for review.",
}
_MANAGED_MISSING_CODES = {
    "missing_source_evidence",
    "official_source_not_found",
    "missing_canonical_developer",
    "missing_canonical_area",
    "missing_approved_cover",
    "missing_bilingual_overview",
}


def source_disagreement(field: str, values: Iterable[object]) -> str | None:
    retained: list[object] = []
    seen: set[str] = set()
    for value in values:
        stable = _stable_value(value)
        if not _missing(value) and stable not in seen:
            seen.add(stable)
            retained.append(value)
    if field in {"size_min", "size_max"} and _equivalent_rounded_sizes(retained):
        return None
    rendered = list(dict.fromkeys(_stable_value(value) for value in retained))
    if len(rendered) < 2:
        return None
    return f"Source disagreement for {field}: {' | '.join(rendered)}."


def _equivalent_rounded_sizes(values: list[object]) -> bool:
    if len(values) < 2:
        return True
    try:
        numeric = [Decimal(str(value)) for value in values]
    except (InvalidOperation, ValueError):
        return False
    largest = max(abs(value) for value in numeric)
    tolerance = max(Decimal("1"), largest * Decimal("0.001"))
    return max(numeric) - min(numeric) <= tolerance


def reconcile_candidate_quality(candidate: ProjectImportCandidate) -> None:
    """Independently rebuild genuine conflicts and evidence-missing diagnostics."""
    summary = dict(candidate.acquisition_summary or {})
    mapping_notes = list(summary.get("mapping_notes") or [])
    genuine: list[str] = []
    for reason in candidate.conflict_reasons:
        if reason in _NON_CONFLICT_MESSAGES:
            continue
        if reason.startswith("Exact official Project evidence maps source label "):
            mapping_notes.append(reason)
            continue
        name_match = _NAME_CONFLICT.fullmatch(reason)
        if name_match:
            if names_genuinely_disagree(name_match.group(1), name_match.group(2)):
                genuine.append(reason)
            continue
        source_match = _SOURCE_CONFLICT.fullmatch(reason)
        if source_match:
            recalculated = source_disagreement(
                source_match.group(1), source_match.group(2).split(" | ")
            )
            if recalculated:
                genuine.append(recalculated)
            continue
        genuine.append(reason)
    candidate.conflict_reasons = list(dict.fromkeys(genuine))
    if mapping_notes:
        summary["mapping_notes"] = list(dict.fromkeys(mapping_notes))

    retained_errors = [
        value
        for value in candidate.validation_errors
        if not (isinstance(value, dict) and str(value.get("code", "")) in _MANAGED_MISSING_CODES)
    ]
    proposal = candidate.normalized_payload or {}
    missing: list[dict[str, str]] = []

    def add(field: str, code: str = "missing_source_evidence") -> None:
        missing.append({"field": field, "code": code})

    if not candidate.proposed_developer_id:
        add("developer", "missing_canonical_developer")
    if not candidate.proposed_area_id:
        add("area", "missing_canonical_area")
    if not candidate.official_source_url:
        add("official_project_source", "official_source_not_found")
    if proposal.get("availability_status") in (None, "", "not-confirmed"):
        add("availability_status")
    if proposal.get("construction_status") in (None, "", "not-confirmed"):
        add("construction_status")
    if not proposal.get("handover_quarter") or not proposal.get("handover_year"):
        add("handover")
    if _missing(proposal.get("bedrooms")):
        add("bedrooms")
    if any(proposal.get(key) in (None, "") for key in ("size_min", "size_max", "size_unit")):
        add("size_range")
    if proposal.get("down_payment_percentage") is None:
        add("down_payment")
    payment = proposal.get("payment_plan")
    if not isinstance(payment, dict) or _missing(payment.get("milestones")):
        add("payment_plan")
    if _missing(proposal.get("amenities")):
        add("amenities")
    loaded = vars(candidate)
    draft = loaded.get("editorial_draft")
    if not draft or not draft.overview_en or not draft.overview_ar:
        add("overview", "missing_bilingual_overview")
    has_cover = any(
        item.category == ProjectMediaCategory.COVER
        and item.stage_status == "downloaded"
        and item.rights_status == MediaRightsStatus.APPROVED
        and item.storage_key
        for item in loaded.get("staged_media", [])
    )
    if not has_cover:
        add("cover", "missing_approved_cover")

    candidate.validation_errors = _deduplicate_errors([*retained_errors, *missing])
    summary["missing_field_count"] = len(missing)
    summary["genuine_conflict_count"] = len(candidate.conflict_reasons)
    candidate.acquisition_summary = summary


def _missing(value: object) -> bool:
    return value in (None, "", [], {})


def _stable_value(value: object) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{key}={_stable_value(value[key])}" for key in sorted(value))
    if isinstance(value, (list, tuple)):
        return ", ".join(_stable_value(item) for item in value)
    return str(value)


def _deduplicate_errors(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        key = (str(value.get("field", "")), str(value.get("code", "")))
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
