from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.acquisition.targeted_evidence import persist_targeted_review, review_observations
from app.db import SessionLocal
from app.import_review import _is_neutral_conceptual_cover, sync_linked_draft_from_candidate
from app.models import (
    AuditLog,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    Project,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportEditorialDraft,
    ProjectImportMedia,
    ProjectMedia,
    ProjectMediaCategory,
)
from app.schemas import PaymentPlanInput
from tests.test_developer_cms import developer_payload


def test_only_the_known_neutral_conceptual_cover_is_replaced_by_exact_media() -> None:
    neutral = ProjectMedia(
        category=ProjectMediaCategory.COVER,
        source_url="owner-approved:aliyas-neutral-cover-temporary-private-preview-20260827",
    )
    owner_exact = ProjectMedia(
        category=ProjectMediaCategory.COVER,
        source_url="owner-approved:project-specific-authorized-render",
    )
    gallery = ProjectMedia(
        category=ProjectMediaCategory.GALLERY,
        source_url="owner-approved:aliyas-neutral-cover-temporary-private-preview-20260827",
    )

    assert _is_neutral_conceptual_cover(neutral)
    assert not _is_neutral_conceptual_cover(owner_exact)
    assert not _is_neutral_conceptual_cover(gallery)


async def authenticate(client: AsyncClient, email: str, password: str) -> dict[str, object]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def translation(name: str) -> dict[str, str]:
    return {
        "official_name": name,
        "short_summary": "Disposable project summary for integration testing.",
        "full_description": "Disposable project description used only in the isolated QA database.",
        "seo_title": name,
        "seo_description": "Disposable project metadata for integration testing only.",
    }


def project_payload(developer_id: str, area_id: str, status: str = "draft") -> dict[str, object]:
    checked_at = datetime.now(UTC).isoformat()
    return {
        "slug": "qa-offplan-project",
        "developer_id": developer_id,
        "area_id": area_id,
        "emirate": "Dubai",
        "status": status,
        "availability_status": "coming-soon",
        "construction_status": "not-confirmed",
        "handover_quarter": None,
        "handover_year": None,
        "original_handover_value": None,
        "size_min": "800",
        "size_max": "1600",
        "size_unit": "sqft",
        "down_payment_percentage": "20",
        "down_payment_source_value": "20% down payment",
        "latitude": "25.204849",
        "longitude": "55.270783",
        "last_verified_at": checked_at,
        "priority": "A",
        "featured": True,
        "display_order": 1,
        "internal_notes": "Disposable QA note.",
        "property_types": ["apartment", "penthouse"],
        "bedroom_options": ["1", "2", "3"],
        "unit_types": [{"label_en": "Type A", "label_ar": "النوع أ", "display_order": 0}],
        "amenities": [{"label_en": "Pool", "label_ar": "مسبح", "display_order": 0}],
        "nearby_places": [
            {
                "name_en": "QA Landmark",
                "name_ar": "معلم اختباري",
                "distance_value": "2.5",
                "distance_unit": "km",
                "travel_time_minutes": 8,
                "display_order": 0,
            }
        ],
        "translations": {
            "en": translation("QA Off-Plan Project"),
            "ar": translation("QA Off-Plan Project"),
        },
        "sources": [
            {
                "source_url": "https://example.com/official-project",
                "source_type": "OFFICIAL_DEVELOPER_PAGE",
                "is_official": True,
                "retrieved_at": checked_at,
                "last_checked_at": checked_at,
                "content_hash": "a" * 64,
                "source_title": "Official disposable source",
                "source_developer_domain": "example.com",
                "is_active": True,
            }
        ],
        "payment_plan": {
            "raw_source_text": "20 percent booking and 80 percent handover.",
            "source_index": 0,
            "is_complete": True,
            "verified_at": checked_at,
            "milestones": [
                {
                    "sequence": 1,
                    "stage": "booking",
                    "label_en": "Booking",
                    "label_ar": None,
                    "percentage": "20",
                    "due_trigger": "On booking",
                    "source_value": "20% booking",
                },
                {
                    "sequence": 2,
                    "stage": "handover",
                    "label_en": "Handover",
                    "label_ar": None,
                    "percentage": "80",
                    "due_trigger": "On handover",
                    "source_value": "80% handover",
                },
            ],
        },
        "media": [
            {
                "category": "cover",
                "source_url": "https://example.com/approved-cover.webp",
                "rights_status": "approved",
                "alt_en": "Disposable project cover",
                "alt_ar": "غلاف مشروع مؤقت",
                "display_order": 0,
                "verified_at": checked_at,
            }
        ],
    }


def test_complete_payment_plan_requires_exact_total() -> None:
    payload = project_payload(str(uuid.uuid4()), str(uuid.uuid4()))["payment_plan"]
    assert isinstance(payload, dict)
    payload["milestones"][1]["percentage"] = "79"  # type: ignore[index]
    with pytest.raises(ValueError, match="100%"):
        PaymentPlanInput.model_validate(payload)


@pytest.mark.asyncio
async def test_project_rbac_publication_and_public_field_boundaries(
    client: AsyncClient, create_user
) -> None:
    limited_email, limited_password = await create_user("content-manager")
    limited = await authenticate(client, limited_email, limited_password)
    denied = await client.get("/api/v1/admin/projects")
    assert denied.status_code == 403
    await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": str(limited["csrf_token"])})

    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    csrf = str(session["csrf_token"])
    developer = await client.post(
        "/api/v1/admin/developers",
        json=developer_payload(slug="qa-project-developer"),
        headers={"X-CSRF-Token": csrf},
    )
    assert developer.status_code == 201, developer.text
    developer_id = developer.json()["id"]
    developer_published = await client.post(
        f"/api/v1/admin/developers/{developer_id}/publish",
        headers={"X-CSRF-Token": csrf},
    )
    assert developer_published.status_code == 200, developer_published.text
    area = await client.post(
        "/api/v1/admin/areas",
        json={
            "slug": "qa-project-area",
            "name_en": "QA Project Area",
            "name_ar": "منطقة اختبار",
            "emirate": "Dubai",
            "status": "published",
            "aliases": [{"alias": "QA, Project Area", "locale": "en"}],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert area.status_code == 201, area.text
    payload = project_payload(developer_id, area.json()["id"])
    mismatch = await client.post(
        "/api/v1/admin/projects",
        json={**payload, "emirate": "Abu Dhabi"},
        headers={"X-CSRF-Token": csrf},
    )
    assert mismatch.status_code == 422
    assert mismatch.json()["error"]["code"] == "project_area_emirate_mismatch"
    payload["media"][0]["rights_status"] = "pending"  # type: ignore[index]
    direct_publish = await client.post(
        "/api/v1/admin/projects",
        json={**payload, "status": "published"},
        headers={"X-CSRF-Token": csrf},
    )
    assert direct_publish.status_code == 422
    created = await client.post(
        "/api/v1/admin/projects", json=payload, headers={"X-CSRF-Token": csrf}
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    media_id = created.json()["media"][0]["id"]
    async with SessionLocal() as db:
        review_batch = ProjectImportBatch(
            name="QA private targeted review",
            source_reference="QA",
            manifest_hash=uuid.uuid4().hex * 2,
            adapter_version="qa",
        )
        db.add(review_batch)
        await db.flush()
        review_candidate = ProjectImportCandidate(
            batch_id=review_batch.id,
            manifest_row_id=1,
            raw_source_payload={},
            owner_manifest_values={},
            normalized_payload={},
            content_hash="f" * 64,
            review_status=ImportReviewStatus.NEEDS_REVIEW,
            linked_project_id=uuid.UUID(project_id),
        )
        db.add(review_candidate)
        await db.flush()
        preview = review_observations(
            [],
            {},
            exact_context="QA exact project context",
            requested_fields={"construction_status"},
        )
        assert await persist_targeted_review(
            db, review_candidate, preview, expected_version=review_candidate.review_version
        )
        await db.commit()
        assert not await persist_targeted_review(
            db, review_candidate, preview, expected_version=review_candidate.review_version
        )
        assert review_candidate.normalized_payload == {}
        with pytest.raises(ValueError, match="stale or has been altered"):
            await persist_targeted_review(
                db,
                review_candidate,
                {**preview, "review_hash": "0" * 64},
                expected_version=review_candidate.review_version,
            )
        with pytest.raises(ValueError, match="stale or has been altered"):
            await persist_targeted_review(
                db,
                review_candidate,
                {**preview, "states": {"construction_status": "verified"}},
                expected_version=review_candidate.review_version,
            )
        assert (
            len(
                (
                    await db.scalars(
                        select(AuditLog).where(AuditLog.entity_id == review_candidate.id)
                    )
                ).all()
            )
            == 1
        )
        await db.delete(review_candidate)
        await db.commit()
    assert (await client.get("/api/v1/public/projects?locale=en")).json()["meta"]["total"] == 0
    image = io.BytesIO()
    Image.new("RGB", (1600, 900), "#745238").save(image, "WEBP")
    uploaded = await client.post(
        f"/api/v1/admin/projects/{project_id}/media/{media_id}",
        files={"image": ("project.webp", image.getvalue(), "image/webp")},
        headers={"X-CSRF-Token": csrf},
    )
    assert uploaded.status_code == 200, uploaded.text
    payload["media"][0]["id"] = media_id  # type: ignore[index]
    payload["media"][0]["rights_status"] = "approved"  # type: ignore[index]
    payload["sources"][0]["content_hash"] = "c" * 64  # type: ignore[index]
    saved = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json=payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert saved.status_code == 200, saved.text
    preview = await client.get(f"/api/v1/admin/projects/{project_id}/preview?locale=en")
    assert preview.status_code == 200, preview.text
    preview_record = preview.json()
    assert preview_record["official_name"] == "QA Off-Plan Project"
    assert preview_record["media"] == []  # No documented permission receipt yet.
    assert "construction_status" not in preview_record
    assert "priority" not in preview_record
    assert "internal_notes" not in preview_record
    assert "sources" not in preview_record
    assert "workflow_status" not in preview_record
    preview_media = await client.get(
        f"/api/v1/admin/projects/{project_id}/preview-media/{media_id}"
    )
    assert preview_media.status_code == 404  # Metadata approval alone grants no binary access.
    submitted = await client.post(
        f"/api/v1/admin/projects/{project_id}/submit-review",
        headers={"X-CSRF-Token": csrf},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["workflow_status"] == "in-review"
    review = (await client.get(f"/api/v1/admin/projects/{project_id}/approval-review")).json()
    review_payload = {
        "content_version": review["content_version"],
        "checks": {
            key: {"confirmed": True, "evidence_reference": "Private synthetic QA review evidence"}
            for key in review["required_checks"]
        },
        "media_permissions": {
            item["sha256"]: "Synthetic QA licence; web use permitted" for item in review["media"]
        },
    }
    no_csrf = await client.post(f"/api/v1/admin/projects/{project_id}/approve", json=review_payload)
    assert no_csrf.status_code == 403
    incomplete = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve",
        json={**review_payload, "checks": {}},
        headers={"X-CSRF-Token": csrf},
    )
    assert incomplete.status_code == 422
    stale = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve",
        json={**review_payload, "content_version": "0" * 64},
        headers={"X-CSRF-Token": csrf},
    )
    assert stale.status_code == 409
    no_permission_evidence = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve",
        json={**review_payload, "media_permissions": {}},
        headers={"X-CSRF-Token": csrf},
    )
    assert no_permission_evidence.status_code == 422
    for invalid_reference in (
        "   Automatically approved by scraping pipeline",
        "https://developer.example.com/project/image.webp",
    ):
        inferred_permission = await client.post(
            f"/api/v1/admin/projects/{project_id}/approve",
            json={
                **review_payload,
                "media_permissions": {
                    item["sha256"]: invalid_reference for item in review["media"]
                },
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert inferred_permission.status_code == 422
    approved = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve",
        json=review_payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["workflow_status"] == "approved"
    reviewed_preview = await client.get(f"/api/v1/admin/projects/{project_id}/preview?locale=en")
    assert reviewed_preview.json()["media"][0]["url"].endswith(
        f"/admin/projects/{project_id}/preview-media/{media_id}"
    )
    permitted_media = await client.get(
        f"/api/v1/admin/projects/{project_id}/preview-media/{media_id}"
    )
    assert permitted_media.status_code == 200
    assert permitted_media.headers["cache-control"] == "private, no-store, max-age=0"
    receipt = (await client.get(f"/api/v1/admin/projects/{project_id}/approval-review")).json()[
        "receipt"
    ]
    assert receipt["current"] is True
    assert receipt["reviewer"] and receipt["reviewed_at"]
    assert (await client.get("/api/v1/public/projects?locale=en")).json()["meta"]["total"] == 0
    changed_image = io.BytesIO()
    Image.new("RGB", (1600, 900), "#335533").save(changed_image, "WEBP")
    replaced_image = await client.post(
        f"/api/v1/admin/projects/{project_id}/media/{media_id}",
        files={"image": ("replacement.webp", changed_image.getvalue(), "image/webp")},
        headers={"X-CSRF-Token": csrf},
    )
    assert replaced_image.status_code == 200
    changed_receipt = (
        await client.get(f"/api/v1/admin/projects/{project_id}/approval-review")
    ).json()["receipt"]
    assert changed_receipt["current"] is False
    replaced_publish = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={**payload, "status": "published"},
        headers={"X-CSRF-Token": csrf},
    )
    assert replaced_publish.status_code == 422
    restored_image = await client.post(
        f"/api/v1/admin/projects/{project_id}/media/{media_id}",
        files={"image": ("project.webp", image.getvalue(), "image/webp")},
        headers={"X-CSRF-Token": csrf},
    )
    assert restored_image.status_code == 200
    # Re-uploading even identical bytes creates a new private asset version.
    # It must be reviewed again, not silently inherit the previous receipt.
    resubmitted = await client.post(
        f"/api/v1/admin/projects/{project_id}/submit-review",
        headers={"X-CSRF-Token": csrf},
    )
    assert resubmitted.status_code == 200
    fresh_review = (await client.get(f"/api/v1/admin/projects/{project_id}/approval-review")).json()
    reapproved = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve",
        json={**review_payload, "content_version": fresh_review["content_version"]},
        headers={"X-CSRF-Token": csrf},
    )
    assert reapproved.status_code == 200, reapproved.text
    changed_publish = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={**payload, "status": "published", "display_order": 55},
        headers={"X-CSRF-Token": csrf},
    )
    assert changed_publish.status_code == 422
    published = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={**payload, "status": "published"},
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200, published.text
    public = await client.get("/api/v1/public/projects/qa-offplan-project?locale=en")
    assert public.status_code == 200, public.text
    public_record = public.json()
    assert public_record["emirate"] == "Dubai"
    assert public_record["area"]["emirate"] == "Dubai"
    assert "construction_status" not in public_record
    assert public_record["cta"] == "register-interest"
    assert "priority" not in public_record
    assert "internal_notes" not in public_record
    assert "price" not in public_record
    assert "raw_source_payload" not in public_record
    assert "sources" not in public_record
    assert "workflow_status" not in public_record
    assert "receipt" not in public_record
    assert "media_permissions" not in public_record
    assert "down_payment_source_value" not in public_record
    assert "source_id" not in public_record["payment_plan"]
    assert "source_value" not in public_record["payment_plan"]["milestones"][0]
    arabic = await client.get("/api/v1/public/projects/qa-offplan-project?locale=ar")
    assert arabic.status_code == 200
    assert arabic.json()["emirate"] == "دبي"
    assert arabic.json()["area"]["emirate"] == "دبي"
    assert (await client.get("/api/v1/admin/projects?emirate=Dubai")).json()["meta"]["total"] == 1
    fujairah = await client.get("/api/v1/admin/projects?emirate=Fujairah")
    assert fujairah.json()["meta"]["total"] == 0
    # Public reads must recheck an imported identity hold and media permission,
    # even when an older Project publication exists. Private source data stays private.
    async with SessionLocal() as db:
        evidence_batch = ProjectImportBatch(
            name="QA targeted visibility",
            source_reference="QA private evidence",
            manifest_hash=uuid.uuid4().hex * 2,
            adapter_version="qa",
        )
        db.add(evidence_batch)
        await db.flush()
        evidence_candidate = ProjectImportCandidate(
            batch_id=evidence_batch.id,
            manifest_row_id=1,
            raw_source_payload={},
            owner_manifest_values={},
            normalized_payload={},
            content_hash="d" * 64,
            review_status=ImportReviewStatus.NEEDS_REVIEW,
            linked_project_id=uuid.UUID(project_id),
            acquisition_summary={"targeted_field_review": {"identity_hold": True}},
        )
        db.add(evidence_candidate)
        await db.commit()
        candidate_id = evidence_candidate.id
    for locale in ("en", "ar"):
        assert (
            await client.get(f"/api/v1/public/projects/qa-offplan-project?locale={locale}")
        ).status_code == 404
        assert (await client.get(f"/api/v1/public/projects?locale={locale}")).json()["meta"][
            "total"
        ] == 0
    assert (
        await client.get(f"/api/v1/public/projects/qa-offplan-project/media/{media_id}")
    ).status_code == 404
    async with SessionLocal() as db:
        evidence_candidate = await db.get(ProjectImportCandidate, candidate_id)
        evidence_candidate.acquisition_summary = {
            "targeted_field_review": {
                "states": {
                    "payment_plan": "conflict",
                    "size_min": "unconfirmed",
                    "availability_status": "unconfirmed",
                }
            }
        }
        await db.commit()
    for locale in ("en", "ar"):
        safe_public = (
            await client.get(f"/api/v1/public/projects/qa-offplan-project?locale={locale}")
        ).json()
        assert "payment_plan" not in safe_public and "down_payment_percentage" not in safe_public
        assert "size_min" not in safe_public and "size_max" not in safe_public
        assert "availability_status" not in safe_public
        assert "targeted_field_review" not in str(safe_public)
    async with SessionLocal() as db:
        evidence_candidate = await db.get(ProjectImportCandidate, candidate_id)
        await db.delete(evidence_candidate)
        await db.commit()
    in_place = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={**payload, "status": "published", "display_order": 99},
        headers={"X-CSRF-Token": csrf},
    )
    assert in_place.status_code == 409
    revision_payload = {**payload, "status": "published", "display_order": 2}
    revision = await client.post(
        f"/api/v1/admin/projects/{project_id}/revisions",
        json={
            "project": revision_payload,
            "media_snapshot": [],
            "field_diff": {"display_order": {"before": 1, "after": 2}},
            "change_summary": "Disposable display-order revision",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert revision.status_code == 201, revision.text
    revision_id = revision.json()["id"]
    live_before_activation = await client.get(
        "/api/v1/public/projects/qa-offplan-project?locale=en"
    )
    assert live_before_activation.json()["display_order"] == 1
    for action in ("submit", "approve", "activate"):
        result = await client.post(
            f"/api/v1/admin/projects/{project_id}/revisions/{revision_id}/{action}",
            json={"note": f"Disposable {action} verification"},
            headers={"X-CSRF-Token": csrf},
        )
        assert result.status_code == 200, result.text
    assert (await client.get("/api/v1/public/projects/qa-offplan-project?locale=en")).json()[
        "display_order"
    ] == 2
    replacement_payload = {**payload, "status": "published", "display_order": 3}
    replacement = await client.post(
        f"/api/v1/admin/projects/{project_id}/revisions",
        json={
            "project": replacement_payload,
            "media_snapshot": [],
            "field_diff": {"display_order": {"before": 2, "after": 3}},
            "change_summary": "Disposable replacement revision",
        },
        headers={"X-CSRF-Token": csrf},
    )
    replacement_id = replacement.json()["id"]
    for action in ("submit", "approve", "activate"):
        result = await client.post(
            f"/api/v1/admin/projects/{project_id}/revisions/{replacement_id}/{action}",
            json={"note": f"Disposable replacement {action}"},
            headers={"X-CSRF-Token": csrf},
        )
        assert result.status_code == 200, result.text
    rollback = await client.post(
        f"/api/v1/admin/projects/{project_id}/revisions/{revision_id}/rollback",
        json={"note": "Disposable rollback verification"},
        headers={"X-CSRF-Token": csrf},
    )
    assert rollback.status_code == 200, rollback.text
    assert (await client.get("/api/v1/public/projects/qa-offplan-project?locale=en")).json()[
        "display_order"
    ] == 2
    archived = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={**payload, "status": "archived"},
        headers={"X-CSRF-Token": csrf},
    )
    assert archived.status_code == 200, archived.text
    assert (
        await client.get("/api/v1/public/projects/qa-offplan-project?locale=en")
    ).status_code == 404
    async with SessionLocal() as db:
        actions = set(
            await db.scalars(
                select(AuditLog.action).where(AuditLog.entity_id == uuid.UUID(project_id))
            )
        )
        assert {
            "project.review.submit",
            "project.approve",
            "project.publish",
            "project.source.update",
            "project.media-rights.update",
        } <= actions


@pytest.mark.asyncio
async def test_import_review_summary_bulk_readiness_and_draft_are_safe(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    csrf = str(session["csrf_token"])
    developer_id = (await client.get("/api/v1/admin/developers?page_size=1")).json()["items"][0][
        "id"
    ]
    area = await client.post(
        "/api/v1/admin/areas",
        json={
            "slug": "qa-import-area",
            "name_en": "QA Import Area",
            "name_ar": "منطقة استيراد مؤقتة",
            "emirate": "Dubai",
            "status": "draft",
            "aliases": [],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert area.status_code == 201, area.text
    batch_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    checked_at = datetime.now(UTC)
    async with SessionLocal() as db:
        batch = ProjectImportBatch(
            id=batch_id,
            name="QA Project Import",
            source_reference="data-intake/qa.csv",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="test",
            total_count=1,
            needs_review_count=1,
        )
        batch.candidates = [
            ProjectImportCandidate(
                id=candidate_id,
                manifest_row_id=1,
                raw_source_payload={"owner_project_name": "Unverified QA candidate"},
                normalized_payload={
                    "project_name": "QA Source-Grounded Project",
                    "project_name_ar": "مشروع اختبار موثق المصدر",
                    "property_types": ["apartment"],
                    "bedrooms": ["1"],
                    "handover_quarter": "Q4",
                    "handover_year": 2030,
                    "original_handover_value": "Q4 2030",
                    "payment_plan": None,
                    "availability_status": "coming-soon",
                    "construction_status": "pre-launch",
                },
                owner_manifest_values={
                    "owner_project_name": "QA Source-Grounded Project",
                    "owner_developer": "QA Developer",
                    "owner_area": "QA Import Area",
                },
                normalized_project_name="QA Source-Grounded Project",
                proposed_developer_id=uuid.UUID(developer_id),
                proposed_area_id=uuid.UUID(area.json()["id"]),
                official_source_url="https://example.com/official-project",
                source_urls=["https://example.com/official-project"],
                extracted_at=checked_at,
                last_verified_at=checked_at,
                content_hash="b" * 64,
                acquisition_summary={
                    "source_first_research": {
                        "exact_documents": ["https://example.com/official-project"],
                        "context_review_completed": True,
                    }
                },
                validation_errors=[],
                conflict_reasons=[],
                arabic_review_required=False,
                human_review_completed=True,
                review_status=ImportReviewStatus.NEEDS_REVIEW,
                editorial_draft=ProjectImportEditorialDraft(
                    overview_en=(
                        "This disposable English Overview is approved only for the isolated "
                        "Project import integration test and contains no market claim."
                    ),
                    overview_ar=(
                        "هذه نظرة عامة عربية مؤقتة ومعتمدة فقط لاختبار تكامل استيراد المشروع "
                        "المعزول ولا تتضمن أي ادعاء عن السوق."
                    ),
                    source_version="qa-source-version",
                    approval_status=EditorialApprovalStatus.APPROVED,
                ),
                staged_media=[
                    ProjectImportMedia(
                        category=ProjectMediaCategory.COVER,
                        source_url="https://example.com/qa-approved-cover.webp",
                        rights_status=MediaRightsStatus.APPROVED,
                        rights_basis="Owner-approved QA fixture permission.",
                        stage_status="downloaded",
                        storage_key=f"qa-{candidate_id}.webp",
                        thumbnail_storage_key=f"qa-thumb-{candidate_id}.webp",
                        mime_type="image/webp",
                        width=1600,
                        height=900,
                        normalized_filename="qa-source-grounded-project-cover-01.webp",
                        processed_sha256="c" * 64,
                        alt_en_draft="Cover image for QA Source-Grounded Project",
                        alt_ar_draft="الصورة الرئيسية — مشروع اختبار مصدر موثق",
                        title_en="QA Source-Grounded Project — Cover image",
                        title_ar="مشروع اختبار مصدر موثق — الصورة الرئيسية",
                        description_en="Cover image for QA Source-Grounded Project.",
                        description_ar="الصورة الرئيسية — مشروع اختبار مصدر موثق.",
                        tags=["QA Source-Grounded Project", "Cover image"],
                        derivative_manifest=[
                            {
                                "format": "webp",
                                "storage_key": f"qa-derivative-{candidate_id}.webp",
                            },
                            {
                                "format": "avif",
                                "storage_key": f"qa-derivative-{candidate_id}.avif",
                            },
                        ],
                    ),
                    ProjectImportMedia(
                        category=ProjectMediaCategory.GALLERY,
                        source_url="https://example.com/qa-rejected-gallery.webp",
                        rights_status=MediaRightsStatus.REJECTED,
                        stage_status="rejected-low-resolution",
                        width=800,
                        height=450,
                        failure_reason=(
                            "Image does not meet the minimum public-readiness dimensions."
                        ),
                    ),
                ],
            )
        ]
        db.add(batch)
        await db.commit()
    summary = await client.get(f"/api/v1/admin/project-imports/{batch_id}")
    assert summary.status_code == 200, summary.text
    assert "manifest_hash" not in summary.json()
    candidate_summary = summary.json()["candidates"][0]
    assert "raw_source_payload" not in candidate_summary
    assert "content_hash" not in candidate_summary
    detail = await client.get(f"/api/v1/admin/project-imports/{batch_id}/candidates/{candidate_id}")
    assert detail.status_code == 200
    assert detail.json()["raw_source_payload"]
    assert detail.json()["media_summary"] == {
        "total_acquired": 2,
        "approved": 1,
        "removed": 1,
    }
    assert detail.json()["automatic_recovery_needs_review"] is False
    assert len(detail.json()["staged_media"]) == 1
    assert detail.json()["staged_media"][0]["rights_status"] == "approved"
    assert detail.json()["overview_provider"] == {
        "state": "configuration-required",
        "message": "Provider configuration required",
        "required_environment_variables": [
            "ARE_OVERVIEW_AI_PROVIDER",
            "ARE_OVERVIEW_AI_MODEL",
            "ARE_OVERVIEW_AI_MODEL_VERSION",
            "ARE_OVERVIEW_AI_API_KEY",
        ],
    }
    preview = await client.get(
        f"/api/v1/admin/project-imports/{batch_id}/candidates/{candidate_id}/preview?locale=en"
    )
    assert preview.status_code == 200, preview.text
    preview_data = preview.json()
    assert preview_data["project_name"] == "QA Source-Grounded Project"
    assert preview_data["availability_status"] == "coming-soon"
    assert preview_data["construction_status"] == "pre-launch"
    assert len(preview_data["media"]) == 1
    assert preview_data["media"][0]["category"] == "cover"
    assert not {
        "source_urls",
        "official_source_url",
        "raw_source_payload",
        "validation_errors",
        "conflict_reasons",
        "priority",
    } & set(preview_data)
    arabic_preview = await client.get(
        f"/api/v1/admin/project-imports/{batch_id}/candidates/{candidate_id}/preview?locale=ar"
    )
    assert arabic_preview.status_code == 200, arabic_preview.text
    assert arabic_preview.json()["project_name"] == "مشروع اختبار موثق المصدر"

    missing_csrf = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/bulk",
        json={
            "action": "mark-ready",
            "candidate_ids": [str(candidate_id)],
            "expected_versions": {str(candidate_id): 1},
            "idempotency_key": f"qa-missing-{uuid.uuid4()}",
        },
    )
    assert missing_csrf.status_code == 403
    ready_payload = {
        "action": "mark-ready",
        "candidate_ids": [str(candidate_id)],
        "expected_versions": {str(candidate_id): 1},
        "idempotency_key": f"qa-ready-{uuid.uuid4()}",
    }
    ready = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/bulk",
        json=ready_payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert ready.status_code == 200, ready.text
    replay = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/bulk",
        json=ready_payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert replay.status_code == 200
    stale = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/bulk",
        json={**ready_payload, "idempotency_key": f"qa-stale-{uuid.uuid4()}"},
        headers={"X-CSRF-Token": csrf},
    )
    assert stale.status_code == 409
    drafts = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/bulk",
        json={
            "action": "create-drafts",
            "candidate_ids": [str(candidate_id)],
            "expected_versions": {str(candidate_id): 2},
            "idempotency_key": f"qa-draft-{uuid.uuid4()}",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert drafts.status_code == 200, drafts.text
    assert (await client.get("/api/v1/public/projects?locale=en")).json()["meta"]["total"] == 0
    async with SessionLocal() as db:
        candidate = await db.scalar(
            select(ProjectImportCandidate)
            .where(ProjectImportCandidate.id == candidate_id)
            .options(
                selectinload(ProjectImportCandidate.evidence),
                selectinload(ProjectImportCandidate.staged_media),
            )
        )
        assert candidate is not None
        assert candidate.review_status == ImportReviewStatus.MERGED
        assert candidate.linked_project_id is not None
        await sync_linked_draft_from_candidate(db, candidate)
        await db.flush()
        await sync_linked_draft_from_candidate(db, candidate)
        await db.commit()
        project = await db.get(Project, candidate.linked_project_id)
        assert project is not None
        assert project.status.value == "draft"
        assert project.priority is None
        audit = await db.scalar(select(AuditLog).where(AuditLog.entity_id == candidate_id).limit(1))
        assert audit is not None
        assert "raw_source_payload" not in str(audit.after_summary)
