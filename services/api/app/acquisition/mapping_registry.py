"""Versioned, inactive source-to-ARE mapping contracts.

This registry is descriptive only. It performs no network access and is not wired to an
acquisition adapter. Source values remain untrusted until normalized and reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Layer = Literal["identity", "fact", "editorial", "media", "provenance"]


@dataclass(frozen=True)
class FieldMapping:
    source_key: str
    are_key: str
    layer: Layer
    ai_editable: bool = False


@dataclass(frozen=True)
class SourceMappingContract:
    provider_key: str
    version: str
    enabled: bool
    fields: tuple[FieldMapping, ...]


TANAMI_V1 = SourceMappingContract(
    provider_key="tanami",
    version="1.0.0",
    enabled=False,
    fields=(
        FieldMapping("project_name", "project_name", "identity"),
        FieldMapping("developer", "developer", "identity"),
        FieldMapping("emirate", "emirate", "fact"),
        FieldMapping("area", "area", "fact"),
        FieldMapping("property_types", "property_types", "fact"),
        FieldMapping("unit_types", "unit_types", "fact"),
        FieldMapping("bedrooms", "bedroom_options", "fact"),
        FieldMapping("size_min", "size_min", "fact"),
        FieldMapping("size_max", "size_max", "fact"),
        FieldMapping("size_unit", "size_unit", "fact"),
        FieldMapping("down_payment", "down_payment_percentage", "fact"),
        FieldMapping("payment_plan_summary", "payment_plan.raw_source_text", "fact"),
        FieldMapping("payment_milestones", "payment_plan.milestones", "fact"),
        FieldMapping("handover_quarter", "handover_quarter", "fact"),
        FieldMapping("handover_year", "handover_year", "fact"),
        FieldMapping("availability", "availability_status", "fact"),
        FieldMapping("construction_status", "construction_status", "fact"),
        FieldMapping("overview", "editorial.overview", "editorial", ai_editable=True),
        FieldMapping("features", "amenities", "fact"),
        FieldMapping("amenities", "amenities", "fact"),
        FieldMapping("floor_plans", "media.floor_plans", "media"),
        FieldMapping("image_gallery", "media.gallery", "media"),
        FieldMapping("latitude", "latitude", "fact"),
        FieldMapping("longitude", "longitude", "fact"),
        FieldMapping("nearby_places", "nearby_places", "fact"),
        FieldMapping("last_verified", "last_verified_at", "provenance"),
        FieldMapping("source", "sources", "provenance"),
    ),
)

SOURCE_MAPPING_REGISTRY = {(TANAMI_V1.provider_key, TANAMI_V1.version): TANAMI_V1}


def mapping_contract(provider_key: str, version: str) -> SourceMappingContract:
    return SOURCE_MAPPING_REGISTRY[(provider_key, version)]
