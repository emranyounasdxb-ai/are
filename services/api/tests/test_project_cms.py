from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    AuditLog,
    ImportReviewStatus,
    Project,
    ProjectImportBatch,
    ProjectImportCandidate,
)
from app.schemas import PaymentPlanInput


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
    developers = await client.get("/api/v1/admin/developers?page_size=1")
    developer_id = developers.json()["items"][0]["id"]
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
    assert (await client.get("/api/v1/public/projects?locale=en")).json()["meta"]["total"] == 0
    image = io.BytesIO()
    Image.new("RGB", (640, 360), "#745238").save(image, "WEBP")
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
    submitted = await client.post(
        f"/api/v1/admin/projects/{project_id}/submit-review",
        headers={"X-CSRF-Token": csrf},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["workflow_status"] == "in-review"
    approved = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve",
        headers={"X-CSRF-Token": csrf},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["workflow_status"] == "approved"
    published = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={**payload, "status": "published"},
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200, published.text
    public = await client.get("/api/v1/public/projects/qa-offplan-project?locale=en")
    assert public.status_code == 200, public.text
    public_record = public.json()
    assert public_record["cta"] == "register-interest"
    assert "priority" not in public_record
    assert "internal_notes" not in public_record
    assert "price" not in public_record
    assert "raw_source_payload" not in public_record
    assert "sources" not in public_record
    assert "workflow_status" not in public_record
    assert "down_payment_source_value" not in public_record
    assert "source_id" not in public_record["payment_plan"]
    assert "source_value" not in public_record["payment_plan"]["milestones"][0]
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
                validation_errors=[],
                conflict_reasons=[],
                arabic_review_required=False,
                human_review_completed=True,
                review_status=ImportReviewStatus.NEEDS_REVIEW,
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
        candidate = await db.get(ProjectImportCandidate, candidate_id)
        assert candidate is not None
        assert candidate.review_status == ImportReviewStatus.MERGED
        assert candidate.linked_project_id is not None
        project = await db.get(Project, candidate.linked_project_id)
        assert project is not None
        assert project.status.value == "draft"
        assert project.priority is None
        audit = await db.scalar(select(AuditLog).where(AuditLog.entity_id == candidate_id).limit(1))
        assert audit is not None
        assert "raw_source_payload" not in str(audit.after_summary)
