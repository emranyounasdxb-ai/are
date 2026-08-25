from __future__ import annotations

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
from app.models import (
    AreaAlias,
    AreaCommunity,
    ConstructionStatus,
    Developer,
    MediaRightsStatus,
    Project,
    ProjectAvailabilityStatus,
    ProjectBedroomValue,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectMedia,
    ProjectMediaCategory,
    ProjectPaymentMilestone,
    ProjectPaymentPlan,
    ProjectPriority,
    ProjectPropertyType,
    ProjectPropertyTypeValue,
    ProjectSource,
    ProjectSourceType,
    ProjectTranslation,
    PublicationStatus,
)
from app.schemas import AreaInput, ImportCandidateReviewInput, ProjectInput
from app.serializers import (
    area_dict,
    import_batch_dict,
    import_candidate_dict,
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
    return developer, area


def validate_publication(record: Project) -> None:
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


async def replace_project_content(record: Project, payload: ProjectInput, db: AsyncSession) -> None:
    record.slug = payload.slug
    record.developer_id = payload.developer_id
    record.area_id = payload.area_id
    record.availability_status = payload.availability_status
    record.construction_status = payload.construction_status
    record.handover_quarter = payload.handover_quarter
    record.handover_year = payload.handover_year
    record.original_handover_value = payload.original_handover_value
    record.last_verified_at = payload.last_verified_at
    record.priority = payload.priority
    record.featured = payload.featured
    record.display_order = payload.display_order
    record.internal_notes = payload.internal_notes
    record.payment_plan = None
    record.translations = []
    record.property_types = []
    record.bedroom_options = []
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
        status=PublicationStatus.DRAFT,
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
    await validate_relations(payload, db)
    publishing = (
        payload.status == PublicationStatus.PUBLISHED
        and record.status != PublicationStatus.PUBLISHED
    )
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
    record.updated_by = context.user.id
    if publishing:
        await db.flush()
        refreshed = await project_or_404(record.id, db)
        validate_publication(refreshed)
        record.published_at = datetime.now(UTC)
        record.archived_at = None
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
    _: AuthContext = Depends(require_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.id == batch_id)
        .options(selectinload(ProjectImportBatch.candidates))
    )
    if not batch:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Import batch not found."},
        )
    return {
        **import_batch_dict(batch),
        "candidates": [import_candidate_dict(item) for item in batch.candidates],
    }


@admin_router.put("/project-imports/candidates/{candidate_id}")
async def review_import_candidate(
    candidate_id: uuid.UUID,
    payload: ImportCandidateReviewInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("project-import.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    candidate = await db.get(ProjectImportCandidate, candidate_id)
    if not candidate:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Import candidate not found."},
        )
    if payload.linked_project_id and not await db.get(Project, payload.linked_project_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_project", "message": "Linked Project does not exist."},
        )
    before = candidate.review_status.value
    candidate.review_status = payload.review_status
    candidate.linked_project_id = payload.linked_project_id
    candidate.reviewed_by = context.user.id
    await write_audit(
        db,
        action=f"project-import.{payload.review_status.value}",
        entity_type="project_import_candidate",
        entity_id=candidate.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before={"status": before},
        after={
            "status": candidate.review_status.value,
            "linked_project_id": str(candidate.linked_project_id)
            if candidate.linked_project_id
            else None,
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
