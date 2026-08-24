from __future__ import annotations

import math
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.db import get_db
from app.models import InsightPost, JobOpening, JobStatus, Property, PublicationStatus, Purpose
from app.serializers import insight_dict, job_dict, property_dict

router = APIRouter(prefix="/public", tags=["public"])


def meta(page: int, page_size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": max(1, math.ceil(total / page_size)),
    }


@router.get("/properties")
async def properties(
    locale: Literal["en", "ar"],
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    purpose: Purpose | None = None,
    property_type: str | None = Query(None, max_length=120),
    emirate: str | None = Query(None, max_length=120),
    sort: Literal["newest", "price-asc", "price-desc"] = "newest",
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = [Property.status == PublicationStatus.PUBLISHED]
    if search:
        filters.append(
            or_(Property.slug.ilike(f"%{search}%"), Property.community.ilike(f"%{search}%"))
        )
    if purpose:
        filters.append(Property.purpose == purpose)
    if property_type:
        filters.append(Property.property_type == property_type)
    if emirate:
        filters.append(Property.emirate == emirate)
    total = int(await db.scalar(select(func.count()).select_from(Property).where(*filters)) or 0)
    order: ColumnElement[Any]
    if sort == "price-asc":
        order = Property.price.asc().nullslast()
    elif sort == "price-desc":
        order = Property.price.desc().nullslast()
    else:
        order = Property.published_at.desc()
    records = (
        await db.scalars(
            select(Property)
            .where(*filters)
            .options(selectinload(Property.translations))
            .order_by(order, Property.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [property_dict(record, locale) for record in records],
        "meta": meta(page, page_size, total),
    }


@router.get("/properties/{slug}")
async def property_detail(
    slug: str, locale: Literal["en", "ar"], db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    record = await db.scalar(
        select(Property)
        .where(Property.slug == slug, Property.status == PublicationStatus.PUBLISHED)
        .options(selectinload(Property.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Property not found."},
        )
    return property_dict(record, locale)


@router.get("/insights")
async def insights(
    locale: Literal["en", "ar"],
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    category: str | None = Query(None, max_length=120),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = [InsightPost.status == PublicationStatus.PUBLISHED]
    if search:
        filters.append(InsightPost.slug.ilike(f"%{search}%"))
    if category:
        filters.append(InsightPost.category == category)
    total = int(await db.scalar(select(func.count()).select_from(InsightPost).where(*filters)) or 0)
    records = (
        await db.scalars(
            select(InsightPost)
            .where(*filters)
            .options(selectinload(InsightPost.translations))
            .order_by(InsightPost.published_at.desc(), InsightPost.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [insight_dict(record, locale) for record in records],
        "meta": meta(page, page_size, total),
    }


@router.get("/insights/{slug}")
async def insight_detail(
    slug: str, locale: Literal["en", "ar"], db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    record = await db.scalar(
        select(InsightPost)
        .where(InsightPost.slug == slug, InsightPost.status == PublicationStatus.PUBLISHED)
        .options(selectinload(InsightPost.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Insight not found."}
        )
    return insight_dict(record, locale)


@router.get("/jobs")
async def jobs(locale: Literal["en", "ar"], db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    records = (
        await db.scalars(
            select(JobOpening)
            .where(JobOpening.status == JobStatus.OPEN)
            .options(selectinload(JobOpening.translations))
            .order_by(JobOpening.created_at.desc())
        )
    ).all()
    return {
        "items": [job_dict(record, locale) for record in records],
        "meta": meta(1, max(1, len(records)), len(records)),
    }


@router.get("/jobs/{slug}")
async def job_detail(
    slug: str, locale: Literal["en", "ar"], db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    record = await db.scalar(
        select(JobOpening)
        .where(JobOpening.slug == slug, JobOpening.status == JobStatus.OPEN)
        .options(selectinload(JobOpening.translations))
    )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": "Job not found."}
        )
    return job_dict(record, locale)
