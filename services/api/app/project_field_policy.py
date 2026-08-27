"""Shared approval/preview treatment of optional facts; never erase private evidence."""

from __future__ import annotations

import re
from typing import Any

OPTIONAL_FIELDS = frozenset(
    {
        "availability",
        "availability_status",
        "construction_status",
        "handover",
        "handover_quarter",
        "handover_year",
        "bedrooms",
        "bedroom_options",
        "size_range",
        "size_ranges",
        "size_min",
        "size_max",
        "size_unit",
        "amenities",
        "down_payment",
        "down_payment_percentage",
        "payment_plan",
        "payment_milestones",
        "property_types",
        "unit_types",
    }
)
IDENTITY_FIELDS = frozenset({"project_identity", "project_name", "developer", "area", "emirate"})


def candidate_evidence_state(
    summary: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    conflicts: list[str],
) -> tuple[set[str], bool]:
    """Optional disagreements hide the affected group; unknown conflicts fail closed."""
    targeted = (summary or {}).get("targeted_field_review", {})
    hidden = {str(item.get("field", "")) for item in errors}
    hidden.update(
        field
        for field, state in targeted.get("states", {}).items()
        if state not in {"verified", "supported"}
    )
    identity_hold = bool(targeted.get("identity_hold"))
    for reason in conflicts:
        match = re.search(r"Source disagreement for ([a-z_]+):", reason)
        if match:
            field = match[1]
            hidden.add(field)
            identity_hold |= field not in OPTIONAL_FIELDS
        else:
            # Do not classify an arbitrary identity warning as an optional payment gap.
            identity_hold = True
    return hidden, identity_hold or bool(hidden & IDENTITY_FIELDS)


def critical_candidate_errors(
    summary: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    conflicts: list[str],
    *,
    canonical_cover_checked: bool = False,
) -> list[str]:
    hidden, identity_hold = candidate_evidence_state(summary, errors, conflicts)
    ignored = OPTIONAL_FIELDS | ({"cover"} if canonical_cover_checked else set())
    result = [f"Critical evidence requires review: {field}" for field in sorted(hidden - ignored)]
    if identity_hold:
        result.append("Unresolved Project identity or unclassified source conflict")
    return result
