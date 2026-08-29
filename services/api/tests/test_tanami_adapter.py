from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.acquisition.adapters import (
    adapter_for,
    official_announcement_url_matches_project,
    official_url_matches_project,
)
from app.acquisition.contracts import FetchResult
from app.acquisition.tanami import (
    _ambiguous_cross_candidate_media_ids,
    _stage_media,
    acquire_explicit_batch,
    acquire_project_documents,
    discover_exact_project_media,
    discover_sharjah_project_urls,
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


class SharjahListingFixtureFetcher:
    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
        del allowed_domains
        assert url == "https://www.tanamiproperties.com/Offplan-Projects-in-Sharjah"
        body = b"""
            <input id="hdnCity" value="114">
            <input id="hdnProjPageRows" value="10">
            <input id="hdnProjRecordCount" value="12">
        """
        return FetchResult(
            url=url,
            status=200,
            retrieved_at=datetime.now(UTC),
            content_type="text/html",
            body=body,
        )

    def post_json(
        self,
        url: str,
        allowed_domains: tuple[str, ...],
        payload: dict[str, object],
        *,
        referer: str,
    ) -> FetchResult:
        del allowed_domains
        assert url.endswith("/CityProjectlist.aspx/GetProjectListbyCity")
        assert referer.endswith("/Offplan-Projects-in-Sharjah")
        assert payload["strCity"] == "114"
        page = int(str(payload["iPageIndex"]))
        count = 10 if page == 1 else 2
        body = json.dumps(
            {
                "d": {
                    "lstprojlist": [
                        {
                            "ProjURL": f"/Projects/Sharjah-{page}-{index}",
                            "ProjName": f"Sharjah {page} {index}",
                            "DevName": "Verified Developer",
                            "ComName": "Verified Area",
                            "ProjCount": "12",
                        }
                        for index in range(count)
                    ]
                }
            }
        ).encode()
        return FetchResult(
            url=url,
            status=200,
            retrieved_at=datetime.now(UTC),
            content_type="application/json",
            body=body,
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


@pytest.mark.asyncio
async def test_sharjah_listing_discovery_is_bounded_complete_and_project_only() -> None:
    result = await discover_sharjah_project_urls(  # type: ignore[arg-type]
        fetcher=SharjahListingFixtureFetcher()
    )

    assert result.total_reported == 12
    assert result.rows_seen == 12
    assert result.pages_fetched == 2
    assert result.duplicate_count == 0
    assert len(result.urls) == 12
    assert len(result.projects) == 12
    assert result.projects[0].developer_name == "Verified Developer"
    assert all(
        value.startswith("https://www.tanamiproperties.com/Projects/") for value in result.urls
    )


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
async def test_same_project_section_title_variants_are_not_conflicts() -> None:
    class SectionTitleFetcher(TanamiFixtureFetcher):
        def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
            result = super().fetch(url, allowed_domains)
            if url == ALPHA_GALLERY:
                return _html_result(
                    "<h1>Alpha Apartments at Sharjah - Features & Amenities</h1>",
                    ALPHA_GALLERY,
                )
            return result

    result = await acquire_project_documents(ALPHA, fetcher=SectionTitleFetcher())

    assert not any(
        reason.startswith("Official source name differs:") for reason in result.normalized.conflicts
    )


@pytest.mark.asyncio
async def test_primary_page_seo_title_is_not_a_source_conflict() -> None:
    class SeoTitleFetcher(TanamiFixtureFetcher):
        def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
            result = super().fetch(url, allowed_domains)
            if url == ALPHA:
                return _html_result(
                    "<h1>Alpha Apartments Summary in Sharjah</h1>",
                    ALPHA,
                )
            return result

    result = await acquire_project_documents(ALPHA, fetcher=SeoTitleFetcher())

    assert not any(
        reason.startswith("Official source name differs:") for reason in result.normalized.conflicts
    )


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
async def test_media_staging_has_no_per_candidate_raster_cap() -> None:
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
    media = tuple(
        (
            f"https://manage.tanamiproperties.com/Project/gallery-{index}.webp",
            ProjectMediaCategory.GALLERY,
        )
        for index in range(31)
    )

    await _stage_media(session, candidate, media)  # type: ignore[arg-type]

    assert len(session.added) == 31
    assert len(candidate.staged_media) == 31


def test_cross_candidate_media_is_rejected_for_urls_and_binary_hashes() -> None:
    from types import SimpleNamespace
    from uuid import uuid4

    shared_official = "https://developer.example.com/media/shared.webp"
    shared_tanami = "https://manage.tanamiproperties.com/Gallery/1/shared.webp"
    first = SimpleNamespace(
        id=uuid4(),
        staged_media=[
            SimpleNamespace(
                id=uuid4(), source_url=shared_official, stage_status="downloaded", sha256="a"
            ),
            SimpleNamespace(
                id=uuid4(), source_url=shared_tanami, stage_status="downloaded", sha256="b"
            ),
        ],
    )
    second = SimpleNamespace(
        id=uuid4(),
        staged_media=[
            SimpleNamespace(
                id=uuid4(), source_url=shared_official, stage_status="downloaded", sha256="a"
            ),
            SimpleNamespace(
                id=uuid4(), source_url=shared_tanami, stage_status="downloaded", sha256="b"
            ),
        ],
    )

    rejected = _ambiguous_cross_candidate_media_ids(SimpleNamespace(candidates=[first, second]))

    assert rejected == {
        first.staged_media[0].id,
        first.staged_media[1].id,
        second.staged_media[0].id,
        second.staged_media[1].id,
    }


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
    assert adapter_for("ARADA Developer") is adapter_for("Arada")
    assert adapter_for("IFA Hotel & Resorts") is adapter_for("IFA Hotels & Resorts")
    assert adapter_for("Alef Group") is not None
    assert adapter_for("Eagle Hills") is not None
    assert adapter_for("Majid Al Futtaim") is not None
    assert adapter_for("Shoumous Properties") is not None
    assert adapter_for("Tiger Group") is not None
    assert adapter_for("Sobha Real") is None
    assert adapter_for("Sobha Group International") is None


def test_official_project_url_requires_phase_tokens_and_rejects_broad_pages() -> None:
    assert official_url_matches_project(
        "Sedra at Masaar 3",
        "https://www.arada.com/en/property/masaar-3-sedra-4br-villa/",
    )
    assert not official_url_matches_project(
        "Olfah 2 by Alef",
        "https://www.alefgroup.ae/alef-communities/olfah/",
    )
    assert not official_url_matches_project(
        "Nama 1",
        "https://www.alefgroup.ae/press/alef-group-partners-with-nama/",
    )
    assert not official_url_matches_project("Signature Villas", "https://www.arada.com/ar/")
    assert not official_url_matches_project(
        "Abu Dhabi Tower", "https://www.tigergroup.ae/abu-dhabi/towers/renad-tower"
    )
    assert not official_url_matches_project(
        "The Boulevard 3", "https://www.arada.com/en/property/the-boulevard-3-bedroom/"
    )
    assert official_url_matches_project(
        "Areej Apartments", "https://www.arada.com/en/property_category/areej/"
    )
    assert official_url_matches_project(
        "The Riff Apartments", "https://www.arada.com/en/property_category/the-riff/"
    )
    assert not official_url_matches_project(
        "Nest at Aljada", "https://www.arada.com/en/property_category/nest-8/"
    )
    assert not official_url_matches_project(
        "Nasma Residences", "https://www.arada.com/en/nasma-central/"
    )
    assert official_url_matches_project(
        "Nesba 1 at Aljada", "https://www.arada.com/en/property_category/nesba-1/"
    )
    assert official_url_matches_project(
        "The Boulevard at Aljada",
        "https://www.arada.com/en/property_category/the-boulevard/",
    )
    assert official_url_matches_project(
        "Ajwan Residences", "https://shurooq.gov.ae/portfolio/Ajwan-Residence"
    )
    assert official_url_matches_project("Bluebay walk", "https://ajmalmakan.com/blue-bay-walk/")


def test_linked_official_domains_are_allowlisted_for_bounded_research() -> None:
    arada = adapter_for("ARADA")
    sharjah_holding = adapter_for("Sharjah Holding")
    shurooq = adapter_for("Shurooq")

    assert arada is not None
    assert "aradawebcontent.blob.core.windows.net" in arada.allowed_domains
    assert sharjah_holding is not None
    assert "alzahia.ae" in sharjah_holding.allowed_domains
    assert shurooq is not None
    assert "ajwan.ae" in shurooq.allowed_domains


def test_official_announcement_match_requires_every_multi_token_identity_part() -> None:
    assert official_announcement_url_matches_project(
        "Al Mamsha Hamsa 2",
        "https://www.alefgroup.ae/press/alef-launches-hamsa-2-in-al-mamsha-sharjah/",
    )
    assert official_announcement_url_matches_project(
        "Masaar Robinia",
        "https://www.arada.com/en/latest-news/arada-launches-robinia-the-third-phase-of-masaar/",
    )
    assert not official_announcement_url_matches_project(
        "Al Mamsha Hamsa 2",
        "https://www.alefgroup.ae/press/alef-launches-hamsa-3-in-al-mamsha-sharjah/",
    )
    assert not official_announcement_url_matches_project(
        "Al Mamsha Hamsa",
        "https://www.alefgroup.ae/press/alef-launches-hamsa-2-in-al-mamsha-sharjah/",
    )
    assert not official_announcement_url_matches_project(
        "Olfah 2 by Alef",
        "https://www.alefgroup.ae/press/alef-group-launches-olfah-project-valued-at-aed-2-5-billion/",
    )
    assert not official_announcement_url_matches_project(
        "Hayyan",
        "https://www.alefgroup.ae/press/alef-announces-new-hayyan-phase/",
    )


def test_register_interest_is_not_availability_evidence() -> None:
    from app.acquisition.parser import explicit_availability

    assert explicit_availability("register your interest") is None
    assert explicit_availability("register interest") is None
    assert explicit_availability("coming soon; register your interest") == "coming-soon"


def test_size_range_retains_units_on_both_endpoints() -> None:
    from app.acquisition.parser import explicit_size_range

    assert explicit_size_range(
        "Plots range from 5,000 sqft to 12,000 sqft. Larger 8,000-12,000 square feet plots."
    ) == (5000, 12000, "sqft")


def test_global_filters_are_not_project_fact_evidence() -> None:
    from app.acquisition.parser import parse_html

    page = parse_html(
        b"<nav>Apartments</nav><select><option>Coming soon</option></select>"
        b"<h1>Example Villas</h1><p>Register your interest.</p><footer>Sold out</footer>",
        "https://example.com/project",
    )
    assert page.text == "Example Villas Register your interest."


def test_related_project_cards_do_not_add_types_or_status_to_current_project() -> None:
    from app.acquisition.contracts import ManifestCandidate
    from app.acquisition.parser import normalize_evidence, parse_html

    page = parse_html(
        b"<h1>QA Residences</h1><p>Property Type: Apartment. Studio, 1 &amp; 2 Bedrooms.</p>"
        b"<h2>More Projects of Developer</h2><p>Other Island Villas. Sold out. 6 bedrooms.</p>",
        "https://example.com/project",
    )
    result = normalize_evidence(page, ManifestCandidate(1, "QA Residences", "Developer", "Sharjah"))
    assert result.normalized_proposal["property_types"] == ["apartment"]
    assert "studio" in result.normalized_proposal["bedrooms"]
    assert "6" not in result.normalized_proposal["bedrooms"]
    assert result.normalized_proposal["availability_status"] is None
