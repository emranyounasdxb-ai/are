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

from app.models import ApplicationStatus, EnquiryStatus, JobStatus, PublicationStatus, Purpose

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
