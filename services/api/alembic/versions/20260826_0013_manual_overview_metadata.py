"""Complete manual Overview pack provenance metadata.

Revision ID: 20260826_0013
Revises: 20260826_0012
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260826_0013"
down_revision: str | None = "20260826_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("project_import_editorial_drafts", sa.Column("overview_pack_hash", sa.String(64)))
    op.add_column("project_import_editorial_drafts", sa.Column("fact_input_version", sa.String(40)))


def downgrade() -> None:
    op.drop_column("project_import_editorial_drafts", "fact_input_version")
    op.drop_column("project_import_editorial_drafts", "overview_pack_hash")
