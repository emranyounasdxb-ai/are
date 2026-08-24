from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Session, User
from app.security import SESSION_COOKIE, resolve_session


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: Session
    permissions: frozenset[str]


async def get_redis(settings: Settings = Depends(get_settings)) -> AsyncIterator[Redis]:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()


async def get_auth_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    record = await resolve_session(db, request.cookies.get(SESSION_COOKIE))
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "authentication_required", "message": "Authentication is required."},
        )
    permissions = frozenset(
        permission.code for role in record.user.roles for permission in role.permissions
    )
    await db.flush()
    return AuthContext(record.user, record, permissions)


def require_permission(permission: str) -> Callable[..., Awaitable[AuthContext]]:
    async def dependency(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if permission not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "permission_denied", "message": "You do not have permission."},
            )
        return context

    return dependency


async def require_csrf(
    request: Request,
    context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not secrets_compare(supplied, context.session.csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "csrf_failed", "message": "The request could not be verified."},
        )
    return context


def secrets_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)


def require_mutation_permission(permission: str) -> Callable[..., Awaitable[AuthContext]]:
    async def dependency(context: AuthContext = Depends(require_csrf)) -> AuthContext:
        if permission not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "permission_denied", "message": "You do not have permission."},
            )
        return context

    return dependency
