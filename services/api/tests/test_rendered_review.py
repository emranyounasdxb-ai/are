from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.acquisition.media_intake import intake_private_media
from app.acquisition.reconciliation import _missing
from app.acquisition.rendered_review import (
    apply_rendered_review,
    fill_gaps,
    reconcile_payment_context,
    rendered_media,
)
from app.acquisition.tanami_context import ContextTable, floor_unit_facts, payment_variants
from app.db import SessionLocal
from app.models import (
    AreaCommunity,
    AuditLog,
    Developer,
    ImportReviewStatus,
    Project,
    ProjectAvailabilityStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    PublicationStatus,
    UAEEmirate,
)
from app.serializers import public_candidate_payment

URL = "https://www.tanamiproperties.com/Projects/QA-Rendered"


def test_source_placeholder_is_missing_not_a_verified_unit_type():
    assert _missing(["Will Be Updated Soon"])
    assert _missing("Not Confirmed")
    assert not _missing(["2 Bedrooms"])
    assert not _missing(0)


def test_nested_payment_provenance_is_never_forwarded_to_public_preview():
    payment = {
        "source_url": URL,
        "source_id": "private",
        "raw_source_text": "10/90",
        "is_complete": True,
        "milestones": [{"percentage": 10, "source_url": URL}],
    }
    assert public_candidate_payment(payment) == {
        "raw_source_text": "10/90",
        "is_complete": True,
        "milestones": [{"percentage": 10}],
    }
    assert payment["source_url"] == URL
    assert public_candidate_payment("10/90") == "10/90"


@pytest.mark.asyncio
async def test_bounded_media_selection_rejects_other_candidate_and_empty_is_noop(test_settings):
    cid, mid = uuid4(), uuid4()
    media = SimpleNamespace(id=mid, stage_status="failed")
    candidate = SimpleNamespace(id=cid, staged_media=[media])
    db = SimpleNamespace(scalar=AsyncMock(return_value=SimpleNamespace(candidates=[candidate])))
    with pytest.raises(ValueError, match="selected image"):
        await intake_private_media(
            db, test_settings, uuid4(), candidate_ids=[cid], media_ids={uuid4()}
        )
    result = await intake_private_media(
        db, test_settings, uuid4(), candidate_ids=[cid], media_ids=set()
    )
    assert result["attempted"] == 0
    assert media.stage_status == "failed"


def test_media_uses_observed_exact_project_urls_without_caps_or_related_images():
    base = {
        "url": URL,
        "images": [
            {
                "context": "Summary",
                "src": "https://manage.tanamiproperties.com/Banner/123/Large/1.webp",
            },
            *[
                {
                    "context": "Image Gallery",
                    "href": f"https://manage.tanamiproperties.com/Gallery/123/Thumb/{i}.webp",
                }
                for i in range(45)
            ],
            {
                "context": "Other Projects",
                "href": "https://manage.tanamiproperties.com/Gallery/123/Thumb/99.webp",
            },
            {
                "context": "Image Gallery",
                "href": "https://manage.tanamiproperties.com/Gallery/999/Thumb/99.webp",
            },
        ],
    }
    media = rendered_media([base], URL)
    assert len(media) == 46
    assert not any("/999/" in url or "99.webp" in url for url, _ in media)
    assert all("/Thumb/" in url for url, _ in media[1:])


def documents(candidate_id):
    common = {
        "candidate_id": str(candidate_id),
        "h1": "QA Rendered",
        "captured_at": datetime.now(UTC).isoformat(),
    }
    return [
        {
            **common,
            "url": URL,
            "requested_url": URL,
            "tables": [{"heading": "Summary", "rows": [["Handover", "Q4 2030"]]}],
        },
        {
            **common,
            "url": URL + "-PaymentPlan",
            "requested_url": URL + "-PaymentPlan",
            "tables": [
                {
                    "heading": "Payment Plan",
                    "rows": [
                        ["Installment", "Payment", "Milestone"],
                        ["Booking", "10%", "On Booking"],
                        ["Final", "90%", "On Handover"],
                    ],
                }
            ],
        },
    ]


def test_gap_fill_preserves_confirmed_and_human_fields():
    original = {
        "handover_year": 2028,
        "bedrooms": [],
        "size_min": None,
        "payment_plan": {"raw_source_text": "10/90"},
    }
    result, changed, retained = fill_gaps(
        original,
        {
            "handover_year": 2030,
            "bedrooms": ["2"],
            "size_min": 500,
            "payment_plan": {"milestones": [{"percentage": 100}]},
        },
        {"size_min"},
    )
    assert result["handover_year"] == 2028
    assert result["size_min"] is None
    assert set(changed) == {"bedrooms", "payment_plan"}
    assert retained["handover_year"]["rendered_value"] == 2030
    assert original["bedrooms"] == []


def test_floor_tables_keep_explicit_unit_context_and_ignore_plan_ids():
    facts = floor_unit_facts(
        [
            ContextTable(
                "Floor Plans",
                [
                    ["Floor Plan", "Category", "Unit Type", "Floor Details", "Sizes", "Type"],
                    [
                        "Plan 27",
                        "Unit Plan",
                        "2 Bedrooms",
                        "Type 9",
                        "900 to 1100 Sq Ft",
                        "Apartment",
                    ],
                ],
            )
        ]
    )
    assert facts["bedrooms"] == ["2"]
    assert facts["size_min"] == 900
    assert facts["unit_summary_evidence"][0]["unit_type"] == "2 Bedrooms"


def test_alternative_offer_resolution_keeps_both_sources_and_real_disagreements():
    plans = payment_variants(
        [
            ContextTable(
                "Option " + str(p),
                [
                    ["Installment", "Payment", "Milestone"],
                    ["Booking", f"{p}%", "On Booking"],
                    ["Final", f"{100 - p}%", "On Handover"],
                ],
            )
            for p in (10, 30)
        ]
    )
    reason = "Source disagreement for down_payment_percentage: 10.0 | 30.0."
    record = SimpleNamespace(
        conflict_reasons=[reason],
        acquisition_summary={
            "official_fact_evidence": [
                {
                    "field": "down_payment_percentage",
                    "sources": [
                        {"source_url": URL, "value": 10},
                        {"source_url": URL + "-PaymentPlan", "value": 30},
                    ],
                }
            ]
        },
    )
    real = deepcopy(record)
    assert reconcile_payment_context(real, URL, plans[:1]) == []
    assert real.conflict_reasons == [reason]
    real.acquisition_summary["official_fact_evidence"][0]["sources"][1]["source_url"] = (
        "https://developer.example/qa"
    )
    assert reconcile_payment_context(real, URL, plans) == []
    assert real.conflict_reasons == [reason]
    resolved = reconcile_payment_context(record, URL, plans)
    assert record.conflict_reasons == []
    assert resolved[0]["requires_human_review"]
    assert len(resolved[0]["observations"]) == 2
    assert reconcile_payment_context(record, URL, plans) == []


@pytest.mark.asyncio
async def test_rendered_review_rejects_unlinked_published_and_cross_candidate(test_settings):
    record = SimpleNamespace(linked_project_id=None)
    db = SimpleNamespace(scalar=AsyncMock(return_value=record))
    with pytest.raises(ValueError, match="existing linked"):
        await apply_rendered_review(db, test_settings, uuid4(), [])
    record.linked_project_id = uuid4()
    db.get = AsyncMock(return_value=SimpleNamespace(status=PublicationStatus.PUBLISHED))
    with pytest.raises(ValueError, match="private Draft"):
        await apply_rendered_review(db, test_settings, uuid4(), [])
    db.get.return_value.status = PublicationStatus.DRAFT
    record.source_urls = [URL]
    with pytest.raises(ValueError, match="another candidate"):
        await apply_rendered_review(db, test_settings, uuid4(), documents(uuid4()))


@pytest.mark.asyncio
async def test_postgres_rendered_review_is_scoped_idempotent_and_source_exact(test_settings):
    async with SessionLocal() as db:
        developer = await db.scalar(select(Developer).limit(1))
        assert developer
        area = AreaCommunity(
            slug="qa-rendered-area",
            name_en="QA Area",
            name_ar="منطقة اختبار",
            emirate=UAEEmirate.SHARJAH,
            status=PublicationStatus.DRAFT,
        )
        db.add(area)
        await db.flush()
        project = Project(
            slug="qa-rendered-project",
            developer_id=developer.id,
            area_id=area.id,
            emirate=UAEEmirate.SHARJAH,
            status=PublicationStatus.DRAFT,
            availability_status=ProjectAvailabilityStatus.NOT_CONFIRMED,
            size_min=777,
            internal_notes="Preserve owner edit",
        )
        batch = ProjectImportBatch(
            name="QA Rendered",
            source_reference="qa-only",
            manifest_hash="e" * 64,
            adapter_version="qa",
            total_count=1,
            needs_review_count=1,
        )
        db.add_all([project, batch])
        await db.flush()
        candidate = ProjectImportCandidate(
            batch_id=batch.id,
            manifest_row_id=1,
            raw_source_payload={},
            owner_manifest_values={},
            normalized_payload={},
            normalized_project_name="QA Rendered",
            content_hash="d" * 64,
            source_urls=[URL],
            linked_project_id=project.id,
            review_status=ImportReviewStatus.NEEDS_REVIEW,
        )
        db.add(candidate)
        await db.commit()
        cid = candidate.id
        try:
            docs = documents(cid)
            first = await apply_rendered_review(db, test_settings, cid, docs)
            await db.commit()
            await db.refresh(project)
            assert "payment_plan" in first["changed"]
            assert project.handover_year == 2030
            assert project.size_min == 777
            assert project.internal_notes == "Preserve owner edit"
            assert project.status == PublicationStatus.DRAFT
            assert project.payment_plan.source_id == next(
                s.id for s in project.sources if s.source_url == URL + "-PaymentPlan"
            )
            snapshots = len(candidate.evidence)
            second = await apply_rendered_review(db, test_settings, cid, list(reversed(docs)))
            assert second["idempotent"]
            assert len(candidate.evidence) == snapshots
            assert len(project.payment_plan.milestones) == 2
            for source in project.sources:
                evidence = next(e for e in candidate.evidence if e.source_url == source.source_url)
                assert source.content_hash == evidence.content_hash
                assert evidence.http_status is None
                assert evidence.outcome == "rendered"
        finally:
            await db.rollback()
            await db.execute(delete(AuditLog).where(AuditLog.entity_id == str(cid)))
            await db.commit()
