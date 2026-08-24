from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.main import app
from app.models import AuditLog, InsightPost, JobOpening, Property, Role, Session, User
from app.security import hash_password


@pytest.fixture(autouse=True)
async def clean_disposable_records() -> AsyncIterator[None]:
    yield
    async with SessionLocal() as db:
        await db.execute(delete(AuditLog).where(AuditLog.request_correlation_id.like("qa-%")))
        await db.execute(delete(Property).where(Property.slug.like("qa-%")))
        await db.execute(delete(InsightPost).where(InsightPost.slug.like("qa-%")))
        await db.execute(delete(JobOpening).where(JobOpening.slug.like("qa-%")))
        user_ids = select(User.id).where(User.email.like("%@qa.are-cms.invalid-example-domain.com"))
        await db.execute(delete(Session).where(Session.user_id.in_(user_ids)))
        await db.execute(
            delete(User).where(User.email.like("%@qa.are-cms.invalid-example-domain.com"))
        )
        await db.commit()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": "http://127.0.0.1:50002", "X-Request-ID": f"qa-{uuid.uuid4()}"},
    ) as value:
        yield value


@pytest.fixture
def create_user() -> Callable[[str], Coroutine[Any, Any, tuple[str, str]]]:
    async def factory(role_slug: str) -> tuple[str, str]:
        email = f"{role_slug}-{uuid.uuid4()}@qa.are-cms.invalid-example-domain.com"
        password = f"Disposable-{uuid.uuid4()}!"
        async with SessionLocal() as db:
            role = await db.scalar(
                select(Role).where(Role.slug == role_slug).options(selectinload(Role.permissions))
            )
            assert role is not None
            db.add(
                User(
                    email=email,
                    display_name="Disposable QA User",
                    password_hash=hash_password(password),
                    roles=[role],
                )
            )
            await db.commit()
        return email, password

    return factory
