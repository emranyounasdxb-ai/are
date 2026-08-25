from __future__ import annotations

import json
import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.db import SessionLocal
from app.manual_overviews import (
    ORIGIN,
    PACK_VERSION,
    build_fact_packet,
    create_overview_pack,
    import_overview_response,
    read_pack_content,
)
from app.models import (
    EditorialApprovalStatus,
    ImportReviewStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectOverviewPack,
    ProjectProcessingStatus,
    User,
)
from app.schemas import ManualOverviewResponse
from app.security import hash_password


async def _authenticate(client: AsyncClient, email: str, password: str) -> dict[str, object]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


async def _fixture(count: int = 2) -> tuple[ProjectImportBatch, User]:
    async with SessionLocal() as db:
        actor = User(
            email=f"manual-overview-{uuid.uuid4()}@qa.are-cms.invalid-example-domain.com",
            display_name="Manual Overview QA",
            password_hash=hash_password(f"Disposable-{uuid.uuid4()}!"),
        )
        batch = ProjectImportBatch(
            name=f"QA Manual Overview {uuid.uuid4()}",
            source_reference="private-synthetic-fixture",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="qa-v1",
            total_count=count,
        )
        for index in range(1, count + 1):
            batch.candidates.append(
                ProjectImportCandidate(
                    manifest_row_id=index,
                    raw_source_payload={
                        "source_url": "https://private.invalid/source",
                        "marketing_copy": "Private source wording " * 20,
                    },
                    normalized_payload={
                        "project_name": f"QA Residence {index}",
                        "project_name_ar": f"مسكن تجريبي {index}",
                        "emirate": "Dubai",
                        "property_types": ["apartment"],
                        "bedrooms": ["1", "2"],
                        "size_min": 500,
                        "size_max": 900,
                        "size_unit": "sqft",
                        "amenities": ["community garden"],
                        "source_value": "must stay private",
                        "availability_status": "unresolved",
                        "construction_status": "not-confirmed",
                    },
                    owner_manifest_values={"owner_project_name": f"QA Residence {index}"},
                    normalized_project_name=f"QA Residence {index}",
                    source_urls=["https://private.invalid/source"],
                    content_hash=f"{index:064x}",
                    review_status=ImportReviewStatus.NEEDS_REVIEW,
                    validation_errors=[],
                    conflict_reasons=[],
                )
            )
        db.add_all([actor, batch])
        await db.commit()
        return batch, actor


def _response(
    pack: ProjectOverviewPack, candidate: ProjectImportCandidate, **changes: object
) -> ManualOverviewResponse:
    item = next(value for value in pack.items if value.candidate_id == candidate.id)
    data: dict[str, object] = {
        "pack_id": str(pack.id),
        "pack_version": PACK_VERSION,
        "items": [
            {
                "pack_id": str(pack.id),
                "pack_version": PACK_VERSION,
                "candidate_id": str(candidate.id),
                "candidate_version": item.candidate_version,
                "fact_input_hash": item.fact_input_hash,
                "overview_en": (
                    "This residential project presents homes and community amenities from the "
                    "reviewed fact packet for careful editorial consideration only."
                ),
                "overview_ar": (
                    "يقدم هذا المشروع السكني منازل ومرافق مجتمعية واردة في حزمة الحقائق "
                    "المراجعة للنظر التحريري الدقيق فقط دون إضافة ادعاءات."
                ),
                "referenced_fact_fields": ["project_name", "amenities"],
                "origin": ORIGIN,
            }
        ],
    }
    data["items"][0].update(changes)  # type: ignore[index, union-attr]
    return ManualOverviewResponse.model_validate(data)


@pytest.mark.asyncio
async def test_pack_is_private_allowlisted_versioned_hashed_and_idempotent(
    test_settings: Settings,
) -> None:
    batch, actor = await _fixture(2)
    candidate_ids = [value.id for value in batch.candidates]
    versions = {value.id: value.review_version for value in batch.candidates}
    async with SessionLocal() as db:
        first = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=candidate_ids,
            expected_versions=versions,
            selection_mode="manual",
            actor_id=actor.id,
            idempotency_key="qa-manual-overview-idempotent",
        )
        await db.commit()
        repeated = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=candidate_ids,
            expected_versions=versions,
            selection_mode="manual",
            actor_id=actor.id,
            idempotency_key="qa-manual-overview-idempotent",
        )
        assert repeated.id == first.id
        payload = json.loads(read_pack_content(repeated, test_settings))
        assert payload["pack_version"] == PACK_VERSION
        assert len(payload["items"]) == 2
        serialized = json.dumps(payload).casefold()
        for forbidden in (
            "tanami",
            "https://",
            "source_url",
            "source_value",
            "private.invalid",
            "priority",
            "provider",
            "model",
        ):
            assert forbidden not in serialized
        assert repeated.pack_hash


@pytest.mark.asyncio
async def test_selection_limit_and_ineligible_reason_are_enforced(test_settings: Settings) -> None:
    batch, actor = await _fixture(2)
    batch.candidates[1].normalized_payload = None
    async with SessionLocal() as db:
        candidate = await db.get(ProjectImportCandidate, batch.candidates[1].id)
        assert candidate is not None
        candidate.normalized_payload = None
        await db.commit()
        pack = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=[value.id for value in batch.candidates],
            expected_versions={value.id: value.review_version for value in batch.candidates},
            selection_mode="first-50",
            actor_id=actor.id,
            idempotency_key="qa-manual-overview-ineligible",
        )
        assert pack.eligible_count == 1 and pack.ineligible_count == 1
        assert next(value for value in pack.items if not value.eligible).exclusion_reasons
        with pytest.raises(ValueError, match="at most 50"):
            await create_overview_pack(
                db,
                test_settings,
                batch_id=batch.id,
                candidate_ids=[uuid.uuid4() for _ in range(51)],
                expected_versions={},
                selection_mode="manual",
                actor_id=actor.id,
                idempotency_key="qa-manual-overview-over-limit",
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("count", "selection_mode"),
    [(1, "single"), (4, "manual"), (25, "first-25"), (50, "first-50"), (7, "all-filtered")],
)
async def test_supported_selection_modes_generate_explicit_bounded_packs(
    test_settings: Settings, count: int, selection_mode: str
) -> None:
    batch, actor = await _fixture(count)
    async with SessionLocal() as db:
        pack = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=[value.id for value in batch.candidates],
            expected_versions={value.id: 1 for value in batch.candidates},
            selection_mode=selection_mode,
            actor_id=actor.id,
            idempotency_key=f"qa-selection-{selection_mode}-{uuid.uuid4()}",
        )
        assert pack.selected_count == count
        assert pack.eligible_count == count
        assert [item.ordinal for item in pack.items] == list(range(1, count + 1))


@pytest.mark.asyncio
async def test_import_is_review_gated_and_exact_repeat_is_idempotent(
    test_settings: Settings,
) -> None:
    batch, actor = await _fixture(1)
    async with SessionLocal() as db:
        pack = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=[batch.candidates[0].id],
            expected_versions={batch.candidates[0].id: 1},
            selection_mode="single",
            actor_id=actor.id,
            idempotency_key="qa-manual-overview-import",
        )
        response = _response(pack, batch.candidates[0])
        result = await import_overview_response(
            db, pack=pack, response=response, correlation_id="qa-manual-import"
        )
        assert result["imported"] == 1 and result["failed"] == 0
        await db.commit()
        loaded = await db.scalar(
            select(ProjectImportCandidate)
            .where(ProjectImportCandidate.id == batch.candidates[0].id)
            .options(selectinload(ProjectImportCandidate.editorial_draft))
        )
        assert loaded and loaded.editorial_draft
        assert loaded.editorial_draft.origin == ORIGIN
        assert (
            loaded.editorial_draft.model_name is None
            and loaded.editorial_draft.model_version is None
        )
        assert loaded.editorial_draft.overview_pack_hash == pack.pack_hash
        assert loaded.editorial_draft.fact_input_version == "normalized-facts-v1"
        assert loaded.editorial_draft.approval_status == EditorialApprovalStatus.NEEDS_REVIEW
        assert loaded.processing_status == ProjectProcessingStatus.NEEDS_REVIEW
        assert loaded.last_successful_stage == "prepare-overview"
        repeated = await import_overview_response(
            db, pack=pack, response=response, correlation_id="qa-manual-repeat"
        )
        assert repeated["results"][0]["status"] == "unchanged"  # type: ignore[index]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"fact_input_hash": "f" * 64}, "fact-hash-mismatch"),
        ({"candidate_version": 999}, "stale-candidate-version"),
        ({"referenced_fact_fields": ["source_url"]}, "unsupported-fact-reference"),
        (
            {
                "overview_en": (
                    "Guaranteed return on investment from this project is presented with private "
                    "source details for buyers."
                )
            },
            "unsupported-or-private-claim",
        ),
        (
            {
                "overview_ar": (
                    "Arabic text is not present in this deliberately invalid editorial response "
                    "and factual review."
                )
            },
            "language-equivalence-review-required",
        ),
    ],
)
async def test_import_rejects_stale_private_unsupported_and_language_failures(
    test_settings: Settings, changes: dict[str, object], expected: str
) -> None:
    batch, actor = await _fixture(1)
    async with SessionLocal() as db:
        pack = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=[batch.candidates[0].id],
            expected_versions={batch.candidates[0].id: 1},
            selection_mode="single",
            actor_id=actor.id,
            idempotency_key=f"qa-manual-reject-{uuid.uuid4()}",
        )
        response = _response(pack, batch.candidates[0], **changes)
        result = await import_overview_response(
            db, pack=pack, response=response, correlation_id="qa-manual-reject"
        )
        assert result["imported"] == 0 and result["failed"] == 1
        assert result["results"][0]["code"] == expected  # type: ignore[index]


@pytest.mark.asyncio
async def test_partial_success_and_human_edit_conflict(test_settings: Settings) -> None:
    batch, actor = await _fixture(2)
    async with SessionLocal() as db:
        pack = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=[value.id for value in batch.candidates],
            expected_versions={value.id: 1 for value in batch.candidates},
            selection_mode="manual",
            actor_id=actor.id,
            idempotency_key="qa-manual-partial",
        )
        second = await db.get(ProjectImportCandidate, batch.candidates[1].id)
        assert second is not None
        second.human_edited_fields = ["amenities"]
        response_one = _response(pack, batch.candidates[0]).items[0]
        response_two = _response(pack, batch.candidates[1]).items[0]
        response = ManualOverviewResponse(
            pack_id=pack.id, pack_version=PACK_VERSION, items=[response_one, response_two]
        )
        result = await import_overview_response(
            db, pack=pack, response=response, correlation_id="qa-manual-partial"
        )
        assert result["imported"] == 1 and result["failed"] == 1
        assert result["results"][1]["code"] == "human-edited-conflict"  # type: ignore[index]


@pytest.mark.asyncio
async def test_failed_item_can_be_retried_without_discarding_success(
    test_settings: Settings,
) -> None:
    batch, actor = await _fixture(1)
    async with SessionLocal() as db:
        pack = await create_overview_pack(
            db,
            test_settings,
            batch_id=batch.id,
            candidate_ids=[batch.candidates[0].id],
            expected_versions={batch.candidates[0].id: 1},
            selection_mode="single",
            actor_id=actor.id,
            idempotency_key="qa-manual-retry-failed",
        )
        failed_response = _response(
            pack,
            batch.candidates[0],
            overview_en=(
                "This reviewed project claims 999 unsupported homes in an intentionally invalid "
                "editorial draft that must be rejected safely."
            ),
            overview_ar=(
                "يدعي هذا المشروع المراجع وجود 999 منزلاً غير مدعوم في مسودة تحريرية غير صالحة "
                "يجب رفضها بأمان دون حفظها."
            ),
        )
        failed = await import_overview_response(
            db, pack=pack, response=failed_response, correlation_id="qa-manual-failed"
        )
        assert failed["results"][0]["code"] == "english-fact-guard-failure"  # type: ignore[index]
        corrected = await import_overview_response(
            db,
            pack=pack,
            response=_response(pack, batch.candidates[0]),
            correlation_id="qa-manual-retried",
        )
        assert corrected["imported"] == 1 and corrected["failed"] == 0


def test_response_schema_rejects_missing_provenance_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ManualOverviewResponse.model_validate(
            {"pack_id": str(uuid.uuid4()), "pack_version": PACK_VERSION, "items": [{"extra": True}]}
        )


@pytest.mark.asyncio
async def test_admin_pack_endpoints_enforce_rbac_and_csrf(client: AsyncClient, create_user) -> None:
    batch, _ = await _fixture(1)
    limited_email, limited_password = await create_user("content-manager")
    limited = await _authenticate(client, limited_email, limited_password)
    denied = await client.get(f"/api/v1/admin/project-imports/{batch.id}/overview-packs")
    assert denied.status_code == 403
    await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": str(limited["csrf_token"])})

    email, password = await create_user("super-admin")
    session = await _authenticate(client, email, password)
    payload = {
        "selection_mode": "single",
        "candidate_ids": [str(batch.candidates[0].id)],
        "expected_versions": {str(batch.candidates[0].id): 1},
        "idempotency_key": f"qa-api-pack-{uuid.uuid4()}",
    }
    missing_csrf = await client.post(
        f"/api/v1/admin/project-imports/{batch.id}/overview-packs", json=payload
    )
    assert missing_csrf.status_code == 403
    created = await client.post(
        f"/api/v1/admin/project-imports/{batch.id}/overview-packs",
        json=payload,
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert created.status_code == 200, created.text
    downloaded = await client.post(
        f"/api/v1/admin/project-overview-packs/{created.json()['id']}/download",
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert downloaded.status_code == 200
    assert downloaded.headers["cache-control"] == "private, no-store, max-age=0"
    assert b"private.invalid" not in downloaded.content


def test_fact_packet_excludes_private_and_unconfirmed_values() -> None:
    candidate = ProjectImportCandidate(
        normalized_payload={
            "project_name": "Safe",
            "source_url": "private",
            "availability_status": "unresolved",
            "construction_status": "not-confirmed",
        },
    )
    facts = build_fact_packet(candidate)
    assert facts == {
        "project_name": "Safe",
        "unresolved_fields": ["availability_status", "construction_status"],
    }
