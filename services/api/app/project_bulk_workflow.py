"""Fail-closed, audited bulk workflow for linked canonical Projects.

The Import Review workspace supplies the bounded selection and durable
idempotency ledger. Every transition still passes the same Project approval and
publication gates used by the individual editor.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit import request_correlation_id, write_audit
from app.dependencies import AuthContext
from app.models import (
    AreaCommunity,
    Developer,
    ImportReviewStatus,
    MediaRightsStatus,
    Project,
    ProjectImportBatch,
    ProjectImportBulkOperation,
    ProjectImportCandidate,
    ProjectMediaCategory,
    ProjectPaymentPlan,
    ProjectPriority,
    ProjectRevision,
    ProjectRevisionStatus,
    ProjectSourceType,
    ProjectWorkflowStatus,
    PublicationStatus,
)
from app.project_approval import (
    CHECKS,
    RECEIPT_VERSION,
    ProjectApprovalInput,
    ReviewAttestation,
    content_version,
    require_current_receipt,
    technical_blockers,
    validate_review,
)
from app.schemas import ProjectInput, ProjectMediaInput

AUTHORITATIVE_SOURCES = {
    ProjectSourceType.DLD_PROJECT_STATUS,
    ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
    ProjectSourceType.OFFICIAL_DEVELOPER_BROCHURE,
    ProjectSourceType.OFFICIAL_MASTER_COMMUNITY_PAGE,
    ProjectSourceType.OWNER_SUPPLIED_DOCUMENT,
    ProjectSourceType.OWNER_APPROVED_PARTNER_FEED,
}

ProjectBulkAction = Literal[
    "assign-standard-priority",
    "submit-review",
    "approve",
    "publish",
]


class ProjectBulkWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: ProjectBulkAction
    candidate_ids: list[uuid.UUID] = Field(min_length=1, max_length=50)
    expected_candidate_versions: dict[uuid.UUID, int]
    expected_content_versions: dict[uuid.UUID, str]
    idempotency_key: str = Field(
        min_length=16,
        max_length=100,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    checks: dict[str, ReviewAttestation] = Field(default_factory=dict)
    media_permission_reference: str | None = Field(default=None, max_length=2000)
    confirmation: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def validate_selection_and_action(self) -> ProjectBulkWorkflowInput:
        selected = set(self.candidate_ids)
        if len(selected) != len(self.candidate_ids):
            raise ValueError("Project selection must not contain duplicates")
        if set(self.expected_candidate_versions) != selected:
            raise ValueError("Every selected candidate requires an expected version")
        if set(self.expected_content_versions) != selected:
            raise ValueError("Every selected Project requires an expected content version")
        if any(
            not re.fullmatch(r"[a-f0-9]{64}", value)
            for value in self.expected_content_versions.values()
        ):
            raise ValueError("Every expected content version must be a SHA-256 hash")
        if self.action == "approve":
            if set(self.checks) != set(CHECKS):
                raise ValueError("All seven approval checklist attestations are required")
            if not self.media_permission_reference or len(self.media_permission_reference) < 12:
                raise ValueError("A private media permission reference is required")
        elif self.checks or self.media_permission_reference:
            raise ValueError("Approval evidence is accepted only by the approve action")
        if self.action == "publish" and self.confirmation != "PUBLISH":
            raise ValueError("Publish requires the explicit PUBLISH confirmation")
        if self.action != "publish" and self.confirmation is not None:
            raise ValueError("Confirmation is accepted only by the publish action")
        return self


def project_options() -> tuple[Any, ...]:
    return (
        selectinload(Project.developer).selectinload(Developer.translations),
        selectinload(Project.area).selectinload(AreaCommunity.aliases),
        selectinload(Project.translations),
        selectinload(Project.property_types),
        selectinload(Project.bedroom_options),
        selectinload(Project.unit_types),
        selectinload(Project.amenities),
        selectinload(Project.nearby_places),
        selectinload(Project.sources),
        selectinload(Project.payment_plan).selectinload(ProjectPaymentPlan.milestones),
        selectinload(Project.media),
    )


def validate_project_publication(record: Project) -> None:
    if record.workflow_status != ProjectWorkflowStatus.APPROVED:
        raise _unprocessable(
            "project_approval_required",
            "The Project must complete review and approval before publication.",
        )
    translations = {
        item.locale
        for item in record.translations
        if all(
            (
                item.official_name,
                item.short_summary,
                item.full_description,
                item.seo_title,
                item.seo_description,
            )
        )
    }
    authoritative = any(
        item.is_active and item.source_type in AUTHORITATIVE_SOURCES for item in record.sources
    )
    cover = next(
        (
            item
            for item in record.media
            if item.category == ProjectMediaCategory.COVER
            and item.storage_key
            and item.rights_status == MediaRightsStatus.APPROVED
            and item.source_url
            and item.alt_en
            and item.alt_ar
        ),
        None,
    )
    if (
        translations != {"en", "ar"}
        or record.developer.status != PublicationStatus.PUBLISHED
        or record.area.status != PublicationStatus.PUBLISHED
        or not record.last_verified_at
        or not authoritative
        or not cover
    ):
        raise _unprocessable(
            "project_publication_incomplete",
            "Publishing requires approved bilingual content, canonical published Developer "
            "and Area records, authoritative provenance, verification, and an approved cover.",
        )


def validate_project_approval(record: Project) -> None:
    translations = {
        item.locale
        for item in record.translations
        if all((item.official_name, item.short_summary, item.full_description))
    }
    authoritative = any(
        item.is_active and item.source_type in AUTHORITATIVE_SOURCES for item in record.sources
    )
    if (
        translations != {"en", "ar"}
        or not record.last_verified_at
        or not authoritative
        or record.priority is None
    ):
        raise _unprocessable(
            "project_approval_incomplete",
            "Approval requires bilingual content, authoritative provenance, Last Verified "
            "and a manually selected ARE Priority.",
        )


async def project_workflow_state(
    db: AsyncSession, candidates: list[ProjectImportCandidate]
) -> dict[str, dict[str, Any]]:
    linked_ids = {item.linked_project_id for item in candidates if item.linked_project_id}
    if not linked_ids:
        return {}
    projects = (
        (
            await db.scalars(
                select(Project).where(Project.id.in_(linked_ids)).options(*project_options())
            )
        )
        .unique()
        .all()
    )
    by_id = {item.id: item for item in projects}
    result: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        linked_id = candidate.linked_project_id
        project = by_id.get(linked_id) if linked_id else None
        if not project:
            continue
        result[str(candidate.id)] = {
            "project_id": str(project.id),
            "status": project.status.value,
            "workflow_status": project.workflow_status.value,
            "priority": project.priority.value if project.priority else None,
            "content_version": content_version(project),
        }
    return result


async def apply_project_bulk_workflow(
    db: AsyncSession,
    batch_id: uuid.UUID,
    payload: ProjectBulkWorkflowInput,
    request: Request,
    context: AuthContext,
) -> dict[str, Any]:
    required_permission = (
        "project.publish" if payload.action in {"approve", "publish"} else "project.update"
    )
    if required_permission not in context.permissions:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": f"{required_permission} permission is required.",
            },
        )
    batch = await db.get(ProjectImportBatch, batch_id)
    if not batch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Import batch not found.")
    request_hash = _request_hash(payload)
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
                    selectinload(ProjectImportCandidate.editorial_draft),
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
        raise _unprocessable("invalid_selection", "All candidates must belong to the active batch.")
    stale_candidates = [
        item.manifest_row_id
        for item in candidates
        if payload.expected_candidate_versions[item.id] != item.review_version
    ]
    if stale_candidates:
        raise _conflict("stale_selection", f"Candidate rows changed: {stale_candidates}.")
    linked_ids = [item.linked_project_id for item in candidates]
    if any(value is None for value in linked_ids) or len(set(linked_ids)) != len(linked_ids):
        raise _unprocessable(
            "invalid_project_links",
            "Every selected candidate must link to one distinct canonical Project.",
        )
    projects = (
        (
            await db.scalars(
                select(Project)
                .where(Project.id.in_(linked_ids))
                .order_by(Project.id)
                .with_for_update()
                .options(*project_options())
            )
        )
        .unique()
        .all()
    )
    if len(projects) != len(candidates):
        raise _unprocessable("invalid_project_links", "A linked canonical Project is missing.")
    by_id = {item.id: item for item in projects}
    pairs: list[tuple[ProjectImportCandidate, Project]] = []
    for candidate in candidates:
        linked_id = candidate.linked_project_id
        if linked_id is None:
            raise _unprocessable("invalid_project_links", "A linked Project ID is missing.")
        pairs.append((candidate, by_id[linked_id]))
    stale_projects = [
        candidate.manifest_row_id
        for candidate, project in pairs
        if payload.expected_content_versions[candidate.id] != content_version(project)
    ]
    if stale_projects:
        raise _conflict("stale_project_selection", f"Project rows changed: {stale_projects}.")

    for candidate, project in pairs:
        await _validate_action_state(payload.action, candidate, project, db)

    correlation_id = request_correlation_id(request)
    now = datetime.now(UTC)
    for candidate, project in pairs:
        before = _state(project, candidate)
        if payload.action == "assign-standard-priority":
            project.priority = ProjectPriority.B
            project.updated_by = context.user.id
            action = "project.priority.assign"
        elif payload.action == "submit-review":
            project.workflow_status = ProjectWorkflowStatus.IN_REVIEW
            project.updated_by = context.user.id
            action = "project.review.submit"
        elif payload.action == "approve":
            review = ProjectApprovalInput(
                content_version=payload.expected_content_versions[candidate.id],
                checks=payload.checks,
                media_permissions={
                    item.sha256: payload.media_permission_reference
                    for item in project.media
                    if item.sha256
                },
            )
            await validate_review(project, review, db)
            project.workflow_status = ProjectWorkflowStatus.APPROVED
            project.updated_by = context.user.id
            action = "project.approve"
        else:
            await _publish(project, context.user.id, now, db)
            candidate.review_status = ImportReviewStatus.MERGED
            candidate.reviewed_by = context.user.id
            candidate.review_version += 1
            action = "project.publish"
        metadata: dict[str, Any] = {
            "bulk_action": payload.action,
            "selection_size": len(pairs),
            "candidate_id": str(candidate.id),
            "project_id": str(project.id),
        }
        if payload.action == "approve":
            metadata.update(
                {
                    "version": RECEIPT_VERSION,
                    "content_version": payload.expected_content_versions[candidate.id],
                    "reviewer": context.user.display_name,
                    "checks": {key: value.model_dump() for key, value in payload.checks.items()},
                    "media_permissions": {
                        item.sha256: payload.media_permission_reference
                        for item in project.media
                        if item.sha256
                    },
                }
            )
        await write_audit(
            db,
            action=action,
            entity_type="project",
            entity_id=project.id,
            actor_user_id=context.user.id,
            correlation_id=correlation_id,
            before=before,
            after=_state(project, candidate),
            metadata=metadata,
        )
        if payload.action == "publish":
            await write_audit(
                db,
                action="project-import.linked-project.published",
                entity_type="project_import_candidate",
                entity_id=candidate.id,
                actor_user_id=context.user.id,
                correlation_id=correlation_id,
                before={"review_status": ImportReviewStatus.READY_FOR_APPROVAL.value},
                after={"review_status": ImportReviewStatus.MERGED.value},
                metadata={"project_id": str(project.id), "selection_size": len(pairs)},
            )

    if payload.action == "publish":
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

    result = {
        "action": payload.action,
        "affected_count": len(pairs),
        "project_ids": [str(project.id) for _, project in pairs],
        "candidate_ids": [str(candidate.id) for candidate, _ in pairs],
        "correlation_id": correlation_id,
        "message": (
            f"{payload.action.replace('-', ' ').title()} completed for {len(pairs)} Project(s)."
        ),
    }
    db.add(
        ProjectImportBulkOperation(
            batch_id=batch_id,
            idempotency_key=payload.idempotency_key,
            action=f"project-{payload.action}",
            request_hash=request_hash,
            result=result,
            actor_user_id=context.user.id,
        )
    )
    await db.commit()
    return result


async def _validate_action_state(
    action: ProjectBulkAction,
    candidate: ProjectImportCandidate,
    project: Project,
    db: AsyncSession,
) -> None:
    if candidate.review_status != ImportReviewStatus.READY_FOR_APPROVAL:
        raise _conflict(
            "invalid_candidate_state",
            f"Candidate {candidate.manifest_row_id} is not Ready for Approval.",
        )
    if project.status != PublicationStatus.DRAFT:
        raise _conflict("invalid_project_state", "Every selected Project must be Draft.")
    if action == "assign-standard-priority":
        if project.workflow_status != ProjectWorkflowStatus.DRAFT or project.priority is not None:
            raise _conflict(
                "invalid_project_state",
                "Priority B can be assigned only to an unprioritized Draft before review.",
            )
        return
    if project.priority != ProjectPriority.B:
        raise _conflict(
            "invalid_project_priority",
            "Every selected Project must have permanent priority B — Standard visibility.",
        )
    expected_workflow = {
        "submit-review": ProjectWorkflowStatus.DRAFT,
        "approve": ProjectWorkflowStatus.IN_REVIEW,
        "publish": ProjectWorkflowStatus.APPROVED,
    }[action]
    if project.workflow_status != expected_workflow:
        raise _conflict(
            "invalid_project_state",
            f"{action} requires workflow state {expected_workflow.value}.",
        )
    if action == "submit-review":
        blockers = await technical_blockers(project, db)
        if blockers:
            raise _unprocessable("project_review_incomplete", "; ".join(blockers))
    elif action == "approve":
        validate_project_approval(project)
    else:
        validate_project_publication(project)
        await require_current_receipt(project, db)


async def _publish(
    project: Project,
    actor_id: uuid.UUID,
    now: datetime,
    db: AsyncSession,
) -> None:
    if project.active_revision_id:
        raise _conflict("unexpected_active_revision", "A Draft cannot have an active revision.")
    revision_number = (
        int(
            await db.scalar(
                select(func.max(ProjectRevision.revision_number)).where(
                    ProjectRevision.project_id == project.id
                )
            )
            or 0
        )
        + 1
    )
    revision = ProjectRevision(
        project_id=project.id,
        revision_number=revision_number,
        status=ProjectRevisionStatus.ACTIVE,
        record_snapshot=_project_input_snapshot(project),
        media_snapshot=[],
        field_diff={},
        change_summary="Initial approved Published version.",
        created_by=actor_id,
        submitted_by=actor_id,
        submitted_at=now,
        approved_by=actor_id,
        approved_at=now,
        activated_at=now,
    )
    db.add(revision)
    await db.flush()
    project.status = PublicationStatus.PUBLISHED
    project.published_at = now
    project.archived_at = None
    project.active_revision_id = revision.id
    project.updated_by = actor_id


def _project_input_snapshot(project: Project) -> dict[str, Any]:
    sources = list(project.sources)
    source_index = {item.id: index for index, item in enumerate(sources)}
    plan = project.payment_plan
    supported_down_payment = bool(project.down_payment_source_value)
    payload: dict[str, Any] = {
        "slug": project.slug,
        "developer_id": project.developer_id,
        "area_id": project.area_id,
        "emirate": project.emirate,
        "status": PublicationStatus.PUBLISHED,
        "workflow_status": ProjectWorkflowStatus.APPROVED,
        "availability_status": project.availability_status,
        "construction_status": project.construction_status,
        "handover_quarter": project.handover_quarter,
        "handover_year": project.handover_year,
        "original_handover_value": project.original_handover_value,
        "size_min": project.size_min,
        "size_max": project.size_max,
        "size_unit": project.size_unit,
        "down_payment_percentage": (
            project.down_payment_percentage if supported_down_payment else None
        ),
        "down_payment_source_value": (
            project.down_payment_source_value if supported_down_payment else None
        ),
        "latitude": project.latitude,
        "longitude": project.longitude,
        "last_verified_at": project.last_verified_at,
        "priority": project.priority,
        "featured": project.featured,
        "display_order": project.display_order,
        "internal_notes": project.internal_notes,
        "property_types": [item.property_type for item in project.property_types],
        "bedroom_options": [item.bedroom_option for item in project.bedroom_options],
        "unit_types": [
            {
                "label_en": item.label_en,
                "label_ar": item.label_ar,
                "display_order": item.display_order,
            }
            for item in project.unit_types
        ],
        "amenities": [
            {
                "label_en": item.label_en,
                "label_ar": item.label_ar,
                "display_order": item.display_order,
            }
            for item in project.amenities
        ],
        "nearby_places": [
            {
                "name_en": item.name_en,
                "name_ar": item.name_ar,
                "distance_value": item.distance_value,
                "distance_unit": item.distance_unit,
                "travel_time_minutes": item.travel_time_minutes,
                "display_order": item.display_order,
            }
            for item in project.nearby_places
        ],
        "translations": {
            item.locale: {
                "official_name": item.official_name,
                "short_summary": item.short_summary,
                "full_description": item.full_description,
                "seo_title": item.seo_title,
                "seo_description": item.seo_description,
            }
            for item in project.translations
        },
        "sources": [
            {
                "source_url": item.source_url,
                "source_type": item.source_type,
                "is_official": item.is_official,
                "retrieved_at": item.retrieved_at,
                "last_checked_at": item.last_checked_at,
                "content_hash": item.content_hash,
                "source_title": item.source_title,
                "source_developer_domain": item.source_developer_domain,
                "is_active": item.is_active,
            }
            for item in sources
        ],
        "payment_plan": (
            {
                "raw_source_text": plan.raw_source_text,
                "source_index": source_index[plan.source_id],
                "is_complete": plan.is_complete,
                "verified_at": plan.verified_at,
                "milestones": [
                    {
                        "sequence": item.sequence,
                        "stage": item.stage,
                        "label_en": item.label_en,
                        "label_ar": item.label_ar,
                        "percentage": item.percentage,
                        "due_trigger": item.due_trigger,
                        "source_value": item.source_value,
                    }
                    for item in plan.milestones
                ],
            }
            if plan
            else None
        ),
        "media": [
            {
                "id": item.id,
                "category": item.category,
                "source_url": item.source_url,
                "rights_status": item.rights_status,
                "alt_en": item.alt_en,
                "alt_ar": item.alt_ar,
                "display_order": item.display_order,
                "verified_at": item.verified_at,
            }
            for item in project.media
        ],
    }
    return _validated_snapshot_payload(payload)


def _validated_snapshot_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    media = payload.pop("media")
    snapshot = ProjectInput.model_validate({**payload, "media": []}).model_dump(mode="json")
    snapshot["media"] = [
        ProjectMediaInput.model_validate(item).model_dump(mode="json") for item in media
    ]
    return snapshot


def _request_hash(payload: ProjectBulkWorkflowInput) -> str:
    request_data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    return hashlib.sha256(
        json.dumps(request_data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _state(project: Project, candidate: ProjectImportCandidate) -> dict[str, Any]:
    return {
        "project_id": str(project.id),
        "candidate_id": str(candidate.id),
        "status": project.status.value,
        "workflow_status": project.workflow_status.value,
        "priority": project.priority.value if project.priority else None,
        "candidate_review_status": candidate.review_status.value,
    }


def _conflict(code: str, message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, "message": message})


def _unprocessable(code: str, message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": code, "message": message},
    )
