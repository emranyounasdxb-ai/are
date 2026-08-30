from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.acquisition.service import acquire_batch, load_manifest, status_summary
from app.audit import write_audit
from app.config import get_settings
from app.db import SessionLocal
from app.manual_overviews import create_overview_pack, import_overview_response, pack_dict
from app.models import ProjectImportBatch, ProjectImportCandidate, ProjectOverviewPack
from app.project_processing import run_worker_once
from app.schemas import ManualOverviewResponse

DEFAULT_MANIFEST = Path("/app/data-intake/offplan-projects-owner-manifest.csv")
SHARJAH_MEDIA_WORKERS = 4


async def _intake_media_parallel(
    batch_id: uuid.UUID,
    candidate_ids: list[uuid.UUID],
    *,
    preserve_review_state: bool = False,
    retry_failed: bool = True,
) -> dict[str, int]:
    """Process disjoint candidates concurrently while retaining per-candidate commits."""
    from app.acquisition.media_intake import intake_private_media

    groups = [candidate_ids[index::SHARJAH_MEDIA_WORKERS] for index in range(SHARJAH_MEDIA_WORKERS)]

    async def process_group(group: list[uuid.UUID]) -> dict[str, int]:
        if not group:
            return {}
        async with SessionLocal() as worker_db:
            return await intake_private_media(
                worker_db,
                get_settings(),
                batch_id,
                candidate_ids=group,
                preserve_review_state=preserve_review_state,
                retry_failed=retry_failed,
            )

    results = await asyncio.gather(*(process_group(group) for group in groups))
    totals: dict[str, int] = {}
    for result in results:
        for key, value in result.items():
            totals[key] = totals.get(key, 0) + value
    return totals


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Bounded ARE official Project acquisition")
    subcommands = value.add_subparsers(dest="command", required=True)
    load = subcommands.add_parser("load", help="Load the immutable 50-row owner manifest")
    load.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    pilot = subcommands.add_parser(
        "sobha-siniya-pilot", help="Run or reuse the one authorized controlled acquisition pilot"
    )
    pilot.add_argument("--refresh", action="store_true")
    subcommands.add_parser(
        "sobha-siniya-process", help="Queue or reuse the authorized pilot processing job"
    )
    subcommands.add_parser(
        "sobha-siniya-official-media",
        help="Intake the reviewed exact-project media from the official Sobha page",
    )
    tanami = subcommands.add_parser(
        "tanami-batch",
        help="Acquire an explicit owner-approved list of exact Tanami Project URLs",
    )
    tanami.add_argument("--url", action="append", required=True, dest="urls")
    sharjah = subcommands.add_parser(
        "tanami-sharjah-batch",
        help="Discover and acquire the complete bounded Tanami Sharjah Project listing",
    )
    sharjah.add_argument("--refresh", action="store_true")
    research = subcommands.add_parser(
        "official-research",
        help="Reinspect one existing private batch without approval/publication",
    )
    research.add_argument("--batch-id", required=True, type=uuid.UUID)
    research.add_argument("--candidate-id", action="append", type=uuid.UUID, default=None)
    research.add_argument(
        "--extra-url",
        action="append",
        default=[],
        metavar="ROW=URL",
        help="Inspect an explicit official URL for one existing manifest row.",
    )
    tanami_refresh = subcommands.add_parser(
        "tanami-refresh-existing",
        help="Refresh only the retained candidates in one existing explicit Tanami batch",
    )
    tanami_refresh.add_argument("--batch-id", required=True, type=uuid.UUID)
    tanami_media_classify = subcommands.add_parser(
        "tanami-media-classify",
        help="Persist DOM-aware media categories for existing mapped Tanami Projects only",
    )
    tanami_media_classify.add_argument("--batch-id", required=True, action="append", type=uuid.UUID)
    tanami_media_acquire = subcommands.add_parser(
        "tanami-media-acquire",
        help="Download and sync classified media without changing review state",
    )
    tanami_media_acquire.add_argument("--batch-id", required=True, action="append", type=uuid.UUID)
    tanami_media_acquire.add_argument(
        "--rights-only",
        action="store_true",
        help="Synchronize owner-authorized rights on already downloaded Tanami media only",
    )
    tanami_media_acquire.add_argument(
        "--no-retry-failed",
        action="store_true",
        help="Prove idempotency without refetching already recorded terminal failures",
    )
    owner_heroes = subcommands.add_parser(
        "owner-hero-import",
        help="Validate and assign the exact owner-created RAK/Sharjah Project Hero pack",
    )
    owner_heroes.add_argument("--directory", required=True, type=Path)
    owner_heroes.add_argument("--actor-id", required=True, type=uuid.UUID)
    for command in (
        "acquire",
        "refresh",
        "retry-failed",
        "media-intake",
        "reconcile-conflicts",
        "status",
    ):
        item = subcommands.add_parser(command)
        item.add_argument("--batch-id")
    worker = subcommands.add_parser("process-worker", help="Run the bounded preparation worker")
    worker.add_argument("--max-items", type=int, default=25)
    worker.add_argument("--worker-id", default="local-project-worker")
    overview_export = subcommands.add_parser(
        "overview-pack-export", help="Create a private manual Overview pack for explicit candidates"
    )
    overview_export.add_argument("--batch-id", required=True, type=uuid.UUID)
    overview_export.add_argument("--candidate-id", required=True, action="append", type=uuid.UUID)
    overview_export.add_argument("--actor-id", required=True, type=uuid.UUID)
    overview_export.add_argument("--selection-mode", default="manual")
    overview_export.add_argument("--idempotency-key", required=True)
    overview_validate = subcommands.add_parser(
        "overview-pack-validate", help="Validate a completed manual Overview response file"
    )
    overview_validate.add_argument("--file", required=True, type=Path)
    overview_import = subcommands.add_parser(
        "overview-pack-import", help="Import a validated response through the review-gated service"
    )
    overview_import.add_argument("--pack-id", required=True, type=uuid.UUID)
    overview_import.add_argument("--file", required=True, type=Path)
    overview_import.add_argument("--actor-id", required=True, type=uuid.UUID)
    overview_import.add_argument("--correlation-id", required=True)
    covers = subcommands.add_parser(
        "generate-illustrative-covers",
        help="Create owner-authorized Project-specific ALIYAS conceptual Covers",
    )
    covers.add_argument("--candidate-id", required=True, action="append", type=uuid.UUID)
    covers.add_argument("--actor-id", required=True, type=uuid.UUID)
    return value


async def run(args: argparse.Namespace) -> None:
    async with SessionLocal() as db:
        if args.command == "owner-hero-import":
            from app.acquisition.owner_hero_banners import import_and_assign_owner_heroes

            result = await import_and_assign_owner_heroes(
                db,
                get_settings(),
                args.directory,
                actor_id=args.actor_id,
            )
            print(json.dumps(result, default=str, indent=2))
            return
        if args.command == "tanami-media-classify":
            from app.acquisition.security import BatchCachingFetcher, SecureFetcher
            from app.acquisition.service import selected_batch
            from app.acquisition.tanami import classify_existing_candidate_media

            fetcher = BatchCachingFetcher(SecureFetcher())
            projects: list[dict[str, object]] = []
            for batch_id in args.batch_id:
                batch = await selected_batch(db, str(batch_id))
                for candidate in sorted(batch.candidates, key=lambda item: item.manifest_row_id):
                    projects.append(
                        await classify_existing_candidate_media(
                            db,
                            get_settings(),
                            candidate.id,
                            fetcher=fetcher,
                        )
                    )
            classification_totals: dict[str, int] = {}
            for project in projects:
                counts = project.get("counts")
                if not isinstance(counts, dict):
                    continue
                for key, count in counts.items():
                    classification_totals[str(key)] = classification_totals.get(str(key), 0) + int(
                        count
                    )
            print(json.dumps({"projects": projects, "totals": classification_totals}, indent=2))
            return
        if args.command == "tanami-media-acquire":
            from app.acquisition.media_intake import _remove_media_output, intake_private_media
            from app.acquisition.service import selected_batch
            from app.acquisition.tanami import (
                TANAMI_ADAPTER_KEY,
                ambiguous_cross_candidate_media_ids,
            )
            from app.import_review import sync_linked_draft_from_candidate

            acquisition_totals: dict[str, int] = {}
            projects_synced = 0
            completed_batches: list[ProjectImportBatch] = []
            for batch_id in args.batch_id:
                batch = await selected_batch(db, str(batch_id))
                media_ids = (
                    {
                        media.id
                        for candidate in batch.candidates
                        if candidate.adapter_key == TANAMI_ADAPTER_KEY
                        for media in candidate.staged_media
                        if media.stage_status == "downloaded"
                    }
                    if args.rights_only
                    else None
                )
                media_intake_result = (
                    await intake_private_media(
                        db,
                        get_settings(),
                        batch.id,
                        media_ids=media_ids,
                        preserve_review_state=True,
                        retry_failed=not args.no_retry_failed,
                    )
                    if args.rights_only
                    else await _intake_media_parallel(
                        batch.id,
                        [candidate.id for candidate in batch.candidates],
                        preserve_review_state=True,
                        retry_failed=not args.no_retry_failed,
                    )
                )
                for key, count in media_intake_result.items():
                    acquisition_totals[key] = acquisition_totals.get(key, 0) + count
                completed_batches.append(await selected_batch(db, str(batch.id)))
            bounded_candidates = [
                candidate for batch in completed_batches for candidate in batch.candidates
            ]
            ambiguous_ids = ambiguous_cross_candidate_media_ids(bounded_candidates)
            if ambiguous_ids:
                from app.storage import PrivateStorage

                storage = PrivateStorage(get_settings())
                for candidate in bounded_candidates:
                    for staged_media in candidate.staged_media:
                        if staged_media.id not in ambiguous_ids:
                            continue
                        _remove_media_output(
                            storage,
                            staged_media,
                            "Identical media was shared across exact Project candidates.",
                        )
                        staged_media.stage_status = "rejected-unrelated"
            for completed_batch in completed_batches:
                for candidate in completed_batch.candidates:
                    if candidate.linked_project_id:
                        await sync_linked_draft_from_candidate(db, candidate, fields={"media"})
                        projects_synced += 1
            await db.commit()
            print(
                json.dumps(
                    {
                        "batches": len(args.batch_id),
                        "projects_synced": projects_synced,
                        "cross_project_duplicates_rejected": len(ambiguous_ids),
                        **acquisition_totals,
                    },
                    indent=2,
                )
            )
            return
        if args.command == "generate-illustrative-covers":
            from app.acquisition.illustrative_cover import generate_candidate_cover

            results = []
            for candidate_id in args.candidate_id:
                results.append(
                    await generate_candidate_cover(db, get_settings(), candidate_id, args.actor_id)
                )
            print(json.dumps({"count": len(results), "results": results}, indent=2))
            return
        if args.command == "official-research":
            from app.acquisition.research import research_existing_batch

            extra_urls: dict[int, list[str]] = {}
            for value in args.extra_url:
                row_text, separator, url = value.partition("=")
                if not separator or not row_text.isdigit() or not url.startswith("https://"):
                    raise ValueError("Each --extra-url must use ROW=https://official.example/path.")
                extra_urls.setdefault(int(row_text), []).append(url)
            result = await research_existing_batch(
                db,
                get_settings(),
                args.batch_id,
                candidate_ids=args.candidate_id,
                extra_urls=extra_urls,
            )
            print(json.dumps(result, indent=2))
            return
        if args.command == "overview-pack-validate":
            response = ManualOverviewResponse.model_validate_json(
                await asyncio.to_thread(args.file.read_bytes)
            )
            print(
                json.dumps(
                    {"valid": True, "pack_id": str(response.pack_id), "items": len(response.items)},
                    indent=2,
                )
            )
            return
        if args.command == "overview-pack-export":
            if len(args.candidate_id) > 50 or len(set(args.candidate_id)) != len(args.candidate_id):
                raise ValueError("Select between 1 and 50 unique candidate IDs.")
            candidates = (
                await db.scalars(
                    select(ProjectImportCandidate).where(
                        ProjectImportCandidate.id.in_(args.candidate_id)
                    )
                )
            ).all()
            versions = {candidate.id: candidate.review_version for candidate in candidates}
            pack = await create_overview_pack(
                db,
                get_settings(),
                batch_id=args.batch_id,
                candidate_ids=args.candidate_id,
                expected_versions=versions,
                selection_mode=args.selection_mode,
                actor_id=args.actor_id,
                idempotency_key=args.idempotency_key,
            )
            await write_audit(
                db,
                action="project-overview-pack.prepare",
                entity_type="project-overview-pack",
                entity_id=pack.id,
                actor_user_id=args.actor_id,
                correlation_id=f"cli:{args.idempotency_key}",
                after={
                    "eligible_count": pack.eligible_count,
                    "selected_count": pack.selected_count,
                },
            )
            await db.commit()
            print(json.dumps(pack_dict(pack), default=str, indent=2))
            return
        if args.command == "overview-pack-import":
            response = ManualOverviewResponse.model_validate_json(
                await asyncio.to_thread(args.file.read_bytes)
            )
            imported_pack = await db.scalar(
                select(ProjectOverviewPack)
                .where(ProjectOverviewPack.id == args.pack_id)
                .options(selectinload(ProjectOverviewPack.items))
            )
            if not imported_pack:
                raise ValueError("Overview pack not found.")
            overview_import_result = await import_overview_response(
                db,
                pack=imported_pack,
                response=response,
                correlation_id=args.correlation_id,
            )
            await write_audit(
                db,
                action="project-overview-pack.import",
                entity_type="project-overview-pack",
                entity_id=imported_pack.id,
                actor_user_id=args.actor_id,
                correlation_id=args.correlation_id,
                after={
                    "imported": overview_import_result["imported"],
                    "failed": overview_import_result["failed"],
                },
            )
            await db.commit()
            print(json.dumps(overview_import_result, default=str, indent=2))
            return
        if args.command == "process-worker":
            processed = 0
            while processed < max(1, min(args.max_items, 100)):
                if not await run_worker_once(db, worker_id=args.worker_id):
                    break
                processed += 1
            print(json.dumps({"processed": processed}, indent=2))
            return
        if args.command == "sobha-siniya-pilot":
            from app.acquisition.sobha_siniya_pilot import run_sobha_siniya_pilot

            pilot_result = await run_sobha_siniya_pilot(db, get_settings(), refresh=args.refresh)
            print(
                json.dumps(
                    {
                        "batch_id": str(pilot_result.batch_id),
                        "candidate_id": str(pilot_result.candidate_id),
                        "developer_id": str(pilot_result.developer_id),
                        "area_id": str(pilot_result.area_id),
                        "reused": pilot_result.reused,
                        "accessed_urls": pilot_result.accessed_urls,
                    },
                    indent=2,
                )
            )
            return
        if args.command == "sobha-siniya-process":
            from app.acquisition.sobha_siniya_pilot import queue_sobha_siniya_processing

            job_id = await queue_sobha_siniya_processing(db)
            print(json.dumps({"processing_job_id": str(job_id)}, indent=2))
            return
        if args.command == "sobha-siniya-official-media":
            from app.acquisition.sobha_siniya_pilot import refresh_sobha_official_media

            sobha_media_result = await refresh_sobha_official_media(db, get_settings())
            print(json.dumps(sobha_media_result, default=str, indent=2))
            return
        if args.command == "tanami-batch":
            from app.acquisition.media_intake import intake_private_media
            from app.acquisition.tanami import acquire_explicit_batch

            batch = await acquire_explicit_batch(db, get_settings(), args.urls)
            media_result = await intake_private_media(db, get_settings(), batch.id)
            print(
                json.dumps(
                    {"batch": status_summary(batch), "media": media_result},
                    indent=2,
                )
            )
            return
        if args.command == "tanami-sharjah-batch":
            from app.acquisition.security import BatchCachingFetcher, SecureFetcher
            from app.acquisition.tanami import (
                SHARJAH_LISTING_URL,
                acquire_explicit_batch,
                discover_sharjah_project_urls,
                finalize_sharjah_private_drafts,
            )

            session_fetcher = SecureFetcher()
            discovery = await discover_sharjah_project_urls(fetcher=session_fetcher)
            manifest_hash = hashlib.sha256(
                json.dumps(discovery.urls, separators=(",", ":")).encode()
            ).hexdigest()
            sharjah_batch = await db.scalar(
                select(ProjectImportBatch)
                .where(ProjectImportBatch.manifest_hash == manifest_hash)
                .options(
                    selectinload(ProjectImportBatch.candidates).selectinload(
                        ProjectImportCandidate.evidence
                    ),
                    selectinload(ProjectImportBatch.candidates).selectinload(
                        ProjectImportCandidate.staged_media
                    ),
                    selectinload(ProjectImportBatch.candidates).selectinload(
                        ProjectImportCandidate.editorial_draft
                    ),
                )
            )
            acquisition_reused = bool(
                not args.refresh
                and sharjah_batch
                and sharjah_batch.completed_at
                and len(sharjah_batch.candidates) == len(discovery.urls)
            )
            if not acquisition_reused:
                sharjah_batch = await acquire_explicit_batch(
                    db,
                    get_settings(),
                    discovery.urls,
                    fetcher=BatchCachingFetcher(session_fetcher),
                    batch_name="Tanami Sharjah Off-Plan Projects",
                )
            if sharjah_batch is None:
                raise RuntimeError("The Sharjah acquisition batch was not available.")
            batch = sharjah_batch
            listing_by_url = {item.url: item for item in discovery.projects}
            for candidate in batch.candidates:
                approved_url = candidate.owner_manifest_values.get("approved_project_url")
                listing_identity = (
                    listing_by_url.get(approved_url) if isinstance(approved_url, str) else None
                )
                owner_values = dict(candidate.owner_manifest_values)
                if listing_identity:
                    owner_values["listing_project_name"] = listing_identity.project_name
                    owner_values["listing_developer"] = listing_identity.developer_name
                    owner_values["listing_area"] = listing_identity.area_name
                    owner_values["source_developer"] = (
                        owner_values.get("source_developer") or listing_identity.developer_name
                    )
                    owner_values["source_area"] = (
                        owner_values.get("source_area") or listing_identity.area_name
                    )
                    candidate.owner_manifest_values = owner_values
                facts = dict(candidate.normalized_payload or {})
                facts["emirate"] = "Sharjah"
                if listing_identity:
                    facts["project_name"] = listing_identity.project_name
                candidate.normalized_payload = facts
                candidate.source_urls = list(
                    dict.fromkeys([*candidate.source_urls, SHARJAH_LISTING_URL])
                )
                candidate.acquisition_summary = {
                    **candidate.acquisition_summary,
                    "listing_source_url": SHARJAH_LISTING_URL,
                    "listing_content_hash": discovery.listing_content_hash,
                    "listing_retrieved_at": discovery.retrieved_at.isoformat(),
                }
            await db.commit()
            media_result = await _intake_media_parallel(
                batch.id, [candidate.id for candidate in batch.candidates]
            )
            refreshed_batch = await db.scalar(
                select(ProjectImportBatch)
                .where(ProjectImportBatch.id == batch.id)
                .execution_options(populate_existing=True)
                .options(
                    selectinload(ProjectImportBatch.candidates).selectinload(
                        ProjectImportCandidate.evidence
                    ),
                    selectinload(ProjectImportBatch.candidates).selectinload(
                        ProjectImportCandidate.staged_media
                    ),
                    selectinload(ProjectImportBatch.candidates).selectinload(
                        ProjectImportCandidate.editorial_draft
                    ),
                )
            )
            if refreshed_batch is None:
                raise RuntimeError("The completed Sharjah batch could not be reloaded.")
            batch = refreshed_batch
            draft_result = await finalize_sharjah_private_drafts(
                db,
                batch,
                fetcher=BatchCachingFetcher(session_fetcher),
            )
            print(
                json.dumps(
                    {
                        "discovery": {
                            "total_reported": discovery.total_reported,
                            "unique_urls": len(discovery.urls),
                            "duplicates": discovery.duplicate_count,
                            "pages": discovery.pages_fetched,
                            "acquisition_reused": acquisition_reused,
                        },
                        "batch": status_summary(batch),
                        "media": media_result,
                        "drafts": draft_result,
                    },
                    indent=2,
                )
            )
            return
        if args.command == "load":
            batch = await load_manifest(db, args.manifest)
        elif args.command == "acquire":
            batch = await acquire_batch(db, get_settings(), args.batch_id)
        elif args.command == "refresh":
            batch = await acquire_batch(db, get_settings(), args.batch_id, refresh=True)
        elif args.command == "retry-failed":
            batch = await acquire_batch(db, get_settings(), args.batch_id, failed_only=True)
        elif args.command == "media-intake":
            from app.acquisition.media_intake import intake_private_media
            from app.acquisition.service import selected_batch

            batch = await selected_batch(db, args.batch_id)
            media_result = await intake_private_media(db, get_settings(), batch.id)
            print(json.dumps(media_result, indent=2))
            return
        elif args.command == "reconcile-conflicts":
            from app.acquisition.reconciliation import reconcile_candidate_quality
            from app.acquisition.service import selected_batch

            batch = await selected_batch(db, args.batch_id)
            before = sum(len(item.conflict_reasons) for item in batch.candidates)
            for candidate in batch.candidates:
                reconcile_candidate_quality(candidate)
            await db.commit()
            print(
                json.dumps(
                    {
                        "batch_id": str(batch.id),
                        "candidates": len(batch.candidates),
                        "conflicts_before": before,
                        "conflicts_after": sum(
                            len(item.conflict_reasons) for item in batch.candidates
                        ),
                    },
                    indent=2,
                )
            )
            return
        if args.command == "tanami-refresh-existing":
            from app.acquisition.media_intake import intake_private_media
            from app.acquisition.reconciliation import reconcile_candidate_quality
            from app.acquisition.security import BatchCachingFetcher, SecureFetcher
            from app.acquisition.service import selected_batch
            from app.acquisition.tanami import refresh_explicit_candidate
            from app.import_review import sync_linked_draft_from_candidate

            batch = await selected_batch(db, str(args.batch_id))
            candidate_ids = [item.id for item in batch.candidates]
            fetcher = BatchCachingFetcher(SecureFetcher())
            succeeded = 0
            failures: list[dict[str, object]] = []
            for candidate_id in candidate_ids:
                try:
                    await refresh_explicit_candidate(
                        db,
                        get_settings(),
                        candidate_id,
                        fetcher=fetcher,
                    )
                    succeeded += 1
                except Exception as exc:
                    await db.rollback()
                    failed_candidate = await db.scalar(
                        select(ProjectImportCandidate)
                        .where(ProjectImportCandidate.id == candidate_id)
                        .options(
                            selectinload(ProjectImportCandidate.staged_media),
                            selectinload(ProjectImportCandidate.editorial_draft),
                        )
                    )
                    if failed_candidate:
                        failed_candidate.validation_errors = [
                            *failed_candidate.validation_errors,
                            {
                                "field": "acquisition",
                                "code": "refresh_failed",
                                "message": f"{type(exc).__name__}: {str(exc)[:300]}",
                            },
                        ]
                        reconcile_candidate_quality(failed_candidate)
                        await db.commit()
                    failures.append(
                        {
                            "candidate_id": str(candidate_id),
                            "error": f"{type(exc).__name__}: {str(exc)[:300]}",
                        }
                    )
            refresh_media_result = await intake_private_media(db, get_settings(), batch.id)
            refreshed_batch = await selected_batch(db, str(batch.id))
            for candidate in refreshed_batch.candidates:
                await sync_linked_draft_from_candidate(db, candidate)
            await db.commit()
            print(
                json.dumps(
                    {
                        "batch_id": str(batch.id),
                        "refreshed": succeeded,
                        "failed": failures,
                        "media": refresh_media_result,
                    },
                    indent=2,
                )
            )
            return
        else:
            from app.acquisition.service import selected_batch

            batch = await selected_batch(db, args.batch_id)
        print(json.dumps(status_summary(batch), indent=2))


def main() -> None:
    asyncio.run(run(parser().parse_args()))


if __name__ == "__main__":
    main()
