from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models import (
    AreaCommunity,
    Developer,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProcessingItemStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportEditorialDraft,
    ProjectImportMedia,
    ProjectMediaCategory,
    ProjectProcessingStatus,
    PublicationStatus,
    UAEEmirate,
    User,
)
from app.project_processing import (
    DeterministicSyntheticOverviewProvider,
    claim_next_item,
    create_processing_job,
    descriptive_media_filename,
    job_detail,
    overview_fact_guard,
    process_claimed_item,
    public_media_metadata,
    resolve_diagnostic,
    retry_failed_items,
)
from app.security import hash_password


async def synthetic_batch(count: int, *, complete: bool = False) -> tuple[ProjectImportBatch, User]:
    async with SessionLocal() as db:
        actor = User(
            email=f"processing-{uuid.uuid4()}@qa.are-cms.invalid-example-domain.com",
            display_name="Synthetic Processing Actor",
            password_hash=hash_password(f"Disposable-{uuid.uuid4()}!"),
        )
        developer = Developer(
            slug=f"qa-processing-developer-{uuid.uuid4().hex[:8]}",
            legal_name="Synthetic Developer LLC",
            source_name="Synthetic Developer LLC",
            internal_aliases=[],
            primary_emirate="Dubai",
            other_presence=[],
            selected_projects=[],
            official_website="https://example.invalid/developer",
            source_url="https://example.invalid/developer/source",
            additional_source_urls=[],
            verification_date=datetime.now(UTC).date(),
            enquiry_types=[],
            featured=False,
            display_order=0,
            status=PublicationStatus.DRAFT,
        )
        area = AreaCommunity(
            slug=f"qa-processing-area-{uuid.uuid4().hex[:8]}",
            name_en="Synthetic Area",
            name_ar="منطقة تجريبية",
            emirate=UAEEmirate.DUBAI,
            status=PublicationStatus.DRAFT,
        )
        db.add_all([actor, developer, area])
        await db.flush()
        batch = ProjectImportBatch(
            name=f"QA Processing {uuid.uuid4()}",
            source_reference="synthetic-private-fixture",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="synthetic-v1",
            total_count=count,
        )
        for index in range(1, count + 1):
            facts = {
                "project_name": f"Synthetic Project {index}",
                "emirate": "Dubai",
                "property_types": ["apartment"],
                "unit_types": ["Type A"],
                "bedroom_options": ["1"],
                "size_min": 500,
                "size_max": 900,
                "size_unit": "sqft",
                "handover_quarter": "Q1",
                "handover_year": 2030,
                "down_payment_percentage": 20,
                "down_payment_source_value": "20% synthetic fixture",
                "payment_plan": [{"stage": "booking", "percentage": 20}],
                "availability_status": "coming-soon",
                "construction_status": "pre-launch",
            }
            candidate = ProjectImportCandidate(
                manifest_row_id=index,
                raw_source_payload={"synthetic": True},
                normalized_payload=facts,
                owner_manifest_values={"owner_project_name": f"Synthetic Project {index}"},
                normalized_project_name=f"Synthetic Project {index}",
                proposed_developer_id=developer.id,
                proposed_area_id=area.id,
                source_urls=[],
                content_hash=f"{index:064x}",
                validation_errors=[],
                conflict_reasons=[],
                review_status=ImportReviewStatus.NEEDS_REVIEW,
            )
            if complete:
                candidate.editorial_draft = ProjectImportEditorialDraft(
                    overview_en=f"Synthetic Project {index} uses reviewed fixture facts.",
                    overview_ar=f"يستخدم المشروع التجريبي {index} حقائق اختبار مراجعة.",
                    source_version=f"{index:064x}",
                    approval_status=EditorialApprovalStatus.APPROVED,
                )
                candidate.staged_media = [
                    ProjectImportMedia(
                        category=ProjectMediaCategory.COVER,
                        source_url=f"https://example.invalid/synthetic-{index}.webp",
                        rights_status=MediaRightsStatus.APPROVED,
                        rights_basis="Synthetic fixture rights only",
                        stage_status="downloaded",
                        storage_key=f"qa-synthetic-{uuid.uuid4()}.webp",
                        mime_type="image/webp",
                        size_bytes=1024,
                        sha256=f"{index + 100:064x}",
                        width=1200,
                        height=800,
                        normalized_filename=f"synthetic-project-{index}-cover-01.webp",
                        alt_en_draft="Synthetic Project cover",
                        alt_ar_draft="غلاف مشروع تجريبي",
                        derivative_manifest=[
                            {"format": "webp", "width": 480},
                            {"format": "avif", "width": 480},
                        ],
                        original_sha256=f"{index + 200:064x}",
                        processed_sha256=f"{index + 100:064x}",
                        processing_version="project-media-v1",
                        public_metadata={"Publisher": "ALIYAS Real Estate"},
                        title_en="Synthetic Project cover",
                        title_ar="غلاف مشروع تجريبي",
                        description_en="Synthetic Project cover fixture.",
                        description_ar="غلاف تجريبي للمشروع.",
                        tags=["synthetic", "cover"],
                    )
                ]
            batch.candidates.append(candidate)
        db.add(batch)
        await db.commit()
        return batch, actor


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("count", "selection_mode"),
    [
        (1, "single"),
        (3, "manual"),
        (25, "first-25"),
        (50, "first-50"),
        (7, "all-filtered"),
        (4, "cross-page"),
        (8, "complete-batch"),
    ],
)
async def test_selection_modes_store_immutable_explicit_snapshots(
    count: int,
    selection_mode: str,
) -> None:
    batch, actor = await synthetic_batch(count)
    candidate_ids = [value.id for value in batch.candidates]
    async with SessionLocal() as db:
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=candidate_ids,
            selection_mode=selection_mode,
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        assert job.selected_record_ids == [str(value) for value in candidate_ids]
        candidate = await db.get(ProjectImportCandidate, candidate_ids[0])
        assert candidate is not None
        candidate.normalized_project_name = "Changed after job creation"
        await db.commit()
        loaded = await job_detail(db, job.id)
        assert loaded.selected_record_ids == [str(value) for value in candidate_ids]


@pytest.mark.asyncio
async def test_duplicate_job_is_idempotent_and_payload_change_is_rejected() -> None:
    batch, actor = await synthetic_batch(2)
    ids = [value.id for value in batch.candidates]
    key = f"qa-{uuid.uuid4()}"
    async with SessionLocal() as db:
        first = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=ids,
            selection_mode="manual",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=key,
        )
        repeated = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=ids,
            selection_mode="manual",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=key,
        )
        assert repeated.id == first.id
        with pytest.raises(ValueError, match="different request"):
            await create_processing_job(
                db,
                batch_id=batch.id,
                candidate_ids=ids[:1],
                selection_mode="single",
                requested_action="clean-and-prepare",
                actor_id=actor.id,
                correlation_id=f"qa-{uuid.uuid4()}",
                idempotency_key=key,
            )


@pytest.mark.asyncio
async def test_partial_success_does_not_roll_back_other_records() -> None:
    batch, actor = await synthetic_batch(2, complete=True)
    async with SessionLocal() as db:
        broken = await db.get(ProjectImportCandidate, batch.candidates[1].id)
        assert broken is not None
        broken.raw_source_payload = {}
        await db.commit()
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=[value.id for value in batch.candidates],
            selection_mode="manual",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        for _ in range(2):
            item = await claim_next_item(db, "qa-worker")
            assert item is not None
            await process_claimed_item(
                db,
                item.id,
                provider=DeterministicSyntheticOverviewProvider(),
            )
        loaded = await job_detail(db, job.id)
        assert loaded.succeeded_count == 1
        assert loaded.failed_count == 1
        assert loaded.items[0].status == ProcessingItemStatus.SUCCEEDED
        ready = await db.get(ProjectImportCandidate, batch.candidates[0].id)
        assert ready is not None
        assert ready.processing_status == ProjectProcessingStatus.READY_TO_POST


@pytest.mark.asyncio
async def test_synthetic_fifty_record_batch_completes_with_multiple_failures() -> None:
    batch, actor = await synthetic_batch(50, complete=True)
    async with SessionLocal() as db:
        for candidate in batch.candidates[::10]:
            record = await db.get(ProjectImportCandidate, candidate.id)
            assert record is not None
            record.raw_source_payload = {}
        await db.commit()
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=[value.id for value in batch.candidates],
            selection_mode="first-50",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        processed = 0
        while item := await claim_next_item(db, "qa-fifty-worker"):
            await process_claimed_item(
                db,
                item.id,
                provider=DeterministicSyntheticOverviewProvider(),
            )
            processed += 1
        loaded = await job_detail(db, job.id)
        assert processed == 50
        assert loaded.succeeded_count == 45
        assert loaded.failed_count == 5


@pytest.mark.asyncio
async def test_expired_worker_lease_is_resumed_without_restarting_completed_stages() -> None:
    batch, actor = await synthetic_batch(1)
    async with SessionLocal() as db:
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=[batch.candidates[0].id],
            selection_mode="single",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        first = await claim_next_item(db, "interrupted-worker", lease_seconds=1)
        assert first is not None
        first.completed_stages = ["validate-raw-evidence", "normalize-facts"]
        first.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await db.commit()
        resumed = await claim_next_item(db, "replacement-worker")
        assert resumed is not None and resumed.id == first.id
        assert resumed.completed_stages == ["validate-raw-evidence", "normalize-facts"]
        assert resumed.attempt_count == 2
        assert job.selected_record_ids == [str(batch.candidates[0].id)]


def test_fact_guard_and_public_metadata_boundaries() -> None:
    facts = {"project_name": "Synthetic Project", "handover_year": 2030, "deposit": "20%"}
    assert overview_fact_guard(
        ("Synthetic Project is planned for 2030 with a 20% deposit.", "مشروع تجريبي 2030 20%"),
        facts,
    )["passed"]
    blocked = overview_fact_guard(
        ("Guaranteed 40% return on investment from Tanami.", "عائد 40%"),
        facts,
    )
    assert not blocked["passed"]
    unsupported_entity = overview_fact_guard(
        (
            "Synthetic Project is located in Palm Jumeirah by Imaginary Developer.",
            "مشروع تجريبي",
        ),
        facts,
    )
    assert not unsupported_entity["passed"]
    assert unsupported_entity["unsupported_locations"] == ["Palm Jumeirah"]
    assert "Imaginary Developer" in unsupported_entity["unsupported_names"]
    metadata = public_media_metadata(
        project_name="Synthetic Project",
        category="Exterior",
        title="Synthetic exterior",
        description="Synthetic fixture description.",
        website="https://example.invalid",
    )
    assert metadata["Publisher"] == "ALIYAS Real Estate"
    assert "Creator" not in metadata
    assert "Copyright" not in metadata
    assert "source" not in " ".join(metadata).casefold()
    assert descriptive_media_filename("Synthetic Project", "Exterior", 1) == (
        "synthetic-project-exterior-01.webp"
    )


@pytest.mark.asyncio
async def test_retry_only_failed_resumes_at_failed_stage() -> None:
    batch, actor = await synthetic_batch(1)
    async with SessionLocal() as db:
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=[batch.candidates[0].id],
            selection_mode="single",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        item = await claim_next_item(db, "qa-worker")
        assert item is not None
        await process_claimed_item(
            db,
            item.id,
            provider=DeterministicSyntheticOverviewProvider(),
        )
        loaded = await job_detail(db, job.id)
        failed = loaded.items[0]
        assert failed.status == ProcessingItemStatus.FAILED
        assert failed.current_stage == "prepare-overview"
        assert "validate-market-status" in failed.completed_stages
        # Human approval is intentionally not a generic retryable failure.
        repeated = await retry_failed_items(db, job.id)
        assert repeated.items[0].status == ProcessingItemStatus.FAILED
        diagnostic = repeated.items[0].diagnostics[-1]
        await resolve_diagnostic(
            db,
            diagnostic.id,
            action="retry-overview",
            note="Retry only the failed Overview stage after operator review",
            actor_id=actor.id,
        )
        resumed = await job_detail(db, job.id)
        assert resumed.items[0].status == ProcessingItemStatus.QUEUED
        assert resumed.items[0].current_stage == "prepare-overview"
        assert "validate-market-status" in resumed.items[0].completed_stages


@pytest.mark.asyncio
async def test_overview_generation_preserves_human_edits_and_raises_conflict() -> None:
    batch, actor = await synthetic_batch(1)
    async with SessionLocal() as db:
        candidate = await db.scalar(
            select(ProjectImportCandidate)
            .where(ProjectImportCandidate.id == batch.candidates[0].id)
            .options(selectinload(ProjectImportCandidate.editorial_draft))
        )
        assert candidate is not None
        candidate.human_edited_fields = ["overview_en", "overview_ar"]
        candidate.editorial_draft = ProjectImportEditorialDraft(
            overview_en="Human English Overview",
            overview_ar="نظرة عامة عربية بشرية",
            source_version=candidate.content_hash,
            approval_status=EditorialApprovalStatus.NEEDS_REVIEW,
        )
        await db.commit()
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=[candidate.id],
            selection_mode="single",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        item = await claim_next_item(db, "qa-human-overview-worker")
        assert item is not None
        await process_claimed_item(
            db,
            item.id,
            provider=DeterministicSyntheticOverviewProvider(),
        )
        loaded = await job_detail(db, job.id)
        assert loaded.items[0].diagnostics[-1].error_code == "human_edited_conflict"
        await db.refresh(candidate, attribute_names=["editorial_draft"])
        assert candidate.editorial_draft is not None
        assert candidate.editorial_draft.overview_en == "Human English Overview"
        assert candidate.editorial_draft.overview_ar == "نظرة عامة عربية بشرية"


@pytest.mark.asyncio
async def test_rights_pending_blocks_ready_to_post() -> None:
    batch, actor = await synthetic_batch(1, complete=True)
    async with SessionLocal() as db:
        candidate = await db.scalar(
            select(ProjectImportCandidate)
            .where(ProjectImportCandidate.id == batch.candidates[0].id)
            .options(selectinload(ProjectImportCandidate.staged_media))
        )
        assert candidate is not None
        candidate.staged_media[0].rights_status = MediaRightsStatus.PENDING
        candidate.staged_media[0].rights_basis = None
        await db.commit()
        job = await create_processing_job(
            db,
            batch_id=batch.id,
            candidate_ids=[candidate.id],
            selection_mode="single",
            requested_action="clean-and-prepare",
            actor_id=actor.id,
            correlation_id=f"qa-{uuid.uuid4()}",
            idempotency_key=f"qa-{uuid.uuid4()}",
        )
        item = await claim_next_item(db, "qa-rights-worker")
        assert item is not None
        await process_claimed_item(
            db,
            item.id,
            provider=DeterministicSyntheticOverviewProvider(),
        )
        loaded = await job_detail(db, job.id)
        diagnostic = loaded.items[0].diagnostics[-1]
        assert diagnostic.error_code == "rights_approval_missing"
        assert loaded.items[0].current_stage == "final-cross-check"


@pytest.mark.asyncio
async def test_processing_permission_denial(client, create_user) -> None:
    email, password = await create_user("content-manager")
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    response = await client.get("/api/v1/admin/project-processing-jobs")
    assert response.status_code == 403
