"""Prevent duplicate media links within one Project.

Revision ID: 20260830_0017
Revises: 20260830_0016
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260830_0017"
down_revision: str | None = "20260830_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_project_media_project_source", "project_media", ["project_id", "source_url"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_project_media_project_source", "project_media", type_="unique")
