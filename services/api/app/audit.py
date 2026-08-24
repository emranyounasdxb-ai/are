from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


def request_correlation_id(request: object) -> str:
    return str(getattr(getattr(request, "state", object()), "correlation_id", uuid.uuid4()))


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    entity_type: str,
    correlation_id: str,
    actor_user_id: uuid.UUID | None = None,
    entity_id: uuid.UUID | None = None,
    outcome: str = "success",
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    record = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        outcome=outcome,
        before_summary=before,
        after_summary=after,
        request_correlation_id=correlation_id,
        metadata_summary=metadata,
    )
    db.add(record)
    await db.flush()
    return record
