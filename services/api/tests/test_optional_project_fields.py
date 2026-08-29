import copy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models import UAEEmirate
from app.project_field_policy import (
    candidate_evidence_state,
    candidate_media_is_preview_eligible,
    critical_candidate_errors,
)
from app.public_project_evidence import omit_unresolved, public_evidenced_project
from app.serializers import candidate_public_preview_dict


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


def _candidate_preview_record(payment_plan, *, conflicts=None):
    return SimpleNamespace(
        id="candidate",
        normalized_payload={
            "project_name": "Verified Project",
            "project_name_ar": "مشروع موثق",
            "availability_status": "not-confirmed",
            "construction_status": "not-confirmed",
            "down_payment_percentage": 20,
            "payment_plan": payment_plan,
            "property_types": [],
            "unit_types": [],
            "bedrooms": [],
            "size_ranges": [],
            "amenities": [],
            "nearby_places": [],
        },
        normalized_project_name="Verified Project",
        acquisition_summary={"targeted_field_review": {"states": {}}},
        validation_errors=[],
        conflict_reasons=conflicts or [],
        editorial_draft=None,
        staged_media=[],
    )


def _preview_parties():
    developer = SimpleNamespace(
        slug="verified-developer",
        translations=[
            SimpleNamespace(locale="en", name="Verified Developer"),
            SimpleNamespace(locale="ar", name="مطور موثق"),
        ],
    )
    area = SimpleNamespace(
        emirate=UAEEmirate.SHARJAH,
        name_en="Verified Area",
        name_ar="منطقة موثقة",
    )
    return developer, area


def test_candidate_preview_omits_unknown_statuses_and_incomplete_payment_plan():
    developer, area = _preview_parties()
    record = _candidate_preview_record(
        {
            "is_complete": False,
            "verified_at": "2026-08-29",
            "milestones": [
                {
                    "percentage": 20,
                    "label": "Booking",
                    "due_trigger": "On booking",
                }
            ],
        }
    )

    result = candidate_public_preview_dict(record, developer, area, "en")

    assert not {
        "availability_status",
        "construction_status",
        "down_payment_percentage",
        "payment_plan",
        "payment_milestones",
    } & set(result)


def test_candidate_preview_keeps_only_complete_sanitized_payment_milestones():
    developer, area = _preview_parties()
    plan = {
        "raw_source_text": "20/80",
        "is_complete": True,
        "verified_at": "2026-08-29",
        "milestones": [
            {
                "sequence": 1,
                "stage": "booking",
                "label": "Booking",
                "label_en": "Booking",
                "label_ar": "الحجز",
                "due_trigger": "On booking",
                "percentage": 20,
            },
            {
                "sequence": 2,
                "stage": "handover",
                "label": "Handover",
                "label_en": "Handover",
                "label_ar": "التسليم",
                "due_trigger": "On handover",
                "percentage": 80,
            },
        ],
    }

    result = candidate_public_preview_dict(_candidate_preview_record(plan), developer, area, "ar")

    assert result["payment_plan"] == {
        "raw_source_text": "20/80",
        "is_complete": True,
        "milestones": [
            {
                "sequence": 1,
                "stage": "booking",
                "label_en": "Booking",
                "label_ar": "الحجز",
                "percentage": 20,
            },
            {
                "sequence": 2,
                "stage": "handover",
                "label_en": "Handover",
                "label_ar": "التسليم",
                "percentage": 80,
            },
        ],
    }
    assert "verified_at" not in result["payment_plan"]


def test_candidate_preview_hides_conflicting_payment_group():
    developer, area = _preview_parties()
    record = _candidate_preview_record(
        {
            "is_complete": True,
            "verified_at": "2026-08-29",
            "milestones": [
                {
                    "percentage": 100,
                    "label": "Payment",
                    "due_trigger": "On completion",
                }
            ],
        },
        conflicts=["Source disagreement for down_payment_percentage: 4 | 5."],
    )

    result = candidate_public_preview_dict(record, developer, area, "en")

    assert not {"down_payment_percentage", "payment_plan", "payment_milestones"} & set(result)


def _prepared_media(rights_basis: str):
    return SimpleNamespace(
        stage_status="downloaded",
        rights_status=SimpleNamespace(value="approved"),
        category=SimpleNamespace(value="cover"),
        rights_basis=rights_basis,
        storage_key="prepared/master.webp",
        thumbnail_storage_key="prepared/thumb.webp",
        mime_type="image/webp",
        processed_sha256="a" * 64,
        normalized_filename="verified-project-cover.webp",
        alt_en_draft="Verified Project exterior",
        alt_ar_draft="واجهة مشروع موثق",
        title_en="Verified Project exterior",
        title_ar="واجهة مشروع موثق",
        description_en="Exterior view of Verified Project.",
        description_ar="إطلالة خارجية على مشروع موثق.",
        tags=["verified-project", "exterior"],
        derivative_manifest=[{"format": "webp"}, {"format": "avif"}],
        width=1920,
        height=1080,
    )


def test_candidate_preview_media_rejects_automatic_rights_assumption():
    media = _prepared_media(
        "Automatically approved exact-Project image from a validated candidate source."
    )

    assert not candidate_media_is_preview_eligible(media)


def test_candidate_preview_media_accepts_complete_explicit_permission():
    media = _prepared_media("Developer media kit licensed for broker marketing use.")

    assert candidate_media_is_preview_eligible(media)
