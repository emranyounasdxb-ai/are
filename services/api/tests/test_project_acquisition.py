from __future__ import annotations

import asyncio
import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from app.acquisition.adapters import ADAPTERS, adapter_for
from app.acquisition.contracts import FetchResult, ManifestCandidate
from app.acquisition.media import duplicate_hash, validate_raster
from app.acquisition.parser import normalize_evidence, parse_html
from app.acquisition.security import AcquisitionSecurityError, validate_public_url
from app.acquisition.service import classify_change, load_manifest, read_manifest
from app.db import SessionLocal
from app.models import ProjectImportBatch


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
    source = Path("/app/data-intake/offplan-projects-owner-manifest.csv")
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
