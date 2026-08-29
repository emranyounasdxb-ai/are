from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.import_review import eligibility_errors
from app.models import (
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportCandidate,
    ProjectImportEditorialDraft,
    ProjectImportMedia,
    ProjectMediaCategory,
    ProjectProcessingStatus,
)
from app.serializers import import_candidate_summary_dict


def candidate() -> ProjectImportCandidate:
    return ProjectImportCandidate(
        id=uuid4(),
        manifest_row_id=1,
        normalized_project_name="Synthetic reviewed project",
        owner_manifest_values={},
        proposed_developer_id=uuid4(),
        proposed_area_id=uuid4(),
        official_source_url="https://developer.example/project",
        source_urls=["https://developer.example/project"],
        normalized_payload={},
        acquisition_summary={
            "source_first_research": {
                "exact_documents": ["https://developer.example/project"],
                "context_review_completed": True,
            }
        },
        validation_errors=[],
        conflict_reasons=[],
        human_review_completed=True,
        arabic_review_required=False,
        review_status=ImportReviewStatus.NEEDS_REVIEW,
        processing_status=ProjectProcessingStatus.NEEDS_REVIEW,
        review_version=1,
        staged_media=[
            ProjectImportMedia(
                category=ProjectMediaCategory.COVER,
                source_url="aliyas-generated://project/qa/cover/one",
                rights_status=MediaRightsStatus.APPROVED,
                rights_basis="Owner-authorized ALIYAS-owned conceptual illustration.",
                stage_status="downloaded",
                storage_key="qa-cover.webp",
                thumbnail_storage_key="qa-cover-thumb.webp",
                mime_type="image/webp",
                width=1920,
                height=1080,
                processed_sha256="a" * 64,
                normalized_filename="qa-project-cover-01-aaaaaaaaaaaa.webp",
                alt_en_draft="Conceptual cover for QA Project",
                alt_ar_draft="غلاف تصوري لمشروع الاختبار",
                title_en="QA Project conceptual cover",
                title_ar="غلاف تصوري لمشروع الاختبار",
                description_en="ALIYAS-owned conceptual illustration.",
                description_ar="تصميم تصوري مملوك لإلياس.",
                tags=["QA Project", "conceptual illustration"],
                derivative_manifest=[{"format": "webp"}, {"format": "avif"}],
            )
        ],
        editorial_draft=ProjectImportEditorialDraft(
            overview_en="A reviewed factual English Overview.",
            overview_ar="نظرة عامة عربية واقعية تمت مراجعتها.",
            source_version="a" * 64,
            approval_status=EditorialApprovalStatus.APPROVED,
            generated_at=datetime.now(UTC),
        ),
        updated_at=datetime.now(UTC),
    )


def test_cms_mark_ready_uses_backend_result_with_hidden_optional_gaps() -> None:
    record = candidate()
    record.validation_errors = [
        {"code": "missing_source_evidence", "field": field}
        for field in (
            "availability_status",
            "construction_status",
            "handover",
            "bedrooms",
            "size_range",
            "amenities",
            "payment_plan",
        )
    ]
    record.conflict_reasons = ["Source disagreement for down_payment_percentage: 4 | 5."]
    record.acquisition_summary = {
        **record.acquisition_summary,
        "targeted_field_review": {"states": {"handover_year": "last-known"}},
    }
    before = deepcopy(
        (record.validation_errors, record.conflict_reasons, record.acquisition_summary)
    )
    assert eligibility_errors(record) == []
    result = import_candidate_summary_dict(record)
    assert result["blockers"] == eligibility_errors(record)
    assert result["eligibility"]["mark-ready"] is True
    assert result["missing_fields"]  # Private evidence remains visible for review.
    assert result["conflict_count"] == 1
    assert (record.validation_errors, record.conflict_reasons, record.acquisition_summary) == before
    assert record.review_status == ImportReviewStatus.NEEDS_REVIEW


def test_rejected_private_gallery_evidence_does_not_block_an_eligible_cover() -> None:
    record = candidate()
    record.staged_media.append(
        ProjectImportMedia(
            category=ProjectMediaCategory.GALLERY,
            source_url="https://portal.example/private-evidence.webp",
            rights_status=MediaRightsStatus.REJECTED,
            rights_basis="Reuse permission is not documented.",
            stage_status="downloaded",
            storage_key="private-evidence.webp",
            thumbnail_storage_key="private-evidence-thumb.webp",
            mime_type="image/webp",
            width=1920,
            height=1080,
            processed_sha256="b" * 64,
            normalized_filename="private-evidence.webp",
            derivative_manifest=[{"format": "webp"}, {"format": "avif"}],
        )
    )

    assert eligibility_errors(record) == []
    result = import_candidate_summary_dict(record)
    assert result["eligibility"]["mark-ready"] is True


def test_ready_candidate_can_return_to_review_without_reopening_other_actions() -> None:
    record = candidate()
    record.review_status = ImportReviewStatus.READY_FOR_APPROVAL

    result = import_candidate_summary_dict(record)

    assert result["eligibility"]["return-to-review"] is True
    assert result["eligibility"]["mark-ready"] is False
    assert result["eligibility"]["assign-area"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("proposed_developer_id", None),
        ("proposed_area_id", None),
        ("official_source_url", None),
        ("normalized_project_name", None),
        ("human_review_completed", False),
        ("arabic_review_required", True),
        ("acquisition_summary", {"targeted_field_review": {"identity_hold": True}}),
        ("conflict_reasons", ["Source disagreement for developer: One | Two."]),
        ("conflict_reasons", ["Unclassified source disagreement"]),
        ("validation_errors", [{"field": "official_project_source"}]),
        ("validation_errors", [{"field": "overview"}]),
        ("validation_errors", [{"field": "cover"}]),
        ("validation_errors", [{"field": "media_rights"}]),
        ("editorial_draft", None),
        ("staged_media", []),
        ("acquisition_summary", {"source_first_research": {"exact_documents": []}}),
    ],
)
def test_cms_retains_each_backend_critical_blocker(field: str, value: object) -> None:
    record = candidate()
    setattr(record, field, value)
    errors = eligibility_errors(record)
    assert errors
    result = import_candidate_summary_dict(record)
    assert result["blockers"] == errors
    assert result["eligibility"]["mark-ready"] is False


@pytest.mark.parametrize("status", list(ImportReviewStatus))
def test_cms_mark_ready_preserves_transition_state(status: ImportReviewStatus) -> None:
    record = candidate()
    record.review_status = status
    result = import_candidate_summary_dict(record)
    assert result["eligibility"]["mark-ready"] == (status == ImportReviewStatus.NEEDS_REVIEW)
    assert record.review_status == status
