from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import (
    AuditLog,
    EditorialApprovalStatus,
    ImportReviewStatus,
    Project,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportEditorialDraft,
    ProjectRevision,
    ProjectWorkflowStatus,
    PublicationStatus,
)
from app.project_bulk_workflow import ProjectBulkWorkflowInput
from tests.test_developer_cms import developer_payload
from tests.test_project_cms import authenticate, project_payload


def test_bulk_project_workflow_contract_is_bounded_and_explicit() -> None:
    candidate_ids = [uuid.uuid4() for _ in range(51)]
    with pytest.raises(ValidationError, match="at most 50"):
        ProjectBulkWorkflowInput.model_validate(
            {
                "action": "assign-standard-priority",
                "candidate_ids": candidate_ids,
                "expected_candidate_versions": {value: 1 for value in candidate_ids},
                "expected_content_versions": {value: "a" * 64 for value in candidate_ids},
                "idempotency_key": f"qa-bounded-{uuid.uuid4()}",
            }
        )
    one = uuid.uuid4()
    with pytest.raises(ValidationError, match="explicit PUBLISH confirmation"):
        ProjectBulkWorkflowInput.model_validate(
            {
                "action": "publish",
                "candidate_ids": [one],
                "expected_candidate_versions": {one: 1},
                "expected_content_versions": {one: "a" * 64},
                "idempotency_key": f"qa-confirm-{uuid.uuid4()}",
            }
        )


@pytest.mark.asyncio
async def test_bulk_project_workflow_is_gated_audited_atomic_and_idempotent(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    csrf = str(session["csrf_token"])
    developer = await client.post(
        "/api/v1/admin/developers",
        json=developer_payload(slug="qa-bulk-project-developer"),
        headers={"X-CSRF-Token": csrf},
    )
    assert developer.status_code == 201, developer.text
    developer_id = developer.json()["id"]
    assert (
        await client.post(
            f"/api/v1/admin/developers/{developer_id}/publish",
            headers={"X-CSRF-Token": csrf},
        )
    ).status_code == 200
    area = await client.post(
        "/api/v1/admin/areas",
        json={
            "slug": "qa-bulk-project-area",
            "name_en": "QA Bulk Project Area",
            "name_ar": "منطقة اختبار النشر الجماعي",
            "emirate": "Dubai",
            "status": "published",
            "aliases": [],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert area.status_code == 201, area.text
    project_data = project_payload(developer_id, area.json()["id"])
    project_data.update({"priority": None, "featured": False})
    created = await client.post(
        "/api/v1/admin/projects",
        json=project_data,
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    media_id = created.json()["media"][0]["id"]
    image = io.BytesIO()
    Image.new("RGB", (1600, 900), "#745238").save(image, "WEBP")
    uploaded = await client.post(
        f"/api/v1/admin/projects/{project_id}/media/{media_id}",
        files={"image": ("bulk-project.webp", image.getvalue(), "image/webp")},
        headers={"X-CSRF-Token": csrf},
    )
    assert uploaded.status_code == 200, uploaded.text
    project_data["media"][0].update(  # type: ignore[index, union-attr]
        {"id": media_id, "rights_status": "approved"}
    )
    saved = await client.put(
        f"/api/v1/admin/projects/{project_id}",
        json=project_data,
        headers={"X-CSRF-Token": csrf},
    )
    assert saved.status_code == 200, saved.text

    # Legacy acquisition rows can retain a normalized percentage without the
    # source wording required by the current input contract. That unsupported
    # optional value remains private and must not block a publication snapshot.
    async with SessionLocal() as db:
        project = await db.get(Project, uuid.UUID(project_id))
        assert project is not None
        project.down_payment_percentage = 10
        project.down_payment_source_value = None
        await db.commit()

    batch_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(
            ProjectImportBatch(
                id=batch_id,
                name="QA Bulk Project Workflow",
                source_reference="Private QA workflow evidence",
                manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
                adapter_version="qa",
                total_count=1,
                clean_count=1,
            )
        )
        db.add(
            ProjectImportCandidate(
                id=candidate_id,
                batch_id=batch_id,
                manifest_row_id=1,
                raw_source_payload={},
                owner_manifest_values={"owner_project_name": "QA Off-Plan Project"},
                normalized_payload={"project_name": "QA Off-Plan Project"},
                normalized_project_name="QA Off-Plan Project",
                proposed_developer_id=uuid.UUID(developer_id),
                proposed_area_id=uuid.UUID(area.json()["id"]),
                official_source_url="https://example.com/official-project",
                source_urls=["https://example.com/official-project"],
                last_verified_at=datetime.now(UTC),
                content_hash="d" * 64,
                review_status=ImportReviewStatus.READY_FOR_APPROVAL,
                linked_project_id=uuid.UUID(project_id),
                human_review_completed=True,
                arabic_review_required=False,
                validation_errors=[],
                conflict_reasons=[],
                editorial_draft=ProjectImportEditorialDraft(
                    overview_en="Approved disposable English QA Overview for bulk publication.",
                    overview_ar="نظرة عامة عربية مؤقتة ومعتمدة لاختبار النشر الجماعي.",
                    source_version="e" * 64,
                    approval_status=EditorialApprovalStatus.APPROVED,
                ),
            )
        )
        await db.commit()

    detail = await client.get(f"/api/v1/admin/project-imports/{batch_id}")
    assert detail.status_code == 200, detail.text
    workflow = detail.json()["project_workflow"][str(candidate_id)]
    candidate_version = detail.json()["all_candidate_versions"][str(candidate_id)]

    def payload(action: str, *, key: str | None = None) -> dict[str, object]:
        return {
            "action": action,
            "candidate_ids": [str(candidate_id)],
            "expected_candidate_versions": {str(candidate_id): candidate_version},
            "expected_content_versions": {str(candidate_id): workflow["content_version"]},
            "idempotency_key": key or f"qa-project-workflow-{uuid.uuid4()}",
            "checks": {},
            "media_permission_reference": None,
            "confirmation": "PUBLISH" if action == "publish" else None,
        }

    no_csrf = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=payload("assign-standard-priority"),
    )
    assert no_csrf.status_code == 403
    stale_payload = payload("assign-standard-priority")
    stale_payload["expected_content_versions"] = {str(candidate_id): "0" * 64}
    stale = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=stale_payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert stale.status_code == 409
    async with SessionLocal() as db:
        assert (await db.get(Project, uuid.UUID(project_id))).priority is None

    priority = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=payload("assign-standard-priority"),
        headers={"X-CSRF-Token": csrf},
    )
    assert priority.status_code == 200, priority.text
    detail = await client.get(f"/api/v1/admin/project-imports/{batch_id}")
    workflow = detail.json()["project_workflow"][str(candidate_id)]
    assert workflow["priority"] == "B"

    submitted = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=payload("submit-review"),
        headers={"X-CSRF-Token": csrf},
    )
    assert submitted.status_code == 200, submitted.text
    detail = await client.get(f"/api/v1/admin/project-imports/{batch_id}")
    workflow = detail.json()["project_workflow"][str(candidate_id)]
    assert workflow["workflow_status"] == "in-review"

    approval = payload("approve")
    approval["checks"] = {
        key: {"confirmed": True, "evidence_reference": "Private QA approval evidence"}
        for key in ("facts", "english", "arabic", "media_rights", "seo", "disclaimer", "preview")
    }
    approval["media_permission_reference"] = "Private QA licence permits website use"
    approved = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=approval,
        headers={"X-CSRF-Token": csrf},
    )
    assert approved.status_code == 200, approved.text
    detail = await client.get(f"/api/v1/admin/project-imports/{batch_id}")
    workflow = detail.json()["project_workflow"][str(candidate_id)]
    assert workflow["workflow_status"] == "approved"

    publish_key = f"qa-project-publish-{uuid.uuid4()}"
    publish = payload("publish", key=publish_key)
    published = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=publish,
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200, published.text
    replay = await client.post(
        f"/api/v1/admin/project-imports/{batch_id}/project-workflow",
        json=publish,
        headers={"X-CSRF-Token": csrf},
    )
    assert replay.status_code == 200
    assert replay.json() == published.json()

    async with SessionLocal() as db:
        project = await db.get(Project, uuid.UUID(project_id))
        candidate = await db.get(ProjectImportCandidate, candidate_id)
        assert project is not None and candidate is not None
        assert project.status == PublicationStatus.PUBLISHED
        assert project.workflow_status == ProjectWorkflowStatus.APPROVED
        assert project.priority.value == "B"
        assert candidate.review_status == ImportReviewStatus.MERGED
        revision = await db.get(ProjectRevision, project.active_revision_id)
        assert revision is not None
        assert revision.record_snapshot["down_payment_percentage"] is None
        assert revision.record_snapshot["down_payment_source_value"] is None
        assert (
            await db.scalar(
                select(func.count(ProjectRevision.id)).where(
                    ProjectRevision.project_id == project.id
                )
            )
        ) == 1
        audits = (
            await db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_id == project.id,
                    AuditLog.action.in_(
                        {
                            "project.priority.assign",
                            "project.review.submit",
                            "project.approve",
                            "project.publish",
                        }
                    ),
                )
            )
        ).all()
        assert len(audits) == 4
        assert all(item.actor_user_id and item.request_correlation_id for item in audits)
        assert all(item.before_summary and item.after_summary for item in audits)
        receipt = next(item for item in audits if item.action == "project.approve")
        assert receipt.metadata_summary["content_version"] == workflow["content_version"]
        assert len(receipt.metadata_summary["checks"]) == 7
    assert (
        await client.get("/api/v1/public/projects/qa-offplan-project?locale=en")
    ).status_code == 200
