from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import select

from app.area_workflow import AreaBulkWorkflowInput
from app.db import SessionLocal
from app.models import AreaCommunity, AuditLog, PublicationStatus
from tests.test_developer_cms import developer_payload
from tests.test_project_cms import authenticate, project_payload


def test_area_bulk_contract_is_bounded_and_explicit() -> None:
    area_ids = [uuid.uuid4() for _ in range(51)]
    with pytest.raises(ValidationError, match="at most 50"):
        AreaBulkWorkflowInput.model_validate(
            {
                "action": "submit-review",
                "area_ids": area_ids,
                "expected_content_versions": {value: "a" * 64 for value in area_ids},
                "idempotency_key": f"qa-area-bounded-{uuid.uuid4()}",
                "confirmation": "SUBMIT",
            }
        )
    one = uuid.uuid4()
    with pytest.raises(ValidationError, match="explicit PUBLISH confirmation"):
        AreaBulkWorkflowInput.model_validate(
            {
                "action": "publish",
                "area_ids": [one],
                "expected_content_versions": {one: "a" * 64},
                "idempotency_key": f"qa-area-confirm-{uuid.uuid4()}",
                "confirmation": "APPROVE",
            }
        )


@pytest.mark.asyncio
async def test_area_approval_requires_project_publish_permission(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("content-manager")
    session = await authenticate(client, email, password)
    area_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json={
            "action": "approve",
            "area_ids": [str(area_id)],
            "expected_content_versions": {str(area_id): "a" * 64},
            "idempotency_key": f"qa-area-permission-{uuid.uuid4()}",
            "confirmation": "APPROVE",
        },
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_area_workflow_is_authenticated_atomic_audited_and_idempotent(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    csrf = str(session["csrf_token"])
    developer = await client.post(
        "/api/v1/admin/developers",
        json=developer_payload(slug="qa-area-workflow-developer"),
        headers={"X-CSRF-Token": csrf},
    )
    assert developer.status_code == 201, developer.text
    area = await client.post(
        "/api/v1/admin/areas",
        json={
            "slug": "qa-area-workflow",
            "name_en": "QA Area Workflow",
            "name_ar": "منطقة اختبار سير العمل",
            "emirate": "Sharjah",
            "status": "draft",
            "aliases": [{"alias": "QA Workflow Area", "locale": "en"}],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert area.status_code == 201, area.text
    area_id = area.json()["id"]
    project_data = project_payload(developer.json()["id"], area_id)
    project_data["emirate"] = "Sharjah"
    project = await client.post(
        "/api/v1/admin/projects",
        json=project_data,
        headers={"X-CSRF-Token": csrf},
    )
    assert project.status_code == 201, project.text
    unreferenced = await client.post(
        "/api/v1/admin/areas",
        json={
            "slug": "qa-area-workflow-unreferenced",
            "name_en": "QA Unreferenced Area",
            "name_ar": "منطقة اختبار غير مرتبطة",
            "emirate": "Sharjah",
            "status": "draft",
            "aliases": [],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert unreferenced.status_code == 201, unreferenced.text

    detail = await client.get(f"/api/v1/admin/areas/{area_id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["workflow"]["workflow_status"] == "draft"
    assert detail.json()["workflow"]["referenced_project_count"] == 1
    version = detail.json()["workflow"]["content_version"]

    def payload(
        action: str,
        *,
        key: str | None = None,
        ids: list[str] | None = None,
        versions: dict[str, str] | None = None,
    ) -> dict[str, object]:
        selected = ids or [area_id]
        return {
            "action": action,
            "area_ids": selected,
            "expected_content_versions": versions or {area_id: version},
            "idempotency_key": key or f"qa-area-workflow-{uuid.uuid4()}",
            "confirmation": {
                "submit-review": "SUBMIT",
                "approve": "APPROVE",
                "publish": "PUBLISH",
            }[action],
        }

    no_csrf = await client.post("/api/v1/admin/areas/bulk-workflow", json=payload("submit-review"))
    assert no_csrf.status_code == 403
    stale = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json=payload("submit-review", versions={area_id: "0" * 64}),
        headers={"X-CSRF-Token": csrf},
    )
    assert stale.status_code == 409

    other_id = unreferenced.json()["id"]
    other_detail = await client.get(f"/api/v1/admin/areas/{other_id}")
    atomic = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json=payload(
            "submit-review",
            ids=[area_id, other_id],
            versions={
                area_id: version,
                other_id: other_detail.json()["workflow"]["content_version"],
            },
        ),
        headers={"X-CSRF-Token": csrf},
    )
    assert atomic.status_code == 422
    assert (await client.get(f"/api/v1/admin/areas/{area_id}")).json()["workflow"][
        "workflow_status"
    ] == "draft"

    submitted = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json=payload("submit-review"),
        headers={"X-CSRF-Token": csrf},
    )
    assert submitted.status_code == 200, submitted.text
    approved = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json=payload("approve"),
        headers={"X-CSRF-Token": csrf},
    )
    assert approved.status_code == 200, approved.text
    approved_detail = (await client.get(f"/api/v1/admin/areas/{area_id}")).json()
    assert approved_detail["workflow"]["workflow_status"] == "approved"
    assert approved_detail["workflow"]["receipt"]["current"] is True

    key = f"qa-area-publish-{uuid.uuid4()}"
    published = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json=payload("publish", key=key),
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200, published.text
    repeated = await client.post(
        "/api/v1/admin/areas/bulk-workflow",
        json=payload("publish", key=key),
        headers={"X-CSRF-Token": csrf},
    )
    assert repeated.status_code == 200
    assert repeated.json() == published.json()
    final = (await client.get(f"/api/v1/admin/areas/{area_id}")).json()
    assert final["status"] == "published"
    rejected_edit = await client.put(
        f"/api/v1/admin/areas/{area_id}",
        json={
            "slug": final["slug"],
            "name_en": final["name_en"],
            "name_ar": final["name_ar"],
            "emirate": final["emirate"],
            "aliases": [
                {"alias": item["alias"], "locale": item["locale"]} for item in final["aliases"]
            ],
            "expected_content_version": final["workflow"]["content_version"],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert rejected_edit.status_code == 409

    async with SessionLocal() as db:
        stored = await db.get(AreaCommunity, uuid.UUID(area_id))
        assert stored is not None and stored.status == PublicationStatus.PUBLISHED
        actions = set(
            await db.scalars(
                select(AuditLog.action).where(
                    AuditLog.entity_type == "area", AuditLog.entity_id == stored.id
                )
            )
        )
        assert {"area.review.submit", "area.approve", "area.publish"} <= actions
