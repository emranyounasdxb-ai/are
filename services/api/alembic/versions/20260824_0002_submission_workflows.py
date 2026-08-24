"""Add enquiries, career applications and private file metadata.

Revision ID: 20260824_0002
Revises: 20260824_0001
Create Date: 2026-08-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260824_0002"
down_revision: str | None = "20260824_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    enquiry_status = postgresql.ENUM(
        "NEW",
        "IN_REVIEW",
        "CONTACTED",
        "QUALIFIED",
        "CLOSED",
        "SPAM",
        name="enquiry_status",
        create_type=False,
    )
    application_status = postgresql.ENUM(
        "NEW",
        "REVIEWED",
        "SHORTLISTED",
        "INTERVIEW",
        "SELECTED",
        "REJECTED",
        name="application_status",
        create_type=False,
    )
    postgresql.ENUM(
        "NEW",
        "IN_REVIEW",
        "CONTACTED",
        "QUALIFIED",
        "CLOSED",
        "SPAM",
        name="enquiry_status",
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "NEW",
        "REVIEWED",
        "SHORTLISTED",
        "INTERVIEW",
        "SELECTED",
        "REJECTED",
        name="application_status",
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "contact_enquiries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_code", sa.String(24), nullable=False, unique=True),
        sa.Column("enquiry_type", sa.String(120), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(48), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB()),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("preferred_contact_method", sa.String(24), nullable=False),
        sa.Column("contact_consent", sa.Boolean(), nullable=False),
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attribution", postgresql.JSONB()),
        sa.Column("status", enquiry_status, nullable=False, server_default="NEW"),
        sa.Column("internal_note", sa.Text()),
        sa.Column("idempotency_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_contact_enquiry_locale"),
    )
    op.create_index(
        "ix_contact_enquiries_status_created", "contact_enquiries", ["status", "created_at"]
    )

    op.create_table(
        "career_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_code", sa.String(24), nullable=False, unique=True),
        sa.Column("applicant_name", sa.String(180), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(48), nullable=False),
        sa.Column("current_location", sa.String(180), nullable=False),
        sa.Column(
            "job_opening_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_openings.id")
        ),
        sa.Column("context_label", sa.String(240), nullable=False),
        sa.Column("linkedin_url", sa.Text()),
        sa.Column("portfolio_url", sa.Text()),
        sa.Column("cover_note", sa.Text(), nullable=False),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("acknowledgement_consent", sa.Boolean(), nullable=False),
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", application_status, nullable=False, server_default="NEW"),
        sa.Column("internal_note", sa.Text()),
        sa.Column("idempotency_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_career_application_locale"),
    )
    op.create_index(
        "ix_career_applications_status_created", "career_applications", ["status", "created_at"]
    )
    op.create_table(
        "private_file_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "career_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("career_applications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("storage_key", sa.String(180), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("declared_mime_type", sa.String(120), nullable=False),
        sa.Column("verified_format", sa.String(16), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("private_file_metadata")
    op.drop_index("ix_career_applications_status_created", table_name="career_applications")
    op.drop_table("career_applications")
    op.drop_index("ix_contact_enquiries_status_created", table_name="contact_enquiries")
    op.drop_table("contact_enquiries")
    postgresql.ENUM(name="application_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="enquiry_status").drop(op.get_bind(), checkfirst=True)
