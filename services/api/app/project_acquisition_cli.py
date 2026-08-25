from __future__ import annotations

import argparse
import asyncio
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
from app.models import ProjectImportCandidate, ProjectOverviewPack
from app.project_processing import run_worker_once
from app.schemas import ManualOverviewResponse

DEFAULT_MANIFEST = Path("/app/data-intake/offplan-projects-owner-manifest.csv")


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
    tanami = subcommands.add_parser(
        "tanami-batch",
        help="Acquire an explicit owner-approved list of exact Tanami Project URLs",
    )
    tanami.add_argument("--url", action="append", required=True, dest="urls")
    for command in ("acquire", "refresh", "retry-failed", "media-intake", "status"):
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
    return value


async def run(args: argparse.Namespace) -> None:
    async with SessionLocal() as db:
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
            result = await import_overview_response(
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
                after={"imported": result["imported"], "failed": result["failed"]},
            )
            await db.commit()
            print(json.dumps(result, default=str, indent=2))
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
        if args.command == "tanami-batch":
            from app.acquisition.tanami import acquire_explicit_batch

            batch = await acquire_explicit_batch(db, get_settings(), args.urls)
            print(json.dumps(status_summary(batch), indent=2))
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
        else:
            from app.acquisition.service import selected_batch

            batch = await selected_batch(db, args.batch_id)
        print(json.dumps(status_summary(batch), indent=2))


def main() -> None:
    asyncio.run(run(parser().parse_args()))


if __name__ == "__main__":
    main()
