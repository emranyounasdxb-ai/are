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


class ProjectAvailabilityStatus(StrEnum):
    NOT_CONFIRMED = "not-confirmed"
    AVAILABLE = "available"
    LIMITED_AVAILABILITY = "limited-availability"
    SOLD_OUT = "sold-out"
    COMING_SOON = "coming-soon"


class ConstructionStatus(StrEnum):
    PRE_LAUNCH = "pre-launch"
    LAUNCHED = "launched"
    UNDER_CONSTRUCTION = "under-construction"
    NEAR_COMPLETION = "near-completion"
    COMPLETED = "completed"
    ON_HOLD = "on-hold"
    NOT_CONFIRMED = "not-confirmed"


class ProjectPriority(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class ProjectWorkflowStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    APPROVED = "approved"


class ProjectSizeUnit(StrEnum):
    SQFT = "sqft"
    SQM = "sqm"


class UAEEmirate(StrEnum):
    DUBAI = "Dubai"
    ABU_DHABI = "Abu Dhabi"
    SHARJAH = "Sharjah"
    AJMAN = "Ajman"
    UMM_AL_QUWAIN = "Umm Al Quwain"
    RAS_AL_KHAIMAH = "Ras Al Khaimah"
    FUJAIRAH = "Fujairah"


class ProjectPropertyType(StrEnum):
    APARTMENT = "apartment"
    VILLA = "villa"
    TOWNHOUSE = "townhouse"
    PENTHOUSE = "penthouse"
    DUPLEX = "duplex"
    MANSION = "mansion"
    RESIDENTIAL_PLOT = "residential-plot"
    OTHER = "other"


class ProjectBedroomOption(StrEnum):
    STUDIO = "studio"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX_PLUS = "6+"


class PaymentStage(StrEnum):
    BOOKING = "booking"
    DURING_CONSTRUCTION = "during-construction"
    HANDOVER = "handover"
    POST_HANDOVER = "post-handover"
    OTHER = "other"


class ProjectSourceType(StrEnum):
    OWNER_MANIFEST = "OWNER_MANIFEST"
    DLD_PROJECT_STATUS = "DLD_PROJECT_STATUS"
    OFFICIAL_DEVELOPER_PAGE = "OFFICIAL_DEVELOPER_PAGE"
    OFFICIAL_DEVELOPER_BROCHURE = "OFFICIAL_DEVELOPER_BROCHURE"
    OFFICIAL_MASTER_COMMUNITY_PAGE = "OFFICIAL_MASTER_COMMUNITY_PAGE"
    OWNER_SUPPLIED_DOCUMENT = "OWNER_SUPPLIED_DOCUMENT"
    OWNER_APPROVED_PARTNER_FEED = "OWNER_APPROVED_PARTNER_FEED"
    APPROVED_SECONDARY_SOURCE = "APPROVED_SECONDARY_SOURCE"


class ProjectMediaCategory(StrEnum):
    COVER = "cover"
    GALLERY = "gallery"
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    AMENITIES = "amenities"
    FLOOR_PLAN = "floor-plan"
    MASTER_PLAN = "master-plan"
    LOCATION_MAP = "location-map"
    CONSTRUCTION = "construction"
    VIDEO_REFERENCE = "video-reference"


class ImportReviewStatus(StrEnum):
    DISCOVERED = "discovered"
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs-review"
    READY_FOR_APPROVAL = "ready-for-approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    MERGED = "merged"


class DeveloperVerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class EditorialApprovalStatus(StrEnum):
    NOT_GENERATED = "not-generated"
    NEEDS_REVIEW = "needs-review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProjectProcessingStatus(StrEnum):
    RAW = "raw"
    SELECTED = "selected"
    QUEUED = "queued"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs-review"
    CLEANED = "cleaned"
    READY_TO_POST = "ready-to-post"
    FAILED_RETRYABLE = "failed-retryable"
    FAILED_HUMAN_INPUT = "failed-human-input-required"
    REJECTED = "rejected"


class ProcessingJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed-with-errors"
    CANCELLED = "cancelled"


class ProcessingItemStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class DiagnosticResolutionStatus(StrEnum):
    OPEN = "open"
    HUMAN_INPUT_REQUIRED = "human-input-required"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ProjectRevisionStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


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


class AreaCommunity(TimestampMixin, Base):
    __tablename__ = "area_communities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(240), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(240), nullable=False)
    emirate: Mapped[UAEEmirate] = mapped_column(
        Enum(UAEEmirate, name="uae_emirate"), nullable=False, index=True
    )
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    aliases: Mapped[list[AreaAlias]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class AreaAlias(Base):
    __tablename__ = "area_aliases"
    __table_args__ = (UniqueConstraint("normalized_alias"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("area_communities.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str | None] = mapped_column(String(2))
    alias: Mapped[str] = mapped_column(String(240), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(240), nullable=False)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    developer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("developers.id"), nullable=False, index=True
    )
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("area_communities.id"), nullable=False, index=True
    )
    emirate: Mapped[UAEEmirate] = mapped_column(
        Enum(UAEEmirate, name="uae_emirate", create_type=False), nullable=False, index=True
    )
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    workflow_status: Mapped[ProjectWorkflowStatus] = mapped_column(
        Enum(ProjectWorkflowStatus, name="project_workflow_status"),
        default=ProjectWorkflowStatus.DRAFT,
        nullable=False,
        index=True,
    )
    availability_status: Mapped[ProjectAvailabilityStatus] = mapped_column(
        Enum(ProjectAvailabilityStatus, name="project_availability_status"), nullable=False
    )
    construction_status: Mapped[ConstructionStatus] = mapped_column(
        Enum(ConstructionStatus, name="project_construction_status"),
        default=ConstructionStatus.NOT_CONFIRMED,
        nullable=False,
    )
    handover_quarter: Mapped[str | None] = mapped_column(String(2))
    handover_year: Mapped[int | None]
    original_handover_value: Mapped[str | None] = mapped_column(String(240))
    size_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    size_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    size_unit: Mapped[ProjectSizeUnit | None] = mapped_column(
        Enum(ProjectSizeUnit, name="project_size_unit")
    )
    down_payment_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    down_payment_source_value: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[ProjectPriority | None] = mapped_column(
        Enum(ProjectPriority, name="project_priority"), nullable=True
    )
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "project_revisions.id",
            name="fk_projects_active_revision_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    developer: Mapped[Developer] = relationship(lazy="joined")
    area: Mapped[AreaCommunity] = relationship(lazy="joined")
    translations: Mapped[list[ProjectTranslation]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    property_types: Mapped[list[ProjectPropertyTypeValue]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    bedroom_options: Mapped[list[ProjectBedroomValue]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    unit_types: Mapped[list[ProjectUnitType]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    amenities: Mapped[list[ProjectAmenity]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    nearby_places: Mapped[list[ProjectNearbyPlace]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    sources: Mapped[list[ProjectSource]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    payment_plan: Mapped[ProjectPaymentPlan | None] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )
    media: Mapped[list[ProjectMedia]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    revisions: Mapped[list[ProjectRevision]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", foreign_keys="ProjectRevision.project_id"
    )


class ProjectTranslation(Base):
    __tablename__ = "project_translations"
    __table_args__ = (UniqueConstraint("project_id", "locale"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    official_name: Mapped[str] = mapped_column(String(240), nullable=False)
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    seo_title: Mapped[str] = mapped_column(String(240), nullable=False)
    seo_description: Mapped[str] = mapped_column(String(320), nullable=False)


class ProjectPropertyTypeValue(Base):
    __tablename__ = "project_property_types"
    __table_args__ = (UniqueConstraint("project_id", "property_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    property_type: Mapped[ProjectPropertyType] = mapped_column(
        Enum(ProjectPropertyType, name="project_property_type"), nullable=False
    )


class ProjectBedroomValue(Base):
    __tablename__ = "project_bedroom_options"
    __table_args__ = (UniqueConstraint("project_id", "bedroom_option"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    bedroom_option: Mapped[ProjectBedroomOption] = mapped_column(
        Enum(ProjectBedroomOption, name="project_bedroom_option"), nullable=False
    )


class ProjectUnitType(Base):
    __tablename__ = "project_unit_types"
    __table_args__ = (UniqueConstraint("project_id", "label_en"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    label_en: Mapped[str] = mapped_column(String(160), nullable=False)
    label_ar: Mapped[str | None] = mapped_column(String(160))
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)


class ProjectAmenity(Base):
    __tablename__ = "project_amenities"
    __table_args__ = (UniqueConstraint("project_id", "label_en"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    label_en: Mapped[str] = mapped_column(String(160), nullable=False)
    label_ar: Mapped[str | None] = mapped_column(String(160))
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)


class ProjectNearbyPlace(Base):
    __tablename__ = "project_nearby_places"
    __table_args__ = (UniqueConstraint("project_id", "name_en"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(200))
    distance_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    distance_unit: Mapped[str | None] = mapped_column(String(20))
    travel_time_minutes: Mapped[int | None]
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)


class ProjectSource(TimestampMixin, Base):
    __tablename__ = "project_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[ProjectSourceType] = mapped_column(
        Enum(ProjectSourceType, name="project_source_type"), nullable=False
    )
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(320))
    source_developer_domain: Mapped[str | None] = mapped_column(String(320))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProjectPaymentPlan(TimestampMixin, Base):
    __tablename__ = "project_payment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    raw_source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_sources.id"), nullable=False
    )
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    milestones: Mapped[list[ProjectPaymentMilestone]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectPaymentMilestone.sequence"
    )


class ProjectPaymentMilestone(Base):
    __tablename__ = "project_payment_milestones"
    __table_args__ = (UniqueConstraint("payment_plan_id", "sequence"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_payment_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(nullable=False)
    stage: Mapped[PaymentStage] = mapped_column(
        Enum(PaymentStage, name="project_payment_stage"), nullable=False
    )
    label_en: Mapped[str] = mapped_column(String(240), nullable=False)
    label_ar: Mapped[str | None] = mapped_column(String(240))
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    due_trigger: Mapped[str | None] = mapped_column(String(320))
    source_value: Mapped[str] = mapped_column(Text, nullable=False)


class ProjectMedia(TimestampMixin, Base):
    __tablename__ = "project_media"
    __table_args__ = (UniqueConstraint("project_id", "source_url"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[ProjectMediaCategory] = mapped_column(
        Enum(ProjectMediaCategory, name="project_media_category"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    rights_status: Mapped[MediaRightsStatus] = mapped_column(
        Enum(MediaRightsStatus, name="media_rights_status", create_type=False), nullable=False
    )
    alt_en: Mapped[str | None] = mapped_column(String(320))
    alt_ar: Mapped[str | None] = mapped_column(String(320))
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(180))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int | None]
    sha256: Mapped[str | None] = mapped_column(String(64))
    width: Mapped[int | None]
    height: Mapped[int | None]
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    title_en: Mapped[str | None] = mapped_column(String(240))
    title_ar: Mapped[str | None] = mapped_column(String(240))
    description_en: Mapped[str | None] = mapped_column(String(500))
    description_ar: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    derivative_manifest: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    private_provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProjectImportBatch(TimestampMixin, Base):
    __tablename__ = "project_import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_count: Mapped[int] = mapped_column(default=0, nullable=False)
    clean_count: Mapped[int] = mapped_column(default=0, nullable=False)
    needs_review_count: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    candidates: Mapped[list[ProjectImportCandidate]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class ProjectImportCandidate(TimestampMixin, Base):
    __tablename__ = "project_import_candidates"
    __table_args__ = (UniqueConstraint("batch_id", "manifest_row_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    manifest_row_id: Mapped[int] = mapped_column(nullable=False)
    raw_source_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    owner_manifest_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_project_name: Mapped[str | None] = mapped_column(String(240))
    proposed_developer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("developers.id")
    )
    proposed_area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("area_communities.id")
    )
    official_source_url: Mapped[str | None] = mapped_column(Text)
    adapter_key: Mapped[str | None] = mapped_column(String(80))
    adapter_version: Mapped[str | None] = mapped_column(String(32))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arabic_review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    acquisition_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    source_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    match_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    conflict_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    review_status: Mapped[ImportReviewStatus] = mapped_column(
        Enum(ImportReviewStatus, name="project_import_review_status"), nullable=False, index=True
    )
    linked_project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id")
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    review_version: Mapped[int] = mapped_column(default=1, nullable=False)
    human_review_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_edited_fields: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(1000))
    processing_status: Mapped[ProjectProcessingStatus] = mapped_column(
        Enum(ProjectProcessingStatus, name="project_processing_status"),
        default=ProjectProcessingStatus.RAW,
        nullable=False,
        index=True,
    )
    last_successful_stage: Mapped[str | None] = mapped_column(String(80))
    evidence: Mapped[list[ProjectSourceSnapshot]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    staged_media: Mapped[list[ProjectImportMedia]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    changes: Mapped[list[ProjectImportChange]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    editorial_draft: Mapped[ProjectImportEditorialDraft | None] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )


class ProjectSourceSnapshot(TimestampMixin, Base):
    __tablename__ = "project_source_snapshots"
    __table_args__ = (UniqueConstraint("candidate_id", "source_url", "content_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[ProjectSourceType] = mapped_column(
        Enum(ProjectSourceType, name="project_source_type", create_type=False), nullable=False
    )
    http_status: Mapped[int | None]
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(80), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(32), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(160))
    size_bytes: Mapped[int | None]
    etag: Mapped[str | None] = mapped_column(String(320))
    last_modified: Mapped[str | None] = mapped_column(String(320))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(180), unique=True)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(String(500))


class ProjectImportMedia(TimestampMixin, Base):
    __tablename__ = "project_import_media"
    __table_args__ = (UniqueConstraint("candidate_id", "source_url"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_source_snapshots.id", ondelete="SET NULL")
    )
    category: Mapped[ProjectMediaCategory] = mapped_column(
        Enum(ProjectMediaCategory, name="project_media_category", create_type=False),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    rights_status: Mapped[MediaRightsStatus] = mapped_column(
        Enum(MediaRightsStatus, name="media_rights_status", create_type=False), nullable=False
    )
    stage_status: Mapped[str] = mapped_column(String(40), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(180), unique=True)
    raw_storage_key: Mapped[str | None] = mapped_column(String(180), unique=True)
    thumbnail_storage_key: Mapped[str | None] = mapped_column(String(180), unique=True)
    mime_type: Mapped[str | None] = mapped_column(String(80))
    size_bytes: Mapped[int | None]
    sha256: Mapped[str | None] = mapped_column(String(64))
    width: Mapped[int | None]
    height: Mapped[int | None]
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_import_media.id")
    )
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(String(500))
    normalized_filename: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    alt_en_draft: Mapped[str | None] = mapped_column(String(320))
    alt_ar_draft: Mapped[str | None] = mapped_column(String(320))
    derivative_manifest: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    change_status: Mapped[str] = mapped_column(String(40), default="newly-added", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rights_basis: Mapped[str | None] = mapped_column(String(500))
    rights_confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    rights_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    original_sha256: Mapped[str | None] = mapped_column(String(64))
    processed_sha256: Mapped[str | None] = mapped_column(String(64))
    processing_version: Mapped[str | None] = mapped_column(String(40))
    public_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(240))
    title_ar: Mapped[str | None] = mapped_column(String(240))
    description_en: Mapped[str | None] = mapped_column(String(500))
    description_ar: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    discovery_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProjectImportBulkOperation(TimestampMixin, Base):
    __tablename__ = "project_import_bulk_operations"
    __table_args__ = (UniqueConstraint("batch_id", "idempotency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class ProjectImportChange(TimestampMixin, Base):
    __tablename__ = "project_import_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    classification: Mapped[str] = mapped_column(String(40), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(120))
    existing_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    source_url: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))


class ProjectImportEditorialDraft(TimestampMixin, Base):
    __tablename__ = "project_import_editorial_drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    overview_en: Mapped[str | None] = mapped_column(Text)
    overview_ar: Mapped[str | None] = mapped_column(Text)
    source_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(160))
    model_version: Mapped[str | None] = mapped_column(String(160))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_status: Mapped[EditorialApprovalStatus] = mapped_column(
        Enum(EditorialApprovalStatus, name="editorial_approval_status"),
        default=EditorialApprovalStatus.NOT_GENERATED,
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    origin: Mapped[str | None] = mapped_column(String(40))
    overview_pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_overview_packs.id", ondelete="SET NULL")
    )
    overview_pack_hash: Mapped[str | None] = mapped_column(String(64))
    fact_input_version: Mapped[str | None] = mapped_column(String(40))
    fact_input_hash: Mapped[str | None] = mapped_column(String(64))
    candidate_version: Mapped[int | None]
    import_correlation_id: Mapped[str | None] = mapped_column(String(120))


class ProjectOverviewPack(TimestampMixin, Base):
    __tablename__ = "project_overview_packs"
    __table_args__ = (UniqueConstraint("created_by", "idempotency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pack_version: Mapped[str] = mapped_column(String(40), nullable=False)
    selection_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    pack_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    selected_count: Mapped[int] = mapped_column(nullable=False)
    eligible_count: Mapped[int] = mapped_column(nullable=False)
    ineligible_count: Mapped[int] = mapped_column(nullable=False)
    imported_count: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    import_correlation_id: Mapped[str | None] = mapped_column(String(120))
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items: Mapped[list[ProjectOverviewPackItem]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectOverviewPackItem.ordinal"
    )


class ProjectOverviewPackItem(TimestampMixin, Base):
    __tablename__ = "project_overview_pack_items"
    __table_args__ = (UniqueConstraint("pack_id", "candidate_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_overview_packs.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ordinal: Mapped[int] = mapped_column(nullable=False)
    candidate_version: Mapped[int] = mapped_column(nullable=False)
    fact_input_version: Mapped[str] = mapped_column(String(40), nullable=False)
    fact_input_hash: Mapped[str | None] = mapped_column(String(64))
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    exclusion_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(String(1000))
    referenced_fact_fields: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    editorial_notes: Mapped[str | None] = mapped_column(String(1000))
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProjectOverviewGeneration(TimestampMixin, Base):
    __tablename__ = "project_overview_generations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    model_version: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    source_version: Mapped[str] = mapped_column(String(64), nullable=False)
    overview_en: Mapped[str | None] = mapped_column(Text)
    overview_ar: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    result_status: Mapped[str] = mapped_column(String(40), nullable=False)
    fact_guard_result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approval_status: Mapped[EditorialApprovalStatus] = mapped_column(
        Enum(EditorialApprovalStatus, name="editorial_approval_status", create_type=False),
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProjectProcessingJob(TimestampMixin, Base):
    __tablename__ = "project_processing_jobs"
    __table_args__ = (UniqueConstraint("created_by", "idempotency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    requested_action: Mapped[str] = mapped_column(String(60), nullable=False)
    selection_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    selected_record_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[ProcessingJobStatus] = mapped_column(
        Enum(ProcessingJobStatus, name="project_processing_job_status"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_count: Mapped[int] = mapped_column(nullable=False)
    queued_count: Mapped[int] = mapped_column(nullable=False)
    processing_count: Mapped[int] = mapped_column(default=0, nullable=False)
    succeeded_count: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    skipped_count: Mapped[int] = mapped_column(default=0, nullable=False)
    cancellation_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    items: Mapped[list[ProjectProcessingItem]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectProcessingItem.ordinal"
    )


class ProjectProcessingItem(TimestampMixin, Base):
    __tablename__ = "project_processing_items"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[ProcessingItemStatus] = mapped_column(
        Enum(ProcessingItemStatus, name="project_processing_item_status"),
        nullable=False,
        index=True,
    )
    current_stage: Mapped[str | None] = mapped_column(String(80))
    completed_stages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    attempt_count: Mapped[int] = mapped_column(default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(default=3, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_owner: Mapped[str | None] = mapped_column(String(120))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    diagnostics: Mapped[list[ProjectProcessingDiagnostic]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class ProjectProcessingDiagnostic(TimestampMixin, Base):
    __tablename__ = "project_processing_diagnostics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_processing_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    error_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    explanation: Mapped[str] = mapped_column(String(1000), nullable=False)
    technical_detail: Mapped[str | None] = mapped_column(String(1000))
    affected_reference: Mapped[str | None] = mapped_column(String(240))
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    first_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latest_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_successful_stage: Mapped[str | None] = mapped_column(String(80))
    suggested_resolution: Mapped[str] = mapped_column(String(1000), nullable=False)
    resolution_status: Mapped[DiagnosticResolutionStatus] = mapped_column(
        Enum(DiagnosticResolutionStatus, name="project_diagnostic_resolution_status"),
        nullable=False,
        index=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(String(1000))
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False)


class ProjectRevision(TimestampMixin, Base):
    __tablename__ = "project_revisions"
    __table_args__ = (UniqueConstraint("project_id", "revision_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_number: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[ProjectRevisionStatus] = mapped_column(
        Enum(ProjectRevisionStatus, name="project_revision_status"), nullable=False, index=True
    )
    base_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_revisions.id", ondelete="SET NULL")
    )
    record_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    media_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    field_diff: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(1000))
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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
    legal_name: Mapped[str | None] = mapped_column(String(320))
    source_name: Mapped[str | None] = mapped_column(String(320))
    internal_aliases: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    primary_emirate: Mapped[str] = mapped_column(String(120), nullable=False)
    other_presence: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    selected_projects: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    official_website: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    additional_source_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    verification_date: Mapped[date] = mapped_column(Date, nullable=False)
    verification_status: Mapped[DeveloperVerificationStatus] = mapped_column(
        Enum(DeveloperVerificationStatus, name="developer_verification_status"),
        default=DeveloperVerificationStatus.PENDING,
        nullable=False,
    )
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
Index(
    "ix_area_communities_search", AreaCommunity.slug, AreaCommunity.name_en, AreaCommunity.emirate
)
Index(
    "ix_projects_search",
    Project.slug,
    Project.status,
    Project.availability_status,
    Project.construction_status,
)
Index("ix_project_sources_project_type", ProjectSource.project_id, ProjectSource.source_type)
Index("ix_project_media_project_category", ProjectMedia.project_id, ProjectMedia.category)
Index(
    "ix_project_import_candidates_dedupe",
    ProjectImportCandidate.normalized_project_name,
    ProjectImportCandidate.proposed_developer_id,
    ProjectImportCandidate.proposed_area_id,
)
Index("ix_project_source_snapshots_candidate", ProjectSourceSnapshot.candidate_id)
Index("ix_project_import_media_candidate", ProjectImportMedia.candidate_id)
Index("ix_project_import_changes_candidate", ProjectImportChange.candidate_id)
Index("ix_job_openings_search", JobOpening.slug, JobOpening.department)
Index("ix_contact_enquiries_status_created", ContactEnquiry.status, ContactEnquiry.created_at)
Index(
    "ix_career_applications_status_created", CareerApplication.status, CareerApplication.created_at
)
