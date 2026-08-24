from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import get_settings
from app.db import SessionLocal, engine
from app.middleware import RequestContextMiddleware, configure_logging
from app.routers import admin, auth, public

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="ALIYAS Real Estate API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(public.router, prefix="/api/v1")


def error_payload(
    request: Request, code: str, message: str, fields: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "correlation_id": str(getattr(request.state, "correlation_id", uuid.uuid4())),
            "fields": fields,
        }
    }


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    detail = (
        exc.detail
        if isinstance(exc.detail, dict)
        else {"code": "request_failed", "message": str(exc.detail)}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            request,
            str(detail.get("code", "request_failed")),
            str(detail.get("message", "The request failed.")),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [
        {
            "location": ".".join(
                str(part) for part in item["loc"] if part not in {"body", "query"}
            ),
            "message": item["msg"],
            "type": item["type"],
        }
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_payload(
            request, "validation_failed", "Please review the submitted fields.", fields
        ),
    )


@app.get("/health", tags=["health"])
@app.get("/api/v1/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
@app.get("/api/v1/ready", tags=["health"])
async def ready() -> dict[str, str]:
    async with SessionLocal() as db:
        await db.execute(text("SELECT 1"))
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.ping()
    finally:
        await redis.aclose()
    return {"status": "ready"}


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=50003, reload=False)
