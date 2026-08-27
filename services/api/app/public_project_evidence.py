"""Public omission of unresolved imported facts; private review data never leaks."""

from __future__ import annotations

import copy
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectImportCandidate
from app.project_approval import content_version, latest_receipt
from app.serializers import project_dict

FIELD_GROUPS = {
    "bedrooms": {"bedroom_options"},
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
    "down_payment": {"down_payment_percentage", "payment_plan"},
    "down_payment_percentage": {"down_payment_percentage", "payment_plan"},
    "payment_plan": {"down_payment_percentage", "payment_plan"},
}


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
    plan = result.get("payment_plan")
    milestones = plan.get("milestones", []) if isinstance(plan, dict) else []
    try:
        percentages = [float(item["percentage"]) for item in milestones]
        complete = (
            bool(percentages)
            and all(0 < value <= 100 for value in percentages)
            and abs(sum(percentages) - 100) < 0.001
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
    if not result.get("availability_status"):
        result["cta"] = "request-current-status"
    return {key: value for key, value in result.items() if value is not None and value != []}


async def public_evidenced_project(
    record: Project, locale: str, db: AsyncSession
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
        summary = candidate.acquisition_summary or {}
        targeted = summary.get("targeted_field_review", {})
        identity_hold |= bool(targeted.get("identity_hold"))
        hidden.update(str(item.get("field")) for item in candidate.validation_errors or [])
        hidden.update(
            field
            for field, state in targeted.get("states", {}).items()
            if state not in {"verified", "supported"}
        )
        for reason in candidate.conflict_reasons or []:
            match = re.search(r"Source disagreement for ([a-z_]+):", reason)
            if match:
                hidden.add(match[1])
            elif "payment" in reason.lower() or "down" in reason.lower():
                hidden.add("payment_plan")
            else:
                # An unclassified conflict cannot safely be assigned to one field.
                identity_hold = True
        if hidden & {"project_identity", "developer", "area"}:
            identity_hold = True
    data = omit_unresolved(
        project_dict(record, locale), hidden_fields=hidden, identity_hold=identity_hold
    )
    if data is None:
        return None
    receipt = await latest_receipt(record, db)
    detail = receipt.metadata_summary if receipt else {}
    permissions = detail.get("media_permissions", {}) if detail else {}
    current = bool(detail and detail.get("content_version") == content_version(record))
    permitted = {str(item.id) for item in record.media if current and item.sha256 in permissions}
    data["media"] = [item for item in data.get("media", []) if str(item["id"]) in permitted]
    return data
