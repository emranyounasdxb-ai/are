"""Add the developer CMS and import the approved public directory.

Revision ID: 20260824_0003
Revises: 20260824_0002
Create Date: 2026-08-24
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260824_0003"
down_revision: str | None = "20260824_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SUPER_ADMIN_ROLE_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
DEVELOPER_PERMISSION_ID = uuid.UUID("20000000-0000-4000-8000-000000000019")
SEED_NAMESPACE = uuid.UUID("6cfcac30-ec7e-46f6-aa91-af049e02bdf1")


def approved_developers() -> list[dict[str, Any]]:
    source = Path(__file__).resolve().parents[2] / "app" / "content" / "approved_developers.json"
    return list(json.loads(source.read_text(encoding="utf-8")))


def upgrade() -> None:
    publication_status = postgresql.ENUM(
        "DRAFT", "PUBLISHED", "ARCHIVED", name="publication_status", create_type=False
    )
    op.create_table(
        "developers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("primary_emirate", sa.String(120), nullable=False),
        sa.Column("other_presence", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("selected_projects", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("official_website", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "additional_source_urls", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("verification_date", sa.Date(), nullable=False),
        sa.Column("enquiry_types", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", publication_status, nullable=False, server_default="DRAFT"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_developers_status", "developers", ["status"])
    op.create_index("ix_developers_search", "developers", ["slug", "primary_emirate", "featured"])
    op.create_table(
        "developer_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "developer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("developers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("focus", sa.Text(), nullable=False),
        sa.Column("verification_note", sa.Text(), nullable=False),
        sa.UniqueConstraint("developer_id", "locale"),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_developer_translation_locale"),
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    op.execute(
        postgresql.insert(permissions)
        .values(id=DEVELOPER_PERMISSION_ID, code="developers.manage")
        .on_conflict_do_nothing(index_elements=["code"])
    )
    op.execute(
        postgresql.insert(role_permissions)
        .values(role_id=SUPER_ADMIN_ROLE_ID, permission_id=DEVELOPER_PERMISSION_ID)
        .on_conflict_do_nothing(index_elements=["role_id", "permission_id"])
    )

    developers = sa.table(
        "developers",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String()),
        sa.column("primary_emirate", sa.String()),
        sa.column("other_presence", postgresql.JSONB()),
        sa.column("selected_projects", postgresql.JSONB()),
        sa.column("official_website", sa.Text()),
        sa.column("source_url", sa.Text()),
        sa.column("additional_source_urls", postgresql.JSONB()),
        sa.column("verification_date", sa.Date()),
        sa.column("enquiry_types", postgresql.JSONB()),
        sa.column("featured", sa.Boolean()),
        sa.column("display_order", sa.Integer()),
        sa.column("status", publication_status),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )
    translations = sa.table(
        "developer_translations",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("developer_id", postgresql.UUID(as_uuid=True)),
        sa.column("locale", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("focus", sa.Text()),
        sa.column("verification_note", sa.Text()),
    )
    verified_at = datetime.fromisoformat("2026-08-24T00:00:00+00:00")
    for display_order, item in enumerate(approved_developers(), start=1):
        developer_id = uuid.uuid5(SEED_NAMESPACE, item["slug"])
        op.execute(
            postgresql.insert(developers)
            .values(
                id=developer_id,
                slug=item["slug"],
                primary_emirate=item["primaryEmirate"],
                other_presence=item["otherPresence"],
                selected_projects=item["selectedProjects"],
                official_website=item["officialWebsite"],
                source_url=item["governmentSourceUrl"],
                additional_source_urls=item["additionalOfficialSourceUrls"],
                verification_date=date.fromisoformat(item["lastVerified"]),
                enquiry_types=item["enquiryTypes"],
                featured=False,
                display_order=display_order,
                status="PUBLISHED",
                published_at=verified_at,
            )
            .on_conflict_do_nothing(index_elements=["slug"])
        )
        for locale in ("en", "ar"):
            op.execute(
                postgresql.insert(translations)
                .values(
                    id=uuid.uuid5(SEED_NAMESPACE, f"{item['slug']}:{locale}"),
                    developer_id=developer_id,
                    locale=locale,
                    name=item.get("officialArabicName", item["officialName"])
                    if locale == "ar"
                    else item["officialName"],
                    description=item["description"][locale],
                    focus=item["focus"][locale],
                    verification_note=item.get("note", {locale: ""})[locale],
                )
                .on_conflict_do_nothing(index_elements=["developer_id", "locale"])
            )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE role_id = :role_id AND permission_id = :permission_id"
        ).bindparams(role_id=SUPER_ADMIN_ROLE_ID, permission_id=DEVELOPER_PERMISSION_ID)
    )
    op.execute(
        sa.text("DELETE FROM permissions WHERE id = :permission_id").bindparams(
            permission_id=DEVELOPER_PERMISSION_ID
        )
    )
    op.drop_table("developer_translations")
    op.drop_table("developers")
