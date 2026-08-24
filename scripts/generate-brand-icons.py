"""Derive web icons from the approved ALIYAS architectural A monogram."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "brand-source" / "aliyas-real-estate-logo-candidate.png"
TARGETS = [ROOT / "apps" / "public-web" / "app", ROOT / "apps" / "admin-web" / "app"]
MONOGRAM_CROP = (749, 300, 2135, 1686)


def main() -> None:
    with Image.open(SOURCE) as source:
        monogram = source.convert("RGBA").crop(MONOGRAM_CROP)
        standard = monogram.resize((512, 512), Image.Resampling.LANCZOS)
        apple = monogram.resize((180, 180), Image.Resampling.LANCZOS)
        for target in TARGETS:
            target.mkdir(parents=True, exist_ok=True)
            standard.save(target / "icon.png", optimize=True)
            apple.save(target / "apple-icon.png", optimize=True)
            standard.save(target / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == "__main__":
    main()
