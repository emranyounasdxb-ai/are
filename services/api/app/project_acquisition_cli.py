from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.acquisition.service import acquire_batch, load_manifest, status_summary
from app.config import get_settings
from app.db import SessionLocal
from app.project_processing import run_worker_once

DEFAULT_MANIFEST = Path("/app/data-intake/offplan-projects-owner-manifest.csv")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Bounded ARE official Project acquisition")
    subcommands = value.add_subparsers(dest="command", required=True)
    load = subcommands.add_parser("load", help="Load the immutable 50-row owner manifest")
    load.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    subcommands.add_parser(
        "sobha-siniya-pilot", help="Run or reuse the one authorized controlled acquisition pilot"
    )
    subcommands.add_parser(
        "sobha-siniya-process", help="Queue or reuse the authorized pilot processing job"
    )
    for command in ("acquire", "refresh", "retry-failed", "media-intake", "status"):
        item = subcommands.add_parser(command)
        item.add_argument("--batch-id")
    worker = subcommands.add_parser("process-worker", help="Run the bounded preparation worker")
    worker.add_argument("--max-items", type=int, default=25)
    worker.add_argument("--worker-id", default="local-project-worker")
    return value


async def run(args: argparse.Namespace) -> None:
    async with SessionLocal() as db:
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

            pilot_result = await run_sobha_siniya_pilot(db, get_settings())
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
