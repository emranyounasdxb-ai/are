from __future__ import annotations

import asyncio
import io
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from app.acquisition.adapters import ADAPTERS, adapter_for
from app.acquisition.contracts import FetchResult, ManifestCandidate
from app.acquisition.media import RasterFetchResult, duplicate_hash, validate_raster
from app.acquisition.media_intake import intake_private_media
from app.acquisition.parser import normalize_evidence, parse_html
from app.acquisition.security import AcquisitionSecurityError, validate_public_url
from app.acquisition.service import classify_change, load_manifest, read_manifest, retry_candidates
from app.db import SessionLocal
from app.models import (
    AreaCommunity,
    Developer,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMediaCategory,
    PublicationStatus,
)
from app.storage import PrivateStorage


def public_resolver(
    host: str, port: int, *, type: object
) -> list[tuple[int, int, int, str, tuple[str, int]]]:
    del host, type
    return [(2, 1, 6, "", ("93.184.216.34", port))]


def private_resolver(
    host: str, port: int, *, type: object
) -> list[tuple[int, int, int, str, tuple[str, int]]]:
    del host, type
    return [(2, 1, 6, "", ("127.0.0.1", port))]


def metadata_resolver(
    host: str, port: int, *, type: object
) -> list[tuple[int, int, int, str, tuple[str, int]]]:
    del host, type
    return [(2, 1, 6, "", ("169.254.169.254", port))]


def test_ssrf_rejects_scheme_domains_private_and_metadata_destinations() -> None:
    allowed = ("example.com",)
    assert (
        validate_public_url("https://projects.example.com/a", allowed, resolver=public_resolver)
        == "https://projects.example.com/a"
    )
    for url, resolver in (
        ("http://example.com/a", public_resolver),
        ("https://unapproved.example/a", public_resolver),
        ("https://example.com/a", private_resolver),
        ("https://example.com/a", metadata_resolver),
    ):
        with pytest.raises(AcquisitionSecurityError):
            validate_public_url(url, allowed, resolver=resolver)


def test_redirect_destination_must_stay_on_public_allowlisted_https() -> None:
    with pytest.raises(AcquisitionSecurityError):
        validate_public_url(
            "https://metadata.invalid/latest/meta-data/",
            ("example.com",),
            resolver=metadata_resolver,
        )


def test_all_required_adapters_are_registered() -> None:
    expected = {
        "Emaar",
        "Sobha Realty",
        "DAMAC",
        "Binghatti",
        "Ellington",
        "Meraas",
        "Beyond",
        "Expo City Dubai",
        "Nakheel",
        "Danube",
        "Azizi",
        "Bold",
        "Zaya",
        "Mr Eight",
        "Reportage",
        "Aldar",
    }
    assert {item.developer_name for item in ADAPTERS.values()} == expected
    assert all(adapter_for(name) is not None for name in expected)


class FixtureFetcher:
    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
        del allowed_domains
        if url.endswith("/sitemap.xml"):
            body = (
                b"<urlset><url><loc>https://properties.emaar.com/en/properties/"
                b"fixture-residence</loc></url></urlset>"
            )
            return FetchResult(url, 200, datetime.now(UTC), "application/xml", body)
        if url.endswith("/fixture-residence"):
            body = b"<html><h1>Fixture Residence</h1><p>Emaar apartments</p></html>"
            return FetchResult(url, 200, datetime.now(UTC), "text/html", body)
        return FetchResult(url, 404, datetime.now(UTC), error_code="http_404")


def test_adapter_discovers_fetches_parses_and_normalizes_fixture() -> None:
    adapter = adapter_for("Emaar")
    assert adapter is not None
    candidate = ManifestCandidate(1, "Fixture Residence", "Emaar", "Dubai")
    discovery = adapter.discover(candidate, FixtureFetcher())
    assert discovery.match_kind == "deterministic"
    fetched, normalized = adapter.acquire(candidate, discovery, FixtureFetcher())
    assert fetched.ok
    assert normalized is not None
    assert normalized.source_extracted["project_name"] == "Fixture Residence"


def test_parser_preserves_source_values_and_marks_conflicts() -> None:
    body = b"""
      <html><head><title>Valia at Creek</title></head><body>
      <h1>Valia at Creek</h1><p>Emaar Dubai Creek Harbour apartments, 1 and 2 bedrooms.</p>
      <p>Handover Q4 2029. Payment Plan 10% booking 70% construction 20% handover.</p>
      <img src="https://properties.emaar.com/media/valia.jpg"></body></html>
    """
    parsed = parse_html(body, "https://properties.emaar.com/en/properties/valia")
    result = normalize_evidence(
        parsed,
        ManifestCandidate(2, "Valia Tower", "Emaar", "Dubai Creek Harbour"),
    )
    assert result.source_extracted["handover_quarter"] == "Q4"
    assert result.source_extracted["handover_year"] == 2029
    assert result.source_extracted["availability_status"] is None
    payment = result.source_extracted["payment_plan"]
    assert isinstance(payment, dict)
    assert payment["is_complete"] is True
    milestones = payment["milestones"]
    assert isinstance(milestones, list)
    assert [item["stage"] for item in milestones] == [
        "booking",
        "during-construction",
        "handover",
    ]
    assert result.conflicts


def test_change_detection_does_not_turn_unavailable_into_sold_out() -> None:
    previous = {"project_name": "A", "availability_status": None}
    assert classify_change(previous, previous, same_hash=True) == "unchanged"
    assert classify_change(previous, None) == "source-unavailable"
    assert classify_change(previous, {**previous, "handover_year": 2030}) == "changed"
    assert (
        classify_change(previous, {**previous, "project_name": "Different"}) == "conflict-detected"
    )


def test_raster_validation_sanitizes_and_detects_duplicates() -> None:
    source = io.BytesIO()
    Image.new("RGB", (640, 360), "white").save(source, "JPEG", exif=b"test-metadata")
    raster = validate_raster(source.getvalue(), "image/jpeg")
    assert raster.width == 640 and raster.height == 360
    assert duplicate_hash({raster.sha256}, raster)
    assert b"test-metadata" not in raster.content
    with pytest.raises(ValueError):
        validate_raster(source.getvalue(), "image/png")


@pytest.mark.asyncio
async def test_manifest_is_exact_and_loading_is_idempotent(tmp_path: Path) -> None:
    source = next(
        parent / "data-intake" / "offplan-projects-owner-manifest.csv"
        for parent in Path(__file__).resolve().parents
        if (parent / "data-intake" / "offplan-projects-owner-manifest.csv").is_file()
    )
    records, _ = await read_manifest(source)
    assert len(records) == 50
    path = tmp_path / "qa-manifest.csv"
    content = await asyncio.to_thread(source.read_bytes)
    await asyncio.to_thread(path.write_bytes, content)
    async with SessionLocal() as db:
        first = await load_manifest(
            db,
            path,
            batch_name="QA Acquisition Import",
            source_reference="qa-manifest.csv",
        )
        second = await load_manifest(
            db,
            path,
            batch_name="QA Acquisition Import",
            source_reference="qa-manifest.csv",
        )
        assert first.id == second.id
        assert len(second.candidates) == 50
        assert len({item.manifest_row_id for item in second.candidates}) == 50
        count = len(
            (
                await db.scalars(
                    select(ProjectImportBatch).where(
                        ProjectImportBatch.manifest_hash == second.manifest_hash
                    )
                )
            ).all()
        )
        assert count == 1


class RasterFixtureFetcher:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> RasterFetchResult:
        assert "emaar.com" in allowed_domains
        return RasterFetchResult(url, self.content, "image/jpeg", 200)


@pytest.mark.asyncio
async def test_private_media_intake_is_sanitized_pending_and_authenticated(
    client, create_user, test_settings
) -> None:
    image = io.BytesIO()
    Image.new("RGB", (640, 360), "#745238").save(image, "JPEG", exif=b"private-metadata")
    batch_id = uuid.uuid4()
    media_id = uuid.uuid4()
    async with SessionLocal() as db:
        batch = ProjectImportBatch(
            id=batch_id,
            name="QA Private Media Import",
            source_reference="qa-media.csv",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="test",
            total_count=1,
        )
        candidate = ProjectImportCandidate(
            manifest_row_id=1,
            raw_source_payload={},
            owner_manifest_values={
                "owner_project_name": "QA Media Project",
                "owner_developer": "Emaar",
                "owner_area": "Dubai",
            },
            source_urls=[],
            content_hash="d" * 64,
            validation_errors=[],
            conflict_reasons=[],
            review_status=ImportReviewStatus.NEEDS_REVIEW,
        )
        candidate.staged_media = [
            ProjectImportMedia(
                id=media_id,
                category=ProjectMediaCategory.GALLERY,
                source_url="https://properties.emaar.com/media/qa-project.jpg",
                rights_status=MediaRightsStatus.PENDING,
                stage_status="reference-only",
            )
        ]
        batch.candidates = [candidate]
        db.add(batch)
        await db.commit()
        stats = await intake_private_media(
            db,
            test_settings,
            batch_id,
            fetcher=RasterFixtureFetcher(image.getvalue()),
        )
        assert stats["downloaded"] == 1
        media = await db.get(ProjectImportMedia, media_id)
        assert media is not None
        assert media.rights_status == MediaRightsStatus.PENDING
        assert media.thumbnail_storage_key
        assert media.storage_key
        sanitized = PrivateStorage(test_settings).read(media.storage_key)
        assert b"private-metadata" not in sanitized

    unauthenticated = await client.get(f"/api/v1/admin/project-import-media/{media_id}/thumbnail")
    assert unauthenticated.status_code == 401
    email, password = await create_user("super-admin")
    await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    preview = await client.get(f"/api/v1/admin/project-import-media/{media_id}/thumbnail")
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "private, no-store, max-age=0"
    assert preview.headers["content-type"].startswith("image/webp")


@pytest.mark.asyncio
async def test_retry_preserves_human_mapping_and_never_auto_marks_ready(test_settings) -> None:
    async with SessionLocal() as db:
        developer = await db.scalar(select(Developer).where(Developer.slug == "emaar-properties"))
        assert developer is not None
        area = AreaCommunity(
            slug="qa-retry-area",
            name_en="QA Retry Area",
            name_ar="منطقة إعادة المحاولة",
            emirate="Dubai",
            status=PublicationStatus.DRAFT,
        )
        batch = ProjectImportBatch(
            name="QA Retry Import",
            source_reference="qa-retry.csv",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="test",
            total_count=1,
        )
        candidate = ProjectImportCandidate(
            manifest_row_id=1,
            raw_source_payload={},
            owner_manifest_values={
                "owner_project_name": "Fixture Residence",
                "owner_developer": "Emaar",
                "owner_area": "QA Retry Area",
            },
            normalized_project_name="Fixture Residence",
            proposed_developer_id=developer.id,
            proposed_area_id=area.id,
            human_review_completed=True,
            source_urls=[],
            content_hash="e" * 64,
            validation_errors=[],
            conflict_reasons=[],
            review_status=ImportReviewStatus.FAILED,
        )
        batch.candidates = [candidate]
        db.add_all([area, batch])
        await db.commit()
        await retry_candidates(
            db,
            test_settings,
            [candidate],
            fetcher=FixtureFetcher(),
        )
        await db.commit()
        assert candidate.proposed_developer_id == developer.id
        assert candidate.proposed_area_id == area.id
        assert candidate.human_review_completed is False
        assert candidate.review_status == ImportReviewStatus.NEEDS_REVIEW
        assert candidate.review_version == 2
