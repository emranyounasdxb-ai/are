"""Durable, review-gated Project preparation jobs.

PostgreSQL owns job and item state. Workers claim short leases and commit after each
candidate so interruption cannot roll back completed records.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AreaCommunity,
    DiagnosticResolutionStatus,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProcessingItemStatus,
    ProcessingJobStatus,
    ProjectImportCandidate,
    ProjectImportEditorialDraft,
    ProjectMediaCategory,
    ProjectOverviewGeneration,
    ProjectProcessingDiagnostic,
    ProjectProcessingItem,
    ProjectProcessingJob,
    ProjectProcessingStatus,
)

PIPELINE_STAGES = (
    "validate-raw-evidence",
    "normalize-facts",
    "resolve-developer",
    "resolve-area",
    "validate-emirate",
    "validate-types-bedrooms",
    "validate-size",
    "validate-handover",
    "validate-payment-plan",
    "validate-market-status",
    "prepare-overview",
    "process-media",
    "final-cross-check",
    "mark-cleaned",
    "mark-ready-to-post",
)

ERROR_CODES = frozenset(
    {
        "source_unavailable",
        "source_removed",
        "timeout_network_error",
        "invalid_response",
        "missing_factual_evidence",
        "developer_unresolved",
        "area_unresolved",
        "emirate_conflict",
        "overview_generation_failure",
        "unsupported_ai_claim",
        "human_approval_required",
        "media_download_failure",
        "invalid_corrupt_image",
        "duplicate_image",
        "metadata_failure",
        "derivative_failure",
        "rights_approval_missing",
        "human_edited_conflict",
        "internal_processing_error",
    }
)

SAFE_RECOVERY_CODES = frozenset(
    {
        "metadata_failure",
        "derivative_failure",
        "duplicate_image",
        "overview_generation_failure",
    }
)


@dataclass(frozen=True)
class OverviewResult:
    overview_en: str
    overview_ar: str
    provider_name: str
    model_name: str
    model_version: str
    prompt_version: str
    confidence: Decimal


class OverviewProvider(Protocol):
    async def generate(self, facts: dict[str, object], source_version: str) -> OverviewResult: ...


class DeterministicSyntheticOverviewProvider:
    """Test-only provider; it never performs network or live AI calls."""

    async def generate(self, facts: dict[str, object], source_version: str) -> OverviewResult:
        name = str(facts.get("project_name") or "Synthetic project")
        return OverviewResult(
            overview_en=f"{name} is presented using reviewed, source-grounded project facts.",
            overview_ar=f"يُعرض {name} باستخدام حقائق مشروع موثقة وخاضعة للمراجعة.",
            provider_name="synthetic",
            model_name="deterministic-fixture",
            model_version="1",
            prompt_version="overview-v1",
            confidence=Decimal("1.0000"),
        )


class DisabledOverviewProvider:
    async def generate(self, facts: dict[str, object], source_version: str) -> OverviewResult:
        del facts, source_version
        raise RuntimeError("No approved Overview provider is configured.")


class ProcessingFailure(Exception):
    def __init__(
        self,
        stage: str,
        code: str,
        explanation: str,
        *,
        retryable: bool = False,
        affected_reference: str | None = None,
        suggested_resolution: str = "Review the diagnostic and correct the affected input.",
    ) -> None:
        super().__init__(explanation)
        if code not in ERROR_CODES:
            raise ValueError(f"Unsupported processing error code: {code}")
        self.stage = stage
        self.code = code
        self.explanation = explanation
        self.retryable = retryable
        self.affected_reference = affected_reference
        self.suggested_resolution = suggested_resolution


def overview_fact_guard(texts: tuple[str, str], facts: dict[str, object]) -> dict[str, object]:
    combined = " ".join(texts)
    normalized_facts = str(facts).casefold()
    unsupported_numbers = sorted(
        value
        for value in set(re.findall(r"\b\d+(?:\.\d+)?%?\b", combined))
        if value.casefold() not in normalized_facts
    )
    blocked_terms = [
        term
        for term in ("guaranteed", "guarantee", "return on investment", "tanami")
        if term in combined.casefold()
    ]
    return {
        "passed": not unsupported_numbers and not blocked_terms,
        "unsupported_numbers": unsupported_numbers,
        "blocked_terms": blocked_terms,
    }


def public_media_metadata(
    *,
    project_name: str,
    category: str,
    title: str,
    description: str,
    website: str,
) -> dict[str, str]:
    """Return the public-safe metadata allowlist for an approved derivative."""
    return {
        "Publisher": "ALIYAS Real Estate",
        "Processed by": "ALIYAS Real Estate",
        "Website": website,
        "Project name": project_name,
        "Image category": category,
        "Title": title,
        "Description": description,
    }


def descriptive_media_filename(project_slug: str, category: str, ordinal: int) -> str:
    safe_slug = re.sub(r"[^a-z0-9-]+", "-", project_slug.casefold()).strip("-")
    safe_category = re.sub(r"[^a-z0-9-]+", "-", category.casefold()).strip("-")
    return f"{safe_slug}-{safe_category}-{ordinal:02d}.webp"


def processing_eligibility_errors(candidate: ProjectImportCandidate) -> list[str]:
    errors: list[str] = []
    if candidate.review_status in {ImportReviewStatus.REJECTED, ImportReviewStatus.MERGED}:
        errors.append(f"Candidate is {candidate.review_status.value} and cannot be prepared.")
    if candidate.processing_status in {
        ProjectProcessingStatus.QUEUED,
        ProjectProcessingStatus.PROCESSING,
        ProjectProcessingStatus.READY_TO_POST,
        ProjectProcessingStatus.REJECTED,
    }:
        errors.append(f"Processing state is {candidate.processing_status.value}.")
    return errors


def job_dict(job: ProjectProcessingJob, *, include_items: bool = True) -> dict[str, object]:
    processed = job.succeeded_count + job.failed_count + job.skipped_count
    result: dict[str, object] = {
        "id": job.id,
        "batch_id": job.batch_id,
        "requested_action": job.requested_action,
        "selection_mode": job.selection_mode,
        "selected_record_ids": job.selected_record_ids,
        "status": job.status.value,
        "created_by": job.created_by,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "total_count": job.total_count,
        "queued_count": job.queued_count,
        "processing_count": job.processing_count,
        "succeeded_count": job.succeeded_count,
        "failed_count": job.failed_count,
        "skipped_count": job.skipped_count,
        "progress_percent": round((processed / job.total_count) * 100, 2),
        "cancellation_requested": job.cancellation_requested,
        "correlation_id": job.correlation_id,
    }
    if include_items:
        result["items"] = [processing_item_dict(item) for item in job.items]
    return result


def processing_item_dict(item: ProjectProcessingItem) -> dict[str, object]:
    return {
        "id": item.id,
        "candidate_id": item.candidate_id,
        "ordinal": item.ordinal,
        "status": item.status.value,
        "current_stage": item.current_stage,
        "completed_stages": item.completed_stages,
        "attempt_count": item.attempt_count,
        "next_retry_at": item.next_retry_at,
        "result_summary": item.result_summary,
        "diagnostics": [diagnostic_dict(value) for value in item.diagnostics],
    }


def diagnostic_dict(value: ProjectProcessingDiagnostic) -> dict[str, object]:
    return {
        "id": value.id,
        "item_id": value.item_id,
        "stage": value.stage,
        "error_code": value.error_code,
        "explanation": value.explanation,
        "technical_detail": value.technical_detail,
        "affected_reference": value.affected_reference,
        "retryable": value.retryable,
        "first_occurred_at": value.first_occurred_at,
        "latest_occurred_at": value.latest_occurred_at,
        "attempt_count": value.attempt_count,
        "next_retry_at": value.next_retry_at,
        "last_successful_stage": value.last_successful_stage,
        "suggested_resolution": value.suggested_resolution,
        "resolution_status": value.resolution_status.value,
        "resolution_note": value.resolution_note,
        "resolved_by": value.resolved_by,
        "resolved_at": value.resolved_at,
        "correlation_id": value.correlation_id,
    }


async def create_processing_job(
    db: AsyncSession,
    *,
    batch_id: uuid.UUID,
    candidate_ids: list[uuid.UUID],
    selection_mode: str,
    requested_action: str,
    actor_id: uuid.UUID,
    correlation_id: str,
    idempotency_key: str,
) -> ProjectProcessingJob:
    existing = await db.scalar(
        select(ProjectProcessingJob).where(
            ProjectProcessingJob.created_by == actor_id,
            ProjectProcessingJob.idempotency_key == idempotency_key,
        )
    )
    if existing:
        if (
            existing.batch_id != batch_id
            or existing.requested_action != requested_action
            or existing.selection_mode != selection_mode
            or set(existing.selected_record_ids) != {str(value) for value in candidate_ids}
        ):
            raise ValueError("The idempotency key was already used for a different request.")
        return existing
    unique_ids = list(dict.fromkeys(candidate_ids))
    records = (
        await db.scalars(
            select(ProjectImportCandidate)
            .where(
                ProjectImportCandidate.batch_id == batch_id,
                ProjectImportCandidate.id.in_(unique_ids),
            )
            .order_by(ProjectImportCandidate.manifest_row_id)
        )
    ).all()
    if not records or len(records) != len(unique_ids):
        raise ValueError("Every selected candidate must belong to the acquisition batch.")
    ineligible = {
        str(record.id): processing_eligibility_errors(record)
        for record in records
        if processing_eligibility_errors(record)
    }
    if ineligible:
        reasons = "; ".join(
            f"{record_id}: {', '.join(values)}" for record_id, values in ineligible.items()
        )
        raise ValueError(f"The immutable selection contains ineligible candidates: {reasons}")
    job = ProjectProcessingJob(
        batch_id=batch_id,
        requested_action=requested_action,
        selection_mode=selection_mode,
        selected_record_ids=[str(record.id) for record in records],
        status=ProcessingJobStatus.QUEUED,
        created_by=actor_id,
        total_count=len(records),
        queued_count=len(records),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )
    job.items = [
        ProjectProcessingItem(
            candidate_id=record.id,
            ordinal=index,
            status=ProcessingItemStatus.QUEUED,
        )
        for index, record in enumerate(records, start=1)
    ]
    db.add(job)
    for record in records:
        record.processing_status = ProjectProcessingStatus.QUEUED
    await db.commit()
    return await job_detail(db, job.id)


async def job_detail(db: AsyncSession, job_id: uuid.UUID) -> ProjectProcessingJob:
    job = await db.scalar(
        select(ProjectProcessingJob)
        .where(ProjectProcessingJob.id == job_id)
        .execution_options(populate_existing=True)
        .options(
            selectinload(ProjectProcessingJob.items).selectinload(ProjectProcessingItem.diagnostics)
        )
    )
    if not job:
        raise ValueError("Processing job not found.")
    return job


async def claim_next_item(
    db: AsyncSession, worker_id: str, *, lease_seconds: int = 60
) -> ProjectProcessingItem | None:
    now = datetime.now(UTC)
    item = await db.scalar(
        select(ProjectProcessingItem)
        .join(ProjectProcessingJob)
        .where(
            ProjectProcessingJob.cancellation_requested.is_(False),
            ProjectProcessingJob.status.in_(
                [
                    ProcessingJobStatus.QUEUED,
                    ProcessingJobStatus.RUNNING,
                ]
            ),
            or_(
                ProjectProcessingItem.status == ProcessingItemStatus.QUEUED,
                (
                    (ProjectProcessingItem.status == ProcessingItemStatus.PROCESSING)
                    & (ProjectProcessingItem.lease_expires_at < now)
                ),
                (
                    (ProjectProcessingItem.status == ProcessingItemStatus.FAILED)
                    & (ProjectProcessingItem.next_retry_at <= now)
                    & (ProjectProcessingItem.attempt_count < ProjectProcessingItem.max_attempts)
                ),
            ),
        )
        .order_by(ProjectProcessingJob.created_at, ProjectProcessingItem.ordinal)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if not item:
        return None
    job = await db.get(ProjectProcessingJob, item.job_id)
    if job and job.status == ProcessingJobStatus.QUEUED:
        job.status = ProcessingJobStatus.RUNNING
        job.started_at = job.started_at or now
    item.status = ProcessingItemStatus.PROCESSING
    item.attempt_count += 1
    item.lease_owner = worker_id
    item.heartbeat_at = now
    item.lease_expires_at = now + timedelta(seconds=lease_seconds)
    await db.commit()
    return item


async def process_claimed_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    *,
    provider: OverviewProvider,
) -> None:
    item = await db.scalar(
        select(ProjectProcessingItem)
        .where(ProjectProcessingItem.id == item_id)
        .options(selectinload(ProjectProcessingItem.diagnostics))
    )
    if not item:
        return
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == item.candidate_id)
        .options(
            selectinload(ProjectImportCandidate.evidence),
            selectinload(ProjectImportCandidate.staged_media),
            selectinload(ProjectImportCandidate.editorial_draft),
        )
    )
    if not candidate:
        await _record_failure(
            db,
            item,
            ProcessingFailure(
                "validate-raw-evidence", "internal_processing_error", "Candidate no longer exists."
            ),
        )
        return
    candidate.processing_status = ProjectProcessingStatus.PROCESSING
    try:
        for stage in PIPELINE_STAGES:
            if stage in item.completed_stages:
                continue
            item.current_stage = stage
            await _run_stage(db, candidate, item, stage, provider)
            await _resolve_rerun_diagnostics(db, item, stage)
            item.completed_stages = [*item.completed_stages, stage]
            candidate.last_successful_stage = stage
            item.heartbeat_at = datetime.now(UTC)
            await db.commit()
        item.status = ProcessingItemStatus.SUCCEEDED
        item.result_summary = {"processing_status": candidate.processing_status.value}
        item.lease_owner = None
        item.lease_expires_at = None
        await db.commit()
    except ProcessingFailure as exc:
        await _record_failure(db, item, exc, candidate)
    await refresh_job_counts(db, item.job_id)


async def _run_stage(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    item: ProjectProcessingItem,
    stage: str,
    provider: OverviewProvider,
) -> None:
    facts = candidate.normalized_payload or {}
    if stage == "validate-raw-evidence" and not candidate.raw_source_payload:
        raise ProcessingFailure(
            stage, "missing_factual_evidence", "Private raw evidence is missing."
        )
    if stage == "normalize-facts" and not facts:
        raise ProcessingFailure(stage, "missing_factual_evidence", "Normalized facts are missing.")
    if stage == "resolve-developer" and not candidate.proposed_developer_id:
        raise ProcessingFailure(stage, "developer_unresolved", "Canonical Developer is unresolved.")
    if stage == "resolve-area" and not candidate.proposed_area_id:
        raise ProcessingFailure(stage, "area_unresolved", "Canonical Area is unresolved.")
    if stage == "validate-emirate" and candidate.proposed_area_id:
        area = await db.get(AreaCommunity, candidate.proposed_area_id)
        if not area or facts.get("emirate") != area.emirate.value:
            raise ProcessingFailure(
                stage, "emirate_conflict", "Project and Area Emirates do not match."
            )
    if stage == "validate-types-bedrooms" and not (
        facts.get("property_types")
        and facts.get("unit_types")
        and (facts.get("bedroom_options") or facts.get("bedrooms"))
    ):
        raise ProcessingFailure(
            stage, "missing_factual_evidence", "Types or bedrooms are incomplete."
        )
    if stage == "validate-size" and not all(
        facts.get(key) for key in ("size_min", "size_max", "size_unit")
    ):
        raise ProcessingFailure(
            stage, "missing_factual_evidence", "Size range or unit is incomplete."
        )
    if stage == "validate-handover" and not all(
        facts.get(key) for key in ("handover_quarter", "handover_year")
    ):
        raise ProcessingFailure(
            stage, "missing_factual_evidence", "Handover evidence is incomplete."
        )
    if stage == "validate-payment-plan" and not (
        facts.get("down_payment_percentage")
        and facts.get("down_payment_source_value")
        and facts.get("payment_plan")
    ):
        raise ProcessingFailure(
            stage,
            "missing_factual_evidence",
            "Down-payment or payment-plan evidence is incomplete.",
        )
    if stage == "validate-market-status" and not all(
        facts.get(key) for key in ("availability_status", "construction_status")
    ):
        raise ProcessingFailure(
            stage, "missing_factual_evidence", "Market statuses are incomplete."
        )
    if stage == "prepare-overview":
        await _prepare_overview(db, candidate, facts, provider)
    if stage == "process-media":
        _validate_media(candidate)
    if stage == "final-cross-check":
        _final_gate(candidate)
    if stage == "mark-cleaned":
        candidate.processing_status = ProjectProcessingStatus.CLEANED
    if stage == "mark-ready-to-post":
        _final_gate(candidate)
        candidate.processing_status = ProjectProcessingStatus.READY_TO_POST
        candidate.review_status = ImportReviewStatus.READY_FOR_APPROVAL


async def _resolve_rerun_diagnostics(
    db: AsyncSession,
    item: ProjectProcessingItem,
    stage: str,
) -> None:
    diagnostics = (
        await db.scalars(
            select(ProjectProcessingDiagnostic).where(
                ProjectProcessingDiagnostic.item_id == item.id,
                ProjectProcessingDiagnostic.stage == stage,
                ProjectProcessingDiagnostic.resolution_status.in_(
                    [
                        DiagnosticResolutionStatus.OPEN,
                        DiagnosticResolutionStatus.HUMAN_INPUT_REQUIRED,
                    ]
                ),
            )
        )
    ).all()
    now = datetime.now(UTC)
    for diagnostic in diagnostics:
        diagnostic.resolution_status = DiagnosticResolutionStatus.RESOLVED
        diagnostic.resolution_note = "The affected validation passed on a later bounded rerun."
        diagnostic.resolved_at = now


async def _prepare_overview(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    facts: dict[str, object],
    provider: OverviewProvider,
) -> None:
    draft = candidate.editorial_draft
    if draft and draft.approval_status == EditorialApprovalStatus.APPROVED:
        guard = overview_fact_guard((draft.overview_en or "", draft.overview_ar or ""), facts)
        if guard["passed"]:
            return
        raise ProcessingFailure(
            "prepare-overview",
            "unsupported_ai_claim",
            "Overview contains unsupported claims.",
            affected_reference="overview",
            suggested_resolution="Regenerate or edit the Overview and rerun the fact guard.",
        )
    try:
        result = await provider.generate(facts, candidate.content_hash)
    except Exception as exc:
        raise ProcessingFailure(
            "prepare-overview",
            "overview_generation_failure",
            "The Overview provider could not produce a draft.",
            retryable=True,
            suggested_resolution="Verify approved provider configuration and retry this stage.",
        ) from exc
    guard = overview_fact_guard((result.overview_en, result.overview_ar), facts)
    generation = ProjectOverviewGeneration(
        candidate_id=candidate.id,
        provider_name=result.provider_name,
        model_name=result.model_name,
        model_version=result.model_version,
        prompt_version=result.prompt_version,
        source_version=candidate.content_hash,
        overview_en=result.overview_en,
        overview_ar=result.overview_ar,
        confidence=result.confidence,
        result_status="generated" if guard["passed"] else "blocked",
        fact_guard_result=guard,
        generated_at=datetime.now(UTC),
        approval_status=EditorialApprovalStatus.NEEDS_REVIEW,
    )
    db.add(generation)
    if draft is None:
        draft = ProjectImportEditorialDraft(
            candidate_id=candidate.id,
            source_version=candidate.content_hash,
        )
        db.add(draft)
        candidate.editorial_draft = draft
    draft.overview_en = result.overview_en
    draft.overview_ar = result.overview_ar
    draft.source_version = candidate.content_hash
    draft.model_name = result.model_name
    draft.model_version = result.model_version
    draft.generated_at = generation.generated_at
    draft.approval_status = EditorialApprovalStatus.NEEDS_REVIEW
    if not guard["passed"]:
        raise ProcessingFailure(
            "prepare-overview",
            "unsupported_ai_claim",
            "Generated Overview failed the factual guard.",
        )
    raise ProcessingFailure(
        "prepare-overview",
        "human_approval_required",
        "Overview drafts were generated and require human approval.",
        affected_reference="overview",
        suggested_resolution="Review and approve both Overview drafts.",
    )


def _validate_media(candidate: ProjectImportCandidate) -> None:
    media = [item for item in candidate.staged_media if item.stage_status == "downloaded"]
    if not media:
        raise ProcessingFailure(
            "process-media", "media_download_failure", "No processed media exists."
        )
    hashes = [item.processed_sha256 or item.sha256 for item in media]
    if len([value for value in hashes if value]) != len(set(value for value in hashes if value)):
        raise ProcessingFailure(
            "process-media", "duplicate_image", "Repeated Project media was detected."
        )
    for item in media:
        if not all((item.width, item.height, item.storage_key, item.derivative_manifest)):
            raise ProcessingFailure(
                "process-media",
                "derivative_failure",
                "Media derivatives are incomplete.",
                affected_reference=str(item.id),
                retryable=True,
            )
        formats = {str(value.get("format")) for value in item.derivative_manifest}
        if not {"webp", "avif"}.issubset(formats):
            raise ProcessingFailure(
                "process-media",
                "derivative_failure",
                "Responsive WebP and AVIF derivatives are required.",
                affected_reference=str(item.id),
                retryable=True,
            )
        if not all((item.original_sha256, item.processed_sha256, item.processing_version)):
            raise ProcessingFailure(
                "process-media",
                "metadata_failure",
                "Original and processed media integrity metadata is incomplete.",
                affected_reference=str(item.id),
                retryable=True,
            )


def _final_gate(candidate: ProjectImportCandidate) -> None:
    draft = candidate.editorial_draft
    media = [item for item in candidate.staged_media if item.stage_status == "downloaded"]
    blockers: list[str] = []
    if not draft or draft.approval_status != EditorialApprovalStatus.APPROVED:
        blockers.append("approved bilingual Overview")
    cover = next((item for item in media if item.category == ProjectMediaCategory.COVER), None)
    if not cover:
        blockers.append("cover image")
    for item in media:
        if item.rights_status != MediaRightsStatus.APPROVED or not item.rights_basis:
            blockers.append("approved media rights")
        if not all(
            (
                item.alt_en_draft,
                item.alt_ar_draft,
                item.normalized_filename,
                item.title_en,
                item.title_ar,
                item.description_en,
                item.description_ar,
                item.tags,
                item.public_metadata,
            )
        ):
            blockers.append("complete media names and alt text")
        public_text = " ".join(
            filter(None, [item.normalized_filename, item.alt_en_draft, item.alt_ar_draft])
        ).casefold()
        if "tanami" in public_text or "http" in public_text:
            blockers.append("public-safe media text")
    if candidate.conflict_reasons:
        blockers.append("resolved critical conflicts")
    if blockers:
        raise ProcessingFailure(
            "final-cross-check",
            "rights_approval_missing"
            if "approved media rights" in blockers
            else "missing_factual_evidence",
            "Ready-to-Post gate failed: " + ", ".join(sorted(set(blockers))) + ".",
        )


async def _record_failure(
    db: AsyncSession,
    item: ProjectProcessingItem,
    failure: ProcessingFailure,
    candidate: ProjectImportCandidate | None = None,
) -> None:
    now = datetime.now(UTC)
    retry_at = (
        now + timedelta(seconds=min(300, 2**item.attempt_count)) if failure.retryable else None
    )
    job = await db.get(ProjectProcessingJob, item.job_id)
    if not job:
        raise RuntimeError("Processing job no longer exists.")
    diagnostic = ProjectProcessingDiagnostic(
        item_id=item.id,
        stage=failure.stage,
        error_code=failure.code,
        explanation=failure.explanation,
        technical_detail=type(failure).__name__,
        affected_reference=failure.affected_reference,
        retryable=failure.retryable,
        first_occurred_at=now,
        latest_occurred_at=now,
        attempt_count=item.attempt_count,
        next_retry_at=retry_at,
        last_successful_stage=(candidate.last_successful_stage if candidate else None),
        suggested_resolution=failure.suggested_resolution,
        resolution_status=(
            DiagnosticResolutionStatus.OPEN
            if failure.retryable
            else DiagnosticResolutionStatus.HUMAN_INPUT_REQUIRED
        ),
        correlation_id=job.correlation_id,
    )
    db.add(diagnostic)
    item.status = ProcessingItemStatus.FAILED
    item.next_retry_at = retry_at
    item.lease_owner = None
    item.lease_expires_at = None
    item.result_summary = {"error_code": failure.code, "stage": failure.stage}
    if candidate:
        if failure.code == "human_approval_required":
            candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
        else:
            candidate.processing_status = (
                ProjectProcessingStatus.FAILED_RETRYABLE
                if failure.retryable
                else ProjectProcessingStatus.FAILED_HUMAN_INPUT
            )
    await db.commit()


async def cancel_processing_job(db: AsyncSession, job_id: uuid.UUID) -> ProjectProcessingJob:
    job = await job_detail(db, job_id)
    if job.status not in {ProcessingJobStatus.QUEUED, ProcessingJobStatus.RUNNING}:
        return job
    job.cancellation_requested = True
    for item in job.items:
        if item.status == ProcessingItemStatus.QUEUED:
            item.status = ProcessingItemStatus.CANCELLED
    await db.commit()
    await refresh_job_counts(db, job_id)
    return await job_detail(db, job_id)


async def retry_failed_items(
    db: AsyncSession,
    job_id: uuid.UUID,
    item_ids: list[uuid.UUID] | None = None,
) -> ProjectProcessingJob:
    job = await job_detail(db, job_id)
    selected = set(item_ids or [])
    matched = 0
    for item in job.items:
        if item.status != ProcessingItemStatus.FAILED:
            continue
        if selected and item.id not in selected:
            continue
        latest = max(item.diagnostics, key=lambda value: value.created_at, default=None)
        if not latest or not latest.retryable or item.attempt_count >= item.max_attempts:
            continue
        item.status = ProcessingItemStatus.QUEUED
        item.next_retry_at = None
        matched += 1
    if selected and matched != len(selected):
        raise ValueError("Every requested item must be an eligible retryable failure.")
    if matched:
        job.status = ProcessingJobStatus.QUEUED
        job.completed_at = None
        job.cancellation_requested = False
    await db.commit()
    await refresh_job_counts(db, job_id)
    return await job_detail(db, job_id)


async def resolve_diagnostic(
    db: AsyncSession,
    diagnostic_id: uuid.UUID,
    *,
    action: str,
    note: str,
    actor_id: uuid.UUID,
) -> ProjectProcessingDiagnostic:
    diagnostic = await db.scalar(
        select(ProjectProcessingDiagnostic)
        .where(ProjectProcessingDiagnostic.id == diagnostic_id)
        .with_for_update()
    )
    if not diagnostic:
        raise ValueError("Processing diagnostic not found.")
    now = datetime.now(UTC)
    if action == "diagnose-ai":
        diagnostic.resolution_note = (
            f"Provider-neutral diagnosis proposal only: {note}. "
            f"Rerun {diagnostic.stage} after a human reviews the source-grounded input."
        )
        diagnostic.resolution_status = DiagnosticResolutionStatus.HUMAN_INPUT_REQUIRED
    elif action == "apply-safe-correction":
        if diagnostic.error_code not in SAFE_RECOVERY_CODES:
            raise ValueError("This failure cannot be changed by an automated safe correction.")
        diagnostic.resolution_note = note
        diagnostic.resolution_status = DiagnosticResolutionStatus.RESOLVED
        item = await db.get(ProjectProcessingItem, diagnostic.item_id)
        if not item:
            raise RuntimeError("Processing item no longer exists.")
        item.status = ProcessingItemStatus.QUEUED
        item.next_retry_at = None
        job = await db.get(ProjectProcessingJob, item.job_id)
        if not job:
            raise RuntimeError("Processing job no longer exists.")
        job.status = ProcessingJobStatus.QUEUED
        job.completed_at = None
        job.cancellation_requested = False
    elif action == "mark-human-input-required":
        diagnostic.resolution_note = note
        diagnostic.resolution_status = DiagnosticResolutionStatus.HUMAN_INPUT_REQUIRED
    elif action == "resolve":
        raise ValueError("A diagnostic is resolved only after its affected validation reruns.")
    elif action == "reject":
        diagnostic.resolution_note = note
        diagnostic.resolution_status = DiagnosticResolutionStatus.REJECTED
    else:
        raise ValueError("Unsupported diagnostic action.")
    diagnostic.resolved_by = actor_id
    diagnostic.resolved_at = now
    await db.commit()
    return diagnostic


async def refresh_job_counts(db: AsyncSession, job_id: uuid.UUID) -> None:
    job = await job_detail(db, job_id)
    counts = {status: 0 for status in ProcessingItemStatus}
    for item in job.items:
        counts[item.status] += 1
    job.queued_count = counts[ProcessingItemStatus.QUEUED]
    job.processing_count = counts[ProcessingItemStatus.PROCESSING]
    job.succeeded_count = counts[ProcessingItemStatus.SUCCEEDED]
    job.failed_count = counts[ProcessingItemStatus.FAILED]
    job.skipped_count = (
        counts[ProcessingItemStatus.SKIPPED] + counts[ProcessingItemStatus.CANCELLED]
    )
    terminal = job.succeeded_count + job.failed_count + job.skipped_count == job.total_count
    if terminal:
        job.completed_at = datetime.now(UTC)
        if job.cancellation_requested:
            job.status = ProcessingJobStatus.CANCELLED
        elif job.failed_count:
            job.status = ProcessingJobStatus.COMPLETED_WITH_ERRORS
        else:
            job.status = ProcessingJobStatus.COMPLETED
    await db.commit()


async def run_worker_once(
    db: AsyncSession,
    *,
    worker_id: str,
    provider: OverviewProvider | None = None,
) -> bool:
    item = await claim_next_item(db, worker_id)
    if not item:
        return False
    await process_claimed_item(db, item.id, provider=provider or DisabledOverviewProvider())
    return True
