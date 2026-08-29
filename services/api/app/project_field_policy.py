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


def candidate_media_is_preview_eligible(media: Any) -> bool:
    """Allow only fully prepared media with explicit, non-automatic reuse permission."""
    from app.acquisition.media import classify_media_dimensions

    rights_status = getattr(getattr(media, "rights_status", None), "value", None)
    category = getattr(getattr(media, "category", None), "value", None)
    rights_basis = getattr(media, "rights_basis", None) or ""
    formats = {
        item.get("format")
        for item in (getattr(media, "derivative_manifest", None) or [])
        if isinstance(item, dict)
    }
    width = getattr(media, "width", None) or 0
    height = getattr(media, "height", None) or 0
    return bool(
        getattr(media, "stage_status", None) == "downloaded"
        and rights_status == "approved"
        and rights_basis
        and not rights_basis.startswith("Automatically approved exact-Project")
        and getattr(media, "storage_key", None)
        and getattr(media, "thumbnail_storage_key", None)
        and getattr(media, "mime_type", None)
        in {"image/jpeg", "image/png", "image/webp", "image/avif"}
        and getattr(media, "processed_sha256", None)
        and getattr(media, "normalized_filename", None)
        and getattr(media, "alt_en_draft", None)
        and getattr(media, "alt_ar_draft", None)
        and getattr(media, "title_en", None)
        and getattr(media, "title_ar", None)
        and getattr(media, "description_en", None)
        and getattr(media, "description_ar", None)
        and getattr(media, "tags", None)
        and {"webp", "avif"} <= formats
        and classify_media_dimensions(width, height, category or "gallery").public_eligible
    )
