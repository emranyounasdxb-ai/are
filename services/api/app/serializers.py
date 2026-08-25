from __future__ import annotations

from typing import Any

from app.models import Developer, InsightPost, JobOpening, Property, TrustProfile


def developer_dict(record: Developer, locale: str | None = None) -> dict[str, Any]:
    translations = {
        item.locale: {
            "name": item.name,
            "description": item.description,
            "focus": item.focus,
            "verification_note": item.verification_note,
        }
        for item in record.translations
    }
    data: dict[str, Any] = {
        "id": record.id,
        "slug": record.slug,
        "primary_emirate": record.primary_emirate,
        "other_presence": record.other_presence,
        "selected_projects": record.selected_projects,
        "official_website": record.official_website,
        "source_url": record.source_url,
        "additional_source_urls": record.additional_source_urls,
        "verification_date": record.verification_date,
        "enquiry_types": record.enquiry_types,
        "featured": record.featured,
        "display_order": record.display_order,
        "status": record.status.value,
        "published_at": record.published_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    if locale:
        data.update(translations.get(locale, {}))
    else:
        data["translations"] = translations
    return data


def property_dict(record: Property, locale: str | None = None) -> dict[str, Any]:
    translations = {
        item.locale: {"title": item.title, "description": item.description}
        for item in record.translations
    }
    data: dict[str, Any] = {
        "id": record.id,
        "slug": record.slug,
        "purpose": record.purpose.value,
        "property_type": record.property_type,
        "emirate": record.emirate,
        "community": record.community,
        "developer": record.developer,
        "bedrooms": record.bedrooms,
        "bathrooms": record.bathrooms,
        "area": record.area,
        "area_unit": record.area_unit,
        "price": record.price,
        "price_on_request": record.price_on_request,
        "currency": record.currency,
        "featured": record.featured,
        "status": record.status.value,
        "published_at": record.published_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    if locale:
        data.update(translations.get(locale, {}))
        media = record.cover_media
        if (
            media
            and media.storage_key
            and media.rights_status.value == "approved"
            and media.alt_en
            and media.alt_ar
        ):
            data["cover_media"] = {
                "url": f"/public/properties/{record.slug}/cover",
                "alt": media.alt_ar if locale == "ar" else media.alt_en,
                "width": media.width,
                "height": media.height,
            }
        else:
            data["cover_media"] = None
    else:
        data.update(
            {
                "provenance_note": record.provenance_note,
                "external_reference_url": record.external_reference_url,
                "source_verified_at": record.source_verified_at,
                "availability_status": record.availability_status.value,
                "cover_media": media_dict(record),
                "translations": translations,
            }
        )
    return data


def media_dict(record: Property) -> dict[str, Any] | None:
    media = record.cover_media
    if not media:
        return None
    return {
        "id": media.id,
        "has_upload": bool(media.storage_key),
        "original_filename": media.original_filename,
        "mime_type": media.mime_type,
        "size_bytes": media.size_bytes,
        "width": media.width,
        "height": media.height,
        "alt_en": media.alt_en,
        "alt_ar": media.alt_ar,
        "provenance_url": media.provenance_url,
        "rights_status": media.rights_status.value,
        "display_position": media.display_position,
        "preview_url": f"/admin/properties/{record.id}/cover" if media.storage_key else None,
    }


def trust_profile_dict(record: TrustProfile) -> dict[str, Any]:
    return {
        "id": record.id,
        "display_name": record.display_name,
        "phone": record.phone,
        "google_business_url": record.google_business_url,
        "google_rating": record.google_rating,
        "google_review_count": record.google_review_count,
        "snapshot_verified_at": record.snapshot_verified_at,
        "office_address": record.office_address,
        "status": record.status.value,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def insight_dict(record: InsightPost, locale: str | None = None) -> dict[str, Any]:
    translations = {
        item.locale: {
            "title": item.title,
            "excerpt": item.excerpt,
            "body": item.body,
            "seo_title": item.seo_title,
            "seo_description": item.seo_description,
        }
        for item in record.translations
    }
    data: dict[str, Any] = {
        "id": record.id,
        "slug": record.slug,
        "category": record.category,
        "author_display_name": record.author_display_name,
        "source_links": record.source_links,
        "status": record.status.value,
        "published_at": record.published_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    if locale:
        data.update(translations.get(locale, {}))
    else:
        data["translations"] = translations
    return data


def job_dict(record: JobOpening, locale: str | None = None) -> dict[str, Any]:
    translations = {
        item.locale: {
            "title": item.title,
            "description": item.description,
            "responsibilities": item.responsibilities,
            "requirements": item.requirements,
            "benefits": item.benefits,
        }
        for item in record.translations
    }
    data: dict[str, Any] = {
        "id": record.id,
        "slug": record.slug,
        "department": record.department,
        "location": record.location,
        "employment_type": record.employment_type,
        "closing_date": record.closing_date,
        "status": record.status.value,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    if locale:
        data.update(translations.get(locale, {}))
    else:
        data["translations"] = translations
    return data
