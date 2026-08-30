import hashlib
import io
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from app.acquisition.owner_hero_banners import (
    EXPECTED_CATEGORIES,
    OwnerHeroAsset,
    project_hero_pool,
    select_owner_hero_asset,
    validate_owner_hero_directory,
)
from app.models import ProjectBedroomOption, ProjectPropertyType


def _webp(color: tuple[int, int, int]) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (400, 200), color).save(output, "WEBP", lossless=True)
    return output.getvalue()


@pytest.mark.asyncio
async def test_owner_hero_gate_accepts_exact_unique_contiguous_2_to_1_pack(tmp_path: Path):
    counts = {category: 3 for category in EXPECTED_CATEGORIES}
    counts["happy-family-living-room"] = 5
    counts["luxury-apartment"] = 6
    counts["luxury-villa"] = 4
    counts["mixed-residential"] = 2
    assert sum(counts.values()) == 65
    color = 1
    for category, count in sorted(counts.items()):
        for index in range(1, count + 1):
            (tmp_path / f"are-hero-{category}-{index:02d}.webp").write_bytes(
                _webp((color, (color * 3) % 255, (color * 7) % 255))
            )
            color += 1

    assets = await validate_owner_hero_directory(tmp_path)

    assert len(assets) == 65
    assert len({asset.sha256 for asset in assets}) == 65
    assert {(asset.width, asset.height) for asset in assets} == {(400, 200)}


@pytest.mark.asyncio
async def test_owner_hero_gate_rejects_non_2_to_1_asset(tmp_path: Path):
    (tmp_path / "are-hero-hotel-01.webp").write_bytes(_webp((1, 2, 3)))
    with pytest.raises(ValueError, match="exactly 65"):
        await validate_owner_hero_directory(tmp_path)


def _project(
    *types: ProjectPropertyType,
    name: str = "Project",
    area: str = "Sharjah",
    units: tuple[str, ...] = (),
    bedrooms: tuple[ProjectBedroomOption, ...] = (),
):
    return SimpleNamespace(
        slug="project",
        translations=[SimpleNamespace(locale="en", official_name=name)],
        area=SimpleNamespace(name_en=area),
        property_types=[SimpleNamespace(property_type=value) for value in types],
        unit_types=[SimpleNamespace(label_en=value) for value in units],
        bedroom_options=[SimpleNamespace(bedroom_option=value) for value in bedrooms],
    )


@pytest.mark.parametrize(
    ("project", "expected"),
    [
        (_project(ProjectPropertyType.APARTMENT, name="Address Residences"), "hotel-branded"),
        (_project(ProjectPropertyType.OTHER, units=("Office",)), "office-commercial"),
        (_project(ProjectPropertyType.RESIDENTIAL_PLOT), "land-community"),
        (_project(ProjectPropertyType.APARTMENT, area="Al Marjan Island"), "waterfront-resort"),
        (_project(ProjectPropertyType.PENTHOUSE), "penthouse"),
        (_project(ProjectPropertyType.DUPLEX), "duplex-loft"),
        (_project(ProjectPropertyType.VILLA), "villa"),
        (_project(ProjectPropertyType.TOWNHOUSE), "townhouse"),
        (_project(ProjectPropertyType.APARTMENT), "apartment-urban"),
        (_project(ProjectPropertyType.OTHER, bedrooms=(ProjectBedroomOption.FIVE,)), "family"),
        (_project(ProjectPropertyType.OTHER, ProjectPropertyType.MANSION), "villa"),
        (_project(ProjectPropertyType.OTHER), "neutral-luxury"),
    ],
)
def test_project_hero_pool_uses_priority_order_and_verified_facts(project, expected):
    assert project_hero_pool(project) == expected


def test_project_id_rotation_is_stable():
    assets = tuple(
        OwnerHeroAsset(
            Path(f"are-hero-hotel-0{index}.webp"),
            f"are-hero-hotel-0{index}.webp",
            "hotel",
            index,
            bytes([index]),
            hashlib.sha256(bytes([index])).hexdigest(),
            400,
            200,
        )
        for index in range(1, 4)
    )
    project_id = uuid.UUID("2db803a6-e13c-4aac-bb89-b00b827dbab5")
    first = select_owner_hero_asset(project_id, "hotel-branded", assets)
    second = select_owner_hero_asset(project_id, "hotel-branded", tuple(reversed(assets)))
    assert first == second
