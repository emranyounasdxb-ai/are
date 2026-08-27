import copy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.project_field_policy import candidate_evidence_state, critical_candidate_errors
from app.public_project_evidence import omit_unresolved, public_evidenced_project


@pytest.mark.parametrize(
    "placeholder", [None, "", "not-confirmed", "Not confirmed", "غير مؤكد", "—", "0"]
)
def test_unknown_optional_rows_are_absent_without_mutating_private_data(placeholder):
    data = {
        "id": "synthetic",
        "availability_status": placeholder,
        "construction_status": placeholder,
        "handover_year": 0,
        "handover_quarter": None,
        "amenities": [{"label": placeholder}],
        "bedroom_options": [placeholder],
        "size_min": 0,
        "size_max": 0,
        "size_unit": "sqft",
        "payment_plan": None,
    }
    before = copy.deepcopy(data)
    assert omit_unresolved(data, hidden_fields=set()) == {
        "id": "synthetic",
        "cta": "request-current-status",
    }
    assert data == before


def test_optional_conflict_hides_full_group_and_identity_conflict_stays_critical():
    summary = {"targeted_field_review": {"states": {"handover": "last-known"}}}
    hidden, hold = candidate_evidence_state(
        summary, [], ["Source disagreement for down_payment_percentage: 4 | 5."]
    )
    assert hidden == {"handover", "down_payment_percentage"}
    assert not hold
    assert not critical_candidate_errors(
        summary, [], ["Source disagreement for down_payment_percentage: 4 | 5."]
    )
    assert critical_candidate_errors({}, [], ["Source disagreement for developer: One | Two."])
    assert critical_candidate_errors({}, [], ["Unclassified source disagreement"])
    assert critical_candidate_errors({}, [{"field": "overview"}], [])


@pytest.mark.parametrize("locale", ["en", "ar"])
@pytest.mark.asyncio
async def test_authenticated_preview_uses_the_same_evidence_and_media_guard(locale):
    candidate = SimpleNamespace(
        acquisition_summary={"targeted_field_review": {"states": {"handover": "historical"}}},
        validation_errors=[{"field": "size_range"}],
        conflict_reasons=["Source disagreement for down_payment_percentage: 4 | 5."],
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=Mock(all=lambda: [candidate])))
    record = SimpleNamespace(id="synthetic", media=[SimpleNamespace(id="one", sha256="a" * 64)])
    data = {
        "id": "synthetic",
        "availability_status": "not-confirmed",
        "construction_status": "not-confirmed",
        "size_min": 1000,
        "size_max": 1200,
        "handover_quarter": "Q4",
        "handover_year": 2025,
        "down_payment_percentage": 4,
        "payment_plan": {"is_complete": True},
        "media": [{"id": "one"}],
    }
    with (
        patch("app.public_project_evidence.project_preview_dict", return_value=data) as serializer,
        patch("app.public_project_evidence.latest_receipt", new=AsyncMock(return_value=None)),
        patch(
            "app.public_project_evidence.permitted_preview_assets",
            new=AsyncMock(return_value=set()),
        ),
    ):
        result = await public_evidenced_project(record, locale, db, preview=True)
    serializer.assert_called_once_with(record, locale)
    assert result == {"id": "synthetic", "cta": "request-current-status", "media": []}
    candidate.acquisition_summary = {"targeted_field_review": {"identity_hold": True}}
    with patch("app.public_project_evidence.project_preview_dict", return_value=data):
        assert await public_evidenced_project(record, locale, db, preview=True) is None


def test_plan_requires_full_percentages_and_explicit_milestone_applicability():
    plan = {
        "is_complete": True,
        "verified_at": "2026-08-27",
        "milestones": [
            {"percentage": 100, "label": "Payment", "due_trigger": None},
        ],
    }
    assert "payment_plan" not in omit_unresolved({"payment_plan": plan}, hidden_fields=set())
    plan["milestones"][0]["due_trigger"] = "On handover"
    assert "payment_plan" in omit_unresolved({"payment_plan": plan}, hidden_fields=set())


@pytest.mark.parametrize("value", ["0.00", 0, "NaN", "Infinity", "-1", "not-confirmed"])
def test_zero_and_invalid_size_values_are_never_public(value):
    assert omit_unresolved(
        {"size_min": value, "size_max": value, "size_unit": "sqft"}, hidden_fields=set()
    ) == {"cta": "request-current-status"}
