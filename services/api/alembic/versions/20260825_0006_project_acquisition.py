"""Add private official-source acquisition evidence and idempotent import fields.

Revision ID: 20260825_0006
Revises: 20260825_0005
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0006"
down_revision: str | None = "20260825_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade() -> None:
    op.add_column(
        "project_import_batches", sa.Column("manifest_hash", sa.String(64), nullable=False)
    )
    op.add_column(
        "project_import_batches", sa.Column("adapter_version", sa.String(32), nullable=False)
    )
    op.create_unique_constraint(
        "uq_project_import_batches_manifest_hash", "project_import_batches", ["manifest_hash"]
    )
    op.add_column(
        "project_import_candidates", sa.Column("manifest_row_id", sa.Integer(), nullable=False)
    )
    op.add_column("project_import_candidates", sa.Column("adapter_key", sa.String(80)))
    op.add_column("project_import_candidates", sa.Column("adapter_version", sa.String(32)))
    op.add_column(
        "project_import_candidates",
        sa.Column("last_verified_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "project_import_candidates",
        sa.Column("arabic_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "project_import_candidates",
        sa.Column(
            "acquisition_summary",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_unique_constraint(
        "uq_project_import_candidate_manifest_row",
        "project_import_candidates",
        ["batch_id", "manifest_row_id"],
    )
    source_type = postgresql.ENUM(name="project_source_type", create_type=False)
    media_category = postgresql.ENUM(name="project_media_category", create_type=False)
    media_rights = postgresql.ENUM(name="media_rights_status", create_type=False)
    op.create_table(
        "project_source_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("http_status", sa.Integer()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("adapter_key", sa.String(80), nullable=False),
        sa.Column("adapter_version", sa.String(32), nullable=False),
        sa.Column("content_type", sa.String(160)),
        sa.Column("etag", sa.String(320)),
        sa.Column("last_modified", sa.String(320)),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(180), unique=True),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_message", sa.String(500)),
        *timestamps(),
        sa.UniqueConstraint("candidate_id", "source_url", "content_hash"),
    )
    op.create_index(
        "ix_project_source_snapshots_candidate", "project_source_snapshots", ["candidate_id"]
    )
    op.create_table(
        "project_import_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_source_snapshots.id", ondelete="SET NULL"),
        ),
        sa.Column("category", media_category, nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("rights_status", media_rights, nullable=False, server_default="PENDING"),
        sa.Column("stage_status", sa.String(40), nullable=False),
        sa.Column("storage_key", sa.String(180), unique=True),
        sa.Column("mime_type", sa.String(80)),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column(
            "duplicate_of_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_media.id"),
        ),
        *timestamps(),
        sa.UniqueConstraint("candidate_id", "source_url"),
    )
    op.create_index("ix_project_import_media_candidate", "project_import_media", ["candidate_id"])
    op.create_table(
        "project_import_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("classification", sa.String(40), nullable=False),
        sa.Column("existing_value", postgresql.JSONB()),
        sa.Column("new_value", postgresql.JSONB()),
        sa.Column("source_url", sa.Text()),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        *timestamps(),
    )
    op.create_index(
        "ix_project_import_changes_candidate", "project_import_changes", ["candidate_id"]
    )


def downgrade() -> None:
    op.drop_table("project_import_changes")
    op.drop_table("project_import_media")
    op.drop_table("project_source_snapshots")
    op.drop_constraint(
        "uq_project_import_candidate_manifest_row", "project_import_candidates", type_="unique"
    )
    for column in (
        "acquisition_summary",
        "arabic_review_required",
        "last_verified_at",
        "adapter_version",
        "adapter_key",
        "manifest_row_id",
    ):
        op.drop_column("project_import_candidates", column)
    op.drop_constraint(
        "uq_project_import_batches_manifest_hash", "project_import_batches", type_="unique"
    )
    op.drop_column("project_import_batches", "adapter_version")
    op.drop_column("project_import_batches", "manifest_hash")
