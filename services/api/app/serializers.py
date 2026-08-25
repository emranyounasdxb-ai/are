from __future__ import annotations

from typing import Any

from app.acquisition.media import classify_media_dimensions
from app.models import (
    AreaCommunity,
    Developer,
    ImportReviewStatus,
    InsightPost,
    JobOpening,
    Project,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportMedia,
    Property,
    TrustProfile,
    UAEEmirate,
)
from app.project_processing import processing_eligibility_errors

EMIRATE_LABELS = {
    "en": {item: item.value for item in UAEEmirate},
    "ar": {
        UAEEmirate.DUBAI: "دبي",
        UAEEmirate.ABU_DHABI: "أبوظبي",
        UAEEmirate.SHARJAH: "الشارقة",
        UAEEmirate.AJMAN: "عجمان",
        UAEEmirate.UMM_AL_QUWAIN: "أم القيوين",
        UAEEmirate.RAS_AL_KHAIMAH: "رأس الخيمة",
        UAEEmirate.FUJAIRAH: "الفجيرة",
    },
}


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
        data["legal_name"] = record.legal_name
        data["source_name"] = record.source_name
        data["internal_aliases"] = record.internal_aliases
        data["verification_status"] = record.verification_status.value
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
        "emirate": record.emirate.value,
        "name_en": record.name_en,
        "name_ar": record.name_ar,
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
        "emirate": record.emirate.value,
        "developer": {"id": record.developer.id, "slug": record.developer.slug},
        "area": {
            "id": record.area.id,
            "slug": record.area.slug,
            "name_en": record.area.name_en,
            "name_ar": record.area.name_ar,
            "emirate": record.area.emirate.value,
        },
        "status": record.status.value,
        "workflow_status": record.workflow_status.value,
        "availability_status": record.availability_status.value,
        "construction_status": record.construction_status.value,
        "handover_quarter": record.handover_quarter,
        "handover_year": record.handover_year,
        "original_handover_value": record.original_handover_value,
        "size_min": record.size_min,
        "size_max": record.size_max,
        "size_unit": record.size_unit.value if record.size_unit else None,
        "down_payment_percentage": record.down_payment_percentage,
        "down_payment_source_value": record.down_payment_source_value,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "last_verified_at": record.last_verified_at,
        "featured": record.featured,
        "display_order": record.display_order,
        "property_types": [item.property_type.value for item in record.property_types],
        "bedroom_options": [item.bedroom_option.value for item in record.bedroom_options],
        "unit_types": [
            {
                "label_en": item.label_en,
                "label_ar": item.label_ar,
                "display_order": item.display_order,
            }
            for item in sorted(record.unit_types, key=lambda value: value.display_order)
        ],
        "amenities": [
            {
                "label_en": item.label_en,
                "label_ar": item.label_ar,
                "display_order": item.display_order,
            }
            for item in sorted(record.amenities, key=lambda value: value.display_order)
        ],
        "nearby_places": [
            {
                "name_en": item.name_en,
                "name_ar": item.name_ar,
                "distance_value": item.distance_value,
                "distance_unit": item.distance_unit,
                "travel_time_minutes": item.travel_time_minutes,
                "display_order": item.display_order,
            }
            for item in sorted(record.nearby_places, key=lambda value: value.display_order)
        ],
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
        data["emirate"] = EMIRATE_LABELS[locale][record.emirate]
        data["area"]["emirate"] = EMIRATE_LABELS[locale][record.area.emirate]
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
        data.pop("sources", None)
        data.pop("workflow_status", None)
        data.pop("down_payment_source_value", None)
        data["unit_types"] = [
            {
                "label": item["label_ar"] if locale == "ar" else item["label_en"],
                "display_order": item["display_order"],
            }
            for item in data["unit_types"]
        ]
        data["amenities"] = [
            {
                "label": item["label_ar"] if locale == "ar" else item["label_en"],
                "display_order": item["display_order"],
            }
            for item in data["amenities"]
        ]
        data["nearby_places"] = [
            {
                "name": item["name_ar"] if locale == "ar" else item["name_en"],
                "distance_value": item["distance_value"],
                "distance_unit": item["distance_unit"],
                "travel_time_minutes": item["travel_time_minutes"],
                "display_order": item["display_order"],
            }
            for item in data["nearby_places"]
        ]
        data["payment_plan"] = (
            {
                "is_complete": plan.is_complete,
                "verified_at": plan.verified_at,
                "milestones": [
                    {
                        "sequence": item.sequence,
                        "stage": item.stage.value,
                        "label": item.label_ar if locale == "ar" else item.label_en,
                        "percentage": item.percentage,
                        "due_trigger": item.due_trigger,
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
            if item["rights_status"] == "approved"
            and item["has_upload"]
            and isinstance(item["width"], int)
            and isinstance(item["height"], int)
            and isinstance(item["category"], str)
            and classify_media_dimensions(
                item["width"], item["height"], item["category"]
            ).public_eligible
        ]
        data.pop("status", None)
        data.pop("archived_at", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
    else:
        data["developer_id"] = record.developer_id
        data["area_id"] = record.area_id
        data["priority"] = record.priority.value if record.priority else None
        data["internal_notes"] = record.internal_notes
        data["translations"] = translations
    return data


def project_preview_dict(record: Project, locale: str) -> dict[str, Any]:
    """Return the public allowlist for an authenticated canonical Project preview."""
    data = project_dict(record, locale)
    data["media"] = [
        {
            **item,
            "url": f"/api/v1/admin/projects/{record.id}/preview-media/{item['id']}",
        }
        for item in data["media"]
    ]
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


def _import_media_quality(item: ProjectImportMedia) -> dict[str, object]:
    if not item.width or not item.height:
        return {
            "quality_status": "not-assessed",
            "public_eligible": False,
            "cover_eligible": False,
            "has_full_preview": False,
        }
    quality = classify_media_dimensions(item.width, item.height, item.category.value)
    return {
        "quality_status": quality.status,
        "public_eligible": quality.public_eligible and item.stage_status == "downloaded",
        "cover_eligible": quality.cover_eligible and item.stage_status == "downloaded",
        "has_full_preview": bool(item.storage_key),
    }


def import_candidate_dict(record: ProjectImportCandidate) -> dict[str, Any]:
    return {
        "id": record.id,
        "batch_id": record.batch_id,
        "manifest_row_id": record.manifest_row_id,
        "raw_source_payload": record.raw_source_payload,
        "normalized_payload": record.normalized_payload,
        "owner_manifest_values": record.owner_manifest_values,
        "normalized_project_name": record.normalized_project_name,
        "proposed_developer_id": record.proposed_developer_id,
        "proposed_area_id": record.proposed_area_id,
        "official_source_url": record.official_source_url,
        "adapter_key": record.adapter_key,
        "adapter_version": record.adapter_version,
        "last_verified_at": record.last_verified_at,
        "arabic_review_required": record.arabic_review_required,
        "acquisition_summary": record.acquisition_summary,
        "source_urls": record.source_urls,
        "extracted_at": record.extracted_at,
        "content_hash": record.content_hash,
        "match_result": record.match_result,
        "validation_errors": record.validation_errors,
        "conflict_reasons": record.conflict_reasons,
        "review_status": record.review_status.value,
        "processing_status": record.processing_status.value,
        "last_successful_stage": record.last_successful_stage,
        "review_version": record.review_version,
        "human_review_completed": record.human_review_completed,
        "human_edited_fields": record.human_edited_fields,
        "rejection_reason": record.rejection_reason,
        "linked_project_id": record.linked_project_id,
        "evidence": [
            {
                "source_url": item.source_url,
                "source_type": item.source_type.value,
                "http_status": item.http_status,
                "retrieved_at": item.retrieved_at,
                "adapter": f"{item.adapter_key}@{item.adapter_version}",
                "content_type": item.content_type,
                "size_bytes": item.size_bytes,
                "etag": item.etag,
                "last_modified": item.last_modified,
                "content_hash": item.content_hash,
                "private_snapshot_reference": item.storage_key,
                "outcome": item.outcome,
                "error_code": item.error_code,
            }
            for item in record.evidence
        ],
        "staged_media": [
            {
                "category": item.category.value,
                "source_url": item.source_url,
                "rights_status": item.rights_status.value,
                "stage_status": item.stage_status,
                "id": item.id,
                "has_thumbnail": bool(item.thumbnail_storage_key),
                "retrieved_at": item.retrieved_at,
                "size_bytes": item.size_bytes,
                "duplicate_of_id": item.duplicate_of_id,
                "failure_reason": item.failure_reason,
                "sha256": item.sha256,
                "width": item.width,
                "height": item.height,
                "normalized_filename": item.normalized_filename,
                "display_order": item.display_order,
                "alt_en_draft": item.alt_en_draft,
                "alt_ar_draft": item.alt_ar_draft,
                "derivatives": item.derivative_manifest,
                "change_status": item.change_status,
                "rights_basis": item.rights_basis,
                "rights_confirmed_at": item.rights_confirmed_at,
                "original_sha256": item.original_sha256,
                "processed_sha256": item.processed_sha256,
                "processing_version": item.processing_version,
                "public_metadata": item.public_metadata,
                "title_en": item.title_en,
                "title_ar": item.title_ar,
                "description_en": item.description_en,
                "description_ar": item.description_ar,
                "tags": item.tags,
                **_import_media_quality(item),
            }
            for item in record.staged_media
        ],
        "changes": [
            {
                "classification": item.classification,
                "field_name": item.field_name,
                "existing_value": item.existing_value,
                "new_value": item.new_value,
                "source_url": item.source_url,
                "detected_at": item.detected_at,
                "content_hash": item.content_hash,
            }
            for item in record.changes
        ],
        "editorial_draft": (
            {
                "overview_en": record.editorial_draft.overview_en,
                "overview_ar": record.editorial_draft.overview_ar,
                "source_version": record.editorial_draft.source_version,
                "model_name": record.editorial_draft.model_name,
                "model_version": record.editorial_draft.model_version,
                "origin": record.editorial_draft.origin,
                "overview_pack_id": record.editorial_draft.overview_pack_id,
                "overview_pack_hash": record.editorial_draft.overview_pack_hash,
                "fact_input_version": record.editorial_draft.fact_input_version,
                "fact_input_hash": record.editorial_draft.fact_input_hash,
                "candidate_version": record.editorial_draft.candidate_version,
                "generated_at": record.editorial_draft.generated_at,
                "approval_status": record.editorial_draft.approval_status.value,
                "approved_at": record.editorial_draft.approved_at,
            }
            if record.editorial_draft
            else None
        ),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


_PREVIEW_LABELS = {
    "ar": {
        "apartment": "شقق",
        "villa": "فلل",
        "mansion": "قصور",
        "Family golf course": "ملعب غولف عائلي",
        "Floating pavilion": "جناح عائم",
        "Event halls": "قاعات للفعاليات",
        "Helix bridge": "جسر حلزوني",
        "White sand beaches": "شواطئ ذات رمال بيضاء",
        "Mangrove and tide trail": "مسار القرم والمد والجزر",
        "Community centre": "مركز مجتمعي",
        "Ecopark": "حديقة بيئية",
        "Play zone": "منطقة ألعاب",
        "Dubai": "دبي",
        "Sharjah": "الشارقة",
        "Al Marjan Island": "جزيرة المرجان",
        "1, 2 and 3 Bedroom Apartments": "شقق بغرفة نوم واحدة وغرفتين وثلاث غرف نوم",
        "4, 5 and 6 Bedroom Villas": "فلل بأربع وخمس وست غرف نوم",
        "Mansions (configuration not confirmed)": "قصور (التكوين غير مؤكد)",
    }
}


def candidate_public_preview_dict(
    record: ProjectImportCandidate,
    developer: Developer,
    area: AreaCommunity,
    locale: str,
) -> dict[str, Any]:
    """Return an authenticated public-style allowlist without provenance or workflow internals."""
    proposal = record.normalized_payload or {}
    ar = locale == "ar"
    labels = _PREVIEW_LABELS.get(locale, {})
    developer_name = next(
        (item.name for item in developer.translations if item.locale == locale), developer.slug
    )
    overview = record.editorial_draft
    approved_overview = (
        overview if overview and overview.approval_status.value == "approved" else None
    )
    media = [
        {
            "id": item.id,
            "category": item.category.value,
            "thumbnail_url": (
                f"/api/v1/admin/project-imports/candidates/{record.id}/preview-media/"
                f"{item.id}?size=thumbnail"
            ),
            "full_url": (
                f"/api/v1/admin/project-imports/candidates/{record.id}/preview-media/"
                f"{item.id}?size=full"
            ),
            "alt": item.alt_ar_draft if ar else item.alt_en_draft,
            "width": item.width,
            "height": item.height,
            "display_order": item.display_order,
        }
        for item in sorted(record.staged_media, key=lambda value: value.display_order)
        if item.stage_status == "downloaded"
        and item.rights_status.value == "approved"
        and item.storage_key
    ]
    milestones = proposal.get("payment_milestones", [])
    return {
        "candidate_id": record.id,
        "locale": locale,
        "project_name": proposal.get("project_name_ar" if ar else "project_name")
        or record.normalized_project_name,
        "developer": {"name": developer_name},
        "emirate": EMIRATE_LABELS[locale][area.emirate],
        "area": area.name_ar if ar else area.name_en,
        "overview": approved_overview.overview_ar
        if ar and approved_overview
        else (approved_overview.overview_en if approved_overview else None),
        "property_types": [
            labels.get(str(value), str(value).replace("-", " ").title())
            for value in proposal.get("property_types", [])
        ],
        "unit_types": [
            labels.get(str(value), str(value)) for value in proposal.get("unit_types", [])
        ],
        "bedrooms": proposal.get("bedrooms", []),
        "size_min": proposal.get("size_min"),
        "size_max": proposal.get("size_max"),
        "size_unit": proposal.get("size_unit"),
        "size_ranges": proposal.get("size_ranges", []),
        "down_payment_percentage": proposal.get("down_payment_percentage"),
        "payment_plan": proposal.get("payment_plan"),
        "payment_milestones": [
            {
                "sequence": index + 1,
                "stage": str(value.get("stage", "other")),
                "percentage": value.get("percentage"),
            }
            for index, value in enumerate(milestones)
            if isinstance(value, dict)
        ],
        "handover_quarter": proposal.get("handover_quarter"),
        "handover_year": proposal.get("handover_year"),
        "handover_verification": "requires-verification",
        "availability_status": "not-confirmed",
        "construction_status": "not-confirmed",
        "amenities": [
            labels.get(str(value), str(value)) for value in proposal.get("amenities", [])
        ],
        "nearby_places": [
            {
                "name": labels.get(str(value.get("name")), str(value.get("name"))),
                "travel_time_minutes": value.get("travel_time_minutes"),
            }
            for value in proposal.get("nearby_places", [])
            if isinstance(value, dict)
        ],
        "media": media,
        "has_cover": any(item["category"] == "cover" for item in media),
    }


def import_candidate_summary_dict(record: ProjectImportCandidate) -> dict[str, Any]:
    missing = [
        str(item.get("field", "Unknown"))
        for item in record.validation_errors
        if isinstance(item, dict)
    ]
    media_statuses = [item.stage_status for item in record.staged_media]
    accepted_media = [item for item in record.staged_media if item.stage_status == "downloaded"]
    blockers = [_review_message(item) for item in record.validation_errors]
    blockers.extend(str(item) for item in record.conflict_reasons)
    if not record.proposed_developer_id:
        blockers.append("Select the canonical Developer.")
    if not record.proposed_area_id:
        blockers.append("Select the canonical Area.")
    if not record.official_source_url:
        blockers.append("Official evidence is incomplete.")
    proposal = record.normalized_payload or {}
    for key in ("property_types", "bedrooms", "availability_status", "construction_status"):
        if proposal.get(key) in (None, [], {}):
            blockers.append(f"Review the source-grounded {key.replace('_', ' ')}.")
    if record.arabic_review_required:
        blockers.append("Arabic evidence requires human review.")
    if not record.human_review_completed:
        blockers.append("Complete the human field review.")
    ready = not blockers and bool(record.official_source_url)
    status = record.review_status
    eligibility = {
        "retry-acquisition": status == ImportReviewStatus.FAILED,
        "assign-developer": status == ImportReviewStatus.NEEDS_REVIEW,
        "assign-area": status == ImportReviewStatus.NEEDS_REVIEW,
        "reject": status
        in {
            ImportReviewStatus.FAILED,
            ImportReviewStatus.NEEDS_REVIEW,
            ImportReviewStatus.READY_FOR_APPROVAL,
        },
        "mark-ready": status == ImportReviewStatus.NEEDS_REVIEW and ready,
        "create-drafts": status == ImportReviewStatus.READY_FOR_APPROVAL,
    }
    return {
        "id": record.id,
        "manifest_row_id": record.manifest_row_id,
        "project_name": record.normalized_project_name
        or record.owner_manifest_values.get("owner_project_name")
        or "Unnamed candidate",
        "owner_developer": record.owner_manifest_values.get("owner_developer"),
        "owner_area": record.owner_manifest_values.get("owner_area"),
        "proposed_developer_id": record.proposed_developer_id,
        "proposed_area_id": record.proposed_area_id,
        "official_source_url": record.official_source_url,
        "review_status": record.review_status.value,
        "processing_status": record.processing_status.value,
        "last_successful_stage": record.last_successful_stage,
        "missing_fields": missing,
        "blockers": blockers,
        "warnings": [
            "Private media rights remain Pending."
            for item in accepted_media
            if item.rights_status.value == "pending"
        ][:1],
        "conflict_count": len(record.conflict_reasons),
        "media_count": len(record.staged_media),
        "media_downloaded_count": sum(value == "downloaded" for value in media_statuses),
        "media_failed_count": sum(value == "failed" for value in media_statuses),
        "last_verified_at": record.last_verified_at,
        "review_version": record.review_version,
        "human_review_completed": record.human_review_completed,
        "arabic_review_state": ("review-required" if record.arabic_review_required else "reviewed"),
        "rights_status": (
            "approved"
            if accepted_media
            and all(item.rights_status.value == "approved" for item in accepted_media)
            else "pending"
            if any(item.rights_status.value == "pending" for item in accepted_media)
            else "none"
        ),
        "eligibility": eligibility,
        "processing_eligibility_errors": processing_eligibility_errors(record),
        "updated_at": record.updated_at,
    }


def _review_message(value: dict[str, Any]) -> str:
    code = str(value.get("code", ""))
    field = str(value.get("field", "evidence")).replace("_", " ")
    messages = {
        "official_source_not_found": "No matching public official Project page was found.",
        "missing_official_evidence": f"Official evidence is incomplete for {field}.",
        "missing_canonical_area": "Select the canonical Area.",
        "missing_canonical_developer": "Select the canonical Developer.",
        "name_conflict": "Manifest and official Project names differ.",
    }
    return messages.get(code, str(value.get("message") or f"Review {field}."))


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
