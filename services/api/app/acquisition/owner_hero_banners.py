"""Deterministic private intake and assignment of owner-created Project Hero media."""

from __future__ import annotations

import asyncio
import hashlib
import io
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.media import (
    OWNER_HERO_SOURCE_PREFIX,
    ValidatedRaster,
    is_tanami_native_media_source,
    responsive_derivatives,
)
from app.audit import write_audit
from app.config import Settings
from app.models import (
    AuditLog,
    MediaRightsStatus,
    Project,
    ProjectMedia,
    ProjectMediaCategory,
    ProjectPropertyType,
    UAEEmirate,
)
from app.project_media_preview import APPROVE, REVOKE, VERSION, asset_version
from app.storage import PrivateStorage

OWNER_HERO_ACTION = "project.hero.owner-media.assign"
OWNER_HERO_AUTHORIZATION = "Owner-created ALIYAS Project Hero batch approved 2026-08-30"
OWNER_HERO_FILENAME = re.compile(r"^are-hero-(?P<category>[a-z0-9-]+)-(?P<index>\d{2})\.webp$")
EXPECTED_ASSET_COUNT = 65
EXPECTED_CATEGORIES = frozenset(
    {
        "branded-residence",
        "commercial",
        "community",
        "duplex",
        "happy-family-living-room",
        "hotel",
        "land",
        "loft",
        "luxury-apartment",
        "luxury-villa",
        "mixed-residential",
        "modern-family",
        "neutral-luxury",
        "office",
        "penthouse",
        "plots",
        "resort-lifestyle",
        "townhouse",
        "urban-residence",
        "waterfront",
    }
)

CATEGORY_POOLS = {
    "hotel-branded": ("hotel", "branded-residence"),
    "office-commercial": ("office", "commercial"),
    "land-community": ("land", "plots", "community"),
    "waterfront-resort": ("waterfront", "resort-lifestyle"),
    "penthouse": ("penthouse",),
    "duplex-loft": ("duplex", "loft"),
    "villa": ("luxury-villa",),
    "townhouse": ("townhouse",),
    "apartment-urban": ("luxury-apartment", "urban-residence"),
    "family": ("modern-family", "happy-family-living-room"),
    "mixed-residential": ("mixed-residential",),
    "neutral-luxury": ("neutral-luxury",),
}

CATEGORY_LABELS = {
    "hotel-branded": ("hotel or branded residence", "إقامة فندقية أو ذات علامة تجارية"),
    "office-commercial": ("office or commercial setting", "بيئة مكتبية أو تجارية"),
    "land-community": ("land or community setting", "أرض أو مجتمع سكني"),
    "waterfront-resort": ("waterfront or resort setting", "واجهة مائية أو منتجع"),
    "penthouse": ("penthouse setting", "مسكن بنتهاوس"),
    "duplex-loft": ("duplex or loft setting", "مسكن دوبلكس أو لوفت"),
    "villa": ("villa setting", "مسكن فيلا"),
    "townhouse": ("townhouse setting", "مسكن تاون هاوس"),
    "apartment-urban": ("apartment or urban residence", "شقة أو مسكن حضري"),
    "family": ("family residence", "مسكن عائلي"),
    "mixed-residential": ("mixed residential setting", "بيئة سكنية متنوعة"),
    "neutral-luxury": ("neutral luxury residence", "مسكن فاخر محايد"),
}


@dataclass(frozen=True)
class OwnerHeroAsset:
    path: Path
    filename: str
    category: str
    index: int
    content: bytes
    sha256: str
    width: int
    height: int


async def validate_owner_hero_directory(directory: Path) -> tuple[OwnerHeroAsset, ...]:
    files = await asyncio.to_thread(lambda: sorted(directory.glob("*"), key=lambda item: item.name))
    if len(files) != EXPECTED_ASSET_COUNT or any(not item.is_file() for item in files):
        raise ValueError(f"Expected exactly {EXPECTED_ASSET_COUNT} owner Hero WebP files.")
    assets: list[OwnerHeroAsset] = []
    checksums: set[str] = set()
    category_indexes: dict[str, list[int]] = {}
    for path in files:
        match = OWNER_HERO_FILENAME.fullmatch(path.name)
        if not match or match.group("category") not in EXPECTED_CATEGORIES:
            raise ValueError(f"Unexpected owner Hero filename: {path.name}")
        content = await asyncio.to_thread(path.read_bytes)
        digest = hashlib.sha256(content).hexdigest()
        if digest in checksums:
            raise ValueError(f"Duplicate owner Hero checksum: {path.name}")
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                width, height = image.size
                image_format = image.format
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError(f"Unreadable owner Hero image: {path.name}") from exc
        if image_format != "WEBP" or width < 320 or height < 180 or width != height * 2:
            raise ValueError(f"Owner Hero must be a genuine exact 2:1 WebP: {path.name}")
        category = match.group("category")
        index = int(match.group("index"))
        checksums.add(digest)
        category_indexes.setdefault(category, []).append(index)
        assets.append(
            OwnerHeroAsset(path, path.name, category, index, content, digest, width, height)
        )
    for category, indexes in category_indexes.items():
        if sorted(indexes) != list(range(1, len(indexes) + 1)):
            raise ValueError(f"Owner Hero category indexes are not contiguous: {category}")
    if set(category_indexes) != EXPECTED_CATEGORIES:
        raise ValueError("Owner Hero category set is incomplete.")
    return tuple(assets)


def project_hero_pool(project: Project) -> str:
    """Choose the first supported owner category using verified stored Project facts only."""
    property_types = {item.property_type for item in project.property_types}
    unit_text = " ".join(item.label_en.casefold() for item in project.unit_types)
    name = next(
        (item.official_name.casefold() for item in project.translations if item.locale == "en"),
        project.slug.casefold(),
    )
    area = project.area.name_en.casefold()
    identity_text = f"{name} {unit_text}"
    if any(
        token in identity_text
        for token in ("hotel", "branded residence", "address residences", "marriott", "rove")
    ):
        return "hotel-branded"
    if any(token in unit_text for token in ("office", "commercial", "retail")):
        return "office-commercial"
    if ProjectPropertyType.RESIDENTIAL_PLOT in property_types or any(
        token in unit_text for token in ("plot", "land")
    ):
        return "land-community"
    if (
        any(
            token in f"{name} {area}"
            for token in ("waterfront", "island", "marjan", "mina al arab", "maryam")
        )
        or "resort" in identity_text
    ):
        return "waterfront-resort"
    if ProjectPropertyType.PENTHOUSE in property_types:
        return "penthouse"
    if ProjectPropertyType.DUPLEX in property_types or "loft" in unit_text:
        return "duplex-loft"
    if ProjectPropertyType.VILLA in property_types or ProjectPropertyType.MANSION in property_types:
        return "villa"
    if ProjectPropertyType.TOWNHOUSE in property_types:
        return "townhouse"
    if ProjectPropertyType.APARTMENT in property_types:
        return "apartment-urban"
    if any(item.bedroom_option.value in {"4", "5", "6+"} for item in project.bedroom_options):
        return "family"
    if len(property_types) > 1:
        return "mixed-residential"
    return "neutral-luxury"


def select_owner_hero_asset(
    project_id: uuid.UUID, pool: str, assets: tuple[OwnerHeroAsset, ...]
) -> OwnerHeroAsset:
    categories = CATEGORY_POOLS[pool]
    eligible = sorted(
        (item for item in assets if item.category in categories), key=lambda item: item.filename
    )
    if not eligible:
        raise ValueError(f"No owner Hero asset is available for {pool}.")
    return eligible[int.from_bytes(project_id.bytes, "big") % len(eligible)]


def _metadata(project: Project, pool: str) -> dict[str, object]:
    english_name = next(item.official_name for item in project.translations if item.locale == "en")
    arabic_name = next(item.official_name for item in project.translations if item.locale == "ar")
    label_en, label_ar = CATEGORY_LABELS[pool]
    return {
        "alt_en": f"ALIYAS conceptual Hero for {english_name}, representing a {label_en}",
        "alt_ar": f"صورة رئيسية تصورية من علياس لمشروع {arabic_name} تمثل {label_ar}",
        "title_en": f"{english_name} — ALIYAS Project Hero",
        "title_ar": f"{arabic_name} — الصورة الرئيسية للمشروع من علياس",
        "description_en": (
            f"Owner-created ALIYAS editorial Hero for {english_name}; it is an illustrative "
            "category visual, not an exact development render."
        ),
        "description_ar": (
            f"صورة رئيسية تحريرية أنشأتها علياس لمشروع {arabic_name}؛ وهي صورة تصورية للفئة "
            "وليست تصميماً دقيقاً للمشروع."
        ),
        "tags": [
            "aliyas-real-estate",
            "owner-created",
            "project-hero",
            pool,
            "علياس-العقارية",
            "صورة-رئيسية",
        ],
    }


async def _asset_bundle(
    storage: PrivateStorage, asset: OwnerHeroAsset
) -> tuple[str, list[dict[str, object]]]:
    existing_master = await storage.existing_owner_hero_keys(normalized_filename=asset.filename)
    master_key = ""
    for key in existing_master:
        if await asyncio.to_thread(storage.read, key) == asset.content:
            master_key = key
            break
    if not master_key:
        master_key = await storage.save_owner_hero_media(
            asset.content, normalized_filename=asset.filename
        )
    raster = ValidatedRaster(
        asset.content, "image/webp", "webp", asset.width, asset.height, asset.sha256
    )
    expected_names = {
        f"{Path(asset.filename).stem}-{width}.{extension}"
        for width in (480, 960, 1600)
        if width <= asset.width
        for extension in ("webp", "avif")
    }
    existing_derivatives: dict[str, str] = {}
    for filename in expected_names:
        keys = await storage.existing_owner_hero_keys(
            normalized_filename=filename, namespace="owner-hero-responsive"
        )
        if len(keys) == 1:
            existing_derivatives[filename] = keys[0]
    if set(existing_derivatives) == expected_names:
        cached_manifest: list[dict[str, object]] = []

        def derivative_order(item: tuple[str, str]) -> tuple[int, int]:
            filename = item[0]
            match = re.search(r"-(\d+)\.(webp|avif)$", filename)
            if not match:
                raise RuntimeError("Stored owner Hero derivative filename is invalid.")
            return int(match.group(1)), 0 if match.group(2) == "webp" else 1

        for _filename, storage_key in sorted(existing_derivatives.items(), key=derivative_order):
            content = await asyncio.to_thread(storage.read, storage_key)
            with Image.open(io.BytesIO(content)) as image:
                width, height = image.size
                image_format = image.format.casefold()
            cached_manifest.append(
                {
                    "format": image_format,
                    "mime_type": f"image/{image_format}",
                    "width": width,
                    "height": height,
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "storage_key": storage_key,
                }
            )
        return master_key, cached_manifest
    manifest: list[dict[str, object]] = []
    for derivative in await asyncio.to_thread(responsive_derivatives, raster):
        filename = f"{Path(asset.filename).stem}-{derivative.width}.{derivative.format}"
        storage_key = await storage.save_owner_hero_media(
            derivative.content,
            normalized_filename=filename,
            namespace="owner-hero-responsive",
        )
        manifest.append(
            {
                "format": derivative.format,
                "mime_type": derivative.mime_type,
                "width": derivative.width,
                "height": derivative.height,
                "size_bytes": derivative.size_bytes,
                "sha256": derivative.sha256,
                "storage_key": storage_key,
            }
        )
    return master_key, manifest


async def _write_preview_permission(
    db: AsyncSession,
    media: ProjectMedia,
    actor_id: uuid.UUID,
    known_permissions: set[tuple[uuid.UUID, str]],
) -> bool:
    version = asset_version(media)
    if (media.id, version) in known_permissions:
        return False
    await write_audit(
        db,
        action=APPROVE,
        entity_type="project_media",
        entity_id=media.id,
        actor_user_id=actor_id,
        correlation_id=f"owner-hero:{media.project_id}",
        metadata={
            "version": VERSION,
            "scope": "authenticated-preview-only",
            "project_id": str(media.project_id),
            "asset_version": version,
            "authorization_reference": OWNER_HERO_AUTHORIZATION,
        },
    )
    known_permissions.add((media.id, version))
    return True


async def import_and_assign_owner_heroes(
    db: AsyncSession,
    settings: Settings,
    directory: Path,
    *,
    actor_id: uuid.UUID,
) -> dict[str, Any]:
    assets = await validate_owner_hero_directory(directory)
    projects = (
        (
            await db.scalars(
                select(Project)
                .where(Project.emirate.in_((UAEEmirate.RAS_AL_KHAIMAH, UAEEmirate.SHARJAH)))
                .options(
                    selectinload(Project.area),
                    selectinload(Project.translations),
                    selectinload(Project.property_types),
                    selectinload(Project.bedroom_options),
                    selectinload(Project.unit_types),
                    selectinload(Project.media),
                )
                .order_by(Project.id)
            )
        )
        .unique()
        .all()
    )
    if len(projects) != 204:
        raise ValueError(f"Expected exactly 204 RAK/Sharjah Projects, found {len(projects)}.")
    storage = PrivateStorage(settings)
    permission_rows = (
        await db.execute(
            select(AuditLog.entity_id, AuditLog.metadata_summary).where(
                AuditLog.entity_type == "project_media",
                AuditLog.action == APPROVE,
                AuditLog.outcome == "success",
            )
        )
    ).all()
    known_permissions = {
        (entity_id, str(metadata["asset_version"]))
        for entity_id, metadata in permission_rows
        if entity_id and isinstance(metadata, dict) and metadata.get("asset_version")
    }
    bundles: dict[str, tuple[str, list[dict[str, object]]]] = {}
    for asset in assets:
        bundles[asset.filename] = await _asset_bundle(storage, asset)

    now = datetime.now(UTC)
    changed = 0
    receipts = 0
    tanami_demoted = 0
    conceptual_private = 0
    assignments: list[dict[str, object]] = []
    for project in projects:
        pool = project_hero_pool(project)
        asset = select_owner_hero_asset(project.id, pool, assets)
        source_url = f"{OWNER_HERO_SOURCE_PREFIX}{asset.filename}"
        master_key, derivative_manifest = bundles[asset.filename]
        existing = next((item for item in project.media if item.source_url == source_url), None)
        target = existing or ProjectMedia(project_id=project.id, source_url=source_url)
        if not existing:
            project.media.append(target)
        before_version = asset_version(target) if existing else None

        metadata = _metadata(project, pool)
        tags = metadata["tags"]
        if not isinstance(tags, list):
            raise RuntimeError("Owner Hero metadata tags are invalid.")
        desired: dict[str, object] = {
            "category": ProjectMediaCategory.COVER,
            "rights_status": MediaRightsStatus.APPROVED,
            "alt_en": str(metadata["alt_en"]),
            "alt_ar": str(metadata["alt_ar"]),
            "title_en": str(metadata["title_en"]),
            "title_ar": str(metadata["title_ar"]),
            "description_en": str(metadata["description_en"]),
            "description_ar": str(metadata["description_ar"]),
            "tags": [str(value) for value in tags],
            "display_order": 0,
            "storage_key": master_key,
            "original_filename": asset.filename,
            "mime_type": "image/webp",
            "size_bytes": len(asset.content),
            "sha256": asset.sha256,
            "width": asset.width,
            "height": asset.height,
            "verified_at": target.verified_at or now,
            "uploaded_by": actor_id,
            "derivative_manifest": derivative_manifest,
            "private_provenance": {
                "origin": "owner-created-aliyas-hero-media",
                "source_filename": asset.filename,
                "source_sha256": asset.sha256,
                "asset_category": asset.category,
                "assignment_pool": pool,
                "usage": "project-hero-only",
                "exact_project_render": False,
                "authorization_reference": OWNER_HERO_AUTHORIZATION,
            },
        }
        target_changed = not existing or any(
            getattr(target, key) != value for key, value in desired.items()
        )
        if target_changed:
            for key, value in desired.items():
                setattr(target, key, value)

        for item in project.media:
            if item is target or item.category != ProjectMediaCategory.COVER:
                continue
            if is_tanami_native_media_source(item.source_url):
                item.category = ProjectMediaCategory.GALLERY
                item.display_order = 0
                tanami_demoted += 1
                await db.flush()
                await db.refresh(item)
                receipts += int(
                    await _write_preview_permission(db, item, actor_id, known_permissions)
                )
            else:
                if item.rights_status != MediaRightsStatus.PENDING:
                    item.rights_status = MediaRightsStatus.PENDING
                    conceptual_private += 1
                    await write_audit(
                        db,
                        action=REVOKE,
                        entity_type="project_media",
                        entity_id=item.id,
                        actor_user_id=actor_id,
                        correlation_id=f"owner-hero:{project.id}",
                        metadata={
                            "scope": "authenticated-preview-only",
                            "reason": "Superseded by owner-created exclusive Project Hero",
                            "project_id": str(project.id),
                        },
                    )

        await db.flush()
        if target_changed:
            await db.refresh(target)
        after_version = asset_version(target)
        if before_version != after_version:
            changed += 1
            await write_audit(
                db,
                action=OWNER_HERO_ACTION,
                entity_type="project_media",
                entity_id=target.id,
                actor_user_id=actor_id,
                correlation_id=f"owner-hero:{project.id}",
                after={
                    "project_id": str(project.id),
                    "asset_filename": asset.filename,
                    "asset_sha256": asset.sha256,
                    "assignment_pool": pool,
                },
            )
        receipts += int(await _write_preview_permission(db, target, actor_id, known_permissions))
        assignments.append(
            {
                "project_id": str(project.id),
                "slug": project.slug,
                "pool": pool,
                "asset": asset.filename,
                "sha256": asset.sha256,
            }
        )
    await db.commit()
    return {
        "assets": len(assets),
        "projects": len(projects),
        "assignments_changed": changed,
        "preview_receipts_created": receipts,
        "tanami_covers_demoted": tanami_demoted,
        "conceptual_covers_made_private": conceptual_private,
        "assignments": assignments,
    }
