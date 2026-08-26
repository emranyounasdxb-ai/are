"""Allow truthful unresolved Project availability in Draft records.

Revision ID: 20260826_0014
Revises: 20260826_0013
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260826_0014"
down_revision: str | None = "20260826_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE project_availability_status ADD VALUE IF NOT EXISTS 'NOT_CONFIRMED'")


def downgrade() -> None:
    previous = postgresql.ENUM(
        "AVAILABLE",
        "LIMITED_AVAILABILITY",
        "SOLD_OUT",
        "COMING_SOON",
        name="project_availability_status_previous",
    )
    previous.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE projects ALTER COLUMN availability_status "
        "TYPE project_availability_status_previous "
        "USING availability_status::text::project_availability_status_previous"
    )
    op.execute("DROP TYPE project_availability_status")
    op.execute(
        "ALTER TYPE project_availability_status_previous RENAME TO project_availability_status"
    )
