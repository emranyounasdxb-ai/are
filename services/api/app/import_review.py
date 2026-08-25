from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.service import retry_candidates
from app.audit import request_correlation_id, write_audit
from app.config import Settings
from app.dependencies import AuthContext
from app.models import (
    AreaCommunity,
    Developer,
    ImportReviewStatus,
    Project,
    ProjectAvailabilityStatus,
    ProjectBedroomOption,
    ProjectBedroomValue,
    ProjectImportBatch,
    ProjectImportBulkOperation,
    ProjectImportCandidate,
    ProjectPaymentMilestone,
    ProjectPaymentPlan,
    ProjectPropertyType,
    ProjectPropertyTypeValue,
    ProjectSource,
    ProjectSourceType,
    PublicationStatus,
)
from app.schemas import ImportBulkActionInput


def eligibility_errors(candidate: ProjectImportCandidate) -> list[str]:
    errors: list[str] = []
    proposal = candidate.normalized_payload or {}
    if not candidate.proposed_developer_id:
        errors.append("Canonical Developer is required.")
    if not candidate.proposed_area_id:
        errors.append("Canonical Area is required.")
    if not candidate.official_source_url:
        errors.append("An official source is required.")
    if not candidate.normalized_project_name:
        errors.append("A source-grounded project name is required.")
    if candidate.validation_errors:
        errors.append("Missing source-grounded fields must be resolved.")
    if candidate.conflict_reasons:
        errors.append("Source conflicts must be resolved.")
    if candidate.arabic_review_required:
        errors.append("Arabic evidence requires human review.")
    if not candidate.human_review_completed:
        errors.append("Human review must be completed.")
    for key in ("property_types", "bedrooms", "availability_status", "construction_status"):
        if proposal.get(key) in (None, [], {}):
            errors.append(f"{key.replace('_', ' ').title()} is required.")
    return errors


async def apply_bulk_action(
    db: AsyncSession,
    batch_id: uuid.UUID,
    payload: ImportBulkActionInput,
    request: Request,
    context: AuthContext,
    settings: Settings,
) -> dict[str, Any]:
    batch = await db.get(ProjectImportBatch, batch_id)
    if not batch:
        raise _not_found("Import batch not found.")
    request_data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    request_hash = hashlib.sha256(
        json.dumps(request_data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    previous = await db.scalar(
        select(ProjectImportBulkOperation).where(
            ProjectImportBulkOperation.batch_id == batch_id,
            ProjectImportBulkOperation.idempotency_key == payload.idempotency_key,
        )
    )
    if previous:
        if previous.request_hash != request_hash:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail={
                    "code": "idempotency_conflict",
                    "message": "This operation key was already used.",
                },
            )
        return previous.result

    candidates = (
        (
            await db.scalars(
                select(ProjectImportCandidate)
                .where(ProjectImportCandidate.id.in_(payload.candidate_ids))
                .with_for_update()
                .options(
                    selectinload(ProjectImportCandidate.evidence),
                    selectinload(ProjectImportCandidate.staged_media),
                )
            )
        )
        .unique()
        .all()
    )
    if len(candidates) != len(payload.candidate_ids) or any(
        item.batch_id != batch_id for item in candidates
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_selection",
                "message": "All candidates must belong to the active batch.",
            },
        )
    stale = [
        item.manifest_row_id
        for item in candidates
        if payload.expected_versions[item.id] != item.review_version
    ]
    if stale:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_selection",
                "message": f"Rows changed since selection: {stale}. Refresh and retry.",
            },
        )

    if payload.action != "create-drafts" and any(
        item.review_status == ImportReviewStatus.MERGED for item in candidates
    ):
        raise _invalid("Candidates already linked to Draft Projects cannot be changed here.")

    if payload.action == "retry-acquisition" and any(
        item.review_status != ImportReviewStatus.FAILED for item in candidates
    ):
        raise _invalid("Retry is limited to Failed or source-unavailable candidates.")
    if payload.action in {"assign-developer", "assign-area"} and any(
        item.review_status != ImportReviewStatus.NEEDS_REVIEW for item in candidates
    ):
        raise _invalid("Canonical mappings can be changed only while a candidate Needs Review.")

    if payload.action == "assign-developer":
        if not await db.get(Developer, payload.developer_id):
            raise _invalid("Canonical Developer does not exist.")
        for item in candidates:
            item.proposed_developer_id = payload.developer_id
            _remove_mapping_issue(item, "developer")
            item.human_review_completed = False
            item.review_status = ImportReviewStatus.NEEDS_REVIEW
    elif payload.action == "assign-area":
        if not await db.get(AreaCommunity, payload.area_id):
            raise _invalid("Canonical Area does not exist.")
        for item in candidates:
            item.proposed_area_id = payload.area_id
            _remove_mapping_issue(item, "area")
            item.human_review_completed = False
            item.review_status = ImportReviewStatus.NEEDS_REVIEW
    elif payload.action == "reject":
        for item in candidates:
            item.review_status = ImportReviewStatus.REJECTED
            item.rejection_reason = payload.rejection_reason
            item.reviewed_by = context.user.id
    elif payload.action == "mark-ready":
        ineligible = {
            item.manifest_row_id: (
                (
                    ["Candidate must be in Needs Review status."]
                    if item.review_status != ImportReviewStatus.NEEDS_REVIEW
                    else []
                )
                + eligibility_errors(item)
            )
            for item in candidates
            if item.review_status != ImportReviewStatus.NEEDS_REVIEW or eligibility_errors(item)
        }
        if ineligible:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "candidate_ineligible",
                    "message": "One or more selected candidates are not Ready.",
                    "results": [
                        {
                            "candidate_id": str(item.id),
                            "manifest_row": item.manifest_row_id,
                            "outcome": "blocked",
                            "reason": "; ".join(ineligible[item.manifest_row_id]),
                        }
                        for item in candidates
                        if item.manifest_row_id in ineligible
                    ],
                },
            )
        for item in candidates:
            item.review_status = ImportReviewStatus.READY_FOR_APPROVAL
            item.reviewed_by = context.user.id
    elif payload.action == "create-drafts":
        if any(item.review_status != ImportReviewStatus.READY_FOR_APPROVAL for item in candidates):
            raise _invalid("Only Ready candidates can create Draft Projects.")
        for item in candidates:
            item.linked_project_id = (await _create_draft(db, item, context.user.id)).id
            item.review_status = ImportReviewStatus.MERGED
            item.reviewed_by = context.user.id
    elif payload.action == "retry-acquisition":
        await retry_candidates(db, settings, list(candidates))

    if payload.action != "retry-acquisition":
        for item in candidates:
            item.review_version += 1
        statuses = list(
            await db.scalars(
                select(ProjectImportCandidate.review_status).where(
                    ProjectImportCandidate.batch_id == batch_id
                )
            )
        )
        batch.total_count = len(statuses)
        batch.clean_count = statuses.count(ImportReviewStatus.READY_FOR_APPROVAL)
        batch.needs_review_count = statuses.count(ImportReviewStatus.NEEDS_REVIEW)
        batch.failed_count = statuses.count(ImportReviewStatus.FAILED)
    affected = sorted(item.manifest_row_id for item in candidates)
    result = {
        "action": payload.action,
        "affected_count": len(candidates),
        "manifest_rows": affected,
        "message": (
            f"{payload.action.replace('-', ' ').title()} completed for "
            f"{len(candidates)} candidate(s)."
        ),
        "results": [
            {
                "candidate_id": str(item.id),
                "manifest_row": item.manifest_row_id,
                "outcome": "succeeded",
                "reason": "The requested review action completed.",
            }
            for item in candidates
        ],
    }
    for item in candidates:
        await write_audit(
            db,
            action=f"project-import.bulk.{payload.action}",
            entity_type="project_import_candidate",
            entity_id=item.id,
            actor_user_id=context.user.id,
            correlation_id=request_correlation_id(request),
            after={
                "manifest_row_id": item.manifest_row_id,
                "review_status": item.review_status.value,
            },
            metadata={"selection_size": len(candidates)},
        )
    db.add(
        ProjectImportBulkOperation(
            batch_id=batch_id,
            idempotency_key=payload.idempotency_key,
            action=payload.action,
            request_hash=request_hash,
            result=result,
            actor_user_id=context.user.id,
        )
    )
    await db.commit()
    return result


async def _create_draft(
    db: AsyncSession, candidate: ProjectImportCandidate, actor_id: uuid.UUID
) -> Project:
    problems = eligibility_errors(candidate)
    if problems:
        raise _invalid(f"Candidate {candidate.manifest_row_id} is not eligible: {problems}")
    proposal = candidate.normalized_payload or {}
    project_name = candidate.normalized_project_name
    if not project_name:
        raise _invalid("A source-grounded project name is required.")
    slug_root = re.sub(r"[^a-z0-9]+", "-", project_name.casefold()).strip("-")
    slug = f"{slug_root}-{candidate.manifest_row_id}"
    if await db.scalar(select(Project.id).where(Project.slug == slug)):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "draft_exists",
                "message": f"A Draft Project already exists for row {candidate.manifest_row_id}.",
            },
        )
    record = Project(
        slug=slug,
        developer_id=candidate.proposed_developer_id,
        area_id=candidate.proposed_area_id,
        status=PublicationStatus.DRAFT,
        availability_status=ProjectAvailabilityStatus(str(proposal["availability_status"])),
        construction_status=str(proposal["construction_status"]),
        handover_quarter=proposal.get("handover_quarter"),
        handover_year=proposal.get("handover_year"),
        original_handover_value=proposal.get("original_handover_value"),
        last_verified_at=candidate.last_verified_at,
        priority=None,
        featured=False,
        display_order=0,
        created_by=actor_id,
        updated_by=actor_id,
    )
    record.property_types = [
        ProjectPropertyTypeValue(property_type=ProjectPropertyType(str(value)))
        for value in proposal.get("property_types", [])
    ]
    record.bedroom_options = [
        ProjectBedroomValue(bedroom_option=ProjectBedroomOption(str(value)))
        for value in proposal.get("bedrooms", [])
    ]
    record.sources = [
        ProjectSource(
            source_url=candidate.official_source_url,
            source_type=ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
            is_official=True,
            retrieved_at=candidate.extracted_at or datetime.now(UTC),
            last_checked_at=candidate.last_verified_at or datetime.now(UTC),
            content_hash=candidate.content_hash,
            is_active=True,
        )
    ]
    db.add(record)
    await db.flush()
    payment = proposal.get("payment_plan")
    if isinstance(payment, dict) and payment.get("raw_source_text"):
        plan = ProjectPaymentPlan(
            project_id=record.id,
            raw_source_text=str(payment["raw_source_text"]),
            source_id=record.sources[0].id,
            is_complete=bool(payment.get("is_complete")),
            verified_at=candidate.last_verified_at,
        )
        plan.milestones = [
            ProjectPaymentMilestone(
                sequence=int(value.get("sequence", index)),
                stage=str(value.get("stage", "other")),
                label_en=str(value.get("source_value", "Source milestone"))[:240],
                percentage=value.get("percentage"),
                source_value=str(value.get("source_value", "")),
            )
            for index, value in enumerate(payment.get("milestones", []))
            if isinstance(value, dict) and value.get("source_value")
        ]
        record.payment_plan = plan
    return record


def _remove_mapping_issue(candidate: ProjectImportCandidate, field: str) -> None:
    candidate.validation_errors = [
        value
        for value in candidate.validation_errors
        if not (isinstance(value, dict) and str(value.get("field", "")).casefold() == field)
    ]
    candidate.conflict_reasons = [
        value for value in candidate.conflict_reasons if field not in value.casefold()
    ]


def _not_found(message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": message}
    )


def _invalid(message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_import_action", "message": message},
    )
