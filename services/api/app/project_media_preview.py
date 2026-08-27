"""Version-bound asset permission for authenticated previews, never publication."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, MediaRightsStatus, Project, ProjectMedia, ProjectMediaCategory

APPROVE = "project.media.preview.approve"
REVOKE = "project.media.preview.revoke"
VERSION = "private-cover-preview-v1"


def asset_version(media: ProjectMedia) -> str:
    # Include ownership, bytes, private location and both localized descriptions.
    fields = (
        "id",
        "project_id",
        "category",
        "source_url",
        "rights_status",
        "alt_en",
        "alt_ar",
        "display_order",
        "storage_key",
        "original_filename",
        "mime_type",
        "size_bytes",
        "sha256",
        "width",
        "height",
        "verified_at",
        "uploaded_by",
        "updated_at",
    )
    encoded = json.dumps(
        {key: getattr(media, key) for key in fields}, sort_keys=True, default=str
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def current_asset_permission(media: ProjectMedia, receipt: AuditLog) -> bool:
    detail = receipt.metadata_summary or {}
    return bool(
        receipt.action == APPROVE
        and receipt.outcome == "success"
        and receipt.entity_type == "project_media"
        and receipt.entity_id == media.id
        and detail.get("version") == VERSION
        and detail.get("scope") == "authenticated-preview-only"
        and detail.get("project_id") == str(media.project_id)
        and detail.get("asset_version") == asset_version(media)
        and detail.get("authorization_reference")
        and media.category == ProjectMediaCategory.COVER
        and media.rights_status == MediaRightsStatus.APPROVED
        and media.storage_key
        and media.sha256
        and media.mime_type in {"image/webp", "image/png", "image/jpeg", "image/avif"}
        and media.alt_en
        and media.alt_ar
        and media.width
        and media.width >= 1600
        and media.height
        and media.height >= 900
        and media.width > media.height
    )


async def permitted_preview_assets(record: Project, db: AsyncSession) -> set[str]:
    media = {item.id: item for item in record.media if item.project_id == record.id}
    if not media:
        return set()
    receipts = (
        await db.scalars(
            select(AuditLog)
            .where(
                AuditLog.entity_id.in_(media),
                AuditLog.entity_type == "project_media",
                AuditLog.action.in_((APPROVE, REVOKE)),
                AuditLog.outcome == "success",
            )
            .order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
        )
    ).all()
    seen = set()
    permitted = set()
    for receipt in receipts:
        if receipt.entity_id in seen or receipt.entity_id not in media:
            continue
        seen.add(receipt.entity_id)
        if current_asset_permission(media[receipt.entity_id], receipt):
            permitted.add(str(receipt.entity_id))
    return permitted
