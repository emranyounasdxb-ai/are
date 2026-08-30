"""Public omission of unresolved imported facts; private review data never leaks."""

from __future__ import annotations

import copy
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectImportCandidate
from app.project_approval import content_version, latest_receipt
from app.project_field_policy import candidate_evidence_state
from app.project_media_preview import permitted_preview_assets
from app.serializers import project_dict, project_preview_dict

FIELD_GROUPS = {
    "availability": {"availability_status"},
    "bedrooms": {"bedroom_options", "bedrooms"},
    "unit_types": {"unit_types"},
    "size_range": {"size_min", "size_max", "size_unit", "size_ranges"},
    "size_min": {"size_min", "size_max", "size_unit", "size_ranges"},
    "size_max": {"size_min", "size_max", "size_unit", "size_ranges"},
    "handover": {
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "handover_verification",
    },
    "handover_quarter": {
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "handover_verification",
    },
    "handover_year": {
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "handover_verification",
    },
    "down_payment": {"down_payment_percentage", "payment_plan", "payment_milestones"},
    "down_payment_percentage": {"down_payment_percentage", "payment_plan", "payment_milestones"},
    "payment_plan": {"down_payment_percentage", "payment_plan", "payment_milestones"},
    "payment_milestones": {"down_payment_percentage", "payment_plan", "payment_milestones"},
}

UNKNOWN = {"", "-", "—", "0", "n/a", "not confirmed", "not-confirmed", "غير مؤكد"}
UNCONFIRMED_TEXT = re.compile(r"\bnot[ -]confirmed\b|غير مؤكد", re.IGNORECASE)


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in UNKNOWN
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def _positive(value: Any) -> bool:
    try:
        number = Decimal(str(value))
        return number.is_finite() and number > 0
    except InvalidOperation:
        return False


def _omit_unconfirmed_sentences(value: Any) -> Any:
    if not isinstance(value, str) or not UNCONFIRMED_TEXT.search(value):
        return value
    sentences = re.findall(r"[^.!؟]+[.!؟]?", value)
    return " ".join(
        sentence.strip() for sentence in sentences if not UNCONFIRMED_TEXT.search(sentence)
    ).strip()


def omit_unresolved(
    data: dict[str, Any],
    *,
    hidden_fields: set[str],
    identity_hold: bool = False,
) -> dict[str, Any] | None:
    if identity_hold:
        return None
    result = copy.deepcopy(data)
    for field in hidden_fields:
        for key in FIELD_GROUPS.get(field, {field}):
            result.pop(key, None)
    for key in ("availability_status", "construction_status"):
        if not _known(result.get(key)):
            result.pop(key, None)
    for key in ("short_summary", "full_description", "seo_description"):
        if key in result:
            result[key] = _omit_unconfirmed_sentences(result[key])
            if not result[key]:
                result.pop(key)
    for key in ("bedroom_options", "bedrooms", "unit_types", "amenities", "property_types"):
        if isinstance(result.get(key), list):
            result[key] = [
                item
                for item in result[key]
                if _known(item.get("label") if isinstance(item, dict) else item)
            ]
    if result.get("handover_quarter") not in {"Q1", "Q2", "Q3", "Q4"} or not _positive(
        result.get("handover_year")
    ):
        for key in FIELD_GROUPS["handover"]:
            result.pop(key, None)
    if not all(_positive(result.get(key)) for key in ("size_min", "size_max")) or not _known(
        result.get("size_unit")
    ):
        for key in FIELD_GROUPS["size_range"]:
            result.pop(key, None)
    plan = result.get("payment_plan")
    milestones = plan.get("milestones", []) if isinstance(plan, dict) else []
    try:
        percentages = [float(item["percentage"]) for item in milestones]
        complete = (
            bool(percentages)
            and all(0 < value <= 100 for value in percentages)
            and abs(sum(percentages) - 100) < 0.001
            and all(
                _known(item.get("label")) and _known(item.get("due_trigger")) for item in milestones
            )
        )
    except (KeyError, TypeError, ValueError):
        complete = False
    if (
        not isinstance(plan, dict)
        or not plan.get("is_complete")
        or not plan.get("verified_at")
        or not complete
    ):
        result.pop("payment_plan", None)
        result.pop("down_payment_percentage", None)
        result.pop("payment_milestones", None)
    if not result.get("availability_status"):
        result["cta"] = "request-current-status"
    return {key: value for key, value in result.items() if value is not None and value != []}


async def public_evidenced_project(
    record: Project, locale: str, db: AsyncSession, *, preview: bool = False
) -> dict[str, Any] | None:
    candidates = (
        await db.execute(
            select(
                ProjectImportCandidate.acquisition_summary,
                ProjectImportCandidate.validation_errors,
                ProjectImportCandidate.conflict_reasons,
            ).where(
                ProjectImportCandidate.linked_project_id == record.id,
            )
        )
    ).all()
    hidden: set[str] = set()
    identity_hold = False
    for candidate in candidates:
        candidate_hidden, candidate_hold = candidate_evidence_state(
            candidate.acquisition_summary,
            candidate.validation_errors or [],
            candidate.conflict_reasons or [],
        )
        hidden.update(candidate_hidden)
        identity_hold |= candidate_hold
    data = omit_unresolved(
        project_preview_dict(record, locale) if preview else project_dict(record, locale),
        hidden_fields=hidden,
        identity_hold=identity_hold,
    )
    if data is None:
        return None
    receipt = await latest_receipt(record, db)
    detail = receipt.metadata_summary if receipt else {}
    permissions = detail.get("media_permissions", {}) if detail else {}
    current = bool(detail and detail.get("content_version") == content_version(record))
    permitted = {str(item.id) for item in record.media if current and item.sha256 in permissions}
    if preview:
        permitted.update(await permitted_preview_assets(record, db))
    data["media"] = [item for item in data.get("media", []) if str(item["id"]) in permitted]
    return data
