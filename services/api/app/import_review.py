from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.reconciliation import reconcile_candidate_quality
from app.acquisition.service import retry_candidates
from app.audit import request_correlation_id, write_audit
from app.config import Settings
from app.dependencies import AuthContext
from app.models import (
    AreaCommunity,
    ConstructionStatus,
    Developer,
    ImportReviewStatus,
    MediaRightsStatus,
    PaymentStage,
    Project,
    ProjectAmenity,
    ProjectAvailabilityStatus,
    ProjectBedroomOption,
    ProjectBedroomValue,
    ProjectImportBatch,
    ProjectImportBulkOperation,
    ProjectImportCandidate,
    ProjectMedia,
    ProjectNearbyPlace,
    ProjectPaymentMilestone,
    ProjectPaymentPlan,
    ProjectPropertyType,
    ProjectPropertyTypeValue,
    ProjectSizeUnit,
    ProjectSource,
    ProjectSourceType,
    ProjectTranslation,
    ProjectUnitType,
    PublicationStatus,
)
from app.schemas import ImportBulkActionInput


def eligibility_errors(candidate: ProjectImportCandidate) -> list[str]:
    errors: list[str] = []
    proposal = candidate.normalized_payload or {}
    if not candidate.proposed_developer_id:
        errors.append("Canonical Developer is required.")
    if not candidate.proposed_area_id:
        errors.append("Canonical Area is required.")
    if not candidate.official_source_url:
        errors.append("An official source is required.")
    if not candidate.normalized_project_name:
        errors.append("A source-grounded project name is required.")
    if candidate.validation_errors:
        errors.append("Missing source-grounded fields must be resolved.")
    if candidate.conflict_reasons:
        errors.append("Source conflicts must be resolved.")
    if candidate.arabic_review_required:
        errors.append("Arabic evidence requires human review.")
    if not candidate.human_review_completed:
        errors.append("Human review must be completed.")
    for key in ("property_types", "bedrooms", "availability_status", "construction_status"):
        if proposal.get(key) in (None, [], {}):
            errors.append(f"{key.replace('_', ' ').title()} is required.")
    return errors


def draft_eligibility_errors(candidate: ProjectImportCandidate) -> list[str]:
    """Validate a private review Draft without applying publication approval gates."""
    errors: list[str] = []
    if not candidate.proposed_developer_id:
        errors.append("Canonical Developer is required.")
    if not candidate.proposed_area_id:
        errors.append("Canonical Area is required.")
    if not candidate.source_urls:
        errors.append("At least one retained source is required.")
    if not candidate.normalized_project_name:
        errors.append("A source-grounded project name is required.")
    overview = candidate.editorial_draft
    if not overview or not overview.overview_en or not overview.overview_ar:
        errors.append("A bilingual Overview draft is required.")
    return errors


async def apply_bulk_action(
    db: AsyncSession,
    batch_id: uuid.UUID,
    payload: ImportBulkActionInput,
    request: Request,
    context: AuthContext,
    settings: Settings,
) -> dict[str, Any]:
    batch = await db.get(ProjectImportBatch, batch_id)
    if not batch:
        raise _not_found("Import batch not found.")
    request_data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    request_hash = hashlib.sha256(
        json.dumps(request_data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    previous = await db.scalar(
        select(ProjectImportBulkOperation).where(
            ProjectImportBulkOperation.batch_id == batch_id,
            ProjectImportBulkOperation.idempotency_key == payload.idempotency_key,
        )
    )
    if previous:
        if previous.request_hash != request_hash:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail={
                    "code": "idempotency_conflict",
                    "message": "This operation key was already used.",
                },
            )
        return previous.result

    candidates = (
        (
            await db.scalars(
                select(ProjectImportCandidate)
                .where(ProjectImportCandidate.id.in_(payload.candidate_ids))
                .with_for_update()
                .options(
                    selectinload(ProjectImportCandidate.evidence),
                    selectinload(ProjectImportCandidate.staged_media),
                    selectinload(ProjectImportCandidate.editorial_draft),
                )
            )
        )
        .unique()
        .all()
    )
    if len(candidates) != len(payload.candidate_ids) or any(
        item.batch_id != batch_id for item in candidates
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_selection",
                "message": "All candidates must belong to the active batch.",
            },
        )
    stale = [
        item.manifest_row_id
        for item in candidates
        if payload.expected_versions[item.id] != item.review_version
    ]
    if stale:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_selection",
                "message": f"Rows changed since selection: {stale}. Refresh and retry.",
            },
        )

    if payload.action != "create-drafts" and any(
        item.review_status == ImportReviewStatus.MERGED for item in candidates
    ):
        raise _invalid("Candidates already linked to Draft Projects cannot be changed here.")

    if payload.action == "retry-acquisition" and any(
        item.review_status != ImportReviewStatus.FAILED for item in candidates
    ):
        raise _invalid("Retry is limited to Failed or source-unavailable candidates.")
    if payload.action in {"assign-developer", "assign-area"} and any(
        item.review_status != ImportReviewStatus.NEEDS_REVIEW for item in candidates
    ):
        raise _invalid("Canonical mappings can be changed only while a candidate Needs Review.")

    if payload.action == "assign-developer":
        if not await db.get(Developer, payload.developer_id):
            raise _invalid("Canonical Developer does not exist.")
        for item in candidates:
            item.proposed_developer_id = payload.developer_id
            _remove_mapping_issue(item, "developer")
            item.human_review_completed = False
            item.review_status = ImportReviewStatus.NEEDS_REVIEW
    elif payload.action == "assign-area":
        if not await db.get(AreaCommunity, payload.area_id):
            raise _invalid("Canonical Area does not exist.")
        for item in candidates:
            item.proposed_area_id = payload.area_id
            _remove_mapping_issue(item, "area")
            item.human_review_completed = False
            item.review_status = ImportReviewStatus.NEEDS_REVIEW
    elif payload.action == "reject":
        for item in candidates:
            item.review_status = ImportReviewStatus.REJECTED
            item.rejection_reason = payload.rejection_reason
            item.reviewed_by = context.user.id
    elif payload.action == "mark-ready":
        ineligible = {
            item.manifest_row_id: (
                (
                    ["Candidate must be in Needs Review status."]
                    if item.review_status != ImportReviewStatus.NEEDS_REVIEW
                    else []
                )
                + eligibility_errors(item)
            )
            for item in candidates
            if item.review_status != ImportReviewStatus.NEEDS_REVIEW or eligibility_errors(item)
        }
        if ineligible:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "candidate_ineligible",
                    "message": "One or more selected candidates are not Ready.",
                    "results": [
                        {
                            "candidate_id": str(item.id),
                            "manifest_row": item.manifest_row_id,
                            "outcome": "blocked",
                            "reason": "; ".join(ineligible[item.manifest_row_id]),
                        }
                        for item in candidates
                        if item.manifest_row_id in ineligible
                    ],
                },
            )
        for item in candidates:
            item.review_status = ImportReviewStatus.READY_FOR_APPROVAL
            item.reviewed_by = context.user.id
    elif payload.action == "create-drafts":
        ineligible = {
            item.manifest_row_id: (
                (
                    ["Candidate is not in a Draft-eligible review state."]
                    if item.review_status
                    not in {
                        ImportReviewStatus.NEEDS_REVIEW,
                        ImportReviewStatus.READY_FOR_APPROVAL,
                    }
                    else []
                )
                + draft_eligibility_errors(item)
            )
            for item in candidates
            if item.review_status
            not in {ImportReviewStatus.NEEDS_REVIEW, ImportReviewStatus.READY_FOR_APPROVAL}
            or draft_eligibility_errors(item)
        }
        if ineligible:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "candidate_draft_ineligible",
                    "message": "One or more selected candidates cannot create a safe Draft.",
                    "results": [
                        {
                            "candidate_id": str(item.id),
                            "manifest_row": item.manifest_row_id,
                            "outcome": "blocked",
                            "reason": "; ".join(
                                ineligible.get(
                                    item.manifest_row_id,
                                    ["Candidate is not in a Draft-eligible review state."],
                                )
                            ),
                        }
                        for item in candidates
                        if item.manifest_row_id in ineligible
                    ],
                },
            )
        for item in candidates:
            item.linked_project_id = (await _create_draft(db, item, context.user.id)).id
            item.review_status = ImportReviewStatus.MERGED
            item.reviewed_by = context.user.id
    elif payload.action == "retry-acquisition":
        await retry_candidates(db, settings, list(candidates))

    if payload.action != "retry-acquisition":
        for item in candidates:
            reconcile_candidate_quality(item)
            item.review_version += 1
        statuses = list(
            await db.scalars(
                select(ProjectImportCandidate.review_status).where(
                    ProjectImportCandidate.batch_id == batch_id
                )
            )
        )
        batch.total_count = len(statuses)
        batch.clean_count = statuses.count(ImportReviewStatus.READY_FOR_APPROVAL)
        batch.needs_review_count = statuses.count(ImportReviewStatus.NEEDS_REVIEW)
        batch.failed_count = statuses.count(ImportReviewStatus.FAILED)
    affected = sorted(item.manifest_row_id for item in candidates)
    result = {
        "action": payload.action,
        "affected_count": len(candidates),
        "manifest_rows": affected,
        "message": (
            f"{payload.action.replace('-', ' ').title()} completed for "
            f"{len(candidates)} candidate(s)."
        ),
        "results": [
            {
                "candidate_id": str(item.id),
                "manifest_row": item.manifest_row_id,
                "outcome": "succeeded",
                "reason": "The requested review action completed.",
            }
            for item in candidates
        ],
    }
    for item in candidates:
        await write_audit(
            db,
            action=f"project-import.bulk.{payload.action}",
            entity_type="project_import_candidate",
            entity_id=item.id,
            actor_user_id=context.user.id,
            correlation_id=request_correlation_id(request),
            after={
                "manifest_row_id": item.manifest_row_id,
                "review_status": item.review_status.value,
            },
            metadata={"selection_size": len(candidates)},
        )
    db.add(
        ProjectImportBulkOperation(
            batch_id=batch_id,
            idempotency_key=payload.idempotency_key,
            action=payload.action,
            request_hash=request_hash,
            result=result,
            actor_user_id=context.user.id,
        )
    )
    await db.commit()
    return result


async def _create_draft(
    db: AsyncSession, candidate: ProjectImportCandidate, actor_id: uuid.UUID
) -> Project:
    problems = draft_eligibility_errors(candidate)
    if problems:
        raise _invalid(f"Candidate {candidate.manifest_row_id} is not eligible: {problems}")
    proposal = candidate.normalized_payload or {}
    project_name = candidate.normalized_project_name
    if not project_name:
        raise _invalid("A source-grounded project name is required.")
    slug_root = re.sub(r"[^a-z0-9]+", "-", project_name.casefold()).strip("-")
    slug = f"{slug_root}-{candidate.manifest_row_id}"
    if await db.scalar(select(Project.id).where(Project.slug == slug)):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "code": "draft_exists",
                "message": f"A Draft Project already exists for row {candidate.manifest_row_id}.",
            },
        )
    area = await db.get(AreaCommunity, candidate.proposed_area_id)
    if not area:
        raise _invalid("The mapped canonical Area no longer exists.")
    record = Project(
        slug=slug,
        developer_id=candidate.proposed_developer_id,
        area_id=candidate.proposed_area_id,
        emirate=area.emirate,
        status=PublicationStatus.DRAFT,
        availability_status=_availability_status(proposal.get("availability_status")),
        construction_status=_construction_status(proposal.get("construction_status")),
        handover_quarter=proposal.get("handover_quarter"),
        handover_year=proposal.get("handover_year"),
        original_handover_value=proposal.get("original_handover_value"),
        size_min=proposal.get("size_min"),
        size_max=proposal.get("size_max"),
        size_unit=(
            ProjectSizeUnit(str(proposal["size_unit"])) if proposal.get("size_unit") else None
        ),
        down_payment_percentage=proposal.get("down_payment_percentage"),
        down_payment_source_value=proposal.get("down_payment_source_value"),
        last_verified_at=candidate.last_verified_at,
        priority=None,
        featured=False,
        display_order=0,
        created_by=actor_id,
        updated_by=actor_id,
    )
    record.property_types = [
        ProjectPropertyTypeValue(property_type=ProjectPropertyType(str(value)))
        for value in proposal.get("property_types", [])
    ]
    record.bedroom_options = [
        ProjectBedroomValue(bedroom_option=_bedroom_option(value))
        for value in proposal.get("bedrooms", [])
    ]
    overview = candidate.editorial_draft
    if not overview or not overview.overview_en or not overview.overview_ar:
        raise _invalid("A bilingual Overview draft is required.")
    project_name_ar = str(proposal.get("project_name_ar") or project_name)
    record.translations = [
        ProjectTranslation(
            locale="en",
            official_name=project_name,
            short_summary=overview.overview_en,
            full_description=overview.overview_en,
            seo_title=project_name,
            seo_description=overview.overview_en[:320],
        ),
        ProjectTranslation(
            locale="ar",
            official_name=project_name_ar,
            short_summary=overview.overview_ar,
            full_description=overview.overview_ar,
            seo_title=project_name_ar,
            seo_description=overview.overview_ar[:320],
        ),
    ]
    record.unit_types = [
        ProjectUnitType(
            label_en=str(value["label_en"]),
            label_ar=str(value["label_ar"]),
            display_order=index,
        )
        for index, value in enumerate(proposal.get("localized_unit_types", []))
        if isinstance(value, dict) and value.get("label_en") and value.get("label_ar")
    ]
    record.amenities = [
        ProjectAmenity(
            label_en=str(value["label_en"]),
            label_ar=str(value["label_ar"]),
            display_order=index,
        )
        for index, value in enumerate(proposal.get("localized_amenities", []))
        if isinstance(value, dict) and value.get("label_en") and value.get("label_ar")
    ]
    record.nearby_places = [
        ProjectNearbyPlace(
            name_en=str(value["name_en"]),
            name_ar=str(value["name_ar"]),
            travel_time_minutes=value.get("travel_time_minutes"),
            display_order=index,
        )
        for index, value in enumerate(proposal.get("localized_nearby_places", []))
        if isinstance(value, dict) and value.get("name_en") and value.get("name_ar")
    ]
    latest_evidence = {
        item.source_url: item
        for item in sorted(candidate.evidence, key=lambda value: value.retrieved_at)
        if item.outcome in {"acquired", "extracted"}
        and item.storage_key
        and item.http_status is not None
        and 200 <= item.http_status < 300
    }
    retained_urls = list(
        dict.fromkeys(
            [
                *([candidate.official_source_url] if candidate.official_source_url else []),
                *candidate.source_urls,
            ]
        )
    )
    primary_secondary = next(
        (value for value in retained_urls if "tanamiproperties.com/Projects/" in value), None
    )
    proposed_payment = proposal.get("payment_plan")
    plan_url = proposed_payment.get("source_url") if isinstance(proposed_payment, dict) else None
    retained_urls = list(
        dict.fromkeys(
            [
                *([candidate.official_source_url] if candidate.official_source_url else []),
                *([primary_secondary] if primary_secondary else []),
                *([plan_url] if plan_url and plan_url in latest_evidence else []),
            ]
        )
    )
    record.sources = []
    for source_url in retained_urls:
        evidence = latest_evidence.get(source_url)
        is_official = source_url == candidate.official_source_url
        record.sources.append(
            ProjectSource(
                source_url=source_url,
                source_type=(
                    ProjectSourceType.OFFICIAL_DEVELOPER_PAGE
                    if is_official
                    else ProjectSourceType.APPROVED_SECONDARY_SOURCE
                ),
                is_official=is_official,
                retrieved_at=(
                    evidence.retrieved_at
                    if evidence
                    else candidate.extracted_at or datetime.now(UTC)
                ),
                last_checked_at=candidate.last_verified_at or datetime.now(UTC),
                content_hash=evidence.content_hash if evidence else candidate.content_hash,
                is_active=True,
            )
        )
    record.media = [
        ProjectMedia(
            category=item.category,
            source_url=item.source_url,
            rights_status=item.rights_status,
            alt_en=item.alt_en_draft,
            alt_ar=item.alt_ar_draft,
            display_order=item.display_order,
            storage_key=item.storage_key,
            original_filename=item.normalized_filename,
            mime_type=item.mime_type,
            size_bytes=item.size_bytes,
            sha256=item.sha256,
            width=item.width,
            height=item.height,
            verified_at=item.rights_confirmed_at,
            uploaded_by=item.rights_confirmed_by,
        )
        for item in candidate.staged_media
        if item.stage_status == "downloaded"
        and item.rights_status.value == "approved"
        and item.storage_key
    ]
    db.add(record)
    await db.flush()
    payment = proposal.get("payment_plan")
    milestones = proposal.get("payment_milestones", [])
    raw_payment = payment if isinstance(payment, str) else None
    if isinstance(payment, dict):
        raw_payment = str(payment.get("raw_source_text") or "") or None
        milestones = payment.get("milestones") or milestones
    if raw_payment and isinstance(milestones, list) and milestones:
        plan_source = next(
            (s for s in record.sources if s.source_url == plan_url), record.sources[0]
        )
        if plan_url and plan_source.source_url != plan_url:
            raise ValueError("Payment plan must retain its exact source evidence.")
        plan = ProjectPaymentPlan(
            project_id=record.id,
            raw_source_text=raw_payment,
            source_id=plan_source.id,
            is_complete=bool(isinstance(payment, dict) and payment.get("is_complete")),
            verified_at=None
            if isinstance(payment, dict) and payment.get("requires_review")
            else candidate.last_verified_at,
        )
        plan.milestones = [
            ProjectPaymentMilestone(
                sequence=int(value.get("sequence", index + 1)),
                stage=str(value.get("stage", "other")),
                label_en=str(value.get("source_value", "Source milestone"))[:240],
                label_ar=(str(value["label_ar"]) if value.get("label_ar") else None),
                percentage=value.get("percentage"),
                source_value=str(value.get("source_value", "")),
            )
            for index, value in enumerate(milestones)
            if isinstance(value, dict) and value.get("source_value")
        ]
        record.payment_plan = plan
    return record


async def sync_linked_draft_from_candidate(
    db: AsyncSession, candidate: ProjectImportCandidate, *, fields: set[str] | None = None
) -> Project | None:
    """Refresh only an existing private Draft with retained source-grounded evidence."""
    if not candidate.linked_project_id:
        return None
    record = await db.scalar(
        select(Project)
        .where(Project.id == candidate.linked_project_id)
        .options(
            selectinload(Project.property_types),
            selectinload(Project.bedroom_options),
            selectinload(Project.unit_types),
            selectinload(Project.amenities),
            selectinload(Project.sources),
            selectinload(Project.payment_plan).selectinload(ProjectPaymentPlan.milestones),
            selectinload(Project.media),
        )
    )
    if not record or record.status != PublicationStatus.DRAFT:
        return record
    proposal = candidate.normalized_payload or {}

    def included(field: str) -> bool:
        return fields is None or field in fields

    if fields is None:
        record.developer_id = candidate.proposed_developer_id or record.developer_id
        record.area_id = candidate.proposed_area_id or record.area_id
        record.last_verified_at = candidate.last_verified_at
    if included("availability_status"):
        record.availability_status = _availability_status(proposal.get("availability_status"))
    if included("construction_status"):
        record.construction_status = _construction_status(proposal.get("construction_status"))
    for field in (
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "size_min",
        "size_max",
        "down_payment_percentage",
        "down_payment_source_value",
    ):
        if included(field):
            setattr(record, field, proposal.get(field))
    if included("size_unit"):
        record.size_unit = (
            ProjectSizeUnit(str(proposal["size_unit"])) if proposal.get("size_unit") else None
        )
    property_types = list(dict.fromkeys(proposal.get("property_types", [])))
    if property_types and included("property_types"):
        desired_property_types = {ProjectPropertyType(str(value)) for value in property_types}
        existing_property_types = {item.property_type: item for item in record.property_types}
        for property_type_value, property_type_row in existing_property_types.items():
            if property_type_value not in desired_property_types:
                await db.delete(property_type_row)
        for property_type_value in desired_property_types - existing_property_types.keys():
            record.property_types.append(
                ProjectPropertyTypeValue(property_type=property_type_value)
            )
    bedrooms = list(dict.fromkeys(proposal.get("bedrooms", [])))
    if bedrooms and included("bedrooms"):
        desired_bedrooms = {_bedroom_option(value) for value in bedrooms}
        existing_bedrooms = {item.bedroom_option: item for item in record.bedroom_options}
        for bedroom_value, bedroom_row in existing_bedrooms.items():
            if bedroom_value not in desired_bedrooms:
                await db.delete(bedroom_row)
        for bedroom_value in desired_bedrooms - existing_bedrooms.keys():
            record.bedroom_options.append(ProjectBedroomValue(bedroom_option=bedroom_value))
    localized_units = proposal.get("localized_unit_types", [])
    if isinstance(localized_units, list) and localized_units and included("localized_unit_types"):
        desired_units = {
            str(value["label_en"]): (str(value["label_ar"]), index)
            for index, value in enumerate(localized_units)
            if isinstance(value, dict) and value.get("label_en") and value.get("label_ar")
        }
        existing_units = {item.label_en: item for item in record.unit_types}
        for label, unit_row in existing_units.items():
            if label not in desired_units:
                await db.delete(unit_row)
        for label, (label_ar, display_order) in desired_units.items():
            target_unit = existing_units.get(label)
            if not target_unit:
                target_unit = ProjectUnitType(label_en=label)
                record.unit_types.append(target_unit)
            target_unit.label_ar = label_ar
            target_unit.display_order = display_order
    localized_amenities = proposal.get("localized_amenities", [])
    if (
        isinstance(localized_amenities, list)
        and localized_amenities
        and included("localized_amenities")
    ):
        desired_amenities = {
            str(value["label_en"]): (str(value["label_ar"]), index)
            for index, value in enumerate(localized_amenities)
            if isinstance(value, dict) and value.get("label_en") and value.get("label_ar")
        }
        existing_amenities = {item.label_en: item for item in record.amenities}
        for label, amenity_row in existing_amenities.items():
            if label not in desired_amenities:
                await db.delete(amenity_row)
        for label, (label_ar, display_order) in desired_amenities.items():
            target_amenity = existing_amenities.get(label)
            if not target_amenity:
                target_amenity = ProjectAmenity(label_en=label)
                record.amenities.append(target_amenity)
            target_amenity.label_ar = label_ar
            target_amenity.display_order = display_order

    latest_evidence = {
        item.source_url: item
        for item in sorted(candidate.evidence, key=lambda value: value.retrieved_at)
        if item.storage_key
        and item.content_hash
        and (
            (
                item.outcome in {"acquired", "extracted"}
                and item.http_status is not None
                and 200 <= item.http_status < 300
            )
            or (item.outcome == "rendered" and item.adapter_version == "tanami-rendered-context-v1")
        )
    }
    existing_sources = {item.source_url: item for item in record.sources}
    retained_urls = list(
        dict.fromkeys(
            [
                *([candidate.official_source_url] if candidate.official_source_url else []),
                *[
                    value
                    for value in candidate.source_urls
                    if "tanamiproperties.com/Projects/" in value
                ][:1],
            ]
        )
    )
    payment = proposal.get("payment_plan")
    payment_url = payment.get("source_url") if isinstance(payment, dict) else None
    if payment_url and payment_url in latest_evidence and included("payment_plan"):
        retained_urls = list(dict.fromkeys([*retained_urls, payment_url]))
    if fields is not None:
        # A bounded gap refresh must not reactivate or restamp unrelated evidence.
        retained_urls = [url for url in retained_urls if url in latest_evidence]
    for source_url in retained_urls:
        evidence = latest_evidence.get(source_url)
        source = existing_sources.get(source_url)
        is_official = source_url == candidate.official_source_url
        if not source:
            source = ProjectSource(source_url=source_url)
            record.sources.append(source)
        source.source_type = (
            ProjectSourceType.OFFICIAL_DEVELOPER_PAGE
            if is_official
            else ProjectSourceType.APPROVED_SECONDARY_SOURCE
        )
        source.is_official = is_official
        source.retrieved_at = (
            evidence.retrieved_at if evidence else candidate.extracted_at or datetime.now(UTC)
        )
        source.last_checked_at = candidate.last_verified_at or datetime.now(UTC)
        source.content_hash = evidence.content_hash if evidence else candidate.content_hash
        source.is_active = True

    existing_media = {item.source_url: item for item in record.media}
    staged_media_by_url = {item.source_url: item for item in candidate.staged_media}
    for source_url, media in list(existing_media.items()):
        if not included("media"):
            break
        staged_media = staged_media_by_url.get(source_url)
        if staged_media and not (
            staged_media.stage_status == "downloaded"
            and staged_media.rights_status == MediaRightsStatus.APPROVED
            and staged_media.storage_key
        ):
            await db.delete(media)
            existing_media.pop(source_url)
    for staged_media in candidate.staged_media:
        if not included("media"):
            break
        if not (
            staged_media.stage_status == "downloaded"
            and staged_media.rights_status == MediaRightsStatus.APPROVED
            and staged_media.storage_key
        ):
            continue
        target_media = existing_media.get(staged_media.source_url)
        if not target_media:
            target_media = ProjectMedia(source_url=staged_media.source_url)
            record.media.append(target_media)
            existing_media[staged_media.source_url] = target_media
        target_media.category = staged_media.category
        target_media.rights_status = staged_media.rights_status
        target_media.alt_en = staged_media.alt_en_draft
        target_media.alt_ar = staged_media.alt_ar_draft
        target_media.display_order = staged_media.display_order
        target_media.storage_key = staged_media.storage_key
        target_media.original_filename = staged_media.normalized_filename
        target_media.mime_type = staged_media.mime_type
        target_media.size_bytes = staged_media.size_bytes
        target_media.sha256 = staged_media.sha256
        target_media.width = staged_media.width
        target_media.height = staged_media.height
        target_media.verified_at = staged_media.rights_confirmed_at
        target_media.uploaded_by = staged_media.rights_confirmed_by

    await db.flush()
    payment = proposal.get("payment_plan")
    milestones = payment.get("milestones", []) if isinstance(payment, dict) else []
    if isinstance(payment, dict) and milestones and record.sources and included("payment_plan"):
        payment_source = next(
            (source for source in record.sources if source.source_url == payment_url),
            record.sources[0],
        )
        if payment_url and payment_source.source_url != payment_url:
            raise ValueError("Payment plan must retain its exact source evidence.")
        if not record.payment_plan:
            record.payment_plan = ProjectPaymentPlan(
                raw_source_text=str(payment.get("raw_source_text") or "Source payment plan"),
                source_id=payment_source.id,
                milestones=[],
            )
        record.payment_plan.source_id = payment_source.id
        record.payment_plan.raw_source_text = str(
            payment.get("raw_source_text") or record.payment_plan.raw_source_text
        )
        record.payment_plan.is_complete = bool(payment.get("is_complete"))
        record.payment_plan.verified_at = candidate.last_verified_at if fields is None else None
        desired_milestones = {
            int(value.get("sequence", index + 1)): value
            for index, value in enumerate(milestones)
            if isinstance(value, dict) and value.get("source_value")
        }
        existing_milestones = {item.sequence: item for item in record.payment_plan.milestones}
        for sequence, milestone_row in existing_milestones.items():
            if sequence not in desired_milestones:
                await db.delete(milestone_row)
        for sequence, milestone_payload in desired_milestones.items():
            target_milestone = existing_milestones.get(sequence)
            if not target_milestone:
                target_milestone = ProjectPaymentMilestone(sequence=sequence)
                record.payment_plan.milestones.append(target_milestone)
            target_milestone.stage = PaymentStage(str(milestone_payload.get("stage", "other")))
            target_milestone.label_en = str(
                milestone_payload.get("source_value", "Source milestone")
            )[:240]
            target_milestone.label_ar = (
                str(milestone_payload["label_ar"]) if milestone_payload.get("label_ar") else None
            )
            target_milestone.percentage = milestone_payload.get("percentage")
            target_milestone.source_value = str(milestone_payload.get("source_value", ""))
    await db.flush()
    return record


def _availability_status(value: object) -> ProjectAvailabilityStatus:
    try:
        return ProjectAvailabilityStatus(str(value))
    except ValueError:
        return ProjectAvailabilityStatus.NOT_CONFIRMED


def _construction_status(value: object) -> ConstructionStatus:
    try:
        return ConstructionStatus(str(value))
    except ValueError:
        return ConstructionStatus.NOT_CONFIRMED


def _bedroom_option(value: object) -> ProjectBedroomOption:
    normalized = "6+" if str(value) == "6" else str(value)
    return ProjectBedroomOption(normalized)


def _remove_mapping_issue(candidate: ProjectImportCandidate, field: str) -> None:
    candidate.validation_errors = [
        value
        for value in candidate.validation_errors
        if not (isinstance(value, dict) and str(value.get("field", "")).casefold() == field)
    ]
    candidate.conflict_reasons = [
        value for value in candidate.conflict_reasons if field not in value.casefold()
    ]


def _not_found(message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND, detail={"code": "not_found", "message": message}
    )


def _invalid(message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_import_action", "message": message},
    )
