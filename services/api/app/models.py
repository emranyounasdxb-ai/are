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


class AvailabilityStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED_AVAILABLE = "verified-available"
    VERIFIED_UNAVAILABLE = "verified-unavailable"


class MediaRightsStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EnquiryStatus(StrEnum):
    NEW = "new"
    IN_REVIEW = "in-review"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CLOSED = "closed"
    SPAM = "spam"


class ApplicationStatus(StrEnum):
    NEW = "new"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    SELECTED = "selected"
    REJECTED = "rejected"


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
    source_verified_at: Mapped[date | None] = mapped_column(Date)
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus, name="property_availability_status"),
        default=AvailabilityStatus.UNVERIFIED,
        nullable=False,
    )
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
    cover_media: Mapped[PropertyCoverMedia | None] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
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


class PropertyCoverMedia(TimestampMixin, Base):
    __tablename__ = "property_cover_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), unique=True
    )
    storage_key: Mapped[str | None] = mapped_column(String(180), unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int | None]
    sha256: Mapped[str | None] = mapped_column(String(64))
    width: Mapped[int | None]
    height: Mapped[int | None]
    alt_en: Mapped[str | None] = mapped_column(String(320))
    alt_ar: Mapped[str | None] = mapped_column(String(320))
    provenance_url: Mapped[str] = mapped_column(Text, nullable=False)
    rights_status: Mapped[MediaRightsStatus] = mapped_column(
        Enum(MediaRightsStatus, name="media_rights_status"),
        default=MediaRightsStatus.PENDING,
        nullable=False,
    )
    display_position: Mapped[int] = mapped_column(default=0, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )


class TrustProfile(TimestampMixin, Base):
    __tablename__ = "trust_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    google_business_url: Mapped[str] = mapped_column(Text, nullable=False)
    google_rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    google_review_count: Mapped[int] = mapped_column(nullable=False)
    snapshot_verified_at: Mapped[date] = mapped_column(Date, nullable=False)
    office_address: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False), nullable=False
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


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


class Developer(TimestampMixin, Base):
    __tablename__ = "developers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    primary_emirate: Mapped[str] = mapped_column(String(120), nullable=False)
    other_presence: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    selected_projects: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    official_website: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    additional_source_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    verification_date: Mapped[date] = mapped_column(Date, nullable=False)
    enquiry_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    translations: Mapped[list[DeveloperTranslation]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class DeveloperTranslation(Base):
    __tablename__ = "developer_translations"
    __table_args__ = (UniqueConstraint("developer_id", "locale"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    developer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("developers.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    focus: Mapped[str] = mapped_column(Text, nullable=False)
    verification_note: Mapped[str] = mapped_column(Text, nullable=False)


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


class ContactEnquiry(TimestampMixin, Base):
    __tablename__ = "contact_enquiries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    enquiry_type: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(String(48), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, str] | None] = mapped_column(JSON)
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    preferred_contact_method: Mapped[str] = mapped_column(String(24), nullable=False)
    contact_consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attribution: Mapped[dict[str, str] | None] = mapped_column(JSON)
    status: Mapped[EnquiryStatus] = mapped_column(
        Enum(EnquiryStatus, name="enquiry_status"), default=EnquiryStatus.NEW, nullable=False
    )
    internal_note: Mapped[str | None] = mapped_column(Text)
    idempotency_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class CareerApplication(TimestampMixin, Base):
    __tablename__ = "career_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    applicant_name: Mapped[str] = mapped_column(String(180), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(String(48), nullable=False)
    current_location: Mapped[str] = mapped_column(String(180), nullable=False)
    job_opening_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_openings.id")
    )
    context_label: Mapped[str] = mapped_column(String(240), nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)
    cover_note: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    acknowledgement_consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.NEW,
        nullable=False,
    )
    internal_note: Mapped[str | None] = mapped_column(Text)
    idempotency_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    file: Mapped[PrivateFileMetadata | None] = relationship(
        back_populates="application", cascade="all, delete-orphan", lazy="selectin"
    )


class PrivateFileMetadata(Base):
    __tablename__ = "private_file_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    declared_mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    verified_format: Mapped[str] = mapped_column(String(16), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    application: Mapped[CareerApplication] = relationship(back_populates="file")


Index("ix_properties_search", Property.slug, Property.property_type, Property.emirate)
Index("ix_insight_posts_search", InsightPost.slug, InsightPost.category)
Index("ix_developers_search", Developer.slug, Developer.primary_emirate, Developer.featured)
Index("ix_job_openings_search", JobOpening.slug, JobOpening.department)
Index("ix_contact_enquiries_status_created", ContactEnquiry.status, ContactEnquiry.created_at)
Index(
    "ix_career_applications_status_created", CareerApplication.status, CareerApplication.created_at
)
