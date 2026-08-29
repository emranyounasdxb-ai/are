"""Persist DOM-aware Tanami media classification evidence.

Revision ID: 20260829_0015
Revises: 20260826_0014
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260829_0015"
down_revision: str | None = "20260826_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project_import_media",
        sa.Column(
            "discovery_manifest",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("project_import_media", "discovery_manifest")
