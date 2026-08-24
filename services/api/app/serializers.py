from __future__ import annotations

from typing import Any

from app.models import InsightPost, JobOpening, Property


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
    else:
        data.update(
            {
                "provenance_note": record.provenance_note,
                "external_reference_url": record.external_reference_url,
                "translations": translations,
            }
        )
    return data


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
