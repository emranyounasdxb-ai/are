from __future__ import annotations

import asyncio
import getpass
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models import InsightPost, InsightPostTranslation, PublicationStatus, Role, User
from app.security import hash_password


async def _create_super_admin(email: str, display_name: str, password: str) -> None:
    async with SessionLocal() as db:
        normalized = email.strip().lower()
        if await db.scalar(select(User).where(User.email == normalized)):
            raise SystemExit("A user with that email already exists.")
        role = await db.scalar(
            select(Role).where(Role.slug == "super-admin").options(selectinload(Role.permissions))
        )
        if not role:
            raise SystemExit("Run database migrations before creating the first Super Admin.")
        user = User(
            email=normalized,
            display_name=display_name.strip(),
            password_hash=hash_password(password),
            roles=[role],
        )
        db.add(user)
        await db.commit()
        print("Super Admin created. No password was printed or written to disk.")


def create_super_admin() -> None:
    email = input("Email: ").strip()
    display_name = input("Display name: ").strip()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if len(password) < 14:
        raise SystemExit("Use at least 14 characters.")
    asyncio.run(_create_super_admin(email, display_name, password))


async def _seed_insights(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    async with SessionLocal() as db:
        for item in payload:
            record = await db.scalar(
                select(InsightPost)
                .where(InsightPost.slug == item["slug"])
                .options(selectinload(InsightPost.translations))
            )
            if not record:
                record = InsightPost(
                    slug=item["slug"],
                    category=item["category"],
                    author_display_name="ALIYAS Real Estate",
                    source_links=item["sources"],
                    status=PublicationStatus.PUBLISHED,
                    published_at=datetime.fromisoformat(item["published"]).replace(tzinfo=UTC),
                )
                record.translations = []
                db.add(record)
                await db.flush()
            else:
                record.category = item["category"]
                record.source_links = item["sources"]
                record.status = PublicationStatus.PUBLISHED
            by_locale = {translation.locale: translation for translation in record.translations}
            for locale, content in item["content"].items():
                translation = by_locale.get(locale) or InsightPostTranslation(
                    insight_post_id=record.id, locale=locale
                )
                translation.title = content["title"]
                translation.excerpt = content["metaDescription"]
                translation.body = content
                translation.seo_title = content["title"]
                translation.seo_description = content["metaDescription"]
                if translation not in record.translations:
                    record.translations.append(translation)
        await db.commit()
    print(f"Seeded {len(payload)} approved bilingual insight records idempotently.")


def seed_insights() -> None:
    default = Path(__file__).parent / "content" / "approved_insights.json"
    path = Path(os.environ.get("ARE_APPROVED_INSIGHTS_PATH", str(default)))
    asyncio.run(_seed_insights(path))
