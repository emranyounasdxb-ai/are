from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
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
from app.dependencies import (
    AuthContext,
    get_auth_context,
    require_mutation_permission,
    require_permission,
)
from app.models import (
    AuditLog,
    CareerApplication,
    ContactEnquiry,
    Developer,
    DeveloperTranslation,
    InsightPost,
    InsightPostTranslation,
    JobOpening,
    JobOpeningTranslation,
    JobStatus,
    Project,
    ProjectImportCandidate,
    Property,
    PropertyCoverMedia,
    PropertyTranslation,
    PublicationStatus,
    TrustProfile,
)
from app.schemas import (
    DeveloperInput,
    InsightInput,
    JobInput,
    PropertyInput,
    PropertyMediaMetadataInput,
    TrustProfileInput,
)
from app.serializers import (
    developer_dict,
    insight_dict,
    job_dict,
    property_dict,
    trust_profile_dict,
)
from app.storage import PrivateStorage

router = APIRouter(prefix="/admin", tags=["admin"])


def ensure_publish_permission(context: AuthContext, permission: str, publishing: bool) -> None:
    if publishing and permission not in context.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "permission_denied", "message": "Publish permission is required."},
        )


def page_meta(page: int, page_size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": max(1, math.ceil(total / page_size)),
    }


async def commit_or_conflict(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "record_conflict",
                "message": "A record with that slug already exists.",
            },
        ) from exc


async def flush_or_conflict(db: AsyncSession) -> None:
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "record_conflict",
                "message": "A record with that slug already exists.",
            },
        ) from exc


@router.get("/dashboard")
async def dashboard(
    _: AuthContext = Depends(get_auth_context), db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, model in (
        ("properties", Property),
        ("insights", InsightPost),
        ("developers", Developer),
        ("projects", Project),
        ("project_candidates", ProjectImportCandidate),
        ("jobs", JobOpening),
        ("enquiries", ContactEnquiry),
        ("applications", CareerApplication),
    ):
        counts[key] = int(await db.scalar(select(func.count()).select_from(model)) or 0)
    return counts


def apply_developer_payload(
    record: Developer, payload: DeveloperInput, actor_user_id: uuid.UUID
) -> None:
    record.slug = payload.slug
    record.primary_emirate = payload.primary_emirate
    record.other_presence = payload.other_presence
    record.selected_projects = payload.selected_projects
    record.official_website = str(payload.official_website)
    record.source_url = str(payload.source_url)
    record.additional_source_urls = [str(url) for url in payload.additional_source_urls]
    record.verification_date = payload.verification_date
    record.enquiry_types = [str(item) for item in payload.enquiry_types]
    record.featured = payload.featured
    record.display_order = payload.display_order
    record.status = payload.status
    record.updated_by = actor_user_id
    by_locale = {item.locale: item for item in record.translations}
    for locale, translation in payload.translations.items():
        item = by_locale.get(locale) or DeveloperTranslation(developer_id=record.id, locale=locale)
        item.name = translation.name
        item.description = translation.description
        item.focus = translation.focus
        item.verification_note = translation.verification_note
        if item not in record.translations:
            record.translations.append(item)


@router.get("/developers")
async def list_developers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    record_status: PublicationStatus | None = Query(None, alias="status"),
    emirate: str | None = Query(None, max_length=120),
    featured: bool | None = None,
    _: AuthContext = Depends(require_permission("developers.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = []
    if record_status:
        filters.append(Developer.status == record_status)
    if emirate:
        filters.append(Developer.primary_emirate == emirate)
    if featured is not None:
        filters.append(Developer.featured == featured)
    if search:
        filters.append(
            or_(
                Developer.slug.ilike(f"%{search}%"),
                Developer.translations.any(DeveloperTranslation.name.ilike(f"%{search}%")),
            )
        )
    total = int(await db.scalar(select(func.count()).select_from(Developer).where(*filters)) or 0)
    records = (
        await db.scalars(
            select(Developer)
            .where(*filters)
            .options(selectinload(Developer.translations))
            .order_by(Developer.display_order, Developer.slug)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [developer_dict(record) for record in records],
        "meta": page_meta(page, page_size, total),
    }


@router.get("/developers/{record_id}")
async def get_developer(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("developers.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(Developer)
        .where(Developer.id == record_id)
        .options(selectinload(Developer.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Developer not found."},
        )
    return developer_dict(record)


@router.post("/developers", status_code=status.HTTP_201_CREATED)
async def create_developer(
    payload: DeveloperInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("developers.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = Developer(created_by=context.user.id, updated_by=context.user.id)
    apply_developer_payload(record, payload, context.user.id)
    record.published_at = (
        datetime.now(UTC) if payload.status == PublicationStatus.PUBLISHED else None
    )
    db.add(record)
    await flush_or_conflict(db)
    await write_audit(
        db,
        action="developer.publish"
        if payload.status == PublicationStatus.PUBLISHED
        else "developer.create",
        entity_type="developer",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return developer_dict(record)


@router.put("/developers/{record_id}")
async def update_developer(
    record_id: uuid.UUID,
    payload: DeveloperInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("developers.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(Developer)
        .where(Developer.id == record_id)
        .options(selectinload(Developer.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Developer not found."},
        )
    before = {"slug": record.slug, "status": record.status.value}
    publishing = payload.status == PublicationStatus.PUBLISHED and record.status != payload.status
    apply_developer_payload(record, payload, context.user.id)
    if publishing:
        record.published_at = datetime.now(UTC)
    action = (
        "developer.publish"
        if publishing
        else "developer.archive"
        if payload.status == PublicationStatus.ARCHIVED
        else "developer.update"
    )
    await write_audit(
        db,
        action=action,
        entity_type="developer",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return developer_dict(record)


async def developer_for_action(record_id: uuid.UUID, db: AsyncSession) -> Developer:
    record = await db.scalar(
        select(Developer)
        .where(Developer.id == record_id)
        .options(selectinload(Developer.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Developer not found."},
        )
    return record


@router.post("/developers/{record_id}/publish")
async def publish_developer(
    record_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("developers.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await developer_for_action(record_id, db)
    translations = {item.locale: item for item in record.translations}
    if set(translations) != {"en", "ar"} or any(
        not all((item.name, item.description, item.focus, item.verification_note))
        for item in translations.values()
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "publication_incomplete",
                "message": "Complete English, Arabic and provenance fields before publication.",
            },
        )
    before = {"slug": record.slug, "status": record.status.value}
    record.status = PublicationStatus.PUBLISHED
    record.published_at = datetime.now(UTC)
    record.updated_by = context.user.id
    await write_audit(
        db,
        action="developer.publish",
        entity_type="developer",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"slug": record.slug, "status": record.status.value},
    )
    await db.commit()
    await db.refresh(record, attribute_names=["updated_at"])
    return developer_dict(record)


@router.post("/developers/{record_id}/archive")
async def archive_developer(
    record_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("developers.manage")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await developer_for_action(record_id, db)
    before = {"slug": record.slug, "status": record.status.value}
    record.status = PublicationStatus.ARCHIVED
    record.updated_by = context.user.id
    await write_audit(
        db,
        action="developer.archive",
        entity_type="developer",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"slug": record.slug, "status": record.status.value},
    )
    await db.commit()
    await db.refresh(record, attribute_names=["updated_at"])
    return developer_dict(record)


@router.get("/properties")
async def list_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    record_status: PublicationStatus | None = Query(None, alias="status"),
    sort: Literal["updated_at", "slug", "created_at"] = "updated_at",
    direction: Literal["asc", "desc"] = "desc",
    _: AuthContext = Depends(require_permission("property.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = []
    if record_status:
        filters.append(Property.status == record_status)
    if search:
        filters.append(
            or_(Property.slug.ilike(f"%{search}%"), Property.community.ilike(f"%{search}%"))
        )
    total = int(await db.scalar(select(func.count()).select_from(Property).where(*filters)) or 0)
    column = getattr(Property, sort)
    statement = (
        select(Property)
        .where(*filters)
        .options(selectinload(Property.translations), selectinload(Property.cover_media))
        .order_by(column.asc() if direction == "asc" else column.desc(), Property.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = (await db.scalars(statement)).all()
    return {
        "items": [property_dict(record) for record in records],
        "meta": page_meta(page, page_size, total),
    }


@router.get("/properties/{record_id}")
async def get_property(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("property.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(Property)
        .where(Property.id == record_id)
        .options(selectinload(Property.translations), selectinload(Property.cover_media))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Property not found."},
        )
    return property_dict(record)


@router.post("/properties", status_code=status.HTTP_201_CREATED)
async def create_property(
    payload: PropertyInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("property.create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    ensure_publish_permission(
        context, "property.publish", payload.status == PublicationStatus.PUBLISHED
    )
    if payload.status == PublicationStatus.PUBLISHED:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "property_media_incomplete",
                "message": (
                    "Save the property as Draft and add an approved cover before publishing."
                ),
            },
        )
    record = Property(
        **payload.model_dump(exclude={"translations", "external_reference_url"}),
        external_reference_url=str(payload.external_reference_url)
        if payload.external_reference_url
        else None,
        created_by=context.user.id,
        updated_by=context.user.id,
        published_at=None,
    )
    record.translations = [
        PropertyTranslation(locale=locale, **translation.model_dump())
        for locale, translation in payload.translations.items()
    ]
    db.add(record)
    await db.flush()
    await write_audit(
        db,
        action="property.create",
        entity_type="property",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    await db.refresh(record, attribute_names=["cover_media"])
    return property_dict(record)


@router.put("/properties/{record_id}")
async def update_property(
    record_id: uuid.UUID,
    payload: PropertyInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("property.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(Property)
        .where(Property.id == record_id)
        .options(selectinload(Property.translations), selectinload(Property.cover_media))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Property not found."},
        )
    publishing = (
        payload.status == PublicationStatus.PUBLISHED
        and record.status != PublicationStatus.PUBLISHED
    )
    ensure_publish_permission(context, "property.publish", publishing)
    if publishing:
        media = record.cover_media
        if (
            not media
            or not media.storage_key
            or media.rights_status.value != "approved"
            or not media.provenance_url
            or not media.alt_en
            or not media.alt_ar
        ):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "property_media_incomplete",
                    "message": (
                        "Publishing requires an uploaded cover with approved rights, provenance, "
                        "and English/Arabic alternative text."
                    ),
                },
            )
    before = {"slug": record.slug, "status": record.status.value}
    for key, value in payload.model_dump(
        exclude={"translations", "external_reference_url"}
    ).items():
        setattr(record, key, value)
    record.external_reference_url = (
        str(payload.external_reference_url) if payload.external_reference_url else None
    )
    record.updated_by = context.user.id
    if publishing:
        record.published_at = datetime.now(UTC)
    by_locale = {item.locale: item for item in record.translations}
    for locale, translation in payload.translations.items():
        item = by_locale.get(locale) or PropertyTranslation(property_id=record.id, locale=locale)
        item.title = translation.title
        item.description = translation.description
        if item not in record.translations:
            record.translations.append(item)
    action = (
        "property.publish"
        if publishing
        else (
            "property.archive"
            if payload.status == PublicationStatus.ARCHIVED
            else "property.update"
        )
    )
    await write_audit(
        db,
        action=action,
        entity_type="property",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return property_dict(record)


async def _property_with_media(record_id: uuid.UUID, db: AsyncSession) -> Property:
    record = await db.scalar(
        select(Property)
        .where(Property.id == record_id)
        .options(selectinload(Property.translations), selectinload(Property.cover_media))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Property not found."},
        )
    return record


@router.post("/properties/{record_id}/cover")
async def upload_property_cover(
    record_id: uuid.UUID,
    request: Request,
    image: UploadFile = File(),
    context: AuthContext = Depends(require_mutation_permission("property.update")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    record = await _property_with_media(record_id, db)
    stored = await PrivateStorage(settings).save_property_image(image)
    media = record.cover_media or PropertyCoverMedia(
        property_id=record.id, provenance_url="", uploaded_by=context.user.id
    )
    previous_key = media.storage_key
    media.storage_key = stored.storage_key
    media.original_filename = stored.original_filename
    media.mime_type = stored.declared_mime_type
    media.size_bytes = stored.size_bytes
    media.sha256 = stored.sha256
    media.width = stored.width
    media.height = stored.height
    media.uploaded_by = context.user.id
    if not record.cover_media:
        db.add(media)
    await write_audit(
        db,
        action="property.cover.upload",
        entity_type="property",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"format": stored.verified_format, "size_bytes": stored.size_bytes},
    )
    await db.commit()
    if previous_key:
        PrivateStorage(settings).delete(previous_key)
    refreshed = await _property_with_media(record_id, db)
    return property_dict(refreshed)


@router.put("/properties/{record_id}/cover")
async def update_property_cover_metadata(
    record_id: uuid.UUID,
    payload: PropertyMediaMetadataInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("property.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await _property_with_media(record_id, db)
    if record.status == PublicationStatus.PUBLISHED and (
        payload.rights_status.value != "approved" or not payload.alt_en or not payload.alt_ar
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "property_media_incomplete",
                "message": (
                    "Published property media must retain approved rights, provenance, and "
                    "English/Arabic alternative text."
                ),
            },
        )
    media = record.cover_media or PropertyCoverMedia(
        property_id=record.id, uploaded_by=context.user.id
    )
    before = {
        "rights_status": media.rights_status.value if record.cover_media else None,
        "provenance_url": media.provenance_url if record.cover_media else None,
    }
    media.alt_en = payload.alt_en or None
    media.alt_ar = payload.alt_ar or None
    media.provenance_url = str(payload.provenance_url)
    media.rights_status = payload.rights_status
    if not record.cover_media:
        db.add(media)
    await write_audit(
        db,
        action="property.cover.update",
        entity_type="property",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"rights_status": media.rights_status.value, "provenance_url": media.provenance_url},
    )
    await db.commit()
    refreshed = await _property_with_media(record_id, db)
    return property_dict(refreshed)


@router.get("/properties/{record_id}/cover")
async def admin_property_cover(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("property.read")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    record = await _property_with_media(record_id, db)
    if (
        not record.cover_media
        or not record.cover_media.storage_key
        or not record.cover_media.mime_type
    ):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Cover image not found."},
        )
    return Response(
        PrivateStorage(settings).read(record.cover_media.storage_key),
        media_type=record.cover_media.mime_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/trust-profile")
async def get_trust_profile(
    _: AuthContext = Depends(require_permission("property.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(select(TrustProfile).limit(1))
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Trust profile not found."},
        )
    return trust_profile_dict(record)


@router.put("/trust-profile")
async def update_trust_profile(
    payload: TrustProfileInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("property.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(select(TrustProfile).limit(1))
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Trust profile not found."},
        )
    before = trust_profile_dict(record)
    for key, value in payload.model_dump(exclude={"google_business_url"}).items():
        setattr(record, key, value)
    record.google_business_url = str(payload.google_business_url)
    record.updated_by = context.user.id
    await write_audit(
        db,
        action="trust_profile.update",
        entity_type="trust_profile",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after=trust_profile_dict(record),
    )
    await db.commit()
    await db.refresh(record)
    return trust_profile_dict(record)


@router.get("/insights")
async def list_insights(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    record_status: PublicationStatus | None = Query(None, alias="status"),
    _: AuthContext = Depends(require_permission("content.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = []
    if record_status:
        filters.append(InsightPost.status == record_status)
    if search:
        filters.append(InsightPost.slug.ilike(f"%{search}%"))
    total = int(await db.scalar(select(func.count()).select_from(InsightPost).where(*filters)) or 0)
    records = (
        await db.scalars(
            select(InsightPost)
            .where(*filters)
            .options(selectinload(InsightPost.translations))
            .order_by(InsightPost.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [insight_dict(record) for record in records],
        "meta": page_meta(page, page_size, total),
    }


@router.get("/insights/{record_id}")
async def get_insight(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("content.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(InsightPost)
        .where(InsightPost.id == record_id)
        .options(selectinload(InsightPost.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Insight not found."}
        )
    return insight_dict(record)


@router.post("/insights", status_code=status.HTTP_201_CREATED)
async def create_insight(
    payload: InsightInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    ensure_publish_permission(
        context, "content.publish", payload.status == PublicationStatus.PUBLISHED
    )
    record = InsightPost(
        slug=payload.slug,
        category=payload.category,
        author_display_name=payload.author_display_name,
        source_links=[{"name": item.name, "url": str(item.url)} for item in payload.source_links],
        status=payload.status,
        published_at=datetime.now(UTC) if payload.status == PublicationStatus.PUBLISHED else None,
        created_by=context.user.id,
        updated_by=context.user.id,
    )
    record.translations = [
        InsightPostTranslation(locale=locale, **translation.model_dump())
        for locale, translation in payload.translations.items()
    ]
    db.add(record)
    await db.flush()
    await write_audit(
        db,
        action="content.publish"
        if payload.status == PublicationStatus.PUBLISHED
        else "content.create",
        entity_type="insight",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return insight_dict(record)


@router.put("/insights/{record_id}")
async def update_insight(
    record_id: uuid.UUID,
    payload: InsightInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("content.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(InsightPost)
        .where(InsightPost.id == record_id)
        .options(selectinload(InsightPost.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Insight not found."}
        )
    publishing = (
        payload.status == PublicationStatus.PUBLISHED
        and record.status != PublicationStatus.PUBLISHED
    )
    ensure_publish_permission(context, "content.publish", publishing)
    before = {"slug": record.slug, "status": record.status.value}
    record.slug = payload.slug
    record.category = payload.category
    record.author_display_name = payload.author_display_name
    record.source_links = [
        {"name": item.name, "url": str(item.url)} for item in payload.source_links
    ]
    record.status = payload.status
    record.updated_by = context.user.id
    if publishing:
        record.published_at = datetime.now(UTC)
    by_locale = {item.locale: item for item in record.translations}
    for locale, translation in payload.translations.items():
        item = by_locale.get(locale) or InsightPostTranslation(
            insight_post_id=record.id, locale=locale
        )
        item.title = translation.title
        item.excerpt = translation.excerpt
        item.body = translation.body
        item.seo_title = translation.seo_title
        item.seo_description = translation.seo_description
        if item not in record.translations:
            record.translations.append(item)
    action = (
        "content.publish"
        if publishing
        else (
            "content.archive" if payload.status == PublicationStatus.ARCHIVED else "content.update"
        )
    )
    await write_audit(
        db,
        action=action,
        entity_type="insight",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return insight_dict(record)


@router.get("/jobs")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    record_status: JobStatus | None = Query(None, alias="status"),
    _: AuthContext = Depends(require_permission("careers.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = []
    if record_status:
        filters.append(JobOpening.status == record_status)
    if search:
        filters.append(
            or_(JobOpening.slug.ilike(f"%{search}%"), JobOpening.department.ilike(f"%{search}%"))
        )
    total = int(await db.scalar(select(func.count()).select_from(JobOpening).where(*filters)) or 0)
    records = (
        await db.scalars(
            select(JobOpening)
            .where(*filters)
            .options(selectinload(JobOpening.translations))
            .order_by(JobOpening.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [job_dict(record) for record in records],
        "meta": page_meta(page, page_size, total),
    }


@router.get("/jobs/{record_id}")
async def get_job(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("careers.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(JobOpening)
        .where(JobOpening.id == record_id)
        .options(selectinload(JobOpening.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Job not found."}
        )
    return job_dict(record)


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("careers.create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    ensure_publish_permission(context, "careers.publish", payload.status == JobStatus.OPEN)
    record = JobOpening(
        **payload.model_dump(exclude={"translations"}),
        created_by=context.user.id,
        updated_by=context.user.id,
    )
    record.translations = [
        JobOpeningTranslation(locale=locale, **translation.model_dump())
        for locale, translation in payload.translations.items()
    ]
    db.add(record)
    await db.flush()
    await write_audit(
        db,
        action="job.open" if payload.status == JobStatus.OPEN else "job.create",
        entity_type="job",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return job_dict(record)


@router.put("/jobs/{record_id}")
async def update_job(
    record_id: uuid.UUID,
    payload: JobInput,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("careers.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(JobOpening)
        .where(JobOpening.id == record_id)
        .options(selectinload(JobOpening.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Job not found."}
        )
    opening = payload.status == JobStatus.OPEN and record.status != JobStatus.OPEN
    ensure_publish_permission(context, "careers.publish", opening)
    before = {"slug": record.slug, "status": record.status.value}
    for key, value in payload.model_dump(exclude={"translations"}).items():
        setattr(record, key, value)
    record.updated_by = context.user.id
    by_locale = {item.locale: item for item in record.translations}
    for locale, translation in payload.translations.items():
        item = by_locale.get(locale) or JobOpeningTranslation(
            job_opening_id=record.id, locale=locale
        )
        item.title = translation.title
        item.description = translation.description
        item.responsibilities = translation.responsibilities
        item.requirements = translation.requirements
        item.benefits = translation.benefits
        if item not in record.translations:
            record.translations.append(item)
    action = (
        "job.open"
        if opening
        else (
            "job.close"
            if payload.status == JobStatus.CLOSED
            else ("job.archive" if payload.status == JobStatus.ARCHIVED else "job.update")
        )
    )
    await write_audit(
        db,
        action=action,
        entity_type="job",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"slug": record.slug, "status": record.status.value},
    )
    await commit_or_conflict(db)
    await db.refresh(record, attribute_names=["updated_at"])
    return job_dict(record)


@router.get("/audit")
async def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: str | None = Query(None, max_length=120),
    _: AuthContext = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters = [AuditLog.action.ilike(f"%{action}%")] if action else []
    total = int(await db.scalar(select(func.count()).select_from(AuditLog).where(*filters)) or 0)
    records = (
        await db.scalars(
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.occurred_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    items = [
        {
            "id": r.id,
            "actor_user_id": r.actor_user_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "occurred_at": r.occurred_at,
            "outcome": r.outcome,
            "before_summary": r.before_summary,
            "after_summary": r.after_summary,
            "request_correlation_id": r.request_correlation_id,
            "metadata_summary": r.metadata_summary,
        }
        for r in records
    ]
    return {"items": items, "meta": page_meta(page, page_size, total)}
