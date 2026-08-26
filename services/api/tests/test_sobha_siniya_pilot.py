from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.acquisition.contracts import FetchResult
from app.acquisition.sobha_siniya_pilot import (
    OFFICIAL_AR_URL,
    OFFICIAL_EN_URL,
    OFFICIAL_MEDIA,
    OFFICIAL_PARTNERSHIP_URL,
    PRIMARY_URL,
    _normalize_sources,
    require_exact_pilot_url,
)
from app.import_review import draft_eligibility_errors
from app.models import EditorialApprovalStatus, ProjectMediaCategory
from app.project_processing import DisabledOverviewProvider, OverviewGenerationPending


def result(url: str, html: str) -> FetchResult:
    return FetchResult(
        url=url,
        status=200,
        retrieved_at=datetime.now(UTC),
        content_type="text/html",
        body=html.encode(),
    )


def test_pilot_rejects_every_url_except_the_authorized_project() -> None:
    assert require_exact_pilot_url(PRIMARY_URL) == PRIMARY_URL
    for url in (
        "https://www.tanamiproperties.com/Projects",
        "https://www.tanamiproperties.com/Projects/Another-Project",
        f"{PRIMARY_URL}/",
        "http://www.tanamiproperties.com/Projects/Sobha-Siniya-Island",
    ):
        with pytest.raises(ValueError, match="only the authorized"):
            require_exact_pilot_url(url)


def test_pilot_normalization_is_source_bounded_and_excludes_prices() -> None:
    tanami = result(
        PRIMARY_URL,
        """
        <html><title>Sobha Siniya Island at Umm Al Quwain</title><body>
        Sobha Siniya Island
        Apartment Sizes 513 to 2,191 Sq Ft
        Villa Sizes 4,815 to 9,788 Sq Ft
        Down Payment: 10%
        Payment Plan: 60/40
        Handover: Q4 - 2027
        1st to 5th Installment
        4 Bedrooms + Maid
        5 Bedrooms + Maid
        6 Bedrooms + Maid
        Master Plan
        Starting From AED 1.34 M
        </body></html>
        """,
    )
    official_en = result(
        OFFICIAL_EN_URL,
        "<html><title>Sobha Siniya Island</title><body>Umm Al Quwain</body></html>",
    )
    official_ar = result(
        OFFICIAL_AR_URL,
        "<html lang='ar'><title>جزيرة شوبا السينية</title><body>جزيرة شوبا السينية</body></html>",
    )
    partnership = result(
        OFFICIAL_PARTNERSHIP_URL,
        """
        <html><title>Partnership</title><body>
        family golf course, floating pavilion, event halls, helix bridge,
        white sand beaches, mangrove and tide trail, community centre,
        ecopark and a play zone
        </body></html>
        """,
    )

    facts, extracted, diagnostics = _normalize_sources(
        tanami, partnership, official_en, official_ar
    )

    assert facts["project_name"] == "Sobha Siniya Island"
    assert facts["emirate"] == "Umm Al Quwain"
    assert facts["availability_status"] == "unresolved"
    assert facts["construction_status"] == "not-confirmed"
    assert "price" not in " ".join(facts).casefold()
    assert extracted["price_fields_intentionally_excluded"] is True
    assert {item["field"] for item in diagnostics} >= {
        "availability_status",
        "construction_status",
        "overview",
        "media_rights",
    }


async def test_missing_approved_overview_provider_is_a_pending_gate() -> None:
    with pytest.raises(OverviewGenerationPending, match="No approved Overview provider"):
        await DisabledOverviewProvider().generate({}, "source-version")


def test_official_media_allowlist_is_exact_and_has_one_cover() -> None:
    assert len(OFFICIAL_MEDIA) == 3
    assert sum(item[1] == ProjectMediaCategory.COVER for item in OFFICIAL_MEDIA) == 1
    assert all(
        item[0].startswith("https://sobharealty.com/sites/default/files/")
        for item in OFFICIAL_MEDIA
    )


def test_unresolved_market_facts_do_not_block_a_private_draft() -> None:
    candidate = SimpleNamespace(
        proposed_developer_id="developer",
        proposed_area_id="area",
        official_source_url=OFFICIAL_EN_URL,
        source_urls=[OFFICIAL_EN_URL],
        normalized_project_name="Sobha Siniya Island",
        normalized_payload={"property_types": ["villa"], "bedrooms": ["4"]},
        human_review_completed=True,
        editorial_draft=SimpleNamespace(
            approval_status=EditorialApprovalStatus.APPROVED,
            overview_en="Approved English Overview.",
            overview_ar="نظرة عامة عربية معتمدة.",
        ),
        validation_errors=[
            {"field": "availability_status", "code": "missing_official_evidence"},
            {"field": "construction_status", "code": "missing_official_evidence"},
        ],
        conflict_reasons=[
            "Current availability is unresolved; an active page or displayed price was not "
            "treated as availability evidence."
        ],
        staged_media=[
            SimpleNamespace(
                category=ProjectMediaCategory.COVER,
                stage_status="downloaded",
                rights_status=SimpleNamespace(value="approved"),
                storage_key="private-cover.webp",
            )
        ],
    )

    assert draft_eligibility_errors(candidate) == []
