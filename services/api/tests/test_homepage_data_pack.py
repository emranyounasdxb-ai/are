from __future__ import annotations

import io
import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException, UploadFile
from httpx import AsyncClient
from PIL import Image, PngImagePlugin

from app.config import Settings
from app.db import SessionLocal
from app.models import PublicationStatus, TrustProfile
from app.schemas import PropertyInput
from app.storage import PrivateStorage


def property_payload() -> dict[str, object]:
    return {
        "slug": "qa-homepage-property",
        "purpose": "buy",
        "property_type": "Apartment",
        "emirate": "Dubai",
        "community": "Business Bay",
        "price_on_request": True,
        "provenance_note": "Disposable QA record.",
        "external_reference_url": "https://example.com/property",
        "source_verified_at": "2026-08-25",
        "availability_status": "unverified",
        "translations": {"en": {"title": "QA property", "description": "QA description only."}},
    }


def test_published_property_requires_bilingual_content() -> None:
    payload = property_payload() | {"status": "published"}
    with pytest.raises(ValueError, match="English and Arabic"):
        PropertyInput.model_validate(payload)


async def test_public_trust_profile_exposes_only_the_verified_snapshot(
    client: AsyncClient,
) -> None:
    record_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(
            TrustProfile(
                id=record_id,
                display_name="ALIYAS Real Estate",
                phone="+971 56 915 7576",
                google_business_url="https://share.google/d7cfjXsrpJPdzVO3v",
                google_rating=Decimal("4.8"),
                google_review_count=22,
                snapshot_verified_at=date(2026, 8, 25),
                office_address="Office 218, Business Village Block B - Dubai",
                status=PublicationStatus.PUBLISHED,
            )
        )
        await db.commit()
    try:
        response = await client.get("/api/v1/public/trust-profile")
        assert response.status_code == 200
        snapshot = response.json()
        assert snapshot["display_name"] == "ALIYAS Real Estate"
        assert snapshot["phone"] == "+971 56 915 7576"
        assert snapshot["google_rating"] == "4.8"
        assert snapshot["google_review_count"] == 22
        assert snapshot["snapshot_verified_at"] == "2026-08-25"
        assert "reviews" not in snapshot
    finally:
        async with SessionLocal() as db:
            record = await db.get(TrustProfile, record_id)
            if record:
                await db.delete(record)
                await db.commit()


async def test_property_cover_is_decoded_sanitized_and_root_confined(
    test_settings: Settings,
) -> None:
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "metadata must not survive")
    source = io.BytesIO()
    Image.new("RGB", (640, 360), "#745238").save(source, "PNG", pnginfo=info)
    stored = await PrivateStorage(test_settings).save_property_image(
        UploadFile(
            filename="cover.png",
            file=io.BytesIO(source.getvalue()),
            headers={"content-type": "image/png"},
        )
    )
    content = PrivateStorage(test_settings).read(stored.storage_key)
    with Image.open(io.BytesIO(content)) as image:
        assert image.size == (640, 360)
        assert "Comment" not in image.info
    assert stored.storage_key.startswith("property-")
    assert stored.original_filename == "cover.png"
    with pytest.raises(RuntimeError, match="Unsafe"):
        PrivateStorage(test_settings).read("../escape.png")


async def test_property_cover_rejects_svg(test_settings: Settings) -> None:
    upload = UploadFile(
        filename="cover.svg",
        file=io.BytesIO(b"<svg xmlns='http://www.w3.org/2000/svg'/>"),
        headers={"content-type": "image/svg+xml"},
    )
    with pytest.raises(HTTPException) as caught:
        await PrivateStorage(test_settings).save_property_image(upload)
    assert caught.value.status_code == 422
