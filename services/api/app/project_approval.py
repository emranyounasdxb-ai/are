"""Private, content-bound approval receipts in the existing append-only audit log.

No approval is inferred from a download, a populated field or an AI draft. The
authenticated reviewer supplies explicit attestations and private evidence refs.
Receipts are invalidated by any material change; publication remains separate.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, EditorialApprovalStatus, Project, ProjectImportCandidate
from app.project_field_policy import critical_candidate_errors
from app.serializers import project_dict

CHECKS = ("facts", "english", "arabic", "media_rights", "seo", "disclaimer", "preview")
RECEIPT_VERSION = "project-approval-v1"


class ReviewAttestation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    confirmed: Literal[True]
    evidence_reference: str = Field(min_length=12, max_length=2000)


class ProjectApprovalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_version: str = Field(pattern=r"^[a-f0-9]{64}$")
    checks: dict[str, ReviewAttestation]
    media_permissions: dict[str, str] = Field(default_factory=dict)


def canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return sorted((canonical(item) for item in value), key=lambda item: json.dumps(item))
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def content_version(record: Project) -> str:
    data = project_dict(record)
    for field in (
        "status",
        "workflow_status",
        "created_at",
        "updated_at",
        "published_at",
        "archived_at",
    ):
        data.pop(field, None)
    # Child rows may be replaced on save without changing their material content.
    for item in data["sources"]:
        item.pop("id", None)
    if data["payment_plan"]:
        plan = data["payment_plan"]
        plan.pop("id", None)
        source_id = plan.pop("source_id", None)
        plan["source_url"] = next((s.source_url for s in record.sources if s.id == source_id), None)
    for item, media in zip(data["media"], record.media, strict=True):
        item.pop("id", None)
        item["sha256"] = media.sha256
        item["storage_key"] = media.storage_key
    return hashlib.sha256(json.dumps(canonical(data), ensure_ascii=False).encode()).hexdigest()


async def technical_blockers(record: Project, db: AsyncSession) -> list[str]:
    blockers = []
    translations = {t.locale: t for t in record.translations}
    for locale in ("en", "ar"):
        t = translations.get(locale)
        if not t or not all(
            (t.official_name, t.short_summary, t.full_description, t.seo_title, t.seo_description)
        ):
            blockers.append(f"Complete {locale.upper()} content and SEO required")
    if not record.priority:
        blockers.append("Manual ARE Priority required")
    if not record.last_verified_at:
        blockers.append("Last Verified required")
    if not any(
        s.is_active and s.is_official and s.content_hash and s.last_checked_at
        for s in record.sources
    ):
        blockers.append("Verified official source evidence required")
    eligible = [
        m
        for m in record.media
        if m.storage_key
        and m.sha256
        and m.rights_status.value == "approved"
        and m.alt_en
        and m.alt_ar
    ]
    if not any(
        m.category.value == "cover"
        and (m.width or 0) >= 1600
        and (m.height or 0) >= 900
        and (m.width or 0) > (m.height or 0)
        for m in eligible
    ):
        blockers.append("Prepared landscape Cover with bilingual metadata required")
    if any(m not in eligible for m in record.media):
        blockers.append(
            "Every attached media asset requires preparation, metadata and rights review"
        )
    candidates = (
        await db.scalars(
            select(ProjectImportCandidate).where(
                ProjectImportCandidate.linked_project_id == record.id
            )
        )
    ).all()
    for candidate in candidates:
        blockers.extend(
            critical_candidate_errors(
                candidate.acquisition_summary,
                candidate.validation_errors,
                candidate.conflict_reasons,
                canonical_cover_checked=True,
            )
        )
        if not candidate.human_review_completed or candidate.arabic_review_required:
            blockers.append("Imported facts and Arabic require human review")
        if (
            not candidate.editorial_draft
            or candidate.editorial_draft.approval_status != EditorialApprovalStatus.APPROVED
        ):
            blockers.append("Imported bilingual Overview requires editorial approval")
    return sorted(set(blockers))


async def latest_receipt(record: Project, db: AsyncSession) -> AuditLog | None:
    result = await db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_id == record.id,
            AuditLog.action == "project.approve",
            AuditLog.outcome == "success",
        )
        .order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    return result if isinstance(result, AuditLog) else None


async def approval_state(record: Project, db: AsyncSession) -> dict[str, Any]:
    version = content_version(record)
    receipt = await latest_receipt(record, db)
    detail = receipt.metadata_summary if receipt else None
    return {
        "content_version": version,
        "required_checks": CHECKS,
        "blockers": await technical_blockers(record, db),
        "media": [
            {"sha256": m.sha256, "category": m.category.value, "source_url": m.source_url}
            for m in record.media
        ],
        "receipt": {
            "id": str(receipt.id),
            "reviewer": detail.get("reviewer"),
            "reviewed_at": receipt.occurred_at,
            "content_version": detail.get("content_version"),
            "checks": detail.get("checks"),
            "current": detail.get("content_version") == version,
        }
        if receipt and detail and detail.get("version") == RECEIPT_VERSION
        else None,
    }


async def validate_review(record: Project, payload: ProjectApprovalInput, db: AsyncSession) -> None:
    if payload.content_version != content_version(record):
        raise HTTPException(
            409,
            detail={
                "code": "stale_project_review",
                "message": "Project changed. Reload and review this version again.",
            },
        )
    blockers = await technical_blockers(record, db)
    if set(payload.checks) != set(CHECKS):
        blockers.append("All seven explicit review attestations are required")
    hashes = {m.sha256 for m in record.media if m.sha256}
    if set(payload.media_permissions) != hashes or any(
        not 12 <= len(ref.strip()) <= 2000
        or ref.strip().casefold().startswith(("automatically approved", "http://", "https://"))
        for ref in payload.media_permissions.values()
    ):
        blockers.append(
            "Documented permission reference for every exact media checksum required; "
            "scraping is not permission"
        )
    if blockers:
        raise HTTPException(
            422, detail={"code": "project_review_incomplete", "message": "; ".join(blockers)}
        )


async def require_current_receipt(record: Project, db: AsyncSession) -> None:
    receipt = await latest_receipt(record, db)
    detail = receipt.metadata_summary if receipt else None
    if (
        not detail
        or detail.get("version") != RECEIPT_VERSION
        or detail.get("content_version") != content_version(record)
    ):
        raise HTTPException(
            422,
            detail={
                "code": "project_review_receipt_required",
                "message": "Publication requires a complete review of this exact Project version.",
            },
        )
    blockers = await technical_blockers(record, db)
    if blockers:
        raise HTTPException(
            422, detail={"code": "project_review_incomplete", "message": "; ".join(blockers)}
        )
