from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from app.models import (
    ApplicationStatus,
    AvailabilityStatus,
    ConstructionStatus,
    EnquiryStatus,
    ImportReviewStatus,
    JobStatus,
    MediaRightsStatus,
    PaymentStage,
    ProjectAvailabilityStatus,
    ProjectBedroomOption,
    ProjectMediaCategory,
    ProjectPriority,
    ProjectPropertyType,
    ProjectSourceType,
    PublicationStatus,
    Purpose,
)

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ErrorBody(BaseModel):
    code: str
    message: str
    correlation_id: str
    fields: list[dict[str, Any]] | None = None


class LoginRequest(StrictModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=1024)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    roles: list[str]
    permissions: list[str]
    csrf_token: str


class TranslationInput(StrictModel):
    title: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=10, max_length=20000)


class PropertyInput(StrictModel):
    slug: str = Field(min_length=2, max_length=180)
    purpose: Purpose
    property_type: str = Field(min_length=2, max_length=120)
    emirate: str = Field(min_length=2, max_length=120)
    community: str = Field(min_length=2, max_length=180)
    developer: str | None = Field(default=None, max_length=180)
    bedrooms: int | None = Field(default=None, ge=0, le=100)
    bathrooms: int | None = Field(default=None, ge=0, le=100)
    area: Decimal | None = Field(default=None, gt=0)
    area_unit: Literal["sqft", "sqm"] | None = None
    price: Decimal | None = Field(default=None, ge=0)
    price_on_request: bool = True
    currency: Literal["AED"] = "AED"
    featured: bool = False
    provenance_note: str = Field(min_length=3, max_length=2000)
    external_reference_url: HttpUrl | None = None
    source_verified_at: date | None = None
    availability_status: AvailabilityStatus = AvailabilityStatus.UNVERIFIED
    status: PublicationStatus = PublicationStatus.DRAFT
    translations: dict[Literal["en", "ar"], TranslationInput]

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("Use a lowercase hyphenated slug")
        return value

    @model_validator(mode="after")
    def validate_publication(self) -> PropertyInput:
        if self.status == PublicationStatus.PUBLISHED and set(self.translations) != {"en", "ar"}:
            raise ValueError("Published properties require English and Arabic content")
        if not self.price_on_request and self.price is None:
            raise ValueError("Provide a price or use price on request")
        return self


class PropertyMediaMetadataInput(StrictModel):
    alt_en: str | None = Field(default=None, max_length=320)
    alt_ar: str | None = Field(default=None, max_length=320)
    provenance_url: HttpUrl
    rights_status: MediaRightsStatus = MediaRightsStatus.PENDING


class TrustProfileInput(StrictModel):
    display_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=7, max_length=40)
    google_business_url: HttpUrl
    google_rating: Decimal = Field(ge=0, le=5)
    google_review_count: int = Field(ge=0)
    snapshot_verified_at: date
    office_address: str = Field(min_length=5, max_length=320)
    status: PublicationStatus = PublicationStatus.DRAFT


class AreaAliasInput(StrictModel):
    alias: str = Field(min_length=1, max_length=240)
    locale: Literal["en", "ar"] | None = None


class AreaInput(StrictModel):
    slug: str = Field(min_length=2, max_length=180)
    name_en: str = Field(min_length=2, max_length=240)
    name_ar: str = Field(min_length=2, max_length=240)
    emirate: str = Field(min_length=2, max_length=120)
    status: PublicationStatus = PublicationStatus.DRAFT
    aliases: list[AreaAliasInput] = Field(default_factory=list, max_length=100)

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("Use a lowercase hyphenated slug")
        return value


class ProjectTranslationInput(StrictModel):
    official_name: str = Field(min_length=2, max_length=240)
    short_summary: str = Field(min_length=10, max_length=2000)
    full_description: str = Field(min_length=10, max_length=30000)
    seo_title: str = Field(min_length=2, max_length=240)
    seo_description: str = Field(min_length=10, max_length=320)


class ProjectSourceInput(StrictModel):
    source_url: HttpUrl
    source_type: ProjectSourceType
    is_official: bool = False
    retrieved_at: datetime
    last_checked_at: datetime
    content_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    source_title: str | None = Field(default=None, max_length=320)
    source_developer_domain: str | None = Field(default=None, max_length=320)
    is_active: bool = True


class PaymentMilestoneInput(StrictModel):
    sequence: int = Field(ge=0, le=1000)
    stage: PaymentStage
    label_en: str = Field(min_length=1, max_length=240)
    label_ar: str | None = Field(default=None, max_length=240)
    percentage: Decimal | None = Field(default=None, ge=0, le=100)
    due_trigger: str | None = Field(default=None, max_length=320)
    source_value: str = Field(min_length=1, max_length=2000)


class PaymentPlanInput(StrictModel):
    raw_source_text: str = Field(min_length=1, max_length=10000)
    source_index: int = Field(ge=0, le=100)
    is_complete: bool = False
    verified_at: datetime | None = None
    milestones: list[PaymentMilestoneInput] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_complete_total(self) -> PaymentPlanInput:
        percentages = [item.percentage for item in self.milestones]
        if self.is_complete and percentages and all(value is not None for value in percentages):
            if sum(value for value in percentages if value is not None) != Decimal("100"):
                raise ValueError("A complete payment plan with all percentages must total 100%")
        return self


class ProjectMediaInput(StrictModel):
    id: uuid.UUID | None = None
    category: ProjectMediaCategory
    source_url: HttpUrl
    rights_status: MediaRightsStatus = MediaRightsStatus.PENDING
    alt_en: str | None = Field(default=None, max_length=320)
    alt_ar: str | None = Field(default=None, max_length=320)
    display_order: int = Field(default=0, ge=0, le=10000)
    verified_at: datetime | None = None


class ProjectInput(StrictModel):
    slug: str = Field(min_length=2, max_length=180)
    developer_id: uuid.UUID
    area_id: uuid.UUID
    status: PublicationStatus = PublicationStatus.DRAFT
    availability_status: ProjectAvailabilityStatus
    construction_status: ConstructionStatus = ConstructionStatus.NOT_CONFIRMED
    handover_quarter: Literal["Q1", "Q2", "Q3", "Q4"] | None = None
    handover_year: int | None = Field(default=None, ge=2000, le=2200)
    original_handover_value: str | None = Field(default=None, max_length=240)
    last_verified_at: datetime | None = None
    priority: ProjectPriority = ProjectPriority.B
    featured: bool = False
    display_order: int = Field(default=0, ge=0, le=10000)
    internal_notes: str | None = Field(default=None, max_length=10000)
    property_types: list[ProjectPropertyType] = Field(default_factory=list, max_length=8)
    bedroom_options: list[ProjectBedroomOption] = Field(default_factory=list, max_length=7)
    translations: dict[Literal["en", "ar"], ProjectTranslationInput]
    sources: list[ProjectSourceInput] = Field(default_factory=list, max_length=50)
    payment_plan: PaymentPlanInput | None = None
    media: list[ProjectMediaInput] = Field(default_factory=list, max_length=100)

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("Use a lowercase hyphenated slug")
        return value

    @model_validator(mode="after")
    def validate_project(self) -> ProjectInput:
        if self.status == PublicationStatus.PUBLISHED and set(self.translations) != {"en", "ar"}:
            raise ValueError("Published projects require complete English and Arabic records")
        if self.payment_plan and self.payment_plan.source_index >= len(self.sources):
            raise ValueError("Payment-plan source_index must reference a supplied source")
        if len(set(self.property_types)) != len(self.property_types):
            raise ValueError("Property types must be unique")
        if len(set(self.bedroom_options)) != len(self.bedroom_options):
            raise ValueError("Bedroom options must be unique")
        return self


class ImportCandidateReviewInput(StrictModel):
    review_status: Literal[
        ImportReviewStatus.NEEDS_REVIEW,
        ImportReviewStatus.READY_FOR_APPROVAL,
        ImportReviewStatus.APPROVED,
        ImportReviewStatus.REJECTED,
        ImportReviewStatus.MERGED,
    ]
    linked_project_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def require_project_for_merge(self) -> ImportCandidateReviewInput:
        if self.review_status == ImportReviewStatus.MERGED and not self.linked_project_id:
            raise ValueError("Merged candidates require a linked canonical Project")
        return self


class PropertyResponse(PropertyInput):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class InsightTranslationInput(StrictModel):
    title: str = Field(min_length=2, max_length=240)
    excerpt: str = Field(min_length=10, max_length=2000)
    body: dict[str, Any]
    seo_title: str = Field(min_length=2, max_length=240)
    seo_description: str = Field(min_length=10, max_length=320)


class SourceLink(StrictModel):
    name: str = Field(min_length=2, max_length=240)
    url: HttpUrl


class InsightInput(StrictModel):
    slug: str = Field(min_length=2, max_length=180)
    category: str = Field(min_length=2, max_length=120)
    author_display_name: str = Field(min_length=2, max_length=160)
    source_links: list[SourceLink]
    status: PublicationStatus = PublicationStatus.DRAFT
    translations: dict[Literal["en", "ar"], InsightTranslationInput]

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("Use a lowercase hyphenated slug")
        return value

    @model_validator(mode="after")
    def validate_publication(self) -> InsightInput:
        if self.status == PublicationStatus.PUBLISHED and set(self.translations) != {"en", "ar"}:
            raise ValueError("Published insights require English and Arabic content")
        return self


class InsightResponse(InsightInput):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class DeveloperTranslationInput(StrictModel):
    name: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=10, max_length=20000)
    focus: str = Field(min_length=2, max_length=2000)
    verification_note: str = Field(min_length=10, max_length=2000)


class DeveloperInput(StrictModel):
    slug: str = Field(min_length=2, max_length=180)
    primary_emirate: str = Field(min_length=2, max_length=120)
    other_presence: list[str] = Field(default_factory=list, max_length=20)
    selected_projects: list[str] = Field(default_factory=list, max_length=100)
    official_website: HttpUrl
    source_url: HttpUrl
    additional_source_urls: list[HttpUrl] = Field(default_factory=list, max_length=20)
    verification_date: date
    enquiry_types: list[Literal["new-booking", "primary-sale", "resale"]] = Field(
        default_factory=list, max_length=3
    )
    featured: bool = False
    display_order: int = Field(default=0, ge=0, le=10000)
    status: PublicationStatus = PublicationStatus.DRAFT
    translations: dict[Literal["en", "ar"], DeveloperTranslationInput]

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("Use a lowercase hyphenated slug")
        return value

    @model_validator(mode="after")
    def validate_publication(self) -> DeveloperInput:
        if self.status == PublicationStatus.PUBLISHED:
            if set(self.translations) != {"en", "ar"}:
                raise ValueError("Published developers require English and Arabic content")
            if not self.source_url or not self.verification_date:
                raise ValueError("Published developers require provenance and a verification date")
        return self


class JobTranslationInput(StrictModel):
    title: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=10, max_length=20000)
    responsibilities: list[str] = Field(min_length=1)
    requirements: list[str] = Field(min_length=1)
    benefits: list[str] = Field(default_factory=list)


class JobInput(StrictModel):
    slug: str = Field(min_length=2, max_length=180)
    department: str = Field(min_length=2, max_length=160)
    location: str = Field(min_length=2, max_length=160)
    employment_type: str = Field(min_length=2, max_length=100)
    closing_date: date | None = None
    status: JobStatus = JobStatus.DRAFT
    translations: dict[Literal["en", "ar"], JobTranslationInput]

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("Use a lowercase hyphenated slug")
        return value

    @model_validator(mode="after")
    def validate_open_job(self) -> JobInput:
        if self.status == JobStatus.OPEN and set(self.translations) != {"en", "ar"}:
            raise ValueError("Open jobs require English and Arabic content")
        return self


class JobResponse(JobInput):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    meta: PageMeta


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    occurred_at: datetime
    outcome: str
    before_summary: dict[str, Any] | None
    after_summary: dict[str, Any] | None
    request_correlation_id: str
    metadata_summary: dict[str, Any] | None


class ContactEnquiryInput(StrictModel):
    enquiry_type: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=180)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=48, pattern=r"^[+0-9 ()-]+$")
    message: str = Field(min_length=10, max_length=5000)
    selected_developer: str | None = Field(default=None, max_length=180)
    selected_property: str | None = Field(default=None, max_length=180)
    locale: Literal["en", "ar"]
    preferred_contact_method: Literal["email", "phone", "whatsapp"]
    contact_consent: Literal[True]
    marketing_consent: bool = False
    attribution: dict[str, str] = Field(default_factory=dict)
    website: str = Field(default="", max_length=0)

    @field_validator("attribution")
    @classmethod
    def safe_attribution(cls, value: dict[str, str]) -> dict[str, str]:
        allowed = {"utm_source", "utm_medium", "utm_campaign", "referrer"}
        if set(value) - allowed or any(len(item) > 300 for item in value.values()):
            raise ValueError("Unsupported attribution context")
        return value


class EnquiryUpdate(StrictModel):
    status: EnquiryStatus
    internal_note: str | None = Field(default=None, max_length=5000)


class CareerApplicationInput(StrictModel):
    applicant_name: str = Field(min_length=2, max_length=180)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=48, pattern=r"^[+0-9 ()-]+$")
    current_location: str = Field(min_length=2, max_length=180)
    job_slug: str | None = Field(default=None, max_length=180)
    context_label: str = Field(min_length=2, max_length=240)
    linkedin_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    cover_note: str = Field(min_length=20, max_length=10000)
    locale: Literal["en", "ar"]
    acknowledgement_consent: Literal[True]
    marketing_consent: bool = False
    website: str = Field(default="", max_length=0)


class ApplicationUpdate(StrictModel):
    status: ApplicationStatus
    internal_note: str | None = Field(default=None, max_length=5000)
