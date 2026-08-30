"""Content-bound review and publication workflow for canonical Areas."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Literal

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit import request_correlation_id, write_audit
from app.dependencies import AuthContext
from app.models import AreaCommunity, AuditLog, Project, PublicationStatus, UAEEmirate

AREA_RECEIPT_VERSION = "area-approval-v1"
TARGET_EMIRATES = (UAEEmirate.RAS_AL_KHAIMAH, UAEEmirate.SHARJAH)
AreaBulkAction = Literal["submit-review", "approve", "publish"]


class AreaAliasUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    alias: str = Field(min_length=1, max_length=240)
    locale: Literal["en", "ar"] | None = None


class AreaUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    slug: str = Field(min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name_en: str = Field(min_length=2, max_length=240)
    name_ar: str = Field(min_length=2, max_length=240)
    emirate: UAEEmirate
    aliases: list[AreaAliasUpdate] = Field(default_factory=list, max_length=100)
    expected_content_version: str = Field(pattern=r"^[a-f0-9]{64}$")


class AreaBulkWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: AreaBulkAction
    area_ids: list[uuid.UUID] = Field(min_length=1, max_length=50)
    expected_content_versions: dict[uuid.UUID, str]
    idempotency_key: str = Field(min_length=16, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    confirmation: str

    @model_validator(mode="after")
    def validate_selection(self) -> AreaBulkWorkflowInput:
        selected = set(self.area_ids)
        if len(selected) != len(self.area_ids):
            raise ValueError("Area selection must not contain duplicates")
        if set(self.expected_content_versions) != selected:
            raise ValueError("Every selected Area requires an expected content version")
        if any(
            not re.fullmatch(r"[a-f0-9]{64}", value)
            for value in self.expected_content_versions.values()
        ):
            raise ValueError("Every expected content version must be a SHA-256 hash")
        expected = {
            "submit-review": "SUBMIT",
            "approve": "APPROVE",
            "publish": "PUBLISH",
        }[self.action]
        if self.confirmation != expected:
            raise ValueError(f"{self.action} requires the explicit {expected} confirmation")
        return self


def content_version(record: AreaCommunity) -> str:
    aliases = sorted(
        ((item.locale, item.alias) for item in record.aliases),
        key=lambda item: (item[0] or "", item[1].casefold()),
    )
    payload = {
        "slug": record.slug,
        "name_en": record.name_en,
        "name_ar": record.name_ar,
        "emirate": record.emirate.value,
        "aliases": [{"locale": locale, "alias": alias} for locale, alias in aliases],
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def area_or_404(area_id: uuid.UUID, db: AsyncSession, *, lock: bool = False) -> AreaCommunity:
    statement = (
        select(AreaCommunity)
        .where(AreaCommunity.id == area_id)
        .options(selectinload(AreaCommunity.aliases))
    )
    if lock:
        statement = statement.with_for_update()
    record = await db.scalar(statement)
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Area not found."},
        )
    return record


async def referenced_project_count(record: AreaCommunity, db: AsyncSession) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.area_id == record.id, Project.emirate.in_(TARGET_EMIRATES))
        )
        or 0
    )


async def blockers(record: AreaCommunity, db: AsyncSession) -> list[str]:
    result: list[str] = []
    if not all((record.slug, record.name_en, record.name_ar, record.emirate)):
        result.append("Complete Area identity and bilingual names required")
    count = await referenced_project_count(record, db)
    if count == 0:
        result.append("Area is not referenced by a target RAK or Sharjah Project")
    mismatches = int(
        await db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.area_id == record.id, Project.emirate != record.emirate)
        )
        or 0
    )
    if mismatches:
        result.append("Referenced Project Emirate does not match the canonical Area")
    return result


async def latest_event(record: AreaCommunity, db: AsyncSession) -> AuditLog | None:
    result = await db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "area",
            AuditLog.entity_id == record.id,
            AuditLog.action.in_(("area.review.submit", "area.approve", "area.publish")),
            AuditLog.outcome == "success",
        )
        .order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    return result if isinstance(result, AuditLog) else None


async def workflow_state(record: AreaCommunity, db: AsyncSession) -> dict[str, Any]:
    version = content_version(record)
    event = await latest_event(record, db)
    metadata = event.metadata_summary if event and event.metadata_summary else {}
    current = metadata.get("content_version") == version
    state = "draft"
    if record.status == PublicationStatus.PUBLISHED:
        state = "published"
    elif current and event and event.action == "area.approve":
        state = "approved"
    elif current and event and event.action == "area.review.submit":
        state = "in_review"
    return {
        "content_version": version,
        "workflow_status": state,
        "referenced_project_count": await referenced_project_count(record, db),
        "blockers": await blockers(record, db),
        "receipt": (
            {
                "id": str(event.id),
                "reviewer": metadata.get("reviewer"),
                "reviewed_at": event.occurred_at,
                "content_version": metadata.get("content_version"),
                "current": current,
            }
            if event
            and event.action == "area.approve"
            and metadata.get("version") == AREA_RECEIPT_VERSION
            else None
        ),
    }


async def apply_bulk_workflow(
    db: AsyncSession,
    payload: AreaBulkWorkflowInput,
    request: Request,
    context: AuthContext,
) -> dict[str, Any]:
    permission = "project.publish" if payload.action in {"approve", "publish"} else "project.update"
    if permission not in context.permissions:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": f"{permission} permission is required.",
            },
        )

    request_hash = _request_hash(payload)
    lock_key = int.from_bytes(
        hashlib.sha256(payload.idempotency_key.encode()).digest()[:8], "big", signed=True
    )
    await db.execute(select(func.pg_advisory_xact_lock(lock_key)))
    previous = await db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "area_bulk_operation",
            AuditLog.action == f"area.bulk.{payload.action}",
            AuditLog.metadata_summary["idempotency_key"].as_string() == payload.idempotency_key,
        )
        .order_by(AuditLog.occurred_at.desc())
        .limit(1)
    )
    if previous and previous.metadata_summary:
        if previous.metadata_summary.get("request_hash") != request_hash:
            raise _conflict("idempotency_conflict", "This operation key was already used.")
        result = previous.metadata_summary.get("result")
        if isinstance(result, dict):
            return result

    records = (
        (
            await db.scalars(
                select(AreaCommunity)
                .where(AreaCommunity.id.in_(payload.area_ids))
                .order_by(AreaCommunity.id)
                .with_for_update()
                .options(selectinload(AreaCommunity.aliases))
            )
        )
        .unique()
        .all()
    )
    if len(records) != len(payload.area_ids):
        raise _unprocessable("invalid_selection", "Every selected Area must exist.")
    stale = [
        record.slug
        for record in records
        if payload.expected_content_versions[record.id] != content_version(record)
    ]
    if stale:
        raise _conflict("stale_area_selection", f"Area rows changed: {stale}.")

    states: dict[uuid.UUID, dict[str, Any]] = {}
    for record in records:
        states[record.id] = await workflow_state(record, db)
        await _validate_action(record, payload.action, states[record.id], db)

    correlation_id = request_correlation_id(request)
    for record in records:
        before = {
            "status": record.status.value,
            "workflow_status": states[record.id]["workflow_status"],
        }
        metadata: dict[str, Any] = {
            "bulk_action": payload.action,
            "selection_size": len(records),
            "content_version": content_version(record),
            "referenced_project_count": states[record.id]["referenced_project_count"],
        }
        if payload.action == "submit-review":
            action = "area.review.submit"
            next_state = "in_review"
        elif payload.action == "approve":
            action = "area.approve"
            next_state = "approved"
            metadata.update(
                {
                    "version": AREA_RECEIPT_VERSION,
                    "reviewer": context.user.display_name,
                    "checks": {
                        "identity": True,
                        "english": True,
                        "arabic": True,
                        "project_scope": True,
                    },
                }
            )
        else:
            action = "area.publish"
            next_state = "published"
            record.status = PublicationStatus.PUBLISHED
        await write_audit(
            db,
            action=action,
            entity_type="area",
            entity_id=record.id,
            actor_user_id=context.user.id,
            correlation_id=correlation_id,
            before=before,
            after={"status": record.status.value, "workflow_status": next_state},
            metadata=metadata,
        )

    result = {
        "action": payload.action,
        "affected_count": len(records),
        "area_ids": [str(record.id) for record in records],
        "correlation_id": correlation_id,
        "message": (
            f"{payload.action.replace('-', ' ').title()} completed for {len(records)} Area(s)."
        ),
    }
    await write_audit(
        db,
        action=f"area.bulk.{payload.action}",
        entity_type="area_bulk_operation",
        actor_user_id=context.user.id,
        correlation_id=correlation_id,
        metadata={
            "idempotency_key": payload.idempotency_key,
            "request_hash": request_hash,
            "result": result,
        },
    )
    await db.commit()
    return result


async def _validate_action(
    record: AreaCommunity,
    action: AreaBulkAction,
    state: dict[str, Any],
    db: AsyncSession,
) -> None:
    if record.status != PublicationStatus.DRAFT:
        raise _conflict("invalid_area_state", "Every selected Area must be Draft.")
    expected = {"submit-review": "draft", "approve": "in_review", "publish": "approved"}[action]
    if state["workflow_status"] != expected:
        raise _conflict("invalid_area_state", f"{action} requires Area workflow state {expected}.")
    current_blockers = await blockers(record, db)
    if current_blockers:
        raise _unprocessable("area_review_incomplete", "; ".join(current_blockers))
    if action == "publish":
        event = await latest_event(record, db)
        metadata = event.metadata_summary if event and event.metadata_summary else {}
        if (
            not event
            or event.action != "area.approve"
            or metadata.get("version") != AREA_RECEIPT_VERSION
            or metadata.get("content_version") != content_version(record)
        ):
            raise _unprocessable(
                "area_review_receipt_required",
                "Publication requires approval of this exact Area version.",
            )


def _request_hash(payload: AreaBulkWorkflowInput) -> str:
    data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _conflict(code: str, message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, "message": message})


def _unprocessable(code: str, message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": code, "message": message},
    )
