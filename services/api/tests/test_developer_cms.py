from __future__ import annotations

from copy import deepcopy

import pytest
from httpx import AsyncClient

from tests.test_admin_cms import authenticate


def developer_payload(status: str = "draft", slug: str = "qa-developer") -> dict[str, object]:
    return {
        "slug": slug,
        "primary_emirate": "Dubai",
        "other_presence": ["Abu Dhabi"],
        "selected_projects": ["QA identity reference"],
        "official_website": "https://example.com/developer",
        "source_url": "https://example.com/government-source",
        "additional_source_urls": ["https://example.com/official-source"],
        "verification_date": "2026-08-24",
        "enquiry_types": ["new-booking", "primary-sale", "resale"],
        "featured": False,
        "display_order": 999,
        "status": status,
        "translations": {
            "en": {
                "name": "QA Developer",
                "description": "Disposable English developer content for integration testing.",
                "focus": "Disposable residential testing",
                "verification_note": "Disposable verification note for integration testing.",
            },
            "ar": {
                "name": "مطور اختبار",
                "description": "محتوى عربي مؤقت لاختبار تكامل دليل المطورين.",
                "focus": "اختبار سكني مؤقت",
                "verification_note": "ملاحظة تحقق مؤقتة لاختبار التكامل فقط.",
            },
        },
    }


@pytest.mark.asyncio
async def test_developer_draft_publish_archive_locale_and_audit(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    headers = {"X-CSRF-Token": str(session["csrf_token"])}
    created = await client.post(
        "/api/v1/admin/developers", json=developer_payload(), headers=headers
    )
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]
    assert (await client.get("/api/v1/public/developers/qa-developer?locale=en")).status_code == 404

    published = await client.post(f"/api/v1/admin/developers/{record_id}/publish", headers=headers)
    assert published.status_code == 200, published.text
    public_en = await client.get("/api/v1/public/developers/qa-developer?locale=en")
    public_ar = await client.get("/api/v1/public/developers/qa-developer?locale=ar")
    assert public_en.json()["name"] == "QA Developer"
    assert public_ar.json()["name"] == "مطور اختبار"

    archived = await client.post(f"/api/v1/admin/developers/{record_id}/archive", headers=headers)
    assert archived.status_code == 200, archived.text
    assert (await client.get("/api/v1/public/developers/qa-developer?locale=en")).status_code == 404
    audit = await client.get("/api/v1/admin/audit")
    actions = {item["action"] for item in audit.json()["items"]}
    assert {"developer.create", "developer.publish", "developer.archive"}.issubset(actions)


@pytest.mark.asyncio
async def test_developer_rbac_csrf_duplicate_slug_and_url_validation(
    client: AsyncClient, create_user
) -> None:
    content_email, content_password = await create_user("content-manager")
    content_session = await authenticate(client, content_email, content_password)
    denied = await client.post(
        "/api/v1/admin/developers",
        json=developer_payload(),
        headers={"X-CSRF-Token": str(content_session["csrf_token"])},
    )
    assert denied.status_code == 403

    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    no_csrf = await client.post("/api/v1/admin/developers", json=developer_payload())
    assert no_csrf.status_code == 403
    headers = {"X-CSRF-Token": str(session["csrf_token"])}
    payload = developer_payload(slug="qa-developer-duplicate")
    assert (
        await client.post("/api/v1/admin/developers", json=payload, headers=headers)
    ).status_code == 201
    duplicate = await client.post("/api/v1/admin/developers", json=payload, headers=headers)
    assert duplicate.status_code == 409

    invalid = deepcopy(developer_payload())
    invalid["slug"] = "qa-invalid-url"
    invalid["official_website"] = "javascript:alert(1)"
    assert (
        await client.post("/api/v1/admin/developers", json=invalid, headers=headers)
    ).status_code == 422
    invalid_source = deepcopy(developer_payload())
    invalid_source["slug"] = "qa-invalid-source"
    invalid_source["source_url"] = "not-a-url"
    assert (
        await client.post("/api/v1/admin/developers", json=invalid_source, headers=headers)
    ).status_code == 422


@pytest.mark.asyncio
async def test_seeded_public_developers_are_complete_and_published(client: AsyncClient) -> None:
    response = await client.get("/api/v1/public/developers?locale=en")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 20
    assert all(item["status"] == "published" for item in items)
    assert {item["slug"] for item in items} >= {
        "emaar-properties",
        "aldar-properties",
        "al-hamra",
        "marjan",
    }


@pytest.mark.asyncio
async def test_developer_publication_requires_complete_bilingual_content(
    client: AsyncClient, create_user
) -> None:
    email, password = await create_user("super-admin")
    session = await authenticate(client, email, password)
    headers = {"X-CSRF-Token": str(session["csrf_token"])}
    payload = developer_payload(slug="qa-incomplete-developer")
    translations = payload["translations"]
    assert isinstance(translations, dict)
    translations.pop("ar")
    created = await client.post("/api/v1/admin/developers", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    blocked = await client.post(
        f"/api/v1/admin/developers/{created.json()['id']}/publish", headers=headers
    )
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "publication_incomplete"
