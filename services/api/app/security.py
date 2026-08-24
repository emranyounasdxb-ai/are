from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import Settings
from app.models import Role, Session, User

SESSION_COOKIE = "are_admin_session"
_password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(password_hash)


def client_fingerprint(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    host = forwarded.split(",", maxsplit=1)[0].strip() if forwarded else ""
    if not host and request.client:
        host = request.client.host
    return hash_value(host or "unknown")


async def enforce_login_rate_limit(
    redis: Redis,
    request: Request,
    email: str,
    settings: Settings,
) -> None:
    key_material = f"{client_fingerprint(request)}:{email.strip().lower()}"
    key = f"are:login:{hash_value(key_material)}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, settings.login_rate_limit_window_seconds)
    if attempts > settings.login_rate_limit_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "login_rate_limited", "message": "Please wait before trying again."},
        )


async def enforce_submission_rate_limit(
    redis: Redis, request: Request, workflow: str, settings: Settings
) -> None:
    key = f"are:submission:{workflow}:{client_fingerprint(request)}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, settings.submission_rate_limit_window_seconds)
    if attempts > settings.submission_rate_limit_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "submission_rate_limited",
                "message": "Please wait before trying again.",
            },
        )


async def create_session(
    db: AsyncSession,
    user: User,
    request: Request,
    settings: Settings,
) -> tuple[str, str, Session]:
    token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    record = Session(
        user_id=user.id,
        token_hash=hash_value(token),
        csrf_token=csrf_token,
        expires_at=now + timedelta(minutes=settings.session_lifetime_minutes),
        last_seen_at=now,
        user_agent_hash=hash_value(request.headers.get("user-agent", "")),
    )
    db.add(record)
    await db.flush()
    return token, csrf_token, record


async def resolve_session(db: AsyncSession, raw_token: str | None) -> Session | None:
    if not raw_token:
        return None
    record = await db.scalar(
        select(Session)
        .where(Session.token_hash == hash_value(raw_token))
        .options(joinedload(Session.user).selectinload(User.roles).selectinload(Role.permissions))
    )
    now = datetime.now(UTC)
    if not record or record.revoked_at or record.expires_at <= now or not record.user.is_active:
        return None
    record.last_seen_at = now
    return record


def set_session_cookie(response: object, token: str, settings: Settings) -> None:
    response.set_cookie(  # type: ignore[attr-defined]
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.session_lifetime_minutes * 60,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def delete_session_cookie(response: object, settings: Settings) -> None:
    response.delete_cookie(  # type: ignore[attr-defined]
        key=SESSION_COOKIE,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
