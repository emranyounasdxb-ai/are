from __future__ import annotations

import copy
from datetime import date

import pytest

from app.acquisition.targeted_evidence import (
    FactObservation,
    project_fact_projection,
    review_observations,
)
from app.public_project_evidence import omit_unresolved


def observation(**changes):
    return FactObservation.model_validate(
        {
            "field": "bedrooms",
            "value": ["1", "2"],
            "source_url": "https://developer.example/project-one",
            "publisher": "Developer",
            "independence_group": "developer",
            "source_kind": "official",
            "source_date": str(date.today()),
            "temporal_status": "current",
            "exact_context": "Project One / Developer / Area One / phase 1",
            "excerpt": "Project One has one and two bedroom apartments.",
            "evidence_hash": "a" * 64,
            **changes,
        }
    )


def review(items, existing=None, **kwargs):
    return review_observations(
        items,
        existing or {},
        exact_context="Project One / Developer / Area One / phase 1",
        requested_fields={"bedrooms"},
        **kwargs,
    )


def test_dated_official_fact_fills_only_missing_value_and_is_idempotent():
    first = review([observation(), observation()])
    assert first["updates"] == {"bedrooms": ["1", "2"]}
    assert len(first["observations"]) == 1
    assert review([observation()]) == first
    assert review([observation()], first["updates"])["updates"] == {}
    assert review([observation()], protected_fields={"bedrooms"})["updates"] == {}


@pytest.mark.parametrize("temporal,source_date", [("undated", None), ("last-known", "2024-01-01")])
def test_historical_or_undated_values_remain_private(temporal, source_date):
    result = review([observation(temporal_status=temporal, source_date=source_date)])
    assert result["updates"] == {}
    assert result["states"]["bedrooms"] == "unconfirmed"
    assert result["observations"][0]["temporal_status"] == temporal


def test_secondary_sources_must_be_independent_not_syndicated():
    first = observation(source_kind="supporting", independence_group="shared-feed")
    second = observation(
        source_kind="supporting",
        publisher="Portal Two",
        source_url="https://second.example/project-one",
        independence_group="shared-feed",
    )
    assert review([first, second])["updates"] == {}
    independent = observation(
        source_kind="supporting",
        publisher="Portal Two",
        source_url="https://second.example/project-one",
        independence_group="separate-reporting",
    )
    assert review([first, independent])["states"]["bedrooms"] == "supported"


def test_disagreement_retains_both_sources_and_never_overwrites():
    a, b = observation(), observation(value=["3"], source_url="https://second.example/one")
    result = review([a, b], {"bedrooms": ["4"]})
    assert result["updates"] == {}
    assert result["states"]["bedrooms"] == "conflict"
    assert len(result["conflicts"]["bedrooms"]) == 2
    assert result["baseline"]["bedrooms"] == ["4"]


@pytest.mark.parametrize(
    "changes",
    [
        {"field": "price", "value": 123},
        {"excerpt": "Starting price AED 123"},
        {"excerpt": "Contact person@example.com"},
        {"value": "To be announced"},
        {"source_date": None},
        {"value": {"amount": "AED 123"}},
    ],
)
def test_forbidden_data_and_placeholders_are_rejected(changes):
    with pytest.raises(ValueError):
        observation(**changes)


def test_wrong_phase_is_rejected():
    with pytest.raises(ValueError, match="different Project"):
        review([observation(exact_context="Project One / Developer / Area One / phase 2")])


def test_legacy_unsafe_baseline_is_hashed_not_copied_into_new_evidence():
    result = review([], {"bedrooms": "Contact for price AED 123"})
    assert result["baseline"]["bedrooms"]["not_copied"] is True
    assert "AED" not in str(result) and "123" not in str(result)
    assert result["updates"] == {}


def test_projection_drops_prices_contacts_and_related_project_data():
    html = b"""<main><h1>Project One</h1><table>
    <tr><td>Property Type</td><td>Apartment</td></tr>
    <tr><td>Unit Type</td><td>1 &amp; 2 Bedrooms</td></tr>
    <tr><td>Starting Price</td><td>AED 123456</td></tr>
    <tr><td>Contact</td><td>person@example.com</td></tr>
    </table><h2>Related Projects</h2><table>
    <tr><td>Handover</td><td>Q1 2030</td></tr></table></main>"""
    result = project_fact_projection(html, "https://developer.example/one", ("Project One",))
    assert result["provisional_fields"]["bedrooms"] == ["1", "2"]
    assert "handover_year" not in result["provisional_fields"]
    assert "123456" not in str(result) and "person@" not in str(result)
    assert (
        project_fact_projection(html, "https://developer.example/one", ("Project Two",))[
            "provisional_fields"
        ]
        == {}
    )


def test_public_omission_is_nonmutating_and_hides_whole_incomplete_plan():
    data = {
        "id": "one",
        "availability_status": "available",
        "amenities": [],
        "size_min": 800,
        "size_max": 1200,
        "down_payment_percentage": 20,
        "payment_plan": {
            "is_complete": False,
            "verified_at": "2026-01-01",
            "milestones": [{"percentage": 20}],
        },
    }
    original = copy.deepcopy(data)
    result = omit_unresolved(data, hidden_fields={"availability_status", "size_range"})
    assert result == {"id": "one", "cta": "request-current-status"}
    assert data == original
    assert omit_unresolved(data, hidden_fields=set(), identity_hold=True) is None


def test_even_complete_payment_is_hidden_when_applicability_conflicts():
    data = {
        "payment_plan": {
            "is_complete": True,
            "verified_at": "2026-01-01",
            "milestones": [{"percentage": 20}, {"percentage": 80}],
        },
        "down_payment_percentage": 20,
    }
    assert omit_unresolved(data, hidden_fields={"payment_plan"}) == {
        "cta": "request-current-status"
    }
    assert "payment_plan" in omit_unresolved(data, hidden_fields=set())
