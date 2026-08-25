from __future__ import annotations

from typing import Any

from app.models import (
    AreaCommunity,
    Developer,
    InsightPost,
    JobOpening,
    Project,
    ProjectImportBatch,
    ProjectImportCandidate,
    Property,
    TrustProfile,
)


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


def area_dict(record: AreaCommunity) -> dict[str, Any]:
    return {
        "id": record.id,
        "slug": record.slug,
        "name_en": record.name_en,
        "name_ar": record.name_ar,
        "emirate": record.emirate,
        "status": record.status.value,
        "aliases": [
            {"alias": item.alias, "locale": item.locale, "normalized_alias": item.normalized_alias}
            for item in record.aliases
        ],
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def project_dict(record: Project, locale: str | None = None) -> dict[str, Any]:
    translations = {
        item.locale: {
            "official_name": item.official_name,
            "short_summary": item.short_summary,
            "full_description": item.full_description,
            "seo_title": item.seo_title,
            "seo_description": item.seo_description,
        }
        for item in record.translations
    }
    sources = [
        {
            "id": item.id,
            "source_url": item.source_url,
            "source_type": item.source_type.value,
            "is_official": item.is_official,
            "retrieved_at": item.retrieved_at,
            "last_checked_at": item.last_checked_at,
            "content_hash": item.content_hash,
            "source_title": item.source_title,
            "source_developer_domain": item.source_developer_domain,
            "is_active": item.is_active,
        }
        for item in record.sources
    ]
    media = [
        {
            "id": item.id,
            "category": item.category.value,
            "source_url": item.source_url,
            "rights_status": item.rights_status.value,
            "alt_en": item.alt_en,
            "alt_ar": item.alt_ar,
            "display_order": item.display_order,
            "has_upload": bool(item.storage_key),
            "mime_type": item.mime_type,
            "width": item.width,
            "height": item.height,
            "size_bytes": item.size_bytes,
            "verified_at": item.verified_at,
        }
        for item in record.media
    ]
    plan = record.payment_plan
    payment_plan = (
        {
            "id": plan.id,
            "raw_source_text": plan.raw_source_text,
            "source_id": plan.source_id,
            "is_complete": plan.is_complete,
            "verified_at": plan.verified_at,
            "milestones": [
                {
                    "sequence": item.sequence,
                    "stage": item.stage.value,
                    "label_en": item.label_en,
                    "label_ar": item.label_ar,
                    "percentage": item.percentage,
                    "due_trigger": item.due_trigger,
                    "source_value": item.source_value,
                }
                for item in plan.milestones
            ],
        }
        if plan
        else None
    )
    data: dict[str, Any] = {
        "id": record.id,
        "slug": record.slug,
        "developer": {"id": record.developer.id, "slug": record.developer.slug},
        "area": {
            "id": record.area.id,
            "slug": record.area.slug,
            "name_en": record.area.name_en,
            "name_ar": record.area.name_ar,
            "emirate": record.area.emirate,
        },
        "status": record.status.value,
        "availability_status": record.availability_status.value,
        "construction_status": record.construction_status.value,
        "handover_quarter": record.handover_quarter,
        "handover_year": record.handover_year,
        "original_handover_value": record.original_handover_value,
        "last_verified_at": record.last_verified_at,
        "featured": record.featured,
        "display_order": record.display_order,
        "property_types": [item.property_type.value for item in record.property_types],
        "bedroom_options": [item.bedroom_option.value for item in record.bedroom_options],
        "sources": sources,
        "payment_plan": payment_plan,
        "media": media,
        "published_at": record.published_at,
        "archived_at": record.archived_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    if locale:
        data.update(translations.get(locale, {}))
        data["developer"]["name"] = next(
            (item.name for item in record.developer.translations if item.locale == locale),
            record.developer.slug,
        )
        data["cta"] = {
            "available": "enquire-now",
            "limited-availability": "check-current-availability",
            "coming-soon": "register-interest",
            "sold-out": "explore-similar-projects",
        }[record.availability_status.value]
        data["sources"] = [
            {
                "source_url": item["source_url"],
                "source_type": item["source_type"],
                "source_title": item["source_title"],
                "last_checked_at": item["last_checked_at"],
            }
            for item in sources
            if item["is_active"] and item["source_type"] != "OWNER_MANIFEST"
        ]
        data["payment_plan"] = (
            {
                "raw_source_text": plan.raw_source_text,
                "is_complete": plan.is_complete,
                "verified_at": plan.verified_at,
                "milestones": [
                    {
                        "sequence": item.sequence,
                        "stage": item.stage.value,
                        "label": item.label_ar if locale == "ar" else item.label_en,
                        "percentage": item.percentage,
                        "due_trigger": item.due_trigger,
                        "source_value": item.source_value,
                    }
                    for item in plan.milestones
                ],
            }
            if plan
            else None
        )
        data["media"] = [
            {
                "id": item["id"],
                "category": item["category"],
                "url": f"/api/v1/public/projects/{record.slug}/media/{item['id']}",
                "alt": item["alt_ar"] if locale == "ar" else item["alt_en"],
                "width": item["width"],
                "height": item["height"],
            }
            for item in media
            if item["rights_status"] == "approved" and item["has_upload"]
        ]
        data.pop("status", None)
        data.pop("archived_at", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
    else:
        data["developer_id"] = record.developer_id
        data["area_id"] = record.area_id
        data["priority"] = record.priority.value
        data["internal_notes"] = record.internal_notes
        data["translations"] = translations
    return data


def import_batch_dict(record: ProjectImportBatch) -> dict[str, Any]:
    return {
        "id": record.id,
        "name": record.name,
        "source_reference": record.source_reference,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "total_count": record.total_count,
        "clean_count": record.clean_count,
        "needs_review_count": record.needs_review_count,
        "failed_count": record.failed_count,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def import_candidate_dict(record: ProjectImportCandidate) -> dict[str, Any]:
    return {
        "id": record.id,
        "batch_id": record.batch_id,
        "raw_source_payload": record.raw_source_payload,
        "normalized_payload": record.normalized_payload,
        "owner_manifest_values": record.owner_manifest_values,
        "normalized_project_name": record.normalized_project_name,
        "proposed_developer_id": record.proposed_developer_id,
        "proposed_area_id": record.proposed_area_id,
        "official_source_url": record.official_source_url,
        "source_urls": record.source_urls,
        "extracted_at": record.extracted_at,
        "content_hash": record.content_hash,
        "match_result": record.match_result,
        "validation_errors": record.validation_errors,
        "conflict_reasons": record.conflict_reasons,
        "review_status": record.review_status.value,
        "linked_project_id": record.linked_project_id,
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
