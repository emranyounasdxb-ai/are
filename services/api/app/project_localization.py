"""Shared Project-name localization rules for CMS and public presentation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

ARABIC_LETTER = re.compile(r"[\u0621-\u064a]")


def approved_arabic_project_name(
    proposal: Mapping[str, Any], english_name: str | None
) -> str | None:
    """Return an explicit Arabic Project name; never silently reuse English."""
    value = proposal.get("project_name_ar")
    if not isinstance(value, str):
        return None
    name = " ".join(value.split())
    if not name or name == " ".join((english_name or "").split()):
        return None
    if ARABIC_LETTER.search(name):
        return name
    retention_reason = proposal.get("project_name_ar_latin_retention_reason")
    if isinstance(retention_reason, str) and retention_reason.strip():
        return name
    return None
