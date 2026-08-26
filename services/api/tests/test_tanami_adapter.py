from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.acquisition.adapters import adapter_for
from app.acquisition.contracts import FetchResult
from app.acquisition.tanami import (
    _stage_media,
    acquire_explicit_batch,
    acquire_project_documents,
    discover_exact_project_media,
    exact_project_media,
    extract_identity,
    normalize_project_urls,
    same_project_urls,
)
from app.db import SessionLocal
from app.models import (
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMediaCategory,
)

ALPHA = "https://www.tanamiproperties.com/Projects/Alpha-Residences"
BETA = "https://www.tanamiproperties.com/Projects/Beta-Residences"
ALPHA_GALLERY = f"{ALPHA}/gallery"


class TanamiFixtureFetcher:
    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
        del allowed_domains
        pages = {
            ALPHA: f"""
                <html><title>Alpha Residences</title><body>
                <h1>Alpha Residences</h1>
                Developer: Unregistered Developments Area: Test Harbour
                Property Type: Apartments Bedrooms: 1 Bedroom and 2 Bedrooms
                Unit type: 1 &amp; 2 BR Size: 650 to 1,250 Sq Ft.
                Down Payment: 10% Handover: Q4 2029
                Payment Plan: 10% booking 90% handover Ras Al Khaimah
                <a href="{ALPHA_GALLERY}">Gallery</a>
                <a href="{BETA}"><img src="https://manage.tanamiproperties.com/Project/related.webp"></a>
                <img src="https://manage.tanamiproperties.com/Project/alpha-cover.webp">
                </body></html>
            """,
            ALPHA_GALLERY: """
                <html><body><h1>Alpha Residences Gallery</h1>
                <img src="https://manage.tanamiproperties.com/Project/alpha-interior.webp">
                <img src="https://manage.tanamiproperties.com/Assets/logo.webp">
                <img src="https://www.tanamiproperties.com/Projects/images/tiktok.webp">
                <img src="https://www.tanamiproperties.com/Projects/images/x.webp">
                </body></html>
            """,
            BETA: """
                <html><title>Beta Residences</title><body><h1>Beta Residences</h1>
                Developer: Unregistered Developments Area: Test Marina
                Property Type: Villas Bedrooms: 3 Bedrooms Handover: Q1 2030
                </body></html>
            """,
        }
        body = pages.get(url)
        if body is None:
            return FetchResult(
                url=url,
                status=404,
                retrieved_at=datetime.now(UTC),
                error_code="http_404",
                error_message="Fixture URL not found.",
            )
        return FetchResult(
            url=url,
            status=200,
            retrieved_at=datetime.now(UTC),
            content_type="text/html",
            body=body.encode(),
        )


def test_explicit_url_contract_supports_one_multiple_and_large_approved_lists() -> None:
    assert normalize_project_urls([ALPHA]) == (ALPHA,)
    assert normalize_project_urls([BETA, ALPHA, ALPHA]) == (ALPHA, BETA)
    assert (
        len(
            normalize_project_urls(
                [
                    f"https://www.tanamiproperties.com/Projects/Approved-{index}"
                    for index in range(50)
                ]
            )
        )
        == 50
    )
    for unsafe in (
        "https://www.tanamiproperties.com/Projects",
        "https://www.tanamiproperties.com/Projects/Alpha?crawl=all",
        "https://example.com/Projects/Alpha",
        "http://www.tanamiproperties.com/Projects/Alpha",
    ):
        with pytest.raises(ValueError, match="exact credential-free HTTPS"):
            normalize_project_urls([unsafe])


def test_same_project_discovery_excludes_related_project_links() -> None:
    floor_plans = f"{ALPHA}-FloorPlans"
    body = (
        f'<a href="{ALPHA_GALLERY}">Gallery</a>'
        f'<a href="{floor_plans}">Floor Plans</a>'
        f'<a href="{BETA}">Related</a>'
    ).encode()
    assert set(same_project_urls(ALPHA, body)) == {ALPHA_GALLERY, floor_plans}


def _html_result(body: str, url: str = ALPHA) -> FetchResult:
    return FetchResult(
        url=url,
        status=200,
        retrieved_at=datetime.now(UTC),
        content_type="text/html",
        body=body.encode(),
    )


def test_identity_uses_exact_json_ld_breadcrumb_aliases() -> None:
    result = _html_result(
        """
        <html><title>SKAI at Mina Al Arab, Ras Al Khaimah - RAK Properties</title><body>
        <h1>SKAI at Mina Al Arab, Ras Al Khaimah - RAK Properties</h1>
        <script type="application/ld+json">
        {"@type":"BreadcrumbList","itemListElement":[
          {"item":{"@type":"Place","name":"Mina Al Arab"}},
          {"item":{"@type":"Brand","name":"RAK Properties"}},
          {"item":{"@type":"House","name":"SKAI at Mina Al Arab"}}
        ]}
        </script></body></html>
        """
    )

    identity = extract_identity(result)

    assert identity.project_name == "SKAI at Mina Al Arab"
    assert identity.developer_name == "RAK Properties"
    assert identity.area_name == "Mina Al Arab"


def test_srcset_prefers_largest_original_and_deduplicates_thumbnail_variant() -> None:
    result = _html_result(
        """
        <picture><source srcset="
          https://manage.tanamiproperties.com/Gallery/1/Thumb/10.webp 480w,
          https://manage.tanamiproperties.com/Gallery/1/Large/10.webp 1600w">
        <img src="https://manage.tanamiproperties.com/Gallery/1/Thumb/10.webp"></picture>
        """
    )
    media = exact_project_media(ALPHA, (result,))
    assert media == (
        (
            "https://manage.tanamiproperties.com/Gallery/1/Large/10.webp",
            ProjectMediaCategory.GALLERY,
        ),
    )


def test_lazy_carousel_discovers_every_exact_project_image() -> None:
    result = _html_result(
        """
        <div class="carousel">
          <a href="https://manage.tanamiproperties.com/Gallery/1/Thumb/11.webp">
            <img src="/Projects/images/Loading.svg"
                 data-echo="https://manage.tanamiproperties.com/Gallery/1/Thumb/11.webp">
          </a>
          <img data-src="https://manage.tanamiproperties.com/Gallery/1/Thumb/12.webp">
          <img data-original="https://manage.tanamiproperties.com/Gallery/1/Thumb/13.webp">
        </div>
        """
    )
    discovery = discover_exact_project_media(ALPHA, (result,))
    assert {url for url, _ in discovery.media} == {
        "https://manage.tanamiproperties.com/Gallery/1/Thumb/11.webp",
        "https://manage.tanamiproperties.com/Gallery/1/Thumb/12.webp",
        "https://manage.tanamiproperties.com/Gallery/1/Thumb/13.webp",
    }
    assert discovery.visible_gallery_count == 3


def test_json_css_and_exact_project_boundary_exclude_branding_and_related_media() -> None:
    result = _html_result(
        f"""
        <script type="application/ld+json">{{"url":"{ALPHA}",
          "image":"https://manage.tanamiproperties.com/Gallery/1/Thumb/14.webp"}}</script>
        <div style="background-image:url('https://manage.tanamiproperties.com/Gallery/1/Thumb/15.webp')"></div>
        <a href="{BETA}"><img src="https://manage.tanamiproperties.com/Gallery/2/Thumb/99.webp"></a>
        <img src="https://manage.tanamiproperties.com/Assets/logo.webp">
        <img src="https://manage.tanamiproperties.com/Assets/social-icon.webp">
        """
    )
    urls = {url for url, _ in exact_project_media(ALPHA, (result,))}
    assert urls == {
        "https://manage.tanamiproperties.com/Gallery/1/Thumb/14.webp",
        "https://manage.tanamiproperties.com/Gallery/1/Thumb/15.webp",
    }


@pytest.mark.asyncio
async def test_media_staging_rejects_embedded_data_and_deduplicates_pending_urls() -> None:
    class RecordingSession:
        def __init__(self) -> None:
            self.added: list[ProjectImportMedia] = []

        def add(self, value: ProjectImportMedia) -> None:
            self.added.append(value)

    session = RecordingSession()
    candidate = type(
        "Candidate",
        (),
        {"id": __import__("uuid").uuid4(), "staged_media": []},
    )()
    valid = "https://example.com/project/gallery.webp"

    await _stage_media(  # type: ignore[arg-type]
        session,
        candidate,
        (
            ("data:image/svg+xml;base64,placeholder", ProjectMediaCategory.GALLERY),
            (valid, ProjectMediaCategory.GALLERY),
            (valid, ProjectMediaCategory.GALLERY),
        ),
    )

    assert [item.source_url for item in session.added] == [valid]
    assert [item.source_url for item in candidate.staged_media] == [valid]


@pytest.mark.asyncio
async def test_exact_project_media_excludes_related_and_brand_assets() -> None:
    result = await acquire_project_documents(ALPHA, fetcher=TanamiFixtureFetcher())
    urls = {url for url, _ in result.media}
    assert "https://manage.tanamiproperties.com/Project/alpha-cover.webp" in urls
    assert "https://manage.tanamiproperties.com/Project/alpha-interior.webp" in urls
    assert "https://manage.tanamiproperties.com/Project/related.webp" not in urls
    assert "https://manage.tanamiproperties.com/Assets/logo.webp" not in urls
    assert "https://www.tanamiproperties.com/Projects/images/tiktok.webp" not in urls
    assert "https://www.tanamiproperties.com/Projects/images/x.webp" not in urls
    assert result.identity.developer_name == "Unregistered Developments"
    assert result.normalized.normalized_proposal["emirate"] == "RAS_AL_KHAIMAH"
    assert result.normalized.normalized_proposal["size_min"] == 650
    assert result.normalized.normalized_proposal["size_max"] == 1250
    assert result.normalized.normalized_proposal["down_payment_percentage"] == 10
    assert result.normalized.normalized_proposal["unit_types"] == ["1 & 2 BR"]


@pytest.mark.asyncio
async def test_explicit_batch_is_idempotent_and_missing_official_source_needs_review(
    test_settings,
) -> None:
    async with SessionLocal() as db:
        first = await acquire_explicit_batch(
            db,
            test_settings,
            [ALPHA],
            fetcher=TanamiFixtureFetcher(),
            batch_name="QA Tanami explicit batch",
        )
        first_id = first.id
        candidate = await db.scalar(
            select(ProjectImportCandidate).where(ProjectImportCandidate.batch_id == first_id)
        )
        assert candidate is not None
        candidate_id = candidate.id
        assert candidate.review_status.value == "needs-review"
        assert any(
            item.get("code") == "official_source_not_found" for item in candidate.validation_errors
        )
        candidate.normalized_payload = {
            **(candidate.normalized_payload or {}),
            "project_name": "Human-reviewed Alpha Residences",
            "availability_status": "available",
        }
        candidate.human_edited_fields = ["project_name"]
        await db.commit()

        second = await acquire_explicit_batch(
            db,
            test_settings,
            [ALPHA],
            fetcher=TanamiFixtureFetcher(),
            batch_name="QA Tanami explicit batch",
        )
        assert second.id == first_id
        await db.refresh(candidate)
        assert candidate.normalized_payload is not None
        assert candidate.normalized_payload["project_name"] == "Human-reviewed Alpha Residences"
        assert candidate.normalized_payload["availability_status"] == "available"
        assert any(
            item.get("field") == "availability_status"
            for item in candidate.acquisition_summary["retained_prior_evidence"]
        )
        assert "Human-edited field preserved" in " ".join(candidate.conflict_reasons)
        assert (
            await db.scalar(
                select(func.count())
                .select_from(ProjectImportCandidate)
                .where(ProjectImportCandidate.batch_id == first_id)
            )
            == 1
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(ProjectImportMedia)
                .where(ProjectImportMedia.candidate_id == candidate_id)
            )
            == 2
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(ProjectImportBatch)
                .where(ProjectImportBatch.manifest_hash == first.manifest_hash)
            )
            == 1
        )


@pytest.mark.asyncio
async def test_explicit_batch_acquires_multiple_urls_and_separates_media_warning_from_conflicts(
    test_settings,
) -> None:
    async with SessionLocal() as db:
        batch = await acquire_explicit_batch(
            db,
            test_settings,
            [BETA, ALPHA],
            fetcher=TanamiFixtureFetcher(),
            batch_name="QA multiple Tanami batch",
        )
        candidates = list(batch.candidates)
        assert len(candidates) == 2
        beta = next(
            item for item in candidates if item.normalized_project_name == "Beta Residences"
        )
        assert beta.review_status.value == "needs-review"
        assert beta.acquisition_summary["media_discovered"] == 0
        assert "Insufficient exact-project media" in str(beta.acquisition_summary["media_warning"])
        assert "Insufficient exact-project media" not in " ".join(beta.conflict_reasons)


@pytest.mark.asyncio
async def test_source_disagreement_retains_each_private_value_and_url() -> None:
    class DisagreementFetcher(TanamiFixtureFetcher):
        def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
            result = super().fetch(url, allowed_domains)
            if url == ALPHA_GALLERY:
                return _html_result(
                    "<h1>Alpha Residences Gallery</h1> Down Payment: 30%",
                    ALPHA_GALLERY,
                )
            return result

    result = await acquire_project_documents(ALPHA, fetcher=DisagreementFetcher())

    assert "Source disagreement for down_payment_percentage: 10.0 | 30.0." in (
        result.normalized.conflicts
    )
    evidence = result.normalized.source_extracted["_source_disagreement_evidence"]
    assert evidence == [
        {
            "field": "down_payment_percentage",
            "sources": [
                {"value": 10.0, "source_url": ALPHA},
                {"value": 30.0, "source_url": ALPHA_GALLERY},
            ],
            "requires_human_review": True,
        }
    ]


def test_official_developer_registry_uses_exact_private_aliases() -> None:
    assert adapter_for("Sobha Group") is adapter_for("Sobha Realty")
    assert adapter_for("شوبا العقارية") is adapter_for("Sobha Realty")
    assert adapter_for("Sobha Real") is None
    assert adapter_for("Sobha Group International") is None
