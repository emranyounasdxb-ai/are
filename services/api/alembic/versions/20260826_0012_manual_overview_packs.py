"""Add private manual Codex-assisted Overview packs.

Revision ID: 20260826_0012
Revises: 20260825_0011
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260826_0012"
down_revision: str | None = "20260825_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_ID = uuid.UUID("20000000-0000-4000-8000-000000000037")
PERMISSION_CODE = "project-overview-pack.manage"


def upgrade() -> None:
    op.create_table(
        "project_overview_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pack_version", sa.String(40), nullable=False),
        sa.Column("selection_mode", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("storage_key", sa.String(180), nullable=False, unique=True),
        sa.Column("pack_hash", sa.String(64), nullable=False),
        sa.Column("selected_count", sa.Integer(), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False),
        sa.Column("ineligible_count", sa.Integer(), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("import_correlation_id", sa.String(120)),
        sa.Column("imported_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("created_by", "idempotency_key"),
    )
    op.create_index("ix_project_overview_packs_batch_id", "project_overview_packs", ["batch_id"])
    op.create_index("ix_project_overview_packs_status", "project_overview_packs", ["status"])
    op.create_table(
        "project_overview_pack_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "pack_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_overview_packs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("candidate_version", sa.Integer(), nullable=False),
        sa.Column("fact_input_version", sa.String(40), nullable=False),
        sa.Column("fact_input_hash", sa.String(64)),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("exclusion_reasons", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("failure_code", sa.String(100)),
        sa.Column("failure_message", sa.String(1000)),
        sa.Column(
            "referenced_fact_fields", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("editorial_notes", sa.String(1000)),
        sa.Column("imported_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("pack_id", "candidate_id"),
    )
    op.create_index(
        "ix_project_overview_pack_items_candidate_id",
        "project_overview_pack_items",
        ["candidate_id"],
    )
    op.create_index(
        "ix_project_overview_pack_items_status", "project_overview_pack_items", ["status"]
    )
    op.add_column("project_import_editorial_drafts", sa.Column("origin", sa.String(40)))
    op.add_column(
        "project_import_editorial_drafts",
        sa.Column(
            "overview_pack_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_overview_packs.id", ondelete="SET NULL"),
        ),
    )
    op.add_column("project_import_editorial_drafts", sa.Column("fact_input_hash", sa.String(64)))
    op.add_column("project_import_editorial_drafts", sa.Column("candidate_version", sa.Integer()))
    op.add_column(
        "project_import_editorial_drafts", sa.Column("import_correlation_id", sa.String(120))
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO permissions (id, code) VALUES (:id, :code) ON CONFLICT (code) DO NOTHING"
        ),
        {"id": PERMISSION_ID, "code": PERMISSION_CODE},
    )
    super_admin_id = connection.execute(
        sa.text("SELECT id FROM roles WHERE slug = 'super-admin'")
    ).scalar()
    if super_admin_id:
        connection.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "VALUES (:role_id, :permission_id) ON CONFLICT DO NOTHING"
            ),
            {"role_id": super_admin_id, "permission_id": PERMISSION_ID},
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM role_permissions WHERE permission_id = :id"), {"id": PERMISSION_ID}
    )
    connection.execute(sa.text("DELETE FROM permissions WHERE id = :id"), {"id": PERMISSION_ID})
    for column in (
        "import_correlation_id",
        "candidate_version",
        "fact_input_hash",
        "overview_pack_id",
        "origin",
    ):
        op.drop_column("project_import_editorial_drafts", column)
    op.drop_index("ix_project_overview_pack_items_status", table_name="project_overview_pack_items")
    op.drop_index(
        "ix_project_overview_pack_items_candidate_id", table_name="project_overview_pack_items"
    )
    op.drop_table("project_overview_pack_items")
    op.drop_index("ix_project_overview_packs_status", table_name="project_overview_packs")
    op.drop_index("ix_project_overview_packs_batch_id", table_name="project_overview_packs")
    op.drop_table("project_overview_packs")
