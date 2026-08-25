"""Prepare controlled acquisition identity, editorial and media review.

Revision ID: 20260825_0010
Revises: 20260825_0009
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0010"
down_revision: str | None = "20260825_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    developer_verification = postgresql.ENUM(
        "PENDING",
        "VERIFIED",
        "REJECTED",
        name="developer_verification_status",
        create_type=False,
    )
    editorial_approval = postgresql.ENUM(
        "NOT_GENERATED",
        "NEEDS_REVIEW",
        "APPROVED",
        "REJECTED",
        name="editorial_approval_status",
        create_type=False,
    )
    developer_verification.create(op.get_bind(), checkfirst=True)
    editorial_approval.create(op.get_bind(), checkfirst=True)

    op.add_column("developers", sa.Column("legal_name", sa.String(320)))
    op.add_column("developers", sa.Column("source_name", sa.String(320)))
    op.add_column(
        "developers",
        sa.Column("internal_aliases", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "developers",
        sa.Column(
            "verification_status",
            developer_verification,
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.execute("UPDATE developers SET verification_status = 'VERIFIED' WHERE status = 'PUBLISHED'")
    op.create_index("ix_developers_source_name", "developers", ["source_name"])

    op.add_column(
        "project_import_candidates",
        sa.Column("human_edited_fields", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("project_source_snapshots", sa.Column("size_bytes", sa.Integer()))
    op.add_column("project_import_changes", sa.Column("field_name", sa.String(120)))

    op.create_table(
        "project_import_editorial_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("overview_en", sa.Text()),
        sa.Column("overview_ar", sa.Text()),
        sa.Column("source_version", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(160)),
        sa.Column("model_version", sa.String(160)),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "approval_status",
            editorial_approval,
            nullable=False,
            server_default="NOT_GENERATED",
        ),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    for column in (
        sa.Column("raw_storage_key", sa.String(180), unique=True),
        sa.Column("normalized_filename", sa.String(255)),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alt_en_draft", sa.String(320)),
        sa.Column("alt_ar_draft", sa.String(320)),
        sa.Column("derivative_manifest", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("change_status", sa.String(40), nullable=False, server_default="newly-added"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
    ):
        op.add_column("project_import_media", column)


def downgrade() -> None:
    for column in (
        "last_seen_at",
        "change_status",
        "derivative_manifest",
        "alt_ar_draft",
        "alt_en_draft",
        "display_order",
        "normalized_filename",
        "raw_storage_key",
    ):
        op.drop_column("project_import_media", column)
    op.drop_table("project_import_editorial_drafts")
    op.drop_column("project_import_changes", "field_name")
    op.drop_column("project_source_snapshots", "size_bytes")
    op.drop_column("project_import_candidates", "human_edited_fields")
    op.drop_index("ix_developers_source_name", table_name="developers")
    op.drop_column("developers", "verification_status")
    op.drop_column("developers", "internal_aliases")
    op.drop_column("developers", "source_name")
    op.drop_column("developers", "legal_name")
    postgresql.ENUM(name="editorial_approval_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="developer_verification_status").drop(op.get_bind(), checkfirst=True)
