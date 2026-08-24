from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit import request_correlation_id, write_audit
from app.config import Settings, get_settings
from app.db import get_db
from app.dependencies import AuthContext, get_auth_context, get_redis, require_csrf
from app.models import Role, User
from app.schemas import LoginRequest, UserResponse
from app.security import (
    client_fingerprint,
    create_session,
    delete_session_cookie,
    enforce_login_rate_limit,
    hash_password,
    password_needs_rehash,
    set_session_cookie,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_response(context: AuthContext) -> UserResponse:
    return UserResponse(
        id=context.user.id,
        email=context.user.email,
        display_name=context.user.display_name,
        roles=sorted(role.name for role in context.user.roles),
        permissions=sorted(context.permissions),
        csrf_token=context.session.csrf_token,
    )


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    origin = request.headers.get("origin")
    if origin and origin not in settings.allowed_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "origin_rejected", "message": "The request origin is not allowed."},
        )
    email = str(payload.email).lower()
    await enforce_login_rate_limit(redis, request, email, settings)
    user = await db.scalar(
        select(User)
        .where(User.email == email)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    if not user or not user.is_active or not verify_password(user.password_hash, payload.password):
        await write_audit(
            db,
            action="auth.login.failed",
            entity_type="session",
            correlation_id=request_correlation_id(request),
            outcome="failure",
            metadata={"client_fingerprint": client_fingerprint(request)},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid email or password."},
        )
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
    token, _, session = await create_session(db, user, request, settings)
    context = AuthContext(
        user=user,
        session=session,
        permissions=frozenset(
            permission.code for role in user.roles for permission in role.permissions
        ),
    )
    await write_audit(
        db,
        action="auth.login.succeeded",
        entity_type="session",
        entity_id=session.id,
        actor_user_id=user.id,
        correlation_id=request_correlation_id(request),
        metadata={"client_fingerprint": client_fingerprint(request)},
    )
    await db.commit()
    set_session_cookie(response, token, settings)
    return user_response(context)


@router.get("/me", response_model=UserResponse)
async def me(
    context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    await db.commit()
    return user_response(context)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    context: AuthContext = Depends(require_csrf),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    context.session.revoked_at = datetime.now(UTC)
    await write_audit(
        db,
        action="auth.logout",
        entity_type="session",
        entity_id=context.session.id,
        actor_user_id=context.user.id,
        correlation_id=request_correlation_id(request),
    )
    await db.commit()
    delete_session_cookie(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
