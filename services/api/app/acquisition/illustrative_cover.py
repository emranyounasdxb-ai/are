"""Owner-authorized, Project-specific ALIYAS conceptual Cover generation.

The generated artwork is an abstract editorial illustration. It never depicts
or claims to depict the physical development and never uses third-party media.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import uuid
from datetime import UTC, datetime

from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.media import (
    normalized_media_filename,
    responsive_derivatives,
    thumbnail,
    validate_raster,
)
from app.audit import write_audit
from app.config import Settings
from app.import_review import sync_linked_draft_from_candidate
from app.models import (
    MediaRightsStatus,
    ProjectImportCandidate,
    ProjectImportMedia,
    ProjectMediaCategory,
)
from app.project_field_policy import candidate_media_is_preview_eligible
from app.storage import PrivateStorage

GENERATOR_VERSION = "aliyas-concept-cover-v1"
RIGHTS_BASIS = (
    "Owner-authorized ALIYAS-owned conceptual illustration; website and derivative use "
    "permitted; not an exact development depiction."
)


class _StableRng:
    """Small deterministic sampler for visual layout; not used for security."""

    def __init__(self, seed: str) -> None:
        self.seed = bytes.fromhex(seed)
        self.counter = 0

    def _fraction(self) -> float:
        self.counter += 1
        digest = hashlib.sha256(self.seed + self.counter.to_bytes(4, "big")).digest()
        return int.from_bytes(digest[:8], "big") / ((1 << 64) - 1)

    def randrange(self, start: int, stop: int) -> int:
        return start + min(stop - start - 1, int(self._fraction() * (stop - start)))

    def uniform(self, start: float, stop: float) -> float:
        return start + self._fraction() * (stop - start)

    def random(self) -> float:
        return self._fraction()


def concept_cover_seed(candidate: ProjectImportCandidate) -> str:
    material = "|".join(
        (
            str(candidate.id),
            str(candidate.linked_project_id or ""),
            candidate.normalized_project_name or "",
            str(candidate.proposed_developer_id or ""),
            str(candidate.proposed_area_id or ""),
            GENERATOR_VERSION,
        )
    )
    return hashlib.sha256(material.encode()).hexdigest()


def render_concept_cover(seed: str, *, width: int = 1920, height: int = 1080) -> bytes:
    """Create unique abstract architecture from a stable project-bound seed."""
    if len(seed) != 64 or not all(value in "0123456789abcdef" for value in seed):
        raise ValueError("A canonical SHA-256 seed is required.")
    rng = _StableRng(seed)
    image = Image.new("RGB", (width, height), "#160f08")
    draw = ImageDraw.Draw(image, "RGBA")
    top = (26 + rng.randrange(0, 12), 18 + rng.randrange(0, 8), 11)
    bottom = (61, 38, 5)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(round(top[index] * (1 - ratio) + bottom[index] * ratio) for index in range(3))
        draw.line((0, y, width, y), fill=(*color, 255))
    horizon = round(height * (0.71 + rng.uniform(-0.04, 0.04)))
    sun_x = round(width * (0.64 + rng.uniform(-0.17, 0.17)))
    sun_y = round(height * (0.25 + rng.uniform(-0.08, 0.12)))
    sun_r = round(height * (0.085 + rng.uniform(0, 0.035)))
    draw.ellipse(
        (sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r),
        fill=(244, 217, 149, 36),
        outline=(244, 217, 149, 130),
        width=3,
    )
    cursor = -rng.randrange(10, 90)
    buildings: list[tuple[int, int, int, int]] = []
    while cursor < width:
        block_width = rng.randrange(120, 285)
        block_height = rng.randrange(round(height * 0.18), round(height * 0.58))
        top_y = horizon - block_height
        inset = rng.randrange(0, max(1, block_width // 5))
        buildings.append((cursor, top_y, cursor + block_width, horizon))
        draw.polygon(
            [
                (cursor, horizon),
                (cursor + inset, top_y),
                (cursor + block_width - inset // 2, top_y + rng.randrange(-20, 35)),
                (cursor + block_width, horizon),
            ],
            fill=(30, 22, 14, rng.randrange(205, 241)),
            outline=(184, 146, 69, rng.randrange(95, 151)),
        )
        cursor += block_width + rng.randrange(18, 75)
    for left, top_y, right, _ in buildings:
        for window_y in range(top_y + 45, horizon - 30, 58):
            for window_x in range(left + 32, right - 18, 52):
                if rng.random() > 0.38:
                    draw.rectangle(
                        (window_x, window_y, window_x + 13, window_y + 5),
                        fill=(244, 217, 149, rng.randrange(55, 126)),
                    )
    draw.rectangle((0, horizon, width, height), fill=(12, 9, 7, 185))
    for index in range(5):
        inset = round(width * (0.08 + index * 0.045))
        y = horizon + round((height - horizon) * (index + 1) / 7)
        draw.line(
            (inset, y, width - inset, y + rng.randrange(-25, 26)), fill=(184, 146, 69, 60), width=2
        )
    draw.rectangle((42, 42, width - 42, height - 42), outline=(184, 146, 69, 130), width=2)
    output = io.BytesIO()
    image.save(output, "WEBP", quality=90, method=6, exif=b"")
    return output.getvalue()


async def generate_candidate_cover(
    db: AsyncSession,
    settings: Settings,
    candidate_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> dict[str, object]:
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == candidate_id)
        .options(
            selectinload(ProjectImportCandidate.staged_media),
            selectinload(ProjectImportCandidate.editorial_draft),
        )
        .with_for_update()
    )
    if not candidate or not candidate.linked_project_id:
        raise ValueError("A linked Draft candidate is required.")
    if (candidate.acquisition_summary or {}).get("targeted_field_review", {}).get("identity_hold"):
        raise ValueError("Identity-hold candidates cannot receive conceptual Covers.")
    existing_cover = next(
        (
            item
            for item in candidate.staged_media
            if item.category == ProjectMediaCategory.COVER
            and candidate_media_is_preview_eligible(item)
        ),
        None,
    )
    if existing_cover:
        return {
            "candidate_id": str(candidate.id),
            "outcome": "preserved",
            "media_id": str(existing_cover.id),
        }

    seed = concept_cover_seed(candidate)
    source_url = f"aliyas-generated://project/{candidate.linked_project_id}/cover/{seed[:16]}"
    existing = next(
        (item for item in candidate.staged_media if item.source_url == source_url), None
    )
    if existing and candidate_media_is_preview_eligible(existing):
        return {
            "candidate_id": str(candidate.id),
            "outcome": "unchanged",
            "media_id": str(existing.id),
        }

    now = datetime.now(UTC)
    content = await asyncio.to_thread(render_concept_cover, seed)
    raster = validate_raster(content, "image/webp")
    slug = candidate.normalized_project_name or f"project-{candidate.manifest_row_id}"
    filename = normalized_media_filename(slug, "cover", 1, raster.sha256, raster.extension)
    storage = PrivateStorage(settings)
    raw_key = await storage.save_acquisition_media(
        content,
        "webp",
        normalized_filename=filename.replace(".webp", "-raw.webp"),
    )
    master_key = await storage.save_acquisition_media(
        raster.content, "webp", normalized_filename=filename
    )
    thumb_content = await asyncio.to_thread(thumbnail, raster)
    thumb_key = await storage.save_acquisition_media(
        thumb_content,
        "webp",
        normalized_filename=filename.replace(".webp", "-thumb.webp"),
        thumbnail=True,
    )
    derivatives = await asyncio.to_thread(responsive_derivatives, raster)
    manifest: list[dict[str, object]] = []
    for derivative in derivatives:
        derivative_filename = filename.replace(".webp", f"-{derivative.width}w.{derivative.format}")
        key = await storage.save_acquisition_media(
            derivative.content,
            derivative.format,
            normalized_filename=derivative_filename,
        )
        manifest.append(
            {
                "storage_key": key,
                "format": derivative.format,
                "mime_type": derivative.mime_type,
                "width": derivative.width,
                "height": derivative.height,
                "size_bytes": derivative.size_bytes,
                "sha256": derivative.sha256,
            }
        )
    for item in candidate.staged_media:
        if item.category == ProjectMediaCategory.COVER:
            item.category = ProjectMediaCategory.GALLERY
        if item.rights_status == MediaRightsStatus.APPROVED and (
            item.rights_basis or ""
        ).startswith("Automatically approved exact-Project"):
            item.rights_status = MediaRightsStatus.REJECTED
            item.failure_reason = (
                "Reuse permission is not documented; retained as private evidence."
            )
    name = candidate.normalized_project_name or "Sharjah Project"
    name_ar = str((candidate.normalized_payload or {}).get("project_name_ar") or name)
    media = existing or ProjectImportMedia(
        candidate_id=candidate.id,
        source_url=source_url,
        category=ProjectMediaCategory.COVER,
        rights_status=MediaRightsStatus.APPROVED,
        stage_status="downloaded",
    )
    if existing is None:
        candidate.staged_media.append(media)
    media.category = ProjectMediaCategory.COVER
    media.rights_status = MediaRightsStatus.APPROVED
    media.rights_basis = RIGHTS_BASIS
    media.rights_confirmed_by = actor_id
    media.rights_confirmed_at = now
    media.stage_status = "downloaded"
    media.raw_storage_key = raw_key
    media.storage_key = master_key
    media.thumbnail_storage_key = thumb_key
    media.mime_type = raster.mime_type
    media.size_bytes = len(raster.content)
    media.sha256 = raster.sha256
    media.original_sha256 = hashlib.sha256(content).hexdigest()
    media.processed_sha256 = raster.sha256
    media.width = raster.width
    media.height = raster.height
    media.retrieved_at = now
    media.last_seen_at = now
    media.normalized_filename = filename
    media.display_order = 0
    media.derivative_manifest = manifest
    media.processing_version = GENERATOR_VERSION
    media.failure_reason = None
    media.alt_en_draft = f"Conceptual ALIYAS editorial illustration for {name}"
    media.alt_ar_draft = f"تصميم تحريري تصوري من إلياس لمشروع {name_ar}"
    media.title_en = f"{name} — conceptual project cover"
    media.title_ar = f"{name_ar} — غلاف تصوري للمشروع"
    media.description_en = (
        f"ALIYAS-owned conceptual editorial cover for {name}; not a depiction of the development."
    )
    media.description_ar = (
        f"غلاف تحريري تصوري مملوك لإلياس لمشروع {name_ar}، ولا يمثل صورة فعلية للتطوير."
    )
    media.tags = [name, "ALIYAS conceptual illustration", "Sharjah"]
    media.public_metadata = {
        "generation_kind": "aliyas-owned-conceptual-illustration",
        "generator_version": GENERATOR_VERSION,
        "input_sha256": seed,
        "project_id": str(candidate.linked_project_id),
        "not_exact_development_depiction": True,
        "permitted_channels": ["aliyas-website"],
        "derivatives_permitted": True,
    }
    await db.flush()
    await sync_linked_draft_from_candidate(db, candidate, fields={"media"})
    await write_audit(
        db,
        actor_user_id=actor_id,
        action="project-import.media.generate-owner-illustration",
        entity_type="project_import_media",
        entity_id=media.id,
        correlation_id=f"concept-cover:{candidate.id}:{GENERATOR_VERSION}",
        after={
            "candidate_id": str(candidate.id),
            "project_id": str(candidate.linked_project_id),
            "sha256": raster.sha256,
            "generator_version": GENERATOR_VERSION,
            "not_exact_development_depiction": True,
        },
        metadata={"owner_authorized_batch": True},
    )
    await db.commit()
    return {
        "candidate_id": str(candidate.id),
        "outcome": "generated",
        "media_id": str(media.id),
        "sha256": raster.sha256,
    }
