from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.models import EditorialApprovalStatus, MediaRightsStatus, ProjectMediaCategory
from app.project_approval import technical_blockers


@pytest.mark.asyncio
async def test_import_review_gates_are_independent_of_populated_fields() -> None:
    content = dict(
        official_name="Synthetic Project",
        short_summary="Synthetic summary",
        full_description="Synthetic description",
        seo_title="Synthetic title",
        seo_description="Synthetic SEO description",
    )
    record = SimpleNamespace(
        id="synthetic-project",
        translations=[SimpleNamespace(locale=locale, **content) for locale in ("en", "ar")],
        priority="B",
        last_verified_at=True,
        sources=[
            SimpleNamespace(
                is_active=True, is_official=True, content_hash="a" * 64, last_checked_at=True
            )
        ],
        media=[
            SimpleNamespace(
                storage_key="private.webp",
                sha256="b" * 64,
                rights_status=MediaRightsStatus.APPROVED,
                alt_en="Synthetic",
                alt_ar="اختبار",
                category=ProjectMediaCategory.COVER,
                source_url="owner-approved:synthetic",
                width=1600,
                height=900,
            )
        ],
        payment_plan=None,
    )
    candidate = SimpleNamespace(
        acquisition_summary={},
        validation_errors=[{"field": "handover", "code": "missing_source_evidence"}],
        conflict_reasons=["Synthetic source disagreement"],
        human_review_completed=False,
        arabic_review_required=True,
        editorial_draft=SimpleNamespace(approval_status=EditorialApprovalStatus.NEEDS_REVIEW),
    )
    db = SimpleNamespace(scalars=AsyncMock(return_value=Mock(all=lambda: [candidate])))
    blockers = await technical_blockers(record, db)
    assert len(blockers) == 3
    assert "Unresolved Project identity or unclassified source conflict" in blockers
    assert "Imported facts and Arabic require human review" in blockers
    assert "Imported bilingual Overview requires editorial approval" in blockers
    candidate.validation_errors = []
    candidate.conflict_reasons = []
    candidate.human_review_completed = True
    candidate.arabic_review_required = False
    candidate.editorial_draft.approval_status = EditorialApprovalStatus.APPROVED
    assert await technical_blockers(record, db) == []
    candidate.validation_errors = [
        {"field": field, "code": "missing_source_evidence"}
        for field in (
            "availability_status",
            "construction_status",
            "handover",
            "bedrooms",
            "size_range",
            "amenities",
            "payment_plan",
            "down_payment",
        )
    ]
    candidate.conflict_reasons = ["Source disagreement for down_payment_percentage: 4 | 5."]
    record.payment_plan = SimpleNamespace(verified_at=None)
    assert await technical_blockers(record, db) == []
    assert candidate.conflict_reasons  # Omission never clears the retained disagreement.
    candidate.acquisition_summary = {"targeted_field_review": {"identity_hold": True}}
    assert any("identity" in item for item in await technical_blockers(record, db))
    candidate.acquisition_summary = {}
    record.media = []
    assert "Prepared landscape Cover with bilingual metadata required" in await technical_blockers(
        record, db
    )


@pytest.mark.asyncio
async def test_owner_authorized_native_tanami_cover_satisfies_cover_gate() -> None:
    content = dict(
        official_name="Synthetic Project",
        short_summary="Synthetic summary",
        full_description="Synthetic description",
        seo_title="Synthetic title",
        seo_description="Synthetic SEO description",
    )
    record = SimpleNamespace(
        id="synthetic-project",
        translations=[SimpleNamespace(locale=locale, **content) for locale in ("en", "ar")],
        priority="B",
        last_verified_at=True,
        sources=[
            SimpleNamespace(
                is_active=True, is_official=True, content_hash="a" * 64, last_checked_at=True
            )
        ],
        media=[
            SimpleNamespace(
                storage_key="tanami-banner.webp",
                sha256="b" * 64,
                rights_status=MediaRightsStatus.APPROVED,
                alt_en="Exact Project banner",
                alt_ar="الصورة الرئيسية للمشروع",
                category=ProjectMediaCategory.COVER,
                source_url=("https://manage.tanamiproperties.com/Banner/1098/Large/7418.webp"),
                width=1400,
                height=600,
            )
        ],
        payment_plan=None,
    )
    db = SimpleNamespace(scalars=AsyncMock(return_value=Mock(all=lambda: [])))

    assert await technical_blockers(record, db) == []
