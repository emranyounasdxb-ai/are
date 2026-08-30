"""Synthetic, database-free regressions for private asset-only permission."""

import hashlib
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models import AuditLog, MediaRightsStatus, ProjectMedia, ProjectMediaCategory
from app.project_approval import require_current_receipt
from app.project_media_preview import (
    APPROVE,
    REVOKE,
    VERSION,
    asset_version,
    current_asset_permission,
    permitted_preview_assets,
)
from app.public_project_evidence import public_evidenced_project
from app.routers.projects import preview_project_media
from app.serializers import _project_media_public_eligible


def approved_asset():
    media = ProjectMedia(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        category=ProjectMediaCategory.COVER,
        source_url="owner-approved:synthetic",
        rights_status=MediaRightsStatus.APPROVED,
        alt_en="Neutral brand cover, not a Project photograph",
        alt_ar="غلاف محايد",
        display_order=0,
        storage_key="synthetic.webp",
        original_filename="synthetic.webp",
        mime_type="image/webp",
        size_bytes=5,
        sha256=hashlib.sha256(b"image").hexdigest(),
        width=1920,
        height=1080,
        verified_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    receipt = AuditLog(
        action=APPROVE,
        entity_type="project_media",
        entity_id=media.id,
        outcome="success",
        metadata_summary={
            "version": VERSION,
            "scope": "authenticated-preview-only",
            "project_id": str(media.project_id),
            "asset_version": asset_version(media),
            "authorization_reference": "Synthetic owner permission for private preview only",
        },
    )
    return media, receipt


@pytest.mark.parametrize(
    "field,value",
    [
        ("sha256", "b" * 64),
        ("project_id", uuid.uuid4()),
        ("id", uuid.uuid4()),
        ("storage_key", "changed.webp"),
        ("alt_en", "Changed"),
        ("alt_ar", "تغيير"),
        ("category", ProjectMediaCategory.GALLERY),
        ("width", 800),
        ("height", 600),
        ("rights_status", MediaRightsStatus.PENDING),
        ("source_url", "owner-approved:changed"),
        ("updated_at", datetime(2026, 1, 1, tzinfo=UTC)),
    ],
)
def test_changed_asset_or_metadata_cannot_reuse_permission(field, value):
    media, receipt = approved_asset()
    assert current_asset_permission(media, receipt)
    setattr(media, field, value)
    assert not current_asset_permission(media, receipt)


@pytest.mark.parametrize(
    ("category", "width", "height"),
    [
        (ProjectMediaCategory.COVER, 1920, 1080),
        (ProjectMediaCategory.GALLERY, 1600, 900),
        (ProjectMediaCategory.AMENITIES, 1400, 900),
        (ProjectMediaCategory.FLOOR_PLAN, 1000, 700),
        (ProjectMediaCategory.LOCATION_MAP, 1200, 900),
        (ProjectMediaCategory.MASTER_PLAN, 1000, 700),
    ],
)
def test_asset_only_permission_supports_separate_public_media_categories(category, width, height):
    media, receipt = approved_asset()
    media.category = category
    media.width = width
    media.height = height
    receipt.metadata_summary["asset_version"] = asset_version(media)

    assert current_asset_permission(media, receipt)


@pytest.mark.parametrize(
    ("category", "width", "height"),
    [
        (ProjectMediaCategory.GALLERY, 800, 450),
        (ProjectMediaCategory.FLOOR_PLAN, 999, 700),
        (ProjectMediaCategory.LOCATION_MAP, 1100, 900),
        (ProjectMediaCategory.VIDEO_REFERENCE, 1920, 1080),
    ],
)
def test_asset_only_permission_rejects_ineligible_or_reference_media(category, width, height):
    media, receipt = approved_asset()
    media.category = category
    media.width = width
    media.height = height
    receipt.metadata_summary["asset_version"] = asset_version(media)

    assert not current_asset_permission(media, receipt)


@pytest.mark.parametrize(
    ("category", "width", "height"),
    [
        (ProjectMediaCategory.COVER, 1400, 600),
        (ProjectMediaCategory.GALLERY, 800, 450),
        (ProjectMediaCategory.AMENITIES, 640, 360),
        (ProjectMediaCategory.FLOOR_PLAN, 640, 360),
        (ProjectMediaCategory.LOCATION_MAP, 640, 360),
        (ProjectMediaCategory.MASTER_PLAN, 640, 360),
    ],
)
def test_owner_authorized_tanami_native_media_can_receive_private_preview_permission(
    category, width, height
):
    media, receipt = approved_asset()
    media.category = category
    media.width = width
    media.height = height
    media.source_url = "https://manage.tanamiproperties.com/Gallery/1098/Thumb/7428.webp"
    receipt.metadata_summary["asset_version"] = asset_version(media)

    assert current_asset_permission(media, receipt)


def test_owner_created_exact_2_to_1_hero_can_receive_private_preview_permission():
    media, receipt = approved_asset()
    media.width = 1774
    media.height = 887
    media.source_url = "owner-created://aliyas/hero-banners/are-hero-hotel-01.webp"
    receipt.metadata_summary["asset_version"] = asset_version(media)

    assert current_asset_permission(media, receipt)


def test_owner_created_native_hero_survives_localized_project_serialization_gate():
    assert _project_media_public_eligible(
        {
            "rights_status": "approved",
            "has_upload": True,
            "width": 1774,
            "height": 887,
            "category": "cover",
            "source_url": "owner-created://aliyas/hero-banners/are-hero-hotel-01.webp",
        }
    )


@pytest.mark.asyncio
async def test_latest_revocation_wins_and_permission_is_project_isolated():
    media, receipt = approved_asset()
    record = SimpleNamespace(id=media.project_id, media=[media])
    revoked = AuditLog(action=REVOKE, entity_id=media.id, entity_type="project_media")
    db = SimpleNamespace(scalars=AsyncMock(return_value=Mock(all=lambda: [revoked, receipt])))
    assert await permitted_preview_assets(record, db) == set()
    db.scalars.return_value = Mock(all=lambda: [receipt])
    assert await permitted_preview_assets(record, db) == {str(media.id)}
    record.id = uuid.uuid4()
    assert await permitted_preview_assets(record, db) == set()


@pytest.mark.asyncio
@pytest.mark.parametrize("locale", ["en", "ar"])
async def test_asset_permission_is_private_only_and_never_approves_project(locale):
    media, receipt = approved_asset()
    record = SimpleNamespace(id=media.project_id, media=[media], status="draft")
    data = {"id": str(record.id), "media": [{"id": str(media.id)}, {"id": "unapproved"}]}
    db = SimpleNamespace(
        execute=AsyncMock(return_value=Mock(all=lambda: [])),
        scalars=AsyncMock(return_value=Mock(all=lambda: [receipt])),
        scalar=AsyncMock(return_value=None),
    )
    with (
        patch("app.public_project_evidence.project_preview_dict", return_value=data),
        patch("app.public_project_evidence.project_dict", return_value=data),
    ):
        private = await public_evidenced_project(record, locale, db, preview=True)
        assert private["media"] == [{"id": str(media.id)}]
        public = await public_evidenced_project(record, locale, db)
        assert public["media"] == []
        with pytest.raises(HTTPException) as error:
            await require_current_receipt(record, db)
        assert error.value.detail["code"] == "project_review_receipt_required"
        assert "project.approve" in str(
            db.scalar.call_args.args[0].compile(compile_kwargs={"literal_binds": True})
        )
    assert record.status == "draft"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["allowed", "unapproved", "identity-hold", "changed-bytes"])
async def test_binary_endpoint_obeys_projection_and_exact_bytes(mode):
    media, _ = approved_asset()
    record = SimpleNamespace(id=media.project_id, media=[media])
    projection = (
        {"media": [{"id": str(media.id)}]}
        if mode in {"allowed", "changed-bytes"}
        else {"media": []}
        if mode == "unapproved"
        else None
    )
    with (
        patch("app.routers.projects.project_or_404", new=AsyncMock(return_value=record)),
        patch(
            "app.routers.projects.public_evidenced_project", new=AsyncMock(return_value=projection)
        ),
        patch("app.routers.projects.PrivateStorage") as storage,
    ):
        storage.return_value.read.return_value = b"changed" if mode == "changed-bytes" else b"image"
        if mode == "allowed":
            response = await preview_project_media(record.id, media.id, None, None, None)
            assert response.body == b"image"
            assert response.headers["cache-control"].startswith("private, no-store")
        else:
            with pytest.raises(HTTPException) as error:
                await preview_project_media(record.id, media.id, None, None, None)
            assert error.value.status_code == 404
        if mode in {"unapproved", "identity-hold"}:
            storage.return_value.read.assert_not_called()
