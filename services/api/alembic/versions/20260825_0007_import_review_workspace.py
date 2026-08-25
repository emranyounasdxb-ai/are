"""Add safe import review state and private media metadata.

Revision ID: 20260825_0007
Revises: 20260825_0006
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0007"
down_revision: str | None = "20260825_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "projects", "priority", existing_type=sa.Enum(name="project_priority"), nullable=True
    )
    op.add_column(
        "project_import_candidates",
        sa.Column("review_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "project_import_candidates",
        sa.Column(
            "human_review_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column("project_import_candidates", sa.Column("rejection_reason", sa.String(1000)))
    op.add_column("project_import_media", sa.Column("thumbnail_storage_key", sa.String(180)))
    op.create_unique_constraint(
        "uq_project_import_media_thumbnail_storage_key",
        "project_import_media",
        ["thumbnail_storage_key"],
    )
    op.add_column("project_import_media", sa.Column("retrieved_at", sa.DateTime(timezone=True)))
    op.add_column("project_import_media", sa.Column("failure_reason", sa.String(500)))
    op.create_table(
        "project_import_bulk_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("batch_id", "idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("project_import_bulk_operations")
    op.drop_column("project_import_media", "failure_reason")
    op.drop_column("project_import_media", "retrieved_at")
    op.drop_constraint(
        "uq_project_import_media_thumbnail_storage_key", "project_import_media", type_="unique"
    )
    op.drop_column("project_import_media", "thumbnail_storage_key")
    op.drop_column("project_import_candidates", "rejection_reason")
    op.drop_column("project_import_candidates", "human_review_completed")
    op.drop_column("project_import_candidates", "review_version")
    op.alter_column(
        "projects", "priority", existing_type=sa.Enum(name="project_priority"), nullable=False
    )
