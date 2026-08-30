"""Support shared private owner-created Project Hero media.

Revision ID: 20260830_0016
Revises: 20260829_0015
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260830_0016"
down_revision: str | None = "20260829_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("project_media_storage_key_key", "project_media", type_="unique")
    op.add_column("project_media", sa.Column("title_en", sa.String(240)))
    op.add_column("project_media", sa.Column("title_ar", sa.String(240)))
    op.add_column("project_media", sa.Column("description_en", sa.String(500)))
    op.add_column("project_media", sa.Column("description_ar", sa.String(500)))
    op.add_column(
        "project_media",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "project_media",
        sa.Column(
            "derivative_manifest",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "project_media",
        sa.Column(
            "private_provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("project_media", "private_provenance")
    op.drop_column("project_media", "derivative_manifest")
    op.drop_column("project_media", "tags")
    op.drop_column("project_media", "description_ar")
    op.drop_column("project_media", "description_en")
    op.drop_column("project_media", "title_ar")
    op.drop_column("project_media", "title_en")
    op.create_unique_constraint("project_media_storage_key_key", "project_media", ["storage_key"])
