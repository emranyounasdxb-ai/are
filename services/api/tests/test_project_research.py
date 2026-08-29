from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from app.acquisition.contracts import DiscoveryResult, FetchResult
from app.acquisition.research import (
    discovery_inspection_urls,
    exact_document_identity,
    readiness_report,
    recalculate_stored_conflicts,
    research_existing_batch,
    research_fingerprint,
)
from app.acquisition.security import AcquisitionSecurityError, host_is_allowed, validate_public_url
from app.db import SessionLocal
from app.import_review import sync_linked_draft_from_candidate
from app.models import (
    AuditLog,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectMediaCategory,
    ProjectSourceSnapshot,
    PublicationStatus,
)


def candidate():
    return SimpleNamespace(
        id=uuid4(),
        linked_project_id=uuid4(),
        manifest_row_id=1,
        normalized_project_name="QA Example",
        proposed_developer_id=uuid4(),
        proposed_area_id=uuid4(),
        official_source_url="https://example.com/qa-example",
        normalized_payload={
            "availability_status": "available",
            "construction_status": "under-construction",
            "handover_quarter": "Q4",
            "handover_year": 2028,
            "bedrooms": ["2"],
            "property_types": ["apartment"],
            "unit_types": ["2 bedroom"],
            "size_min": 1000,
            "size_max": 1200,
            "size_unit": "sqft",
            "down_payment_percentage": 10,
            "payment_plan": {"milestones": [{"percentage": 100}], "is_complete": True},
            "amenities": ["Swimming pool"],
        },
        acquisition_summary={"source_first_research": {"exact_documents": ["example"]}},
        conflict_reasons=[],
        validation_errors=[],
        human_review_completed=True,
        arabic_review_required=False,
        editorial_draft=SimpleNamespace(
            overview_en="Reviewed English",
            overview_ar="محتوى معتمد",
            approval_status=EditorialApprovalStatus.APPROVED,
        ),
        staged_media=[
            SimpleNamespace(
                stage_status="downloaded",
                category=ProjectMediaCategory.COVER,
                rights_status=MediaRightsStatus.APPROVED,
                storage_key="qa-cover.webp",
                rights_basis="Owner approval reference QA-1",
            )
        ],
    )


def test_identity_does_not_fuzzily_merge_phases_or_unit_counts():
    assert exact_document_identity("Nama 2 at Al Mamsha", "Nama 2")
    assert exact_document_identity("Nama 2 at Al Mamsha", "Nama 2 at Al Mamsha by Alef Group")
    assert exact_document_identity(
        "Al Mamsha Hamsa 2",
        "Alef Launches Al Mamsha Hamsa 2 in Al Mamsha Sharjah",
    )
    assert exact_document_identity(
        "Nama 5 at Al Mamsha",
        "Alef Group launches Nama 5 at Al Mamsha Raseel in Sharjah",
    )
    assert exact_document_identity("The Riff Apartments", "About The Riff")
    assert exact_document_identity("Safa at Aljada", "Safa Apartments")
    assert exact_document_identity("Olfah by Alef", "Olfah By Alef")
    assert exact_document_identity(
        "Hayyan", "Hayyan - Buy Modern Luxury Villas & Townhouses in Sharjah by Alef"
    )
    assert not exact_document_identity("Nama 2 at Al Mamsha", "Nama 3")
    assert not exact_document_identity("Al Mamsha Hamsa 2", "Al Mamsha Hamsa 3 launched")
    assert not exact_document_identity("Al Mamsha Hamsa", "Al Mamsha Hamsa 2 launched")
    assert not exact_document_identity(
        "Olfah 2 by Alef", "Olfah Residential Project AED 2.5 Billion Launch"
    )
    assert not exact_document_identity("Nasma Residences", "Nasma Central")
    assert not exact_document_identity("The Boulevard 3", "The Boulevard 3 Bedroom")
    assert not exact_document_identity("Abu Dhabi Tower", "Renad Tower")


def test_fuzzy_discovery_is_bounded_to_private_document_identity_inspection():
    suggestion = "https://www.arada.com/en/property_category/areej/"
    discovery = DiscoveryResult(
        source_url=suggestion,
        match_kind="fuzzy-suggestion",
        suggested_url=suggestion,
    )
    assert discovery_inspection_urls(discovery) == [suggestion]
    assert discovery_inspection_urls(DiscoveryResult(source_url=None, match_kind="not-found")) == []


def test_research_fingerprint_ignores_observation_times_only():
    original = {
        "checked_at": "2026-08-29T10:00:00+00:00",
        "documents": [
            {
                "source_url": "https://example.com/project",
                "retrieved_at": "2026-08-29T10:00:00+00:00",
                "sha256": "a" * 64,
            }
        ],
    }
    repeated = {
        **original,
        "checked_at": "2026-08-29T11:00:00+00:00",
        "documents": [{**original["documents"][0], "retrieved_at": "2026-08-29T11:00:00+00:00"}],
    }
    changed = {
        **repeated,
        "documents": [{**repeated["documents"][0], "sha256": "b" * 64}],
    }
    assert research_fingerprint(original) == research_fingerprint(repeated)
    assert research_fingerprint(original) != research_fingerprint(changed)


def test_malformed_source_hostname_is_rejected_without_network_or_batch_crash():
    malformed = f"{'a' * 71}.example.com"
    assert not host_is_allowed(malformed, ("example.com",))
    assert host_is_allowed("projects.example.com", ("example.com",))
    assert not host_is_allowed("example.com.attacker.invalid", ("example.com",))
    with pytest.raises(AcquisitionSecurityError, match="outside the adapter allowlist"):
        validate_public_url(f"https://{malformed}/project", ("example.com",))


def test_automatic_media_approval_is_not_documented_reuse_permission():
    record = candidate()
    record.staged_media[
        0
    ].rights_basis = "Automatically approved exact-Project image from a validated candidate source."
    report = readiness_report(record)
    assert not report["ready"]
    assert report["rights_unclear_media"] == 1
    assert report["rights_cleared_cover"] == 0
    assert "Documented media reuse permission required" in report["blockers"]


def test_readiness_preserves_independent_missing_conflict_and_editorial_gates():
    record = candidate()
    record.normalized_payload["construction_status"] = None
    record.normalized_payload["payment_plan"]["is_complete"] = False
    record.conflict_reasons = ["Source disagreement for down_payment_percentage: 5 | 10."]
    record.editorial_draft.approval_status = EditorialApprovalStatus.NEEDS_REVIEW
    before = record.editorial_draft.approval_status
    first = readiness_report(record)
    second = readiness_report(record)
    assert first == second
    assert not first["ready"]
    assert "construction_status" in first["missing"]
    assert "payment_plan" in first["missing"]
    assert len(first["conflicts"]) == 1
    assert record.editorial_draft.approval_status == before


def test_conflict_replay_requires_readable_evidence_and_preserves_other_conflicts():
    record = candidate()
    record.conflict_reasons = [
        "Source disagreement for size_min: 5000.0 | 8000.0.",
        "Source disagreement for down_payment_percentage: 5 | 10.",
    ]
    record.acquisition_summary["official_fact_evidence"] = [
        {
            "field": "size_min",
            "source_url": "https://example.com/qa-example",
            "retained_value": 5000.0,
            "official_value": 8000.0,
        }
    ]
    record.evidence = []
    storage = SimpleNamespace(read=lambda _: b"<p>Plots from 5,000 sqft to 12,000 sqft.</p>")
    assert not recalculate_stored_conflicts(record, storage)
    assert len(record.conflict_reasons) == 2
    record.evidence = [
        SimpleNamespace(
            source_url="https://example.com/qa-example",
            storage_key="qa-evidence.html",
            content_type="text/html",
            retrieved_at=datetime.now(UTC),
        )
    ]
    resolutions = recalculate_stored_conflicts(record, storage)
    assert len(resolutions) == 1
    assert record.conflict_reasons == ["Source disagreement for down_payment_percentage: 5 | 10."]
    assert recalculate_stored_conflicts(record, storage) == resolutions


def test_missing_current_fact_is_not_proof_that_a_conflict_is_resolved():
    record = candidate()
    record.conflict_reasons = [
        "Source disagreement for availability_status: sold-out | coming-soon."
    ]
    record.acquisition_summary["official_fact_evidence"] = [
        {
            "field": "availability_status",
            "source_url": "https://example.com/qa-example",
            "retained_value": "sold-out",
            "official_value": "coming-soon",
        }
    ]
    record.evidence = [
        SimpleNamespace(
            source_url="https://example.com/qa-example",
            storage_key="qa-evidence.html",
            content_type="text/html",
            retrieved_at=datetime.now(UTC),
        )
    ]
    storage = SimpleNamespace(read=lambda _: b"<p>No current availability statement.</p>")
    assert not recalculate_stored_conflicts(record, storage)
    assert len(record.conflict_reasons) == 1
    storage.read = lambda _: b"<p>Register your interest.</p>"
    assert len(recalculate_stored_conflicts(record, storage)) == 1
    assert record.conflict_reasons == []


def test_unreadable_snapshot_cannot_clear_conflict():
    record = candidate()
    record.conflict_reasons = ["Source disagreement for size_min: 5000.0 | 8000.0."]
    record.acquisition_summary["official_fact_evidence"] = [
        {
            "field": "size_min",
            "source_url": "https://example.com/qa-example",
            "retained_value": 5000,
            "official_value": 8000,
        }
    ]
    record.evidence = [
        SimpleNamespace(
            source_url="https://example.com/qa-example",
            storage_key="missing.html",
            content_type="text/html",
            retrieved_at=datetime.now(UTC),
        )
    ]

    def unreadable(_):
        raise FileNotFoundError("Missing private evidence")

    assert not recalculate_stored_conflicts(record, SimpleNamespace(read=unreadable))
    assert len(record.conflict_reasons) == 1


@pytest.mark.asyncio
async def test_bounded_research_is_private_idempotent_and_keeps_success_on_retry(test_settings):
    url = "https://www.alefgroup.ae/qa-example/"

    class Fetcher:
        failed = False

        def fetch(self, requested, domains):
            assert requested == url
            assert "alefgroup.ae" in domains
            return FetchResult(
                url,
                503 if self.failed else 200,
                datetime.now(UTC),
                "text/html",
                b"" if self.failed else b"<h1>QA Example</h1><p>Register interest</p>",
                error_code="http_error" if self.failed else None,
            )

    async with SessionLocal() as db:
        batch = ProjectImportBatch(
            name="QA Official Research",
            source_reference="qa-only",
            manifest_hash=uuid4().hex * 2,
            adapter_version="test",
            total_count=1,
        )
        record = ProjectImportCandidate(
            manifest_row_id=1,
            raw_source_payload={},
            normalized_payload={},
            normalized_project_name="QA Example",
            owner_manifest_values={"source_developer": "Alef Group"},
            source_urls=[],
            content_hash="e" * 64,
            validation_errors=[],
            conflict_reasons=[],
            review_status=ImportReviewStatus.NEEDS_REVIEW,
        )
        batch.candidates = [record]
        db.add(batch)
        await db.commit()
        fetcher = Fetcher()
        try:
            first = await research_existing_batch(
                db,
                test_settings,
                batch.id,
                fetcher=fetcher,
                discover=False,
                candidate_ids=[record.id],
                extra_urls={1: [url]},
            )
            repeated = await research_existing_batch(
                db,
                test_settings,
                batch.id,
                fetcher=fetcher,
                discover=False,
                candidate_ids=[record.id],
                extra_urls={1: [url]},
            )
            assert first["count"] == 1 and first["ready"] == 0 and first["mutated"] == 1
            assert repeated["count"] == 1 and repeated["mutated"] == 0
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(ProjectSourceSnapshot)
                    .where(ProjectSourceSnapshot.candidate_id == record.id)
                )
                == 1
            )
            assert record.normalized_payload == {}
            assert record.linked_project_id is None
            assert not record.human_review_completed
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(AuditLog)
                    .where(
                        AuditLog.entity_id == str(record.id),
                        AuditLog.action == "project.import.official_research",
                    )
                )
                == 1
            )
            fetcher.failed = True
            await research_existing_batch(
                db,
                test_settings,
                batch.id,
                fetcher=fetcher,
                discover=False,
                candidate_ids=[record.id],
                extra_urls={1: [url]},
            )
            research = record.acquisition_summary["source_first_research"]
            assert research["documents"][0]["status"] == 200
            assert any("Retry failed" in item for item in research["failures"])
            with pytest.raises(ValueError, match="Every selected candidate"):
                await research_existing_batch(
                    db, test_settings, batch.id, candidate_ids=[record.id, uuid4()]
                )
        finally:
            await db.execute(delete(AuditLog).where(AuditLog.entity_id == str(record.id)))
            await db.commit()


@pytest.mark.asyncio
async def test_draft_sync_keeps_extracted_official_snapshot_hash_and_timestamp():
    record = candidate()
    record.normalized_payload = {}
    record.staged_media = []
    record.source_urls = []
    record.extracted_at = datetime(2025, 1, 1, tzinfo=UTC)
    record.last_verified_at = datetime.now(UTC)
    record.content_hash = "a" * 64
    record.evidence = [
        SimpleNamespace(
            source_url=record.official_source_url,
            outcome="extracted",
            storage_key="source.html",
            http_status=200,
            retrieved_at=record.last_verified_at,
            content_hash="b" * 64,
        )
    ]
    project = SimpleNamespace(
        status=PublicationStatus.DRAFT,
        property_types=[],
        bedroom_options=[],
        unit_types=[],
        amenities=[],
        sources=[],
        media=[],
        payment_plan=None,
    )
    db = SimpleNamespace(scalar=AsyncMock(return_value=project), flush=AsyncMock())
    await sync_linked_draft_from_candidate(db, record)
    assert project.sources[0].content_hash == "b" * 64
    assert project.sources[0].retrieved_at == record.last_verified_at
