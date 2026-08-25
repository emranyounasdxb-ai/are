"""Private, review-gated manual Codex-assisted Overview packs."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.models import (
    EditorialApprovalStatus,
    ProjectImportCandidate,
    ProjectImportChange,
    ProjectImportEditorialDraft,
    ProjectOverviewPack,
    ProjectOverviewPackItem,
    ProjectProcessingStatus,
)
from app.project_processing import overview_fact_guard
from app.schemas import ManualOverviewResponse
from app.storage import PrivateStorage

PACK_VERSION = "manual-overview-pack-v1"
FACT_INPUT_VERSION = "normalized-facts-v1"
ORIGIN = "CODEX_ASSISTED_MANUAL"
EXPLANATION = (
    "This pack does not call Codex automatically. Give the private pack to an authorized "
    "local Codex task, then import the completed draft file. Human approval remains required."
)

_FACT_KEYS = (
    "project_name",
    "project_name_ar",
    "developer",
    "developer_ar",
    "developer_name",
    "developer_name_ar",
    "area",
    "area_ar",
    "area_name",
    "area_name_ar",
    "emirate",
    "property_types",
    "unit_types",
    "bedrooms",
    "size_min",
    "size_max",
    "size_unit",
    "size_ranges",
    "down_payment_percentage",
    "payment_plan",
    "payment_milestones",
    "handover_quarter",
    "handover_year",
    "amenities",
    "nearby_places",
    "floor_plans",
    "floor_plan_units",
    "floor_plan_categories",
    "master_plan_present",
)
_FORBIDDEN_FACT_KEYS = re.compile(
    r"(?:source|url|path|contact|phone|email|price|prompt|provider|model|priority|secret|token|raw|diagnostic|original)",
    re.I,
)
_FORBIDDEN_TEXT = re.compile(
    r"(?:https?://|www\.|tanami|source url|official source|starting price|current price|"
    r"guaranteed|guarantee|return on investment|\broi\b|assured return|"
    r"السعر|ضمان|عائد مضمون|عائد على الاستثمار|المصدر)",
    re.I,
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _safe_value(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): _safe_value(item)
            for key, item in value.items()
            if not _FORBIDDEN_FACT_KEYS.search(str(key))
        }
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    return value


def build_fact_packet(candidate: ProjectImportCandidate) -> dict[str, object]:
    normalized = candidate.normalized_payload or {}
    facts = {
        key: _safe_value(normalized[key])
        for key in _FACT_KEYS
        if key in normalized and normalized[key] not in (None, "", [], {})
    }
    aliases = {
        "developer_name": "developer_public_name",
        "developer_name_ar": "developer_public_name_ar",
        "area_name": "area_public_name",
        "area_name_ar": "area_public_name_ar",
    }
    for source, target in aliases.items():
        if source in facts:
            facts[target] = facts.pop(source)
    facts["unresolved_fields"] = sorted(
        key
        for key in ("availability_status", "construction_status")
        if normalized.get(key) in (None, "", "unresolved", "not-confirmed")
    )
    return facts


def _fact_paths(value: object, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        result: set[str] = set()
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.add(path)
            result.update(_fact_paths(item, path))
        return result
    return set()


def _pack_exclusion(candidate: ProjectImportCandidate, expected_version: int) -> list[str]:
    reasons: list[str] = []
    if candidate.review_version != expected_version:
        reasons.append("Candidate version changed; refresh the selection.")
    if not candidate.normalized_payload:
        reasons.append("Normalized facts are unavailable.")
    if not build_fact_packet(candidate).get("project_name"):
        reasons.append("A normalized Project name is required.")
    if candidate.processing_status in {
        ProjectProcessingStatus.REJECTED,
        ProjectProcessingStatus.READY_TO_POST,
    }:
        reasons.append(f"Candidate state {candidate.processing_status.value} is not eligible.")
    return reasons


async def create_overview_pack(
    db: AsyncSession,
    settings: Settings,
    *,
    batch_id: uuid.UUID,
    candidate_ids: list[uuid.UUID],
    expected_versions: dict[uuid.UUID, int],
    selection_mode: str,
    actor_id: uuid.UUID,
    idempotency_key: str,
) -> ProjectOverviewPack:
    existing = await db.scalar(
        select(ProjectOverviewPack)
        .where(
            ProjectOverviewPack.created_by == actor_id,
            ProjectOverviewPack.idempotency_key == idempotency_key,
        )
        .options(selectinload(ProjectOverviewPack.items))
    )
    if existing:
        return existing
    if len(candidate_ids) > 50:
        raise ValueError("A manual Overview pack may contain at most 50 candidates.")
    candidates = (
        await db.scalars(
            select(ProjectImportCandidate).where(
                ProjectImportCandidate.batch_id == batch_id,
                ProjectImportCandidate.id.in_(candidate_ids),
            )
        )
    ).all()
    by_id = {value.id: value for value in candidates}
    if len(by_id) != len(candidate_ids):
        raise ValueError("One or more selected candidates do not belong to this batch.")

    pack_id = uuid.uuid4()
    generated_at = datetime.now(UTC)
    private_items: list[dict[str, object]] = []
    db_items: list[ProjectOverviewPackItem] = []
    for ordinal, candidate_id in enumerate(candidate_ids, start=1):
        candidate = by_id[candidate_id]
        exclusions = _pack_exclusion(candidate, expected_versions[candidate_id])
        facts = build_fact_packet(candidate)
        fact_hash = hashlib.sha256(_canonical_bytes(facts)).hexdigest() if not exclusions else None
        db_items.append(
            ProjectOverviewPackItem(
                id=uuid.uuid4(),
                pack_id=pack_id,
                candidate_id=candidate.id,
                ordinal=ordinal,
                candidate_version=candidate.review_version,
                fact_input_version=FACT_INPUT_VERSION,
                fact_input_hash=fact_hash,
                eligible=not exclusions,
                status="awaiting-response" if not exclusions else "ineligible",
                exclusion_reasons=exclusions,
            )
        )
        if not exclusions:
            private_items.append(
                {
                    "candidate_id": str(candidate.id),
                    "candidate_version": candidate.review_version,
                    "fact_input_hash": fact_hash,
                    "fact_input_version": FACT_INPUT_VERSION,
                    "facts": facts,
                }
            )
    payload = {
        "pack_id": str(pack_id),
        "pack_version": PACK_VERSION,
        "created_at": generated_at.isoformat(),
        "instructions": EXPLANATION,
        "response_contract": {
            "origin": ORIGIN,
            "required_fields": [
                "pack_id",
                "pack_version",
                "candidate_id",
                "candidate_version",
                "fact_input_hash",
                "overview_en",
                "overview_ar",
                "referenced_fact_fields",
                "origin",
            ],
        },
        "items": private_items,
    }
    content = _canonical_bytes(payload)
    stored = await PrivateStorage(settings).save_private_json(
        content, prefix="manual-overview-pack"
    )
    pack = ProjectOverviewPack(
        id=pack_id,
        batch_id=batch_id,
        pack_version=PACK_VERSION,
        selection_mode=selection_mode,
        status="awaiting-response" if private_items else "no-eligible-items",
        storage_key=stored.storage_key,
        pack_hash=stored.sha256,
        selected_count=len(candidate_ids),
        eligible_count=len(private_items),
        ineligible_count=len(candidate_ids) - len(private_items),
        created_by=actor_id,
        idempotency_key=idempotency_key,
        items=db_items,
    )
    db.add(pack)
    await db.flush()
    return pack


def pack_dict(pack: ProjectOverviewPack, *, include_items: bool = True) -> dict[str, object]:
    value: dict[str, object] = {
        "id": pack.id,
        "batch_id": pack.batch_id,
        "pack_version": pack.pack_version,
        "selection_mode": pack.selection_mode,
        "status": pack.status,
        "pack_hash": pack.pack_hash,
        "selected_count": pack.selected_count,
        "eligible_count": pack.eligible_count,
        "ineligible_count": pack.ineligible_count,
        "imported_count": pack.imported_count,
        "failed_count": pack.failed_count,
        "created_at": pack.created_at,
        "imported_at": pack.imported_at,
        "explanation": EXPLANATION,
    }
    if include_items:
        value["items"] = [
            {
                "candidate_id": item.candidate_id,
                "candidate_version": item.candidate_version,
                "fact_input_hash": item.fact_input_hash,
                "eligible": item.eligible,
                "status": item.status,
                "exclusion_reasons": item.exclusion_reasons,
                "failure_code": item.failure_code,
                "failure_message": item.failure_message,
            }
            for item in pack.items
        ]
    return value


def read_pack_content(pack: ProjectOverviewPack, settings: Settings) -> bytes:
    content = PrivateStorage(settings).read(pack.storage_key)
    if hashlib.sha256(content).hexdigest() != pack.pack_hash:
        raise ValueError("Private pack integrity check failed.")
    return content


def _language_guard(overview_en: str, overview_ar: str) -> str | None:
    if not re.search(r"[A-Za-z]", overview_en) or re.search(r"[\u0600-\u06ff]", overview_en):
        return "English Overview must contain English text only."
    if not re.search(r"[\u0600-\u06ff]", overview_ar):
        return "Arabic Overview must contain Arabic text."
    translate_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    en_numbers = re.findall(r"\d+(?:\.\d+)?%?", overview_en.translate(translate_digits))
    ar_numbers = re.findall(r"\d+(?:\.\d+)?%?", overview_ar.translate(translate_digits))
    if sorted(en_numbers) != sorted(ar_numbers):
        return "English and Arabic factual numbers are not equivalent."
    return None


def _unresolved_market_claim(text: str, facts: dict[str, object]) -> str | None:
    raw_unresolved = facts.get("unresolved_fields", [])
    unresolved = (
        set(str(value) for value in raw_unresolved) if isinstance(raw_unresolved, list) else set()
    )
    if "availability_status" in unresolved and re.search(
        r"(?:\bavailable\b|availability|sold out|coming soon|متاح|متوفرة|نفدت|قريب[ةاً]*)",
        text,
        re.I,
    ):
        return "Availability is unresolved in the normalized fact packet."
    if "construction_status" in unresolved and re.search(
        r"(?:under construction|completed|launched|near completion|"
        r"قيد الإنشاء|مكتمل|تم إطلاق|قرب الاكتمال)",
        text,
        re.I,
    ):
        return "Construction status is unresolved in the normalized fact packet."
    return None


def _copied_source_wording(candidate: ProjectImportCandidate, text: str) -> bool:
    normalized_text = " ".join(text.casefold().split())
    stack: list[object] = [candidate.raw_source_payload]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
        elif isinstance(value, str):
            phrase = " ".join(value.casefold().split())
            if len(phrase) >= 80 and phrase in normalized_text:
                return True
    return False


async def import_overview_response(
    db: AsyncSession,
    *,
    pack: ProjectOverviewPack,
    response: ManualOverviewResponse,
    correlation_id: str,
) -> dict[str, object]:
    if response.pack_id != pack.id or response.pack_version != pack.pack_version:
        raise ValueError("Response pack identity or version does not match.")
    item_by_candidate = {item.candidate_id: item for item in pack.items}
    results: list[dict[str, object]] = []
    imported = failed = 0
    seen: set[uuid.UUID] = set()
    for response_item in response.items:
        if response_item.candidate_id in seen:
            results.append(
                {
                    "candidate_id": response_item.candidate_id,
                    "status": "failed",
                    "code": "duplicate-response-item",
                }
            )
            failed += 1
            continue
        seen.add(response_item.candidate_id)
        pack_item = item_by_candidate.get(response_item.candidate_id)
        candidate = await db.scalar(
            select(ProjectImportCandidate)
            .where(ProjectImportCandidate.id == response_item.candidate_id)
            .options(selectinload(ProjectImportCandidate.editorial_draft))
            .with_for_update()
        )
        code: str | None = None
        message: str | None = None
        facts: dict[str, object] = {}
        if not pack_item or not pack_item.eligible or not candidate:
            code, message = "candidate-not-eligible", "Candidate is not eligible in this pack."
        elif (
            response_item.candidate_version != candidate.review_version
            or response_item.candidate_version != pack_item.candidate_version
        ):
            code, message = (
                "stale-candidate-version",
                "Candidate facts changed after pack generation.",
            )
        else:
            facts = build_fact_packet(candidate)
            current_hash = hashlib.sha256(_canonical_bytes(facts)).hexdigest()
            if (
                current_hash != response_item.fact_input_hash
                or current_hash != pack_item.fact_input_hash
            ):
                code, message = (
                    "fact-hash-mismatch",
                    "Normalized fact input no longer matches the pack.",
                )
        available_paths = _fact_paths(facts)
        if not code and any(
            field not in available_paths for field in response_item.referenced_fact_fields
        ):
            code, message = (
                "unsupported-fact-reference",
                "Response references a field not present in the fact packet.",
            )
        edited = set(candidate.human_edited_fields if candidate else [])
        if not code and any(
            field.split(".", 1)[0] in edited or field in edited
            for field in response_item.referenced_fact_fields
        ):
            code, message = (
                "human-edited-conflict",
                "A referenced fact has been edited by a human since acquisition.",
            )
        language_error = _language_guard(response_item.overview_en, response_item.overview_ar)
        if not code and language_error:
            code, message = "language-equivalence-review-required", language_error
        if not code and (
            _FORBIDDEN_TEXT.search(response_item.overview_en)
            or _FORBIDDEN_TEXT.search(response_item.overview_ar)
        ):
            code, message = (
                "unsupported-or-private-claim",
                "Overview contains a prohibited claim or private source reference.",
            )
        en_guard = overview_fact_guard((response_item.overview_en, ""), facts)
        ar_guard = overview_fact_guard((response_item.overview_ar, ""), facts)
        if not code and not en_guard["passed"]:
            code, message = (
                "english-fact-guard-failure",
                "English draft contains facts outside the packet.",
            )
        if not code and not ar_guard["passed"]:
            code, message = (
                "arabic-fact-guard-failure",
                "Arabic draft contains facts outside the packet.",
            )
        market_error = _unresolved_market_claim(
            f"{response_item.overview_en} {response_item.overview_ar}", facts
        )
        if not code and market_error:
            code, message = "unsupported-market-status", market_error
        if (
            not code
            and candidate
            and (
                _copied_source_wording(candidate, response_item.overview_en)
                or _copied_source_wording(candidate, response_item.overview_ar)
            )
        ):
            code, message = "copied-source-wording", "Draft appears to copy private source wording."
        existing = candidate.editorial_draft if candidate else None
        if not code and existing:
            exact_repeat = (
                existing.origin == ORIGIN
                and existing.overview_pack_id == pack.id
                and existing.fact_input_hash == response_item.fact_input_hash
                and existing.overview_en == response_item.overview_en
                and existing.overview_ar == response_item.overview_ar
            )
            if exact_repeat:
                results.append({"candidate_id": response_item.candidate_id, "status": "unchanged"})
                continue
            if existing.approval_status == EditorialApprovalStatus.APPROVED:
                code, message = (
                    "approved-overview-conflict",
                    "An approved editorial Overview requires a separate revision workflow.",
                )
            elif {"overview", "overview_en", "overview_ar"} & edited:
                code, message = (
                    "human-edited-conflict",
                    "A human-edited editorial Overview cannot be replaced by bulk import.",
                )
        if code:
            if pack_item:
                pack_item.status = "failed"
                pack_item.failure_code = code
                pack_item.failure_message = message
            failed += 1
            results.append(
                {
                    "candidate_id": response_item.candidate_id,
                    "status": "failed",
                    "code": code,
                    "message": message,
                }
            )
            continue
        assert candidate is not None and pack_item is not None
        imported_at = datetime.now(UTC)
        if existing:
            db.add(
                ProjectImportChange(
                    candidate_id=candidate.id,
                    classification="editorial-revision",
                    field_name="overview",
                    existing_value={
                        "overview_en": existing.overview_en,
                        "overview_ar": existing.overview_ar,
                        "source_version": existing.source_version,
                        "approval_status": existing.approval_status.value,
                        "origin": existing.origin,
                        "overview_pack_id": str(existing.overview_pack_id)
                        if existing.overview_pack_id
                        else None,
                        "fact_input_hash": existing.fact_input_hash,
                    },
                    new_value={
                        "overview_en": response_item.overview_en.strip(),
                        "overview_ar": response_item.overview_ar.strip(),
                        "source_version": candidate.content_hash,
                        "approval_status": EditorialApprovalStatus.NEEDS_REVIEW.value,
                        "origin": ORIGIN,
                        "overview_pack_id": str(pack.id),
                        "fact_input_hash": response_item.fact_input_hash,
                    },
                    detected_at=imported_at,
                    content_hash=response_item.fact_input_hash,
                )
            )
            existing.overview_en = response_item.overview_en.strip()
            existing.overview_ar = response_item.overview_ar.strip()
            existing.source_version = candidate.content_hash
            existing.generated_at = imported_at
            existing.approval_status = EditorialApprovalStatus.NEEDS_REVIEW
            existing.approved_by = None
            existing.approved_at = None
            existing.origin = ORIGIN
            existing.overview_pack_id = pack.id
            existing.overview_pack_hash = pack.pack_hash
            existing.fact_input_version = pack_item.fact_input_version
            existing.fact_input_hash = response_item.fact_input_hash
            existing.candidate_version = response_item.candidate_version
            existing.import_correlation_id = correlation_id
        else:
            candidate.editorial_draft = ProjectImportEditorialDraft(
                overview_en=response_item.overview_en.strip(),
                overview_ar=response_item.overview_ar.strip(),
                source_version=candidate.content_hash,
                generated_at=imported_at,
                approval_status=EditorialApprovalStatus.NEEDS_REVIEW,
                origin=ORIGIN,
                overview_pack_id=pack.id,
                overview_pack_hash=pack.pack_hash,
                fact_input_version=pack_item.fact_input_version,
                fact_input_hash=response_item.fact_input_hash,
                candidate_version=response_item.candidate_version,
                import_correlation_id=correlation_id,
            )
        candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
        candidate.last_successful_stage = "prepare-overview"
        pack_item.status = "imported-needs-review"
        pack_item.failure_code = None
        pack_item.failure_message = None
        pack_item.referenced_fact_fields = response_item.referenced_fact_fields
        pack_item.editorial_notes = response_item.editorial_notes
        pack_item.imported_at = datetime.now(UTC)
        imported += 1
        results.append(
            {"candidate_id": response_item.candidate_id, "status": "imported-needs-review"}
        )
    pack.imported_count = sum(1 for value in pack.items if value.status == "imported-needs-review")
    pack.failed_count = sum(1 for value in pack.items if value.status == "failed")
    pack.status = "completed" if pack.failed_count == 0 else "completed-with-errors"
    pack.import_correlation_id = correlation_id
    pack.imported_at = datetime.now(UTC)
    await db.flush()
    return {"pack": pack_dict(pack), "imported": imported, "failed": failed, "results": results}
