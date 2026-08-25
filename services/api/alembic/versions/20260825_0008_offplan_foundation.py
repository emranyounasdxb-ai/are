"""Complete the empty Off-Plan project foundation.

Revision ID: 20260825_0008
Revises: 20260825_0007
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0008"
down_revision: str | None = "20260825_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    workflow = postgresql.ENUM("DRAFT", "IN_REVIEW", "APPROVED", name="project_workflow_status")
    size_unit = postgresql.ENUM("SQFT", "SQM", name="project_size_unit")
    workflow.create(op.get_bind(), checkfirst=True)
    size_unit.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "projects",
        sa.Column(
            "workflow_status",
            workflow,
            nullable=False,
            server_default="DRAFT",
        ),
    )
    op.create_index("ix_projects_workflow_status", "projects", ["workflow_status"])
    op.add_column("projects", sa.Column("size_min", sa.Numeric(12, 2)))
    op.add_column("projects", sa.Column("size_max", sa.Numeric(12, 2)))
    op.add_column("projects", sa.Column("size_unit", size_unit))
    op.add_column("projects", sa.Column("down_payment_percentage", sa.Numeric(5, 2)))
    op.add_column("projects", sa.Column("down_payment_source_value", sa.String(500)))
    op.add_column("projects", sa.Column("latitude", sa.Numeric(9, 6)))
    op.add_column("projects", sa.Column("longitude", sa.Numeric(9, 6)))
    for table_name, name_column in (
        ("project_unit_types", "label_en"),
        ("project_amenities", "label_en"),
    ):
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "project_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("label_en", sa.String(160), nullable=False),
            sa.Column("label_ar", sa.String(160)),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("project_id", name_column),
        )
    op.create_table(
        "project_nearby_places",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("name_ar", sa.String(200)),
        sa.Column("distance_value", sa.Numeric(8, 2)),
        sa.Column("distance_unit", sa.String(20)),
        sa.Column("travel_time_minutes", sa.Integer()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("project_id", "name_en"),
    )


def downgrade() -> None:
    op.drop_table("project_nearby_places")
    op.drop_table("project_amenities")
    op.drop_table("project_unit_types")
    for column in (
        "longitude",
        "latitude",
        "down_payment_source_value",
        "down_payment_percentage",
        "size_unit",
        "size_max",
        "size_min",
    ):
        op.drop_column("projects", column)
    op.drop_index("ix_projects_workflow_status", table_name="projects")
    op.drop_column("projects", "workflow_status")
    postgresql.ENUM(name="project_size_unit").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="project_workflow_status").drop(op.get_bind(), checkfirst=True)
