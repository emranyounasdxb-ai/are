from __future__ import annotations

import io
import uuid
import zipfile

import pytest
from httpx import AsyncClient


def enquiry(locale: str = "en") -> dict[str, object]:
    return {
        "enquiry_type": "general",
        "name": "QA Visitor",
        "email": f"visitor-{uuid.uuid4()}@qa.are-cms.invalid-example-domain.com",
        "phone": "+971 50 000 0000",
        "message": "Disposable integration test enquiry.",
        "locale": locale,
        "preferred_contact_method": "email",
        "contact_consent": True,
        "marketing_consent": False,
        "attribution": {},
        "website": "",
    }


def application_data() -> dict[str, str]:
    return {
        "applicant_name": "QA Applicant",
        "email": f"applicant-{uuid.uuid4()}@qa.are-cms.invalid-example-domain.com",
        "phone": "+971 50 000 0001",
        "current_location": "Dubai",
        "context_label": "General application",
        "cover_note": "Disposable integration test application cover note.",
        "locale": "en",
        "acknowledgement_consent": "true",
        "marketing_consent": "false",
        "website": "",
    }


def docx() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return output.getvalue()


def job_payload() -> dict[str, object]:
    translation_en = {
        "title": "QA role",
        "description": "Disposable role for submission testing.",
        "responsibilities": ["Test"],
        "requirements": ["Evidence"],
        "benefits": [],
    }
    translation_ar = {
        "title": "وظيفة اختبار",
        "description": "وظيفة مؤقتة لاختبار التقديم.",
        "responsibilities": ["اختبار"],
        "requirements": ["دليل"],
        "benefits": [],
    }
    return {
        "slug": "qa-submission-role",
        "department": "QA",
        "location": "Dubai",
        "employment_type": "Full time",
        "closing_date": None,
        "status": "open",
        "translations": {"en": translation_en, "ar": translation_ar},
    }


async def login(client: AsyncClient, create_user) -> dict[str, object]:
    email, password = await create_user("super-admin")
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_bilingual_enquiries_are_idempotent_and_reviewable(
    client: AsyncClient, create_user
) -> None:
    keys = []
    for locale in ("en", "ar"):
        key = str(uuid.uuid4())
        keys.append(key)
        created = await client.post(
            "/api/v1/public/enquiries",
            json=enquiry(locale),
            headers={"Idempotency-Key": key, "X-Forwarded-For": f"198.51.100.{len(keys)}"},
        )
        assert created.status_code == 201, created.text
        duplicate = await client.post(
            "/api/v1/public/enquiries",
            json=enquiry(locale),
            headers={"Idempotency-Key": key, "X-Forwarded-For": f"198.51.100.{len(keys)}"},
        )
        assert duplicate.json() == {
            "reference_id": created.json()["reference_id"],
            "duplicate": True,
        }
    session = await login(client, create_user)
    listed = await client.get("/api/v1/admin/enquiries")
    record = next(
        item for item in listed.json()["items"] if item["reference_code"].startswith("ENQ-")
    )
    updated = await client.put(
        f"/api/v1/admin/enquiries/{record['id']}",
        json={"status": "contacted", "internal_note": "QA reviewed"},
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert updated.status_code == 200 and updated.json()["status"] == "contacted"


@pytest.mark.asyncio
async def test_private_cv_validation_download_and_audit(client: AsyncClient, create_user) -> None:
    invalid = await client.post(
        "/api/v1/public/applications",
        data=application_data(),
        files={"cv": ("resume.txt", b"plain", "text/plain")},
        headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.20"},
    )
    assert invalid.status_code == 422
    oversized = await client.post(
        "/api/v1/public/applications",
        data=application_data(),
        files={"cv": ("resume.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024), "application/pdf")},
        headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.22"},
    )
    assert oversized.status_code == 413
    pdf = await client.post(
        "/api/v1/public/applications",
        data=application_data(),
        files={"cv": ("resume.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
        headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.23"},
    )
    assert pdf.status_code == 201
    doc = await client.post(
        "/api/v1/public/applications",
        data=application_data(),
        files={
            "cv": ("resume.doc", bytes.fromhex("D0CF11E0A1B11AE1") + b"QA", "application/msword")
        },
        headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.24"},
    )
    assert doc.status_code == 201
    docx_content = docx()
    created = await client.post(
        "/api/v1/public/applications",
        data=application_data(),
        files={
            "cv": (
                "resume.docx",
                docx_content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.21"},
    )
    assert created.status_code == 201, created.text
    assert (await client.get("/api/v1/admin/applications")).status_code == 401
    session = await login(client, create_user)
    job = await client.post(
        "/api/v1/admin/jobs",
        json=job_payload(),
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert job.status_code == 201, job.text
    specific_data = application_data()
    specific_data["job_slug"] = "qa-submission-role"
    specific = await client.post(
        "/api/v1/public/applications",
        data=specific_data,
        files={"cv": ("specific.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
        headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.25"},
    )
    assert specific.status_code == 201
    listed = await client.get("/api/v1/admin/applications")
    record = next(
        item
        for item in listed.json()["items"]
        if item["reference_code"] == created.json()["reference_id"]
    )
    download = await client.get(f"/api/v1/admin/applications/{record['id']}/cv")
    assert download.status_code == 200 and download.content == docx_content
    assert "private" in download.headers["cache-control"]
    updated = await client.put(
        f"/api/v1/admin/applications/{record['id']}",
        json={"status": "shortlisted", "internal_note": "QA review"},
        headers={"X-CSRF-Token": str(session["csrf_token"])},
    )
    assert updated.status_code == 200 and updated.json()["status"] == "shortlisted"
    audit = await client.get("/api/v1/admin/audit")
    actions = {item["action"] for item in audit.json()["items"]}
    assert {"application.cv.accessed", "application.update"}.issubset(actions)


@pytest.mark.asyncio
async def test_submission_rate_limit_and_invalid_payload(client: AsyncClient) -> None:
    assert (
        await client.post(
            "/api/v1/public/enquiries", json={}, headers={"Idempotency-Key": str(uuid.uuid4())}
        )
    ).status_code == 422
    statuses = []
    for _ in range(9):
        response = await client.post(
            "/api/v1/public/enquiries",
            json=enquiry(),
            headers={"Idempotency-Key": str(uuid.uuid4()), "X-Forwarded-For": "198.51.100.99"},
        )
        statuses.append(response.status_code)
    assert statuses[-1] == 429
