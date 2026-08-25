from __future__ import annotations

import asyncio
import io
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from app.acquisition.adapters import ADAPTERS, adapter_for
from app.acquisition.contracts import FetchResult, ManifestCandidate
from app.acquisition.mapping_registry import TANAMI_V1, mapping_contract
from app.acquisition.media import (
    RasterFetchResult,
    classify_media_quality,
    duplicate_hash,
    normalized_media_filename,
    responsive_derivatives,
    validate_raster,
)
from app.acquisition.media_intake import intake_private_media
from app.acquisition.parser import normalize_evidence, parse_html
from app.acquisition.security import AcquisitionSecurityError, validate_public_url
from app.acquisition.service import (
    classify_change,
    compare_fields,
    load_manifest,
    match_developer_identity,
    read_manifest,
    retry_candidates,
)
from app.db import SessionLocal
from app.models import (
    AreaCommunity,
    Developer,
    DeveloperTranslation,
    DeveloperVerificationStatus,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportChange,
    ProjectImportEditorialDraft,
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


def owner_manifest_path() -> Path:
    return next(
        parent / "data-intake" / "offplan-projects-owner-manifest.csv"
        for parent in Path(__file__).resolve().parents
        if (parent / "data-intake" / "offplan-projects-owner-manifest.csv").is_file()
    )


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


def test_inactive_mapping_registry_covers_project_contract_and_limits_ai() -> None:
    contract = mapping_contract("tanami", "1.0.0")
    assert contract is TANAMI_V1
    assert contract.enabled is False
    assert {field.are_key for field in contract.fields} >= {
        "project_name",
        "developer",
        "emirate",
        "area",
        "property_types",
        "unit_types",
        "bedroom_options",
        "size_min",
        "size_max",
        "size_unit",
        "down_payment_percentage",
        "payment_plan.raw_source_text",
        "payment_plan.milestones",
        "handover_quarter",
        "handover_year",
        "availability_status",
        "construction_status",
        "editorial.overview",
        "amenities",
        "media.floor_plans",
        "media.gallery",
        "latitude",
        "longitude",
        "nearby_places",
        "last_verified_at",
        "sources",
    }
    assert [field.are_key for field in contract.fields if field.ai_editable] == [
        "editorial.overview"
    ]
    assert {field.source_key for field in contract.fields if field.are_key == "amenities"} == {
        "features",
        "amenities",
    }


def test_field_change_review_preserves_human_edits() -> None:
    changes = compare_fields(
        {"overview": "Human wording", "handover": "Q1 2030", "removed": "value"},
        {"overview": "Source wording", "handover": "Q2 2030", "new": "value"},
        human_edited_fields={"overview"},
    )
    states = {change["field"]: change["classification"] for change in changes}
    assert states == {
        "handover": "changed",
        "new": "newly-added",
        "overview": "human-edited-conflict",
        "removed": "removed-from-source",
    }
    assert not any(change["may_apply_automatically"] for change in changes)


def test_media_derivatives_are_normalized_sanitized_and_responsive() -> None:
    source = io.BytesIO()
    Image.new("RGB", (1200, 800), "#745238").save(source, "JPEG", exif=b"private-metadata")
    raster = validate_raster(source.getvalue(), "image/jpeg")
    filename = normalized_media_filename(
        "Fixture Residence / Phase 1", "gallery", 2, raster.sha256, raster.extension
    )
    assert filename.startswith("fixture-residence-phase-1-gallery-02-")
    derivatives = responsive_derivatives(raster)
    assert {(item.format, item.width) for item in derivatives} == {
        ("webp", 480),
        ("avif", 480),
        ("webp", 960),
        ("avif", 960),
    }
    assert all(item.width <= raster.width for item in derivatives)
    for derivative in derivatives:
        assert derivative.size_bytes == len(derivative.content)
        with Image.open(io.BytesIO(derivative.content)) as image:
            assert image.width == derivative.width
            assert not image.getexif()


@pytest.mark.asyncio
async def test_developer_identity_matches_internal_source_name_and_alias() -> None:
    async with SessionLocal() as db:
        developer = Developer(
            slug="qa-fixture-source-developer",
            legal_name="Fixture Source Developer LLC",
            source_name="Fixture Source Developer LLC",
            internal_aliases=["Fixture Source Dev"],
            primary_emirate="Dubai",
            other_presence=[],
            selected_projects=[],
            official_website="https://example.com",
            source_url="https://example.com/source",
            additional_source_urls=[],
            verification_date=datetime(2026, 8, 25, tzinfo=UTC).date(),
            enquiry_types=[],
            featured=False,
            display_order=0,
            status=PublicationStatus.DRAFT,
        )
        db.add(developer)
        await db.flush()
        assert await match_developer_identity(db, "Fixture Source Developer LLC") == developer.id
        assert await match_developer_identity(db, "Fixture Source Dev") == developer.id
        await db.rollback()


@pytest.mark.asyncio
async def test_raw_normalized_and_editorial_layers_stay_separate_and_private() -> None:
    async with SessionLocal() as db:
        batch = ProjectImportBatch(
            name="QA Layer Separation",
            source_reference="synthetic-fixture",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="synthetic-v1",
            total_count=1,
        )
        candidate = ProjectImportCandidate(
            manifest_row_id=1,
            raw_source_payload={"overview": "Untrusted synthetic source wording"},
            owner_manifest_values={"owner_project_name": "QA Layer Fixture"},
            normalized_payload={"project_name": "QA Layer Fixture", "handover_year": 2030},
            source_urls=["https://example.com/synthetic-source"],
            content_hash="f" * 64,
            validation_errors=[],
            conflict_reasons=[],
            review_status=ImportReviewStatus.NEEDS_REVIEW,
            editorial_draft=ProjectImportEditorialDraft(
                overview_en="Human review required for this synthetic overview.",
                overview_ar="هذه نظرة عامة تجريبية تتطلب مراجعة بشرية.",
                source_version="synthetic-source-v1",
                model_name="synthetic-model",
                model_version="test-only",
                generated_at=datetime.now(UTC),
                approval_status=EditorialApprovalStatus.NEEDS_REVIEW,
            ),
        )
        batch.candidates = [candidate]
        db.add(batch)
        await db.commit()
        loaded = await db.scalar(
            select(ProjectImportCandidate).where(ProjectImportCandidate.id == candidate.id)
        )
        assert loaded is not None and loaded.editorial_draft is not None
        assert loaded.raw_source_payload["overview"] == "Untrusted synthetic source wording"
        assert loaded.normalized_payload == {
            "project_name": "QA Layer Fixture",
            "handover_year": 2030,
        }
        assert loaded.editorial_draft.source_version == "synthetic-source-v1"
        assert loaded.editorial_draft.approval_status == EditorialApprovalStatus.NEEDS_REVIEW
        assert loaded.review_status == ImportReviewStatus.NEEDS_REVIEW


@pytest.mark.asyncio
async def test_manifest_is_exact_and_loading_is_idempotent(tmp_path: Path) -> None:
    source = owner_manifest_path()
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
    Image.new("RGB", (1600, 1000), "#745238").save(image, "JPEG", exif=b"private-metadata")
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
        assert media.raw_storage_key
        assert media.storage_key
        assert media.normalized_filename
        assert {item["format"] for item in media.derivative_manifest} == {"webp", "avif"}
        assert media.change_status == "newly-added"
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
    full = await client.get(f"/api/v1/admin/project-import-media/{media_id}/preview")
    assert full.status_code == 200
    assert full.headers["cache-control"] == "private, no-store, max-age=0"
    assert full.headers["content-type"].startswith("image/jpeg")


@pytest.mark.asyncio
async def test_low_resolution_media_is_private_review_only_and_rerun_is_idempotent(
    test_settings,
) -> None:
    image = io.BytesIO()
    Image.new("RGB", (800, 450), "#745238").save(image, "JPEG")
    batch_id = uuid.uuid4()
    async with SessionLocal() as db:
        batch = ProjectImportBatch(
            id=batch_id,
            name="QA Low Resolution Media",
            source_reference="qa-low-resolution",
            manifest_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            adapter_version="test",
            total_count=1,
        )
        candidate = ProjectImportCandidate(
            manifest_row_id=1,
            raw_source_payload={},
            owner_manifest_values={
                "owner_project_name": "QA Low Resolution Project",
                "owner_developer": "Emaar",
                "owner_area": "Dubai",
            },
            normalized_project_name="QA Low Resolution Project",
            acquisition_summary={"visible_gallery_count": 2, "media_excluded": 3},
            source_urls=[],
            content_hash="e" * 64,
            validation_errors=[],
            conflict_reasons=[],
            review_status=ImportReviewStatus.NEEDS_REVIEW,
        )
        media = ProjectImportMedia(
            category=ProjectMediaCategory.GALLERY,
            source_url="https://properties.emaar.com/media/qa-low.jpg",
            rights_status=MediaRightsStatus.PENDING,
            stage_status="reference-only",
        )
        candidate.staged_media = [media]
        batch.candidates = [candidate]
        db.add(batch)
        await db.commit()
        first = await intake_private_media(
            db,
            test_settings,
            batch_id,
            fetcher=RasterFixtureFetcher(image.getvalue()),
        )
        await db.refresh(media)
        first_keys = (media.raw_storage_key, media.storage_key, media.thumbnail_storage_key)
        assert first["low_resolution_rejected"] == 1
        assert media.stage_status == "rejected-low-resolution"
        assert (
            media.failure_reason == "Image does not meet the minimum public-readiness dimensions."
        )
        assert media.derivative_manifest == []
        assert all(first_keys)
        assert "Media coverage incomplete" in candidate.conflict_reasons
        assert "High-resolution Cover image required" in candidate.conflict_reasons

        second = await intake_private_media(
            db,
            test_settings,
            batch_id,
            fetcher=RasterFixtureFetcher(image.getvalue()),
        )
        await db.refresh(media)
        assert second["attempted"] == 0
        assert second["low_resolution_rejected"] == 1
        assert (media.raw_storage_key, media.storage_key, media.thumbnail_storage_key) == first_keys


def test_cover_quality_gate_requires_real_1600_by_900_landscape_master() -> None:
    low = io.BytesIO()
    Image.new("RGB", (1400, 600), "#745238").save(low, "JPEG")
    low_quality = classify_media_quality(validate_raster(low.getvalue(), "image/jpeg"), "cover")
    assert not low_quality.public_eligible
    assert low_quality.rejection_reason == "High-resolution Cover image required"

    valid = io.BytesIO()
    Image.new("RGB", (1600, 900), "#745238").save(valid, "JPEG")
    valid_quality = classify_media_quality(validate_raster(valid.getvalue(), "image/jpeg"), "cover")
    assert valid_quality.public_eligible
    assert valid_quality.cover_eligible


@pytest.mark.asyncio
async def test_retry_preserves_human_mapping_and_never_auto_marks_ready(test_settings) -> None:
    async with SessionLocal() as db:
        developer = Developer(
            slug="qa-retry-developer",
            legal_name="QA Retry Developer LLC",
            source_name="QA Retry Developer",
            internal_aliases=["QA Retry Dev"],
            primary_emirate="Dubai",
            other_presence=[],
            selected_projects=[],
            official_website="https://example.com/qa-retry-developer",
            source_url="https://example.com/qa-retry-developer/source",
            additional_source_urls=[],
            verification_date=date(2026, 8, 26),
            verification_status=DeveloperVerificationStatus.VERIFIED,
            enquiry_types=[],
            status=PublicationStatus.DRAFT,
            translations=[
                DeveloperTranslation(
                    locale="en",
                    name="QA Retry Developer",
                    description="Disposable Developer fixture.",
                    focus="Disposable Project fixtures.",
                    verification_note="Synthetic QA evidence only.",
                ),
                DeveloperTranslation(
                    locale="ar",
                    name="مطور اختبار إعادة المحاولة",
                    description="بيانات مطور مؤقتة للاختبار.",
                    focus="مشاريع اختبار مؤقتة.",
                    verification_note="أدلة اختبار اصطناعية فقط.",
                ),
            ],
        )
        db.add(developer)
        await db.flush()
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
            normalized_payload={"project_name": "Human-approved Fixture Residence"},
            human_edited_fields=["project_name"],
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
        assert candidate.normalized_payload is not None
        assert candidate.normalized_payload["project_name"] == "Human-approved Fixture Residence"
        conflict = await db.scalar(
            select(ProjectImportChange).where(
                ProjectImportChange.candidate_id == candidate.id,
                ProjectImportChange.field_name == "project_name",
            )
        )
        assert conflict is not None
        assert conflict.classification == "human-edited-conflict"
