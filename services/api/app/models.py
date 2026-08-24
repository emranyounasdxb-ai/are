from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PublicationStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class JobStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Purpose(StrEnum):
    BUY = "buy"
    RENT = "rent"
    OFF_PLAN = "off-plan"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    roles: Mapped[list[Role]] = relationship(secondary="user_roles", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    users: Mapped[list[User]] = relationship(secondary="user_roles", back_populates="roles")
    permissions: Mapped[list[Permission]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    roles: Mapped[list[Role]] = relationship(
        secondary="role_permissions", back_populates="permissions"
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_agent_hash: Mapped[str | None] = mapped_column(String(64))
    user: Mapped[User] = relationship(lazy="joined")


class Property(TimestampMixin, Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    purpose: Mapped[Purpose] = mapped_column(Enum(Purpose, name="property_purpose"), nullable=False)
    property_type: Mapped[str] = mapped_column(String(120), nullable=False)
    emirate: Mapped[str] = mapped_column(String(120), nullable=False)
    community: Mapped[str] = mapped_column(String(180), nullable=False)
    developer: Mapped[str | None] = mapped_column(String(180))
    bedrooms: Mapped[int | None]
    bathrooms: Mapped[int | None]
    area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    area_unit: Mapped[str | None] = mapped_column(String(24))
    price: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    price_on_request: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="AED", nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance_note: Mapped[str] = mapped_column(Text, nullable=False)
    external_reference_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status"),
        default=PublicationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    translations: Mapped[list[PropertyTranslation]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class PropertyTranslation(Base):
    __tablename__ = "property_translations"
    __table_args__ = (UniqueConstraint("property_id", "locale"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class InsightPost(TimestampMixin, Base):
    __tablename__ = "insight_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    author_display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_links: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    translations: Mapped[list[InsightPostTranslation]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class InsightPostTranslation(Base):
    __tablename__ = "insight_post_translations"
    __table_args__ = (UniqueConstraint("insight_post_id", "locale"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insight_posts.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    seo_title: Mapped[str] = mapped_column(String(240), nullable=False)
    seo_description: Mapped[str] = mapped_column(String(320), nullable=False)


class JobOpening(TimestampMixin, Base):
    __tablename__ = "job_openings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    department: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    closing_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.DRAFT, nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    translations: Mapped[list[JobOpeningTranslation]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class JobOpeningTranslation(Base):
    __tablename__ = "job_opening_translations"
    __table_args__ = (UniqueConstraint("job_opening_id", "locale"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_opening_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_openings.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsibilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    requirements: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    action: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    outcome: Mapped[str] = mapped_column(String(40), default="success", nullable=False)
    before_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    request_correlation_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    metadata_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)


Index("ix_properties_search", Property.slug, Property.property_type, Property.emirate)
Index("ix_insight_posts_search", InsightPost.slug, InsightPost.category)
Index("ix_job_openings_search", JobOpening.slug, JobOpening.department)
