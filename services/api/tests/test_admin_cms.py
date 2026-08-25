from __future__ import annotations

import io
from copy import deepcopy

import pytest
from httpx import AsyncClient
from PIL import Image


async def authenticate(client: AsyncClient, email: str, password: str) -> dict[str, object]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def property_payload(status: str = "draft") -> dict[str, object]:
    return {
        "slug": "qa-source-verified-home",
        "purpose": "buy",
        "property_type": "Apartment",
        "emirate": "Dubai",
        "community": "QA community",
        "developer": None,
        "bedrooms": 2,
        "bathrooms": 2,
        "area": "1200.00",
        "area_unit": "sqft",
        "price": None,
        "price_on_request": True,
        "currency": "AED",
        "featured": False,
        "provenance_note": "Disposable integration-test evidence only.",
        "external_reference_url": None,
        "status": status,
        "translations": {
            "en": {
                "title": "QA verified home",
                "description": "Disposable English integration-test content.",
            },
            "ar": {
                "title": "منزل اختبار موثق",
                "description": "محتوى عربي مؤقت لاختبار التكامل فقط.",
            },
        },
    }


def insight_payload(status: str = "draft") -> dict[str, object]:
    return {
        "slug": "qa-approved-insight",
        "category": "guides",
        "author_display_name": "ALIYAS Real Estate",
        "source_links": [{"name": "Official QA source", "url": "https://example.com/qa"}],
        "status": status,
        "translations": {
            "en": {
                "title": "QA insight",
                "excerpt": "Disposable English excerpt for integration testing.",
                "body": {"paragraphs": ["Disposable body."]},
                "seo_title": "QA insight",
                "seo_description": "Disposable English metadata for integration testing.",
            },
            "ar": {
                "title": "مقال اختبار",
                "excerpt": "مقتطف عربي مؤقت لاختبار التكامل فقط.",
                "body": {"paragraphs": ["محتوى مؤقت."]},
                "seo_title": "مقال اختبار",
                "seo_description": "بيانات عربية مؤقتة لاختبار التكامل فقط.",
            },
        },
    }


def job_payload(status: str = "draft") -> dict[str, object]:
    return {
        "slug": "qa-approved-role",
        "department": "QA",
        "location": "UAE",
        "employment_type": "Full time",
        "closing_date": None,
        "status": status,
        "translations": {
            "en": {
                "title": "QA role",
                "description": "Disposable role description for integration testing.",
                "responsibilities": ["Test safely"],
                "requirements": ["QA evidence"],
                "benefits": [],
            },
            "ar": {
                "title": "وظيفة اختبار",
                "description": "وصف مؤقت للوظيفة لاختبار التكامل فقط.",
                "responsibilities": ["اختبار آمن"],
                "requirements": ["دليل اختبار"],
                "benefits": [],
            },
        },
    }


@pytest.mark.asyncio
async def test_health_readiness_and_secure_session_lifecycle(
    client: AsyncClient, create_user
) -> None:
    assert (await client.get("/health")).json() == {"status": "ok"}
    assert (await client.get("/ready")).json() == {"status": "ready"}
    email, password = await create_user("super-admin")
    invalid = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Wrong-password!!"}
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "invalid_credentials"
    session = await authenticate(client, email, password)
    assert "are_admin_session" in client.cookies
    assert set(session["roles"]) == {"Super Admin"}
    refreshed = await client.get("/api/v1/auth/me")
    assert refreshed.status_code == 200
    csrf = refreshed.json()["csrf_token"]
    logged_out = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert logged_out.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_rbac_denies_unauthorized_property_creation(client: AsyncClient, create_user) -> None:
    email, password = await create_user("content-manager")
    session = await authenticate(client, email, password)
    denied = await client.post(
        "/api/v1/admin/properties",
        json=property_payload(),
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "permission_denied"


@pytest.mark.asyncio
async def test_property_draft_archive_and_publication_boundaries(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    csrf = str(session["csrf_token"])
    direct_publish = await client.post(
        "/api/v1/admin/properties",
        json=property_payload("published"),
        headers={"X-CSRF-Token": csrf},
    )
    assert direct_publish.status_code == 422
    assert direct_publish.json()["error"]["code"] == "property_media_incomplete"
    created = await client.post(
        "/api/v1/admin/properties", json=property_payload(), headers={"X-CSRF-Token": csrf}
    )
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]
    assert (await client.get("/api/v1/public/properties?locale=en")).json()["meta"]["total"] == 0
    image = io.BytesIO()
    Image.new("RGB", (640, 360), "#745238").save(image, "WEBP")
    uploaded = await client.post(
        f"/api/v1/admin/properties/{record_id}/cover",
        files={"image": ("cover.webp", image.getvalue(), "image/webp")},
        headers={"X-CSRF-Token": csrf},
    )
    assert uploaded.status_code == 200, uploaded.text
    reviewed = await client.put(
        f"/api/v1/admin/properties/{record_id}/cover",
        json={
            "alt_en": "Disposable property cover",
            "alt_ar": "غلاف عقار مؤقت",
            "provenance_url": "https://example.com/property-cover.webp",
            "rights_status": "approved",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert reviewed.status_code == 200, reviewed.text
    published_payload = property_payload("published")
    published = await client.put(
        f"/api/v1/admin/properties/{record_id}",
        json=published_payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200, published.text
    public_en = await client.get("/api/v1/public/properties/qa-source-verified-home?locale=en")
    public_ar = await client.get("/api/v1/public/properties/qa-source-verified-home?locale=ar")
    assert public_en.json()["title"] == "QA verified home"
    assert public_ar.json()["title"] == "منزل اختبار موثق"
    assert public_en.json()["cover_media"]["alt"] == "Disposable property cover"
    assert (
        await client.get("/api/v1/public/properties/qa-source-verified-home/cover")
    ).status_code == 200
    weakened_media = await client.put(
        f"/api/v1/admin/properties/{record_id}/cover",
        json={
            "alt_en": "Disposable property cover",
            "alt_ar": "غلاف عقار مؤقت",
            "provenance_url": "https://example.com/property-cover.webp",
            "rights_status": "pending",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert weakened_media.status_code == 422
    assert weakened_media.json()["error"]["code"] == "property_media_incomplete"
    archived_payload = deepcopy(published_payload)
    archived_payload["status"] = "archived"
    assert (
        await client.put(
            f"/api/v1/admin/properties/{record_id}",
            json=archived_payload,
            headers={"X-CSRF-Token": csrf},
        )
    ).status_code == 200
    assert (
        await client.get("/api/v1/public/properties/qa-source-verified-home?locale=en")
    ).status_code == 404


@pytest.mark.asyncio
async def test_insight_and_job_publication_workflows_create_audit(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    csrf = str(session["csrf_token"])
    insight = await client.post(
        "/api/v1/admin/insights", json=insight_payload("published"), headers={"X-CSRF-Token": csrf}
    )
    job = await client.post(
        "/api/v1/admin/jobs", json=job_payload("open"), headers={"X-CSRF-Token": csrf}
    )
    assert insight.status_code == 201, insight.text
    assert job.status_code == 201, job.text
    assert (
        await client.get("/api/v1/public/insights/qa-approved-insight?locale=ar")
    ).status_code == 200
    assert (await client.get("/api/v1/public/jobs/qa-approved-role?locale=en")).status_code == 200
    closed = job_payload("closed")
    assert (
        await client.put(
            f"/api/v1/admin/jobs/{job.json()['id']}", json=closed, headers={"X-CSRF-Token": csrf}
        )
    ).status_code == 200
    assert (await client.get("/api/v1/public/jobs/qa-approved-role?locale=en")).status_code == 404
    audit = await client.get("/api/v1/admin/audit")
    assert audit.status_code == 200
    actions = {item["action"] for item in audit.json()["items"]}
    assert {"content.publish", "job.open", "job.close"}.issubset(actions)
