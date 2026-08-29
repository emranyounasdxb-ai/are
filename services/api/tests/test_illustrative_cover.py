import hashlib
import io

from PIL import Image

from app.acquisition.illustrative_cover import render_concept_cover
from app.acquisition.media import responsive_derivatives, validate_raster


def test_project_seed_produces_unique_clean_landscape_cover_and_derivatives():
    first_seed = hashlib.sha256(b"project-one").hexdigest()
    second_seed = hashlib.sha256(b"project-two").hexdigest()
    first = render_concept_cover(first_seed)
    second = render_concept_cover(second_seed)

    assert first != second
    raster = validate_raster(first, "image/webp")
    assert (raster.width, raster.height) == (1920, 1080)
    assert raster.sha256 == hashlib.sha256(raster.content).hexdigest()
    with Image.open(io.BytesIO(raster.content)) as image:
        assert not image.getexif()
    derivatives = responsive_derivatives(raster)
    assert {item.format for item in derivatives} == {"webp", "avif"}
    assert {item.width for item in derivatives} == {480, 960, 1600}
