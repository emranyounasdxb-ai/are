from __future__ import annotations

import math
import re
import secrets
import uuid
from datetime import datetime
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit import request_correlation_id, write_audit
from app.config import Settings, get_settings
from app.db import get_db
from app.dependencies import AuthContext, get_redis, require_mutation_permission, require_permission
from app.models import (
    ApplicationStatus,
    CareerApplication,
    ContactEnquiry,
    EnquiryStatus,
    JobOpening,
    JobStatus,
    PrivateFileMetadata,
)
from app.schemas import (
    ApplicationUpdate,
    CareerApplicationInput,
    ContactEnquiryInput,
    EnquiryUpdate,
)
from app.security import enforce_submission_rate_limit, hash_value
from app.storage import PrivateStorage

router = APIRouter(tags=["submissions"])
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{16,200}$")


def _idempotency(value: str) -> str:
    if not IDEMPOTENCY_PATTERN.fullmatch(value):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_idempotency_key",
                "message": "Provide a valid idempotency key.",
            },
        )
    return hash_value(value)


def _reference(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6).upper()}"


def _meta(page: int, size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "page_size": size,
        "total": total,
        "pages": max(1, math.ceil(total / size)),
    }


def enquiry_dict(item: ContactEnquiry) -> dict[str, Any]:
    return {
        "id": item.id,
        "reference_code": item.reference_code,
        "enquiry_type": item.enquiry_type,
        "name": item.name,
        "email": item.email,
        "phone": item.phone,
        "message": item.message,
        "context": item.context,
        "locale": item.locale,
        "preferred_contact_method": item.preferred_contact_method,
        "contact_consent": item.contact_consent,
        "marketing_consent": item.marketing_consent,
        "attribution": item.attribution,
        "status": item.status.value,
        "internal_note": item.internal_note,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def application_dict(item: CareerApplication) -> dict[str, Any]:
    file = item.file
    return {
        "id": item.id,
        "reference_code": item.reference_code,
        "applicant_name": item.applicant_name,
        "email": item.email,
        "phone": item.phone,
        "current_location": item.current_location,
        "job_opening_id": item.job_opening_id,
        "context_label": item.context_label,
        "linkedin_url": item.linkedin_url,
        "portfolio_url": item.portfolio_url,
        "cover_note": item.cover_note,
        "locale": item.locale,
        "acknowledgement_consent": item.acknowledgement_consent,
        "marketing_consent": item.marketing_consent,
        "status": item.status.value,
        "internal_note": item.internal_note,
        "file": None
        if not file
        else {
            "original_filename": file.original_filename,
            "verified_format": file.verified_format,
            "size_bytes": file.size_bytes,
        },
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.post("/public/enquiries", status_code=status.HTTP_201_CREATED)
async def create_enquiry(
    payload: ContactEnquiryInput,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    await enforce_submission_rate_limit(redis, request, "enquiry", settings)
    digest = _idempotency(idempotency_key)
    existing = await db.scalar(
        select(ContactEnquiry).where(ContactEnquiry.idempotency_hash == digest)
    )
    if existing:
        return {"reference_id": existing.reference_code, "duplicate": True}
    record = ContactEnquiry(
        reference_code=_reference("ENQ"),
        enquiry_type=payload.enquiry_type,
        name=payload.name,
        email=str(payload.email),
        phone=payload.phone,
        message=payload.message,
        context={"developer": payload.selected_developer, "property": payload.selected_property},
        locale=payload.locale,
        preferred_contact_method=payload.preferred_contact_method,
        contact_consent=payload.contact_consent,
        marketing_consent=payload.marketing_consent,
        attribution=payload.attribution,
        idempotency_hash=digest,
    )
    db.add(record)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(ContactEnquiry).where(ContactEnquiry.idempotency_hash == digest)
        )
        if existing:
            return {"reference_id": existing.reference_code, "duplicate": True}
        raise
    return {"reference_id": record.reference_code, "duplicate": False}


@router.post("/public/applications", status_code=status.HTTP_201_CREATED)
async def create_application(
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    applicant_name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    current_location: Annotated[str, Form()],
    context_label: Annotated[str, Form()],
    cover_note: Annotated[str, Form()],
    locale: Annotated[str, Form()],
    acknowledgement_consent: Annotated[bool, Form()],
    cv: Annotated[UploadFile, File()],
    job_slug: Annotated[str | None, Form()] = None,
    linkedin_url: Annotated[str | None, Form()] = None,
    portfolio_url: Annotated[str | None, Form()] = None,
    marketing_consent: Annotated[bool, Form()] = False,
    website: Annotated[str, Form()] = "",
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    await enforce_submission_rate_limit(redis, request, "application", settings)
    digest = _idempotency(idempotency_key)
    existing = await db.scalar(
        select(CareerApplication).where(CareerApplication.idempotency_hash == digest)
    )
    if existing:
        return {"reference_id": existing.reference_code, "duplicate": True}
    try:
        payload = CareerApplicationInput.model_validate(
            {
                "applicant_name": applicant_name,
                "email": email,
                "phone": phone,
                "current_location": current_location,
                "job_slug": job_slug,
                "context_label": context_label,
                "linkedin_url": linkedin_url or None,
                "portfolio_url": portfolio_url or None,
                "cover_note": cover_note,
                "locale": locale,
                "acknowledgement_consent": acknowledgement_consent,
                "marketing_consent": marketing_consent,
                "website": website,
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "validation_failed", "message": "Please review the submitted fields."},
        ) from exc
    job = None
    if payload.job_slug:
        job = await db.scalar(
            select(JobOpening).where(
                JobOpening.slug == payload.job_slug, JobOpening.status == JobStatus.OPEN
            )
        )
        if not job:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "job_unavailable",
                    "message": "The selected job is not accepting applications.",
                },
            )
    storage = PrivateStorage(settings)
    stored = await storage.save_cv(cv)
    try:
        record = CareerApplication(
            reference_code=_reference("APP"),
            applicant_name=payload.applicant_name,
            email=str(payload.email),
            phone=payload.phone,
            current_location=payload.current_location,
            job_opening_id=job.id if job else None,
            context_label=payload.context_label,
            linkedin_url=str(payload.linkedin_url) if payload.linkedin_url else None,
            portfolio_url=str(payload.portfolio_url) if payload.portfolio_url else None,
            cover_note=payload.cover_note,
            locale=payload.locale,
            acknowledgement_consent=payload.acknowledgement_consent,
            marketing_consent=payload.marketing_consent,
            idempotency_hash=digest,
        )
        record.file = PrivateFileMetadata(**stored.__dict__)
        db.add(record)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        storage.delete(stored.storage_key)
        existing = await db.scalar(
            select(CareerApplication).where(CareerApplication.idempotency_hash == digest)
        )
        if existing:
            return {"reference_id": existing.reference_code, "duplicate": True}
        raise
    except Exception:
        await db.rollback()
        storage.delete(stored.storage_key)
        raise
    return {"reference_id": record.reference_code, "duplicate": False}


async def _list(
    model: Any,
    page: int,
    page_size: int,
    search: str | None,
    record_status: Any,
    date_from: datetime | None,
    date_to: datetime | None,
    db: AsyncSession,
    extra_filters: list[Any] | None = None,
) -> dict[str, Any]:
    filters: list[Any] = list(extra_filters or [])
    if record_status:
        filters.append(model.status == record_status)
    if search:
        name = model.name if model is ContactEnquiry else model.applicant_name
        filters.append(
            or_(
                model.reference_code.ilike(f"%{search}%"),
                name.ilike(f"%{search}%"),
                model.email.ilike(f"%{search}%"),
            )
        )
    if date_from:
        filters.append(model.created_at >= date_from)
    if date_to:
        filters.append(model.created_at <= date_to)
    total = int(await db.scalar(select(func.count()).select_from(model).where(*filters)) or 0)
    statement = (
        select(model)
        .where(*filters)
        .order_by(model.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if model is CareerApplication:
        statement = statement.options(selectinload(CareerApplication.file))
    items = (await db.scalars(statement)).all()
    serializer = enquiry_dict if model is ContactEnquiry else application_dict
    return {"items": [serializer(item) for item in items], "meta": _meta(page, page_size, total)}


@router.get("/admin/enquiries")
async def list_enquiries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    record_status: EnquiryStatus | None = Query(None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    enquiry_type: str | None = Query(None, max_length=120),
    _: AuthContext = Depends(require_permission("enquiries.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list(
        ContactEnquiry,
        page,
        page_size,
        search,
        record_status,
        date_from,
        date_to,
        db,
        [ContactEnquiry.enquiry_type == enquiry_type] if enquiry_type else None,
    )


@router.get("/admin/enquiries/{record_id}")
async def get_enquiry(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("enquiries.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.get(ContactEnquiry, record_id)
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Enquiry not found."}
        )
    return enquiry_dict(record)


@router.put("/admin/enquiries/{record_id}")
async def update_enquiry(
    record_id: uuid.UUID,
    payload: EnquiryUpdate,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("enquiries.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.get(ContactEnquiry, record_id)
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Enquiry not found."}
        )
    before = {"status": record.status.value, "has_internal_note": bool(record.internal_note)}
    record.status, record.internal_note, record.updated_by = (
        payload.status,
        payload.internal_note,
        context.user.id,
    )
    await write_audit(
        db,
        action="enquiry.update",
        entity_type="enquiry",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"status": record.status.value, "has_internal_note": bool(record.internal_note)},
    )
    await db.commit()
    await db.refresh(record)
    return enquiry_dict(record)


@router.get("/admin/applications")
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    record_status: ApplicationStatus | None = Query(None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    job_opening_id: uuid.UUID | None = None,
    _: AuthContext = Depends(require_permission("applications.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list(
        CareerApplication,
        page,
        page_size,
        search,
        record_status,
        date_from,
        date_to,
        db,
        [CareerApplication.job_opening_id == job_opening_id] if job_opening_id else None,
    )


@router.get("/admin/applications/{record_id}")
async def get_application(
    record_id: uuid.UUID,
    _: AuthContext = Depends(require_permission("applications.read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(CareerApplication)
        .where(CareerApplication.id == record_id)
        .options(selectinload(CareerApplication.file))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Application not found."},
        )
    return application_dict(record)


@router.put("/admin/applications/{record_id}")
async def update_application(
    record_id: uuid.UUID,
    payload: ApplicationUpdate,
    request: Request,
    context: AuthContext = Depends(require_mutation_permission("applications.update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    record = await db.scalar(
        select(CareerApplication)
        .where(CareerApplication.id == record_id)
        .options(selectinload(CareerApplication.file))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Application not found."},
        )
    before = {"status": record.status.value, "has_internal_note": bool(record.internal_note)}
    record.status, record.internal_note, record.updated_by = (
        payload.status,
        payload.internal_note,
        context.user.id,
    )
    await write_audit(
        db,
        action="application.update",
        entity_type="application",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        before=before,
        after={"status": record.status.value, "has_internal_note": bool(record.internal_note)},
    )
    await db.commit()
    await db.refresh(record)
    return application_dict(record)


@router.get("/admin/applications/{record_id}/cv")
async def download_cv(
    record_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_permission("applications.read")),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    record = await db.scalar(
        select(CareerApplication)
        .where(CareerApplication.id == record_id)
        .options(selectinload(CareerApplication.file))
    )
    if not record or not record.file:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "CV not found."}
        )
    content = PrivateStorage(settings).read(record.file.storage_key)
    await write_audit(
        db,
        action="application.cv.accessed",
        entity_type="application",
        entity_id=record.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
        metadata={"format": record.file.verified_format, "size_bytes": record.file.size_bytes},
    )
    await db.commit()
    filename = quote(record.file.original_filename, safe="")
    return Response(
        content,
        media_type=record.file.declared_mime_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
