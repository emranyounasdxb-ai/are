"""Add durable Project preparation jobs, diagnostics and revisions.

Revision ID: 20260825_0011
Revises: 20260825_0010
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0011"
down_revision: str | None = "20260825_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "project-processing.run": uuid.UUID("20000000-0000-4000-8000-000000000031"),
    "project-processing.recover": uuid.UUID("20000000-0000-4000-8000-000000000032"),
    "project-editorial.approve": uuid.UUID("20000000-0000-4000-8000-000000000033"),
    "project-media.approve": uuid.UUID("20000000-0000-4000-8000-000000000034"),
    "project-revision.approve": uuid.UUID("20000000-0000-4000-8000-000000000035"),
    "project-revision.rollback": uuid.UUID("20000000-0000-4000-8000-000000000036"),
}


def _enum(name: str, *values: str) -> postgresql.ENUM:
    value = postgresql.ENUM(*values, name=name, create_type=False)
    value.create(op.get_bind(), checkfirst=True)
    return value


def upgrade() -> None:
    processing_status = _enum(
        "project_processing_status",
        "RAW",
        "SELECTED",
        "QUEUED",
        "PROCESSING",
        "NEEDS_REVIEW",
        "CLEANED",
        "READY_TO_POST",
        "FAILED_RETRYABLE",
        "FAILED_HUMAN_INPUT",
        "REJECTED",
    )
    job_status = _enum(
        "project_processing_job_status",
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "COMPLETED_WITH_ERRORS",
        "CANCELLED",
    )
    item_status = _enum(
        "project_processing_item_status",
        "QUEUED",
        "PROCESSING",
        "SUCCEEDED",
        "FAILED",
        "SKIPPED",
        "CANCELLED",
    )
    resolution_status = _enum(
        "project_diagnostic_resolution_status",
        "OPEN",
        "HUMAN_INPUT_REQUIRED",
        "RESOLVED",
        "REJECTED",
    )
    revision_status = _enum(
        "project_revision_status", "DRAFT", "IN_REVIEW", "APPROVED", "ACTIVE", "SUPERSEDED"
    )

    op.add_column("projects", sa.Column("active_revision_id", postgresql.UUID(as_uuid=True)))
    op.add_column(
        "project_import_candidates",
        sa.Column("processing_status", processing_status, nullable=False, server_default="RAW"),
    )
    op.add_column("project_import_candidates", sa.Column("last_successful_stage", sa.String(80)))
    op.create_index(
        "ix_project_import_candidates_processing_status",
        "project_import_candidates",
        ["processing_status"],
    )

    for column in (
        sa.Column("rights_basis", sa.String(500)),
        sa.Column("rights_confirmed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("rights_confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("original_sha256", sa.String(64)),
        sa.Column("processed_sha256", sa.String(64)),
        sa.Column("processing_version", sa.String(40)),
        sa.Column("public_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("title_en", sa.String(240)),
        sa.Column("title_ar", sa.String(240)),
        sa.Column("description_en", sa.String(500)),
        sa.Column("description_ar", sa.String(500)),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
    ):
        op.add_column("project_import_media", column)

    op.create_table(
        "project_overview_generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(120), nullable=False),
        sa.Column("model_name", sa.String(160), nullable=False),
        sa.Column("model_version", sa.String(160), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("source_version", sa.String(64), nullable=False),
        sa.Column("overview_en", sa.Text()),
        sa.Column("overview_ar", sa.Text()),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("result_status", sa.String(40), nullable=False),
        sa.Column("fact_guard_result", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "approval_status",
            postgresql.ENUM(name="editorial_approval_status", create_type=False),
            nullable=False,
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
    op.create_index(
        "ix_project_overview_generations_candidate_id",
        "project_overview_generations",
        ["candidate_id"],
    )

    op.create_table(
        "project_processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requested_action", sa.String(60), nullable=False),
        sa.Column("selection_mode", sa.String(40), nullable=False),
        sa.Column("selected_record_ids", postgresql.JSONB(), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("queued_count", sa.Integer(), nullable=False),
        sa.Column("processing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("correlation_id", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("created_by", "idempotency_key"),
    )
    op.create_index("ix_project_processing_jobs_status", "project_processing_jobs", ["status"])

    op.create_table(
        "project_processing_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_processing_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("status", item_status, nullable=False),
        sa.Column("current_stage", sa.String(80)),
        sa.Column("completed_stages", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("lease_owner", sa.String(120)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("result_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("job_id", "candidate_id"),
    )
    op.create_index("ix_project_processing_items_status", "project_processing_items", ["status"])

    op.create_table(
        "project_processing_diagnostics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_processing_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(80), nullable=False),
        sa.Column("error_code", sa.String(100), nullable=False),
        sa.Column("explanation", sa.String(1000), nullable=False),
        sa.Column("technical_detail", sa.String(1000)),
        sa.Column("affected_reference", sa.String(240)),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("first_occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("last_successful_stage", sa.String(80)),
        sa.Column("suggested_resolution", sa.String(1000), nullable=False),
        sa.Column("resolution_status", resolution_status, nullable=False),
        sa.Column("resolution_note", sa.String(1000)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("correlation_id", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_project_processing_diagnostics_stage", "project_processing_diagnostics", ["stage"]
    )
    op.create_index(
        "ix_project_processing_diagnostics_error_code",
        "project_processing_diagnostics",
        ["error_code"],
    )
    op.create_index(
        "ix_project_processing_diagnostics_retryable",
        "project_processing_diagnostics",
        ["retryable"],
    )
    op.create_index(
        "ix_project_processing_diagnostics_resolution_status",
        "project_processing_diagnostics",
        ["resolution_status"],
    )

    op.create_table(
        "project_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("status", revision_status, nullable=False),
        sa.Column(
            "base_revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_revisions.id", ondelete="SET NULL"),
        ),
        sa.Column("record_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("media_snapshot", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("field_diff", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("change_summary", sa.String(1000)),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("project_id", "revision_number"),
    )
    op.create_index("ix_project_revisions_project_id", "project_revisions", ["project_id"])
    op.create_index("ix_project_revisions_status", "project_revisions", ["status"])
    op.create_foreign_key(
        "fk_projects_active_revision_id",
        "projects",
        "project_revisions",
        ["active_revision_id"],
        ["id"],
        ondelete="SET NULL",
    )

    connection = op.get_bind()
    super_admin_id = connection.execute(
        sa.text("SELECT id FROM roles WHERE slug = 'super-admin'")
    ).scalar()
    for code, permission_id in PERMISSIONS.items():
        connection.execute(
            sa.text(
                "INSERT INTO permissions (id, code) "
                "VALUES (:id, :code) ON CONFLICT (code) DO NOTHING"
            ),
            {"id": permission_id, "code": code},
        )
        if super_admin_id:
            connection.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "VALUES (:role_id, :permission_id) ON CONFLICT DO NOTHING"
                ),
                {"role_id": super_admin_id, "permission_id": permission_id},
            )


def downgrade() -> None:
    connection = op.get_bind()
    for permission_id in PERMISSIONS.values():
        connection.execute(
            sa.text("DELETE FROM role_permissions WHERE permission_id = :id"), {"id": permission_id}
        )
        connection.execute(sa.text("DELETE FROM permissions WHERE id = :id"), {"id": permission_id})
    op.drop_constraint("fk_projects_active_revision_id", "projects", type_="foreignkey")
    op.drop_index("ix_project_revisions_status", table_name="project_revisions")
    op.drop_index("ix_project_revisions_project_id", table_name="project_revisions")
    op.drop_table("project_revisions")
    op.drop_index(
        "ix_project_processing_diagnostics_resolution_status",
        table_name="project_processing_diagnostics",
    )
    op.drop_index(
        "ix_project_processing_diagnostics_retryable", table_name="project_processing_diagnostics"
    )
    op.drop_index(
        "ix_project_processing_diagnostics_error_code", table_name="project_processing_diagnostics"
    )
    op.drop_index(
        "ix_project_processing_diagnostics_stage", table_name="project_processing_diagnostics"
    )
    op.drop_table("project_processing_diagnostics")
    op.drop_index("ix_project_processing_items_status", table_name="project_processing_items")
    op.drop_table("project_processing_items")
    op.drop_index("ix_project_processing_jobs_status", table_name="project_processing_jobs")
    op.drop_table("project_processing_jobs")
    op.drop_index(
        "ix_project_overview_generations_candidate_id", table_name="project_overview_generations"
    )
    op.drop_table("project_overview_generations")
    for column in (
        "tags",
        "description_ar",
        "description_en",
        "title_ar",
        "title_en",
        "public_metadata",
        "processing_version",
        "processed_sha256",
        "original_sha256",
        "rights_confirmed_at",
        "rights_confirmed_by",
        "rights_basis",
    ):
        op.drop_column("project_import_media", column)
    op.drop_index(
        "ix_project_import_candidates_processing_status", table_name="project_import_candidates"
    )
    op.drop_column("project_import_candidates", "last_successful_stage")
    op.drop_column("project_import_candidates", "processing_status")
    op.drop_column("projects", "active_revision_id")
    for name in (
        "project_revision_status",
        "project_diagnostic_resolution_status",
        "project_processing_item_status",
        "project_processing_job_status",
        "project_processing_status",
    ):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
