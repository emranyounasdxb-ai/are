from __future__ import annotations

import asyncio
import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit import request_correlation_id, write_audit
from app.config import Settings, get_settings
from app.db import get_db
from app.dependencies import AuthContext, require_mutation_permission, require_permission
from app.import_review import apply_bulk_action, eligibility_errors
from app.manual_overviews import (
    create_overview_pack,
    import_overview_response,
    pack_dict,
    read_pack_content,
)
from app.models import (
    AreaAlias,
    AreaCommunity,
    ConstructionStatus,
    Developer,
    DiagnosticResolutionStatus,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProcessingItemStatus,
    ProcessingJobStatus,
    Project,
    ProjectAmenity,
    ProjectAvailabilityStatus,
    ProjectBedroomValue,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMedia,
    ProjectMediaCategory,
    ProjectNearbyPlace,
    ProjectOverviewGeneration,
    ProjectOverviewPack,
    ProjectPaymentMilestone,
    ProjectPaymentPlan,
    ProjectPriority,
    ProjectProcessingDiagnostic,
    ProjectProcessingItem,
    ProjectProcessingJob,
    ProjectPropertyType,
    ProjectPropertyTypeValue,
    ProjectRevision,
    ProjectRevisionStatus,
    ProjectSource,
    ProjectSourceType,
    ProjectTranslation,
    ProjectUnitType,
    ProjectWorkflowStatus,
    PublicationStatus,
    UAEEmirate,
)
from app.project_processing import (
    cancel_processing_job,
    create_processing_job,
    diagnostic_dict,
    job_detail,
    job_dict,
    public_media_metadata,
    resolve_diagnostic,
    retry_failed_items,
)
from app.schemas import (
    AreaInput,
    DiagnosticResolutionInput,
    EditorialApprovalInput,
    ImportBulkActionInput,
    ImportCandidateReviewInput,
    ManualOverviewResponse,
    MediaApprovalInput,
    MediaPreparationInput,
    OverviewPackCreateInput,
    ProcessingJobCreateInput,
    ProcessingRetryInput,
    ProjectInput,
    ProjectRevisionActionInput,
    ProjectRevisionInput,
)
from app.serializers import (
    area_dict,
    import_batch_dict,
    import_candidate_dict,
    import_candidate_summary_dict,
    project_dict,
)
from app.storage import PrivateStorage

admin_router = APIRouter(prefix="/admin", tags=["admin-projects"])
public_router = APIRouter(prefix="/public", tags=["public-projects"])

AUTHORITATIVE_SOURCES = {
    ProjectSourceType.DLD_PROJECT_STATUS,
    ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
    ProjectSourceType.OFFICIAL_DEVELOPER_BROCHURE,
    ProjectSourceType.OFFICIAL_MASTER_COMMUNITY_PAGE,
    ProjectSourceType.OWNER_SUPPLIED_DOCUMENT,
    ProjectSourceType.OWNER_APPROVED_PARTNER_FEED,
}


def meta(page: int, page_size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": max(1, math.ceil(total / page_size)),
    }


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


async def project_or_404(record_id: uuid.UUID, db: AsyncSession) -> Project:
    record = await db.scalar(
        select(Project).where(Project.id == record_id).options(*project_options())
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Project not found."},
        )
    return record


def normalize_alias(value: str) -> str:
    return " ".join(value.casefold().replace(",", " ").split())


async def commit_or_conflict(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "record_conflict", "message": "A slug, alias or relation conflicts."},
        ) from exc


async def validate_relations(
    payload: ProjectInput, db: AsyncSession
) -> tuple[Developer, AreaCommunity]:
    developer = await db.get(Developer, payload.developer_id)
    area = await db.get(AreaCommunity, payload.area_id)
    if not developer or not area:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_canonical_relation",
                "message": "Developer and Area must reference canonical records.",
            },
        )
    if area.emirate != payload.emirate:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "project_area_emirate_mismatch",
                "message": "Project Emirate must match the canonical Area Emirate.",
            },
        )
    return developer, area


def validate_publication(record: Project) -> None:
    if record.workflow_status != ProjectWorkflowStatus.APPROVED:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "project_approval_required",
                "message": "The Project must complete review and approval before publication.",
            },
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
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "project_publication_incomplete",
                "message": (
                    "Publishing requires approved bilingual content, canonical published Developer "
                    "and Area records, authoritative provenance, verification, and an approved "
                    "cover."
                ),
            },
        )


def validate_approval(record: Project) -> None:
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
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "project_approval_incomplete",
                "message": (
                    "Approval requires bilingual content, authoritative provenance, Last "
                    "Verified and a manually selected ARE Priority."
                ),
            },
        )


async def replace_project_content(record: Project, payload: ProjectInput, db: AsyncSession) -> None:
    record.slug = payload.slug
    record.developer_id = payload.developer_id
    record.area_id = payload.area_id
    record.emirate = payload.emirate
    record.availability_status = payload.availability_status
    record.construction_status = payload.construction_status
    record.handover_quarter = payload.handover_quarter
    record.handover_year = payload.handover_year
    record.original_handover_value = payload.original_handover_value
    record.size_min = payload.size_min
    record.size_max = payload.size_max
    record.size_unit = payload.size_unit
    record.down_payment_percentage = payload.down_payment_percentage
    record.down_payment_source_value = payload.down_payment_source_value
    record.latitude = payload.latitude
    record.longitude = payload.longitude
    record.last_verified_at = payload.last_verified_at
    record.priority = payload.priority
    record.featured = payload.featured
    record.display_order = payload.display_order
    record.internal_notes = payload.internal_notes
    record.payment_plan = None
    record.translations = []
    record.property_types = []
    record.bedroom_options = []
    record.unit_types = []
    record.amenities = []
    record.nearby_places = []
    await db.flush()
    record.sources = []
    await db.flush()
    record.translations = [
        ProjectTranslation(locale=locale, **translation.model_dump())
        for locale, translation in payload.translations.items()
    ]
    record.property_types = [
        ProjectPropertyTypeValue(property_type=value) for value in payload.property_types
    ]
    record.bedroom_options = [
        ProjectBedroomValue(bedroom_option=value) for value in payload.bedroom_options
    ]
    record.unit_types = [ProjectUnitType(**item.model_dump()) for item in payload.unit_types]
    record.amenities = [ProjectAmenity(**item.model_dump()) for item in payload.amenities]
    record.nearby_places = [
        ProjectNearbyPlace(**item.model_dump()) for item in payload.nearby_places
    ]
    record.sources = [
        ProjectSource(**item.model_dump(exclude={"source_url"}), source_url=str(item.source_url))
        for item in payload.sources
    ]
    existing_media = {item.id: item for item in record.media}
    next_media: list[ProjectMedia] = []
    retained_ids: set[uuid.UUID] = set()
    for item in payload.media:
        media = existing_media.get(item.id) if item.id else None
        values = item.model_dump(exclude={"id", "source_url"})
        if media:
            retained_ids.add(media.id)
            for key, value in values.items():
                setattr(media, key, value)
            media.source_url = str(item.source_url)
        else:
            media = ProjectMedia(**values, source_url=str(item.source_url))
        next_media.append(media)
    next_media.extend(
        item for item in existing_media.values() if item.storage_key and item.id not in retained_ids
    )
    record.media = next_media
    await db.flush()
    if payload.payment_plan:
        source = record.sources[payload.payment_plan.source_index]
        plan = ProjectPaymentPlan(
            raw_source_text=payload.payment_plan.raw_source_text,
            source_id=source.id,
            is_complete=payload.payment_plan.is_complete,
            verified_at=payload.payment_plan.verified_at,
        )
        plan.milestones = [
            ProjectPaymentMilestone(**item.model_dump()) for item in payload.payment_plan.milestones
        ]
        record.payment_plan = plan


@admin_router.get("/areas")
async def list_areas(
    _: AuthContext = Depends(require_permission("project.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    records = (
        await db.scalars(
            select(AreaCommunity)
            .options(selectinload(AreaCommunity.aliases))
            .order_by(AreaCommunity.name_en)
        )
    ).all()
    return {
        "items": [area_dict(item) for item in records],
        "meta": meta(1, max(1, len(records)), len(records)),
    }


@admin_router.post("/areas", status_code=status.HTTP_201_CREATED)
async def create_area(
    payload: AreaInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if (
        payload.status == PublicationStatus.PUBLISHED
        and "project.publish" not in context.permissions
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"code": "permission_denied", "message": "Publish permission is required."},
        )
    record = AreaCommunity(**payload.model_dump(exclude={"aliases"}))
    record.aliases = [
        AreaAlias(
            alias=item.alias, locale=item.locale, normalized_alias=normalize_alias(item.alias)
        )
        for item in payload.aliases
    ]
    db.add(record)
    await write_audit(
        db,
        action="area.create",
        entity_type="area",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record)
    return area_dict(record)


@admin_router.get("/projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    developer_id: uuid.UUID | None = None,
    area_id: uuid.UUID | None = None,
    emirate: UAEEmirate | None = None,
    property_type: ProjectPropertyType | None = None,
    availability: ProjectAvailabilityStatus | None = None,
    construction: ConstructionStatus | None = None,
    publication: PublicationStatus | None = None,
    priority: ProjectPriority | None = None,
    verified_age_days: int | None = Query(None, ge=1, le=3650),
    _: AuthContext = Depends(require_permission("project.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = []
    if developer_id:
        filters.append(Project.developer_id == developer_id)
    if area_id:
        filters.append(Project.area_id == area_id)
    if emirate:
        filters.append(Project.emirate == emirate)
    if availability:
        filters.append(Project.availability_status == availability)
    if construction:
        filters.append(Project.construction_status == construction)
    if publication:
        filters.append(Project.status == publication)
    if priority:
        filters.append(Project.priority == priority)
    if verified_age_days:
        filters.append(
            or_(
                Project.last_verified_at.is_(None),
                Project.last_verified_at < datetime.now(UTC) - timedelta(days=verified_age_days),
            )
        )
    if property_type:
        filters.append(Project.property_types.any(property_type=property_type))
    if search:
        filters.append(
            or_(
                Project.slug.ilike(f"%{search}%"),
                Project.translations.any(ProjectTranslation.official_name.ilike(f"%{search}%")),
            )
        )
    total = int(await db.scalar(select(func.count()).select_from(Project).where(*filters)) or 0)
    records = (
        (
            await db.scalars(
                select(Project)
                .where(*filters)
                .options(*project_options())
                .order_by(Project.display_order, Project.slug)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .unique()
        .all()
    )
    return {"items": [project_dict(item) for item in records], "meta": meta(page, page_size, total)}


@admin_router.get("/projects/{record_id}")
async def get_project(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return project_dict(await project_or_404(record_id, db))


@admin_router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if payload.status == PublicationStatus.PUBLISHED:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "project_publication_incomplete",
                "message": "Create the Project as Draft before review and publication.",
            },
        )
    await validate_relations(payload, db)
    record = Project(
        slug=payload.slug,
        developer_id=payload.developer_id,
        area_id=payload.area_id,
        emirate=payload.emirate,
        status=PublicationStatus.DRAFT,
        workflow_status=ProjectWorkflowStatus.DRAFT,
        availability_status=payload.availability_status,
        construction_status=payload.construction_status,
        translations=[],
        property_types=[],
        bedroom_options=[],
        sources=[],
        media=[],
    )
    db.add(record)
    await replace_project_content(record, payload, db)
    record.created_by = context.user.id
    record.updated_by = context.user.id
    await write_audit(
        db,
        action="project.create",
        entity_type="project",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    return project_dict(await project_or_404(record.id, db))


@admin_router.put("/projects/{record_id}")
async def update_project(
    record_id: uuid.UUID,
    payload: ProjectInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await project_or_404(record_id, db)
    if record.status == PublicationStatus.PUBLISHED:
        if payload.status == PublicationStatus.ARCHIVED:
            record.status = PublicationStatus.ARCHIVED
            record.archived_at = datetime.now(UTC)
            record.updated_by = context.user.id
            await write_audit(
                db,
                action="project.archive",
                entity_type="project",
                entity_id=record.id,
                actor_user_id=context.user.id,
                correlation_id=request_correlation_id(request),
                before={"status": PublicationStatus.PUBLISHED.value},
                after={"status": PublicationStatus.ARCHIVED.value},
            )
            await db.commit()
            return project_dict(await project_or_404(record.id, db))
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "published_project_requires_revision",
                "message": "Create a private revision instead of editing the live Project.",
            },
        )
    await validate_relations(payload, db)
    publishing = payload.status == PublicationStatus.PUBLISHED
    if publishing and "project.publish" not in context.permissions:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"code": "permission_denied", "message": "Publish permission is required."},
        )
    before_sources = sorted(
        (item.source_type.value, item.source_url, item.content_hash, item.is_active)
        for item in record.sources
    )
    before_media_rights = [item.rights_status.value for item in record.media]
    before = {
        "slug": record.slug,
        "status": record.status.value,
        "last_verified_at": str(record.last_verified_at) if record.last_verified_at else None,
        "source_count": len(before_sources),
        "media_rights": before_media_rights,
    }
    await replace_project_content(record, payload, db)
    record.status = payload.status
    if not publishing:
        record.workflow_status = ProjectWorkflowStatus.DRAFT
    record.updated_by = context.user.id
    if publishing:
        await db.flush()
        refreshed = await project_or_404(record.id, db)
        validate_publication(refreshed)
        record.published_at = datetime.now(UTC)
        record.archived_at = None
        baseline_number = (
            int(
                await db.scalar(
                    select(func.max(ProjectRevision.revision_number)).where(
                        ProjectRevision.project_id == record.id
                    )
                )
                or 0
            )
            + 1
        )
        baseline = ProjectRevision(
            project_id=record.id,
            revision_number=baseline_number,
            status=ProjectRevisionStatus.ACTIVE,
            record_snapshot=payload.model_dump(mode="json"),
            media_snapshot=[],
            field_diff={},
            change_summary="Initial approved Published version.",
            created_by=context.user.id,
            submitted_by=context.user.id,
            submitted_at=datetime.now(UTC),
            approved_by=context.user.id,
            approved_at=datetime.now(UTC),
            activated_at=datetime.now(UTC),
        )
        db.add(baseline)
        await db.flush()
        record.active_revision_id = baseline.id
    elif payload.status == PublicationStatus.ARCHIVED:
        record.archived_at = datetime.now(UTC)
    action = (
        "project.publish"
        if publishing
        else "project.archive"
        if payload.status == PublicationStatus.ARCHIVED
        else "project.update"
    )
    after = {"slug": record.slug, "status": record.status.value}
    await write_audit(
        db,
        action=action,
        entity_type="project",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after=after,
    )
    current_sources = sorted(
        (item.source_type.value, item.source_url, item.content_hash, item.is_active)
        for item in record.sources
    )
    if before_sources != current_sources:
        await write_audit(
            db,
            action="project.source.update",
            entity_type="project",
            entity_id=record.id,
            actor_user_id=context.user.id,
            correlation_id=request_correlation_id(request),
            before={"count": len(before_sources)},
            after={"count": len(current_sources)},
        )
    current_media_rights = [item.rights_status.value for item in record.media]
    if before_media_rights != current_media_rights:
        await write_audit(
            db,
            action="project.media-rights.update",
            entity_type="project",
            entity_id=record.id,
            actor_user_id=context.user.id,
            correlation_id=request_correlation_id(request),
            before={"rights": before_media_rights},
            after={"rights": current_media_rights},
        )
    if before["last_verified_at"] != (
        str(record.last_verified_at) if record.last_verified_at else None
    ):
        await write_audit(
            db,
            action="project.verification.update",
            entity_type="project",
            entity_id=record.id,
            actor_user_id=context.user.id,
            correlation_id=request_correlation_id(request),
        )
    await commit_or_conflict(db)
    return project_dict(await project_or_404(record.id, db))


def revision_dict(record: ProjectRevision) -> dict[str, object]:
    return {
        "id": record.id,
        "project_id": record.project_id,
        "revision_number": record.revision_number,
        "status": record.status.value,
        "base_revision_id": record.base_revision_id,
        "record_snapshot": record.record_snapshot,
        "media_snapshot": record.media_snapshot,
        "field_diff": record.field_diff,
        "change_summary": record.change_summary,
        "created_by": record.created_by,
        "submitted_by": record.submitted_by,
        "submitted_at": record.submitted_at,
        "approved_by": record.approved_by,
        "approved_at": record.approved_at,
        "activated_at": record.activated_at,
        "created_at": record.created_at,
    }


async def revision_or_404(
    project_id: uuid.UUID,
    revision_id: uuid.UUID,
    db: AsyncSession,
) -> ProjectRevision:
    revision = await db.scalar(
        select(ProjectRevision)
        .where(
            ProjectRevision.id == revision_id,
            ProjectRevision.project_id == project_id,
        )
        .with_for_update()
    )
    if not revision:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Project revision not found."},
        )
    return revision


@admin_router.get("/projects/{project_id}/revisions")
async def list_project_revisions(
    project_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    await project_or_404(project_id, db)
    revisions = (
        await db.scalars(
            select(ProjectRevision)
            .where(ProjectRevision.project_id == project_id)
            .order_by(ProjectRevision.revision_number.desc())
        )
    ).all()
    return {
        "items": [revision_dict(value) for value in revisions],
        "meta": meta(1, max(1, len(revisions)), len(revisions)),
    }


@admin_router.post(
    "/projects/{project_id}/revisions",
    status_code=status.HTTP_201_CREATED,
)
async def create_project_revision(
    project_id: uuid.UUID,
    payload: ProjectRevisionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    project = await project_or_404(project_id, db)
    if project.status != PublicationStatus.PUBLISHED:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "revision_not_required",
                "message": "Only a live Published Project is edited through revisions.",
            },
        )
    if payload.project.status != PublicationStatus.PUBLISHED:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "revision_publication_state_invalid",
                "message": "A live revision snapshot must retain Published status.",
            },
        )
    await validate_relations(payload.project, db)
    latest_number = int(
        await db.scalar(
            select(func.max(ProjectRevision.revision_number)).where(
                ProjectRevision.project_id == project_id
            )
        )
        or 0
    )
    revision = ProjectRevision(
        project_id=project.id,
        revision_number=latest_number + 1,
        status=ProjectRevisionStatus.DRAFT,
        base_revision_id=project.active_revision_id,
        record_snapshot=payload.project.model_dump(mode="json"),
        media_snapshot=payload.media_snapshot,
        field_diff=payload.field_diff,
        change_summary=payload.change_summary,
        created_by=context.user.id,
    )
    db.add(revision)
    await write_audit(
        db,
        action="project-revision.create",
        entity_type="project-revision",
        entity_id=revision.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"project_id": str(project.id), "revision_number": latest_number + 1},
    )
    await commit_or_conflict(db)
    await db.refresh(revision)
    return revision_dict(revision)


@admin_router.post("/projects/{project_id}/revisions/{revision_id}/submit")
async def submit_project_revision(
    project_id: uuid.UUID,
    revision_id: uuid.UUID,
    payload: ProjectRevisionActionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    revision = await revision_or_404(project_id, revision_id, db)
    if revision.status != ProjectRevisionStatus.DRAFT:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Only a Draft can be submitted.")
    revision.status = ProjectRevisionStatus.IN_REVIEW
    revision.submitted_by = context.user.id
    revision.submitted_at = datetime.now(UTC)
    await write_audit(
        db,
        action="project-revision.submit",
        entity_type="project-revision",
        entity_id=revision.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"note_supplied": bool(payload.note), "status": revision.status.value},
    )
    await db.commit()
    return revision_dict(revision)


@admin_router.post("/projects/{project_id}/revisions/{revision_id}/approve")
async def approve_project_revision(
    project_id: uuid.UUID,
    revision_id: uuid.UUID,
    payload: ProjectRevisionActionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-revision.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    revision = await revision_or_404(project_id, revision_id, db)
    if revision.status != ProjectRevisionStatus.IN_REVIEW:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Only an In Review revision can be approved."
        )
    revision.status = ProjectRevisionStatus.APPROVED
    revision.approved_by = context.user.id
    revision.approved_at = datetime.now(UTC)
    await write_audit(
        db,
        action="project-revision.approve",
        entity_type="project-revision",
        entity_id=revision.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"note_supplied": bool(payload.note), "status": revision.status.value},
    )
    await db.commit()
    return revision_dict(revision)


async def activate_revision(
    project: Project,
    revision: ProjectRevision,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    payload = ProjectInput.model_validate(revision.record_snapshot)
    await validate_relations(payload, db)
    await replace_project_content(project, payload, db)
    project.updated_by = actor_id
    await db.flush()
    refreshed = await project_or_404(project.id, db)
    validate_publication(refreshed)
    if project.active_revision_id and project.active_revision_id != revision.id:
        active = await db.get(ProjectRevision, project.active_revision_id)
        if active:
            active.status = ProjectRevisionStatus.SUPERSEDED
    revision.status = ProjectRevisionStatus.ACTIVE
    revision.activated_at = datetime.now(UTC)
    project.active_revision_id = revision.id


@admin_router.post("/projects/{project_id}/revisions/{revision_id}/activate")
async def activate_project_revision(
    project_id: uuid.UUID,
    revision_id: uuid.UUID,
    payload: ProjectRevisionActionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-revision.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    project = await project_or_404(project_id, db)
    revision = await revision_or_404(project_id, revision_id, db)
    if revision.status != ProjectRevisionStatus.APPROVED:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Only an Approved revision can activate."
        )
    await activate_revision(project, revision, context.user.id, db)
    await write_audit(
        db,
        action="project-revision.activate",
        entity_type="project-revision",
        entity_id=revision.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"note_supplied": bool(payload.note), "revision_number": revision.revision_number},
    )
    await commit_or_conflict(db)
    return revision_dict(revision)


@admin_router.post("/projects/{project_id}/revisions/{revision_id}/rollback")
async def rollback_project_revision(
    project_id: uuid.UUID,
    revision_id: uuid.UUID,
    payload: ProjectRevisionActionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-revision.rollback")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    project = await project_or_404(project_id, db)
    revision = await revision_or_404(project_id, revision_id, db)
    if revision.status != ProjectRevisionStatus.SUPERSEDED or not revision.approved_at:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Rollback requires a previously approved superseded revision.",
        )
    revision.status = ProjectRevisionStatus.APPROVED
    await activate_revision(project, revision, context.user.id, db)
    await write_audit(
        db,
        action="project-revision.rollback",
        entity_type="project-revision",
        entity_id=revision.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"note_supplied": bool(payload.note), "revision_number": revision.revision_number},
    )
    await commit_or_conflict(db)
    return revision_dict(revision)


@admin_router.post("/projects/{record_id}/submit-review")
async def submit_project_for_review(
    record_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await project_or_404(record_id, db)
    if record.status != PublicationStatus.DRAFT:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "invalid_project_state",
                "message": "Only Draft Projects can enter review.",
            },
        )
    record.workflow_status = ProjectWorkflowStatus.IN_REVIEW
    record.updated_by = context.user.id
    await write_audit(
        db,
        action="project.review.submit",
        entity_type="project",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"workflow_status": record.workflow_status.value},
    )
    await db.commit()
    return project_dict(await project_or_404(record.id, db))


@admin_router.post("/projects/{record_id}/approve")
async def approve_project(
    record_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project.publish")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await project_or_404(record_id, db)
    if record.workflow_status != ProjectWorkflowStatus.IN_REVIEW:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "invalid_project_state",
                "message": "Submit the Project for review first.",
            },
        )
    validate_approval(record)
    record.workflow_status = ProjectWorkflowStatus.APPROVED
    record.updated_by = context.user.id
    await write_audit(
        db,
        action="project.approve",
        entity_type="project",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"workflow_status": record.workflow_status.value},
    )
    await db.commit()
    return project_dict(await project_or_404(record.id, db))


@admin_router.post("/projects/{record_id}/media/{media_id}")
async def upload_project_media(
    record_id: uuid.UUID,
    media_id: uuid.UUID,
    request: Request,
    image: UploadFile = File(),
    context: AuthContext = Depends(require_mutation_permission("project.update")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    record = await project_or_404(record_id, db)
    media = next((item for item in record.media if item.id == media_id), None)
    if not media:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Project media not found."},
        )
    stored = await PrivateStorage(settings).save_project_image(image)
    previous_key = media.storage_key
    media.storage_key = stored.storage_key
    media.original_filename = stored.original_filename
    media.mime_type = stored.declared_mime_type
    media.size_bytes = stored.size_bytes
    media.sha256 = stored.sha256
    media.width = stored.width
    media.height = stored.height
    media.uploaded_by = context.user.id
    await write_audit(
        db,
        action="project.media.upload",
        entity_type="project",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={
            "media_id": str(media.id),
            "category": media.category.value,
            "size_bytes": stored.size_bytes,
        },
    )
    await db.commit()
    if previous_key:
        PrivateStorage(settings).delete(previous_key)
    return project_dict(await project_or_404(record.id, db))


@admin_router.get("/project-imports")
async def list_import_batches(
    _: AuthContext = Depends(require_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    records = (
        await db.scalars(select(ProjectImportBatch).order_by(ProjectImportBatch.created_at.desc()))
    ).all()
    return {
        "items": [import_batch_dict(item) for item in records],
        "meta": meta(1, max(1, len(records)), len(records)),
    }


@admin_router.get("/project-imports/{batch_id}")
async def import_batch_detail(
    batch_id: uuid.UUID,
    q: str = Query(default="", max_length=160),
    review_status: str | None = Query(default=None),
    developer_id: uuid.UUID | None = Query(default=None),
    area_id: uuid.UUID | None = Query(default=None),
    area_mapping: Literal["mapped", "unmapped"] | None = Query(default=None),
    official_source: Literal["available", "missing"] | None = Query(default=None),
    missing_evidence: bool | None = Query(default=None),
    arabic_review: Literal["reviewed", "review-required"] | None = Query(default=None),
    has_conflicts: bool | None = Query(default=None),
    media_status: str | None = Query(default=None),
    sort: Literal["row", "project", "status", "last-checked"] = Query(default="row"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=25),
    _: AuthContext = Depends(require_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.id == batch_id)
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            ),
        )
    )
    if not batch:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Import batch not found."},
        )
    all_candidates = list(batch.candidates)
    metrics = {
        "all": len(all_candidates),
        "needs-review": sum(
            item.review_status == ImportReviewStatus.NEEDS_REVIEW for item in all_candidates
        ),
        "failed": sum(item.review_status == ImportReviewStatus.FAILED for item in all_candidates),
        "ready-for-approval": sum(
            item.review_status == ImportReviewStatus.READY_FOR_APPROVAL for item in all_candidates
        ),
        "rejected": sum(
            item.review_status == ImportReviewStatus.REJECTED for item in all_candidates
        ),
        "merged": sum(item.review_status == ImportReviewStatus.MERGED for item in all_candidates),
    }
    normalized_query = q.casefold().strip()
    records = [
        item
        for item in all_candidates
        if (
            not normalized_query
            or normalized_query
            in " ".join(
                (
                    item.normalized_project_name or "",
                    str(item.owner_manifest_values.get("owner_project_name", "")),
                    str(item.owner_manifest_values.get("owner_developer", "")),
                    str(item.owner_manifest_values.get("owner_area", "")),
                    str(item.manifest_row_id),
                )
            ).casefold()
        )
        and (not review_status or item.review_status.value == review_status)
        and (not developer_id or item.proposed_developer_id == developer_id)
        and (not area_id or item.proposed_area_id == area_id)
        and (
            area_mapping is None
            or (item.proposed_area_id is not None) == (area_mapping == "mapped")
        )
        and (
            official_source is None
            or bool(item.official_source_url) == (official_source == "available")
        )
        and (missing_evidence is None or bool(item.validation_errors) == missing_evidence)
        and (
            arabic_review is None
            or item.arabic_review_required == (arabic_review == "review-required")
        )
        and (has_conflicts is None or bool(item.conflict_reasons) == has_conflicts)
        and (
            not media_status
            or any(media.stage_status == media_status for media in item.staged_media)
        )
    ]
    key = {
        "row": lambda item: item.manifest_row_id,
        "project": lambda item: (item.normalized_project_name or "").casefold(),
        "status": lambda item: item.review_status.value,
        "last-checked": lambda item: item.last_verified_at or datetime.min.replace(tzinfo=UTC),
    }[sort]
    records.sort(key=key, reverse=direction == "desc")
    total = len(records)
    start = (page - 1) * page_size
    summaries = {str(item.id): import_candidate_summary_dict(item) for item in records}
    return {
        **import_batch_dict(batch),
        "metrics": metrics,
        "candidates": [summaries[str(item.id)] for item in records[start : start + page_size]],
        "candidate_meta": meta(page, page_size, total),
        "filtered_candidate_ids": [item.id for item in records],
        "all_candidate_ids": [item.id for item in all_candidates],
        "all_candidate_versions": {str(item.id): item.review_version for item in all_candidates},
        "filtered_candidate_versions": {str(item.id): item.review_version for item in records},
        "filtered_candidate_info": {
            str(item.id): {
                "project_name": summaries[str(item.id)]["project_name"],
                "owner_developer": summaries[str(item.id)]["owner_developer"],
                "owner_area": summaries[str(item.id)]["owner_area"],
                "review_status": summaries[str(item.id)]["review_status"],
                "eligibility": summaries[str(item.id)]["eligibility"],
                "processing_eligibility_errors": summaries[str(item.id)][
                    "processing_eligibility_errors"
                ],
            }
            for item in records
        },
        "all_candidate_info": {
            str(item.id): {
                "project_name": import_candidate_summary_dict(item)["project_name"],
                "owner_developer": import_candidate_summary_dict(item)["owner_developer"],
                "owner_area": import_candidate_summary_dict(item)["owner_area"],
                "review_status": import_candidate_summary_dict(item)["review_status"],
                "eligibility": import_candidate_summary_dict(item)["eligibility"],
                "processing_eligibility_errors": import_candidate_summary_dict(item)[
                    "processing_eligibility_errors"
                ],
            }
            for item in all_candidates
        },
    }


@admin_router.post(
    "/project-imports/{batch_id}/processing-jobs",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_processing_job(
    batch_id: uuid.UUID,
    payload: ProcessingJobCreateInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-processing.run")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        job = await create_processing_job(
            db,
            batch_id=batch_id,
            candidate_ids=payload.candidate_ids,
            selection_mode=payload.selection_mode,
            requested_action=payload.requested_action,
            actor_id=context.user.id,
            correlation_id=request_correlation_id(request),
            idempotency_key=payload.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_processing_selection", "message": str(exc)},
        ) from exc
    await write_audit(
        db,
        action="project-processing.start",
        entity_type="project-processing-job",
        entity_id=job.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={
            "selection_mode": payload.selection_mode,
            "selected_count": len(payload.candidate_ids),
            "requested_action": payload.requested_action,
        },
    )
    await db.commit()
    return job_dict(await job_detail(db, job.id))


@admin_router.get("/project-processing-jobs")
async def list_processing_jobs(
    _: AuthContext = Depends(require_permission("project-processing.run")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    jobs = (
        await db.scalars(
            select(ProjectProcessingJob).order_by(ProjectProcessingJob.created_at.desc())
        )
    ).all()
    return {
        "items": [job_dict(value, include_items=False) for value in jobs],
        "meta": meta(1, max(1, len(jobs)), len(jobs)),
    }


@admin_router.get("/project-processing-jobs/{job_id}")
async def get_processing_job(
    job_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project-processing.run")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        return job_dict(await job_detail(db, job_id))
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": str(exc)},
        ) from exc


@admin_router.post("/project-processing-jobs/{job_id}/cancel")
async def cancel_job(
    job_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-processing.run")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        job = await cancel_processing_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await write_audit(
        db,
        action="project-processing.cancel",
        entity_type="project-processing-job",
        entity_id=job.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"cancellation_requested": True},
    )
    await db.commit()
    return job_dict(await job_detail(db, job.id))


@admin_router.post("/project-processing-jobs/{job_id}/retry")
async def retry_job_items(
    job_id: uuid.UUID,
    payload: ProcessingRetryInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-processing.recover")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        job = await retry_failed_items(db, job_id, payload.item_ids)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "retry_not_eligible", "message": str(exc)},
        ) from exc
    await write_audit(
        db,
        action="project-processing.retry",
        entity_type="project-processing-job",
        entity_id=job.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"item_count": len(payload.item_ids or []) or job.failed_count},
    )
    await db.commit()
    return job_dict(await job_detail(db, job.id))


@admin_router.get("/project-recovery")
async def list_project_recovery(
    stage: str | None = Query(default=None, max_length=80),
    error_code: str | None = Query(default=None, max_length=100),
    retryable: bool | None = Query(default=None),
    resolution_status: DiagnosticResolutionStatus | None = Query(default=None),
    job_id: uuid.UUID | None = Query(default=None),
    attempt_count: int | None = Query(default=None, ge=1),
    _: AuthContext = Depends(require_permission("project-processing.recover")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    filters: list[Any] = []
    if stage:
        filters.append(ProjectProcessingDiagnostic.stage == stage)
    if error_code:
        filters.append(ProjectProcessingDiagnostic.error_code == error_code)
    if retryable is not None:
        filters.append(ProjectProcessingDiagnostic.retryable == retryable)
    if resolution_status:
        filters.append(ProjectProcessingDiagnostic.resolution_status == resolution_status)
    if attempt_count:
        filters.append(ProjectProcessingDiagnostic.attempt_count == attempt_count)
    statement = select(ProjectProcessingDiagnostic).join(ProjectProcessingItem)
    if job_id:
        filters.append(ProjectProcessingItem.job_id == job_id)
    diagnostics = (
        await db.scalars(
            statement.where(*filters).order_by(
                ProjectProcessingDiagnostic.latest_occurred_at.desc()
            )
        )
    ).all()
    return {
        "items": [diagnostic_dict(value) for value in diagnostics],
        "meta": meta(1, max(1, len(diagnostics)), len(diagnostics)),
    }


@admin_router.post("/project-recovery/{diagnostic_id}/actions")
async def apply_recovery_action(
    diagnostic_id: uuid.UUID,
    payload: DiagnosticResolutionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-processing.recover")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    if payload.action in {"retry-acquisition", "retry-official-source", "retry-media"}:
        diagnostic_record = await db.get(ProjectProcessingDiagnostic, diagnostic_id)
        if not diagnostic_record:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Processing diagnostic not found."},
            )
        processing_item = await db.get(ProjectProcessingItem, diagnostic_record.item_id)
        if not processing_item:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Processing item not found."},
            )
        candidate = await db.get(ProjectImportCandidate, processing_item.candidate_id)
        if not candidate:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Import candidate not found."},
            )
        if payload.action in {"retry-acquisition", "retry-official-source"}:
            from app.acquisition.tanami import TANAMI_ADAPTER_KEY, refresh_explicit_candidate

            if candidate.adapter_key == TANAMI_ADAPTER_KEY:
                await refresh_explicit_candidate(db, settings, candidate.id)
            else:
                from app.acquisition.sobha_siniya_pilot import (
                    PILOT_ADAPTER_KEY,
                    run_sobha_siniya_pilot,
                )

                if candidate.adapter_key == PILOT_ADAPTER_KEY:
                    await run_sobha_siniya_pilot(db, settings, refresh=True)
        if payload.action == "retry-media":
            from app.acquisition.media_intake import intake_private_media

            await intake_private_media(
                db, settings, candidate.batch_id, candidate_ids=[candidate.id]
            )
    try:
        diagnostic = await resolve_diagnostic(
            db,
            diagnostic_id,
            action=payload.action,
            note=payload.note,
            actor_id=context.user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "unsafe_recovery_action", "message": str(exc)},
        ) from exc
    await write_audit(
        db,
        action=f"project-processing.recovery.{payload.action}",
        entity_type="project-processing-diagnostic",
        entity_id=diagnostic.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"action": payload.action, "note_supplied": True},
    )
    await db.commit()
    return diagnostic_dict(diagnostic)


@admin_router.get("/project-imports/{batch_id}/candidates/{candidate_id}")
async def import_candidate_detail(
    batch_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(
            ProjectImportCandidate.id == candidate_id,
            ProjectImportCandidate.batch_id == batch_id,
        )
        .options(
            selectinload(ProjectImportCandidate.evidence),
            selectinload(ProjectImportCandidate.staged_media),
            selectinload(ProjectImportCandidate.changes),
            selectinload(ProjectImportCandidate.editorial_draft),
        )
    )
    if not candidate:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Import candidate not found."},
        )
    latest_generation = await db.scalar(
        select(ProjectOverviewGeneration)
        .where(ProjectOverviewGeneration.candidate_id == candidate.id)
        .order_by(ProjectOverviewGeneration.generated_at.desc())
        .limit(1)
    )
    return {
        **import_candidate_summary_dict(candidate),
        **import_candidate_dict(candidate),
        "eligibility_errors": eligibility_errors(candidate),
        "overview_provider": {
            "state": (
                "configured"
                if settings.overview_ai_provider
                and settings.overview_ai_model
                and settings.overview_ai_model_version
                and settings.overview_ai_api_key
                else "configuration-required"
            ),
            "message": (
                "Provider configured; generation remains review-gated."
                if settings.overview_ai_provider
                else "Provider configuration required"
            ),
            "required_environment_variables": [
                "ARE_OVERVIEW_AI_PROVIDER",
                "ARE_OVERVIEW_AI_MODEL",
                "ARE_OVERVIEW_AI_MODEL_VERSION",
                "ARE_OVERVIEW_AI_API_KEY",
            ],
        },
        "overview_generation": (
            {
                "state": latest_generation.result_status,
                "fact_guard_result": latest_generation.fact_guard_result,
                "generated_at": latest_generation.generated_at,
                "approval_status": latest_generation.approval_status.value,
            }
            if latest_generation
            else None
        ),
    }


@admin_router.post("/project-imports/{batch_id}/bulk")
async def bulk_import_candidates(
    batch_id: uuid.UUID,
    payload: ImportBulkActionInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    return await apply_bulk_action(db, batch_id, payload, request, context, settings)


@admin_router.get("/project-imports/{batch_id}/overview-packs")
async def list_overview_packs(
    batch_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project-overview-pack.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    packs = (
        await db.scalars(
            select(ProjectOverviewPack)
            .where(ProjectOverviewPack.batch_id == batch_id)
            .options(selectinload(ProjectOverviewPack.items))
            .order_by(ProjectOverviewPack.created_at.desc())
        )
    ).all()
    return {
        "items": [pack_dict(pack) for pack in packs],
        "meta": meta(1, max(1, len(packs)), len(packs)),
    }


@admin_router.post("/project-imports/{batch_id}/overview-packs")
async def prepare_overview_pack(
    batch_id: uuid.UUID,
    payload: OverviewPackCreateInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-overview-pack.manage")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    try:
        pack = await create_overview_pack(
            db,
            settings,
            batch_id=batch_id,
            candidate_ids=payload.candidate_ids,
            expected_versions=payload.expected_versions,
            selection_mode=payload.selection_mode,
            actor_id=context.user.id,
            idempotency_key=payload.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_overview_pack", "message": str(exc)},
        ) from exc
    await write_audit(
        db,
        action="project-overview-pack.prepare",
        entity_type="project-overview-pack",
        entity_id=pack.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={
            "pack_version": pack.pack_version,
            "selected_count": pack.selected_count,
            "eligible_count": pack.eligible_count,
            "ineligible_count": pack.ineligible_count,
        },
    )
    await db.commit()
    return pack_dict(pack)


async def _overview_pack_or_404(db: AsyncSession, pack_id: uuid.UUID) -> ProjectOverviewPack:
    pack = await db.scalar(
        select(ProjectOverviewPack)
        .where(ProjectOverviewPack.id == pack_id)
        .options(selectinload(ProjectOverviewPack.items))
    )
    if not pack:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Overview pack not found."},
        )
    return pack


@admin_router.get("/project-overview-packs/{pack_id}")
async def get_overview_pack(
    pack_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project-overview-pack.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    return pack_dict(await _overview_pack_or_404(db, pack_id))


@admin_router.post("/project-overview-packs/{pack_id}/download")
async def download_overview_pack(
    pack_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-overview-pack.manage")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    pack = await _overview_pack_or_404(db, pack_id)
    try:
        content = await asyncio.to_thread(read_pack_content, pack, settings)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "private_pack_unavailable", "message": str(exc)},
        ) from exc
    await write_audit(
        db,
        action="project-overview-pack.download",
        entity_type="project-overview-pack",
        entity_id=pack.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"pack_hash": pack.pack_hash},
    )
    await db.commit()
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Cache-Control": "private, no-store, max-age=0",
            "Content-Disposition": f'attachment; filename="overview-pack-{pack.id}.json"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@admin_router.post("/project-overview-packs/{pack_id}/import")
async def import_manual_overview_pack(
    pack_id: uuid.UUID,
    request: Request,
    response_file: UploadFile = File(),
    context: AuthContext = Depends(require_mutation_permission("project-overview-pack.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if response_file.content_type not in {"application/json", "application/x-ndjson"}:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_overview_response", "message": "Upload a JSON response file."},
        )
    content = await response_file.read(5 * 1024 * 1024 + 1)
    await response_file.close()
    if not content or len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "code": "invalid_overview_response",
                "message": "Response file is empty or too large.",
            },
        )
    try:
        response = ManualOverviewResponse.model_validate_json(content)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_overview_response", "message": str(exc)},
        ) from exc
    pack = await _overview_pack_or_404(db, pack_id)
    correlation_id = request_correlation_id(request)
    try:
        result = await import_overview_response(
            db, pack=pack, response=response, correlation_id=correlation_id
        )
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "overview_response_mismatch", "message": str(exc)},
        ) from exc
    await write_audit(
        db,
        action="project-overview-pack.import",
        entity_type="project-overview-pack",
        entity_id=pack.id,
        actor_user_id=context.user.id,
        correlation_id=correlation_id,
        after={"imported": result["imported"], "failed": result["failed"]},
    )
    await db.commit()
    return result


@admin_router.get("/project-import-media/{media_id}/thumbnail")
async def import_media_thumbnail(
    media_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    media = await db.get(ProjectImportMedia, media_id)
    if not media or not media.thumbnail_storage_key:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Private thumbnail not found."},
        )
    content = await asyncio.to_thread(PrivateStorage(settings).read, media.thumbnail_storage_key)
    return Response(
        content=content,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
        },
    )


@admin_router.get("/project-import-media/{media_id}/preview")
async def import_media_full_preview(
    media_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    media = await db.get(ProjectImportMedia, media_id)
    if not media or not media.storage_key or not media.mime_type:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Private full-size preview not found."},
        )
    content = await asyncio.to_thread(PrivateStorage(settings).read, media.storage_key)
    return Response(
        content=content,
        media_type=media.mime_type,
        headers={
            "Cache-Control": "private, no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; img-src 'self'; sandbox",
        },
    )


@admin_router.post("/project-imports/candidates/{candidate_id}/overview-approval")
async def approve_candidate_overview(
    candidate_id: uuid.UUID,
    payload: EditorialApprovalInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-editorial.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == candidate_id)
        .options(selectinload(ProjectImportCandidate.editorial_draft))
        .with_for_update()
    )
    if not candidate or not candidate.editorial_draft:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Overview draft not found."},
        )
    draft = candidate.editorial_draft
    if draft.source_version != payload.expected_source_version:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "stale_overview", "message": "The source evidence changed."},
        )
    draft.approval_status = (
        EditorialApprovalStatus.APPROVED if payload.approved else EditorialApprovalStatus.REJECTED
    )
    draft.approved_by = context.user.id
    draft.approved_at = datetime.now(UTC)
    generations = (
        await db.scalars(
            select(ProjectOverviewGeneration).where(
                ProjectOverviewGeneration.candidate_id == candidate.id,
                ProjectOverviewGeneration.source_version == draft.source_version,
            )
        )
    ).all()
    for generation in generations:
        generation.approval_status = draft.approval_status
        generation.approved_by = context.user.id
        generation.approved_at = draft.approved_at
    if payload.approved:
        items = (
            await db.scalars(
                select(ProjectProcessingItem).where(
                    ProjectProcessingItem.candidate_id == candidate.id,
                    ProjectProcessingItem.status == ProcessingItemStatus.FAILED,
                    ProjectProcessingItem.current_stage == "prepare-overview",
                )
            )
        ).all()
        job_ids: set[uuid.UUID] = set()
        for item in items:
            item.status = ProcessingItemStatus.QUEUED
            item.next_retry_at = None
            job_ids.add(item.job_id)
        for job_id in job_ids:
            job = await db.get(ProjectProcessingJob, job_id)
            if job:
                job.status = ProcessingJobStatus.QUEUED
                job.completed_at = None
    await write_audit(
        db,
        action="project-processing.overview.approve"
        if payload.approved
        else "project-processing.overview.reject",
        entity_type="project-import-candidate",
        entity_id=candidate.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"source_version": draft.source_version, "approved": payload.approved},
    )
    await db.commit()
    return import_candidate_dict(candidate)


@admin_router.post("/project-import-media/{media_id}/rights-approval")
async def approve_import_media_rights(
    media_id: uuid.UUID,
    payload: MediaApprovalInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-media.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    media = await db.scalar(
        select(ProjectImportMedia).where(ProjectImportMedia.id == media_id).with_for_update()
    )
    if not media:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project media not found.")
    media.rights_status = (
        MediaRightsStatus.APPROVED if payload.approved else MediaRightsStatus.REJECTED
    )
    media.rights_basis = payload.rights_basis
    media.rights_confirmed_by = context.user.id
    media.rights_confirmed_at = datetime.now(UTC)
    await write_audit(
        db,
        action="project-processing.media-rights.approve"
        if payload.approved
        else "project-processing.media-rights.reject",
        entity_type="project-import-media",
        entity_id=media.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"approved": payload.approved, "rights_basis_supplied": True},
    )
    await db.commit()
    return {
        "id": media.id,
        "rights_status": media.rights_status.value,
        "rights_basis": media.rights_basis,
        "rights_confirmed_at": media.rights_confirmed_at,
    }


@admin_router.put("/project-import-media/{media_id}/preparation")
async def update_import_media_preparation(
    media_id: uuid.UUID,
    payload: MediaPreparationInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    media = await db.scalar(
        select(ProjectImportMedia).where(ProjectImportMedia.id == media_id).with_for_update()
    )
    if not media:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project media not found.")
    candidate = await db.get(ProjectImportCandidate, media.candidate_id)
    if not candidate:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Import candidate not found.")
    media.category = payload.category
    media.display_order = payload.display_order
    media.normalized_filename = payload.normalized_filename
    media.alt_en_draft = payload.alt_en
    media.alt_ar_draft = payload.alt_ar
    media.title_en = payload.title_en
    media.title_ar = payload.title_ar
    media.description_en = payload.description_en
    media.description_ar = payload.description_ar
    media.tags = payload.tags
    project_name = candidate.normalized_project_name or "Project"
    media.public_metadata = public_media_metadata(
        project_name=project_name,
        category=payload.category.value.replace("-", " ").title(),
        title=payload.title_en,
        description=payload.description_en,
        website="https://aliyasrealestate.ae",
    )
    await write_audit(
        db,
        action="project-processing.media-metadata.update",
        entity_type="project-import-media",
        entity_id=media.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={
            "category": media.category.value,
            "display_order": media.display_order,
            "bilingual_metadata_complete": True,
        },
    )
    await db.commit()
    return {
        "id": media.id,
        "category": media.category.value,
        "display_order": media.display_order,
        "normalized_filename": media.normalized_filename,
        "metadata_complete": True,
    }


@admin_router.put("/project-imports/candidates/{candidate_id}")
async def review_import_candidate(
    candidate_id: uuid.UUID,
    payload: ImportCandidateReviewInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == candidate_id)
        .with_for_update()
    )
    if not candidate:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Import candidate not found."},
        )
    if candidate.review_version != payload.expected_version:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_candidate",
                "message": "This candidate changed. Refresh and retry.",
            },
        )
    if candidate.review_status != ImportReviewStatus.NEEDS_REVIEW:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "review_state_locked",
                "message": "Mappings and review decisions can change only while Needs Review.",
            },
        )
    if payload.proposed_developer_id and not await db.get(Developer, payload.proposed_developer_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_developer", "message": "Canonical Developer does not exist."},
        )
    if payload.proposed_area_id and not await db.get(AreaCommunity, payload.proposed_area_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_area", "message": "Canonical Area does not exist."},
        )
    before = {
        "developer_id": str(candidate.proposed_developer_id)
        if candidate.proposed_developer_id
        else None,
        "area_id": str(candidate.proposed_area_id) if candidate.proposed_area_id else None,
        "human_review_completed": candidate.human_review_completed,
    }
    candidate.proposed_developer_id = payload.proposed_developer_id
    candidate.proposed_area_id = payload.proposed_area_id
    candidate.human_review_completed = payload.human_review_completed
    candidate.arabic_review_required = payload.arabic_review_required
    candidate.reviewed_by = context.user.id
    candidate.review_version += 1
    await write_audit(
        db,
        action="project-import.review.update",
        entity_type="project_import_candidate",
        entity_id=candidate.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={
            "developer_id": str(candidate.proposed_developer_id)
            if candidate.proposed_developer_id
            else None,
            "area_id": str(candidate.proposed_area_id) if candidate.proposed_area_id else None,
            "human_review_completed": candidate.human_review_completed,
            "review_version": candidate.review_version,
        },
    )
    await db.commit()
    await db.refresh(candidate)
    return import_candidate_dict(candidate)


@public_router.get("/projects")
async def public_projects(
    locale: Literal["en", "ar"],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    records = (
        (
            await db.scalars(
                select(Project)
                .where(Project.status == PublicationStatus.PUBLISHED)
                .options(*project_options())
                .order_by(Project.featured.desc(), Project.display_order, Project.slug)
            )
        )
        .unique()
        .all()
    )
    return {
        "items": [project_dict(item, locale) for item in records],
        "meta": meta(1, max(1, len(records)), len(records)),
    }


@public_router.get("/projects/{slug}")
async def public_project_detail(
    slug: str,
    locale: Literal["en", "ar"],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(Project)
        .where(Project.slug == slug, Project.status == PublicationStatus.PUBLISHED)
        .options(*project_options())
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Project not found."}
        )
    return project_dict(record, locale)


@public_router.get("/projects/{slug}/media/{media_id}")
async def public_project_media(
    slug: str,
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    record = await db.scalar(
        select(Project)
        .where(Project.slug == slug, Project.status == PublicationStatus.PUBLISHED)
        .options(selectinload(Project.media))
    )
    media = next((item for item in record.media if item.id == media_id), None) if record else None
    if (
        not media
        or media.rights_status != MediaRightsStatus.APPROVED
        or not media.storage_key
        or not media.mime_type
    ):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Project media not found."},
        )
    return Response(
        PrivateStorage(settings).read(media.storage_key),
        media_type=media.mime_type,
        headers={"Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )
