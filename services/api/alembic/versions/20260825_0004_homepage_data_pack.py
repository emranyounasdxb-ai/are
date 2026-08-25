"""Add property-media readiness and the verified trust profile.

Revision ID: 20260825_0004
Revises: 20260824_0003
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0004"
down_revision: str | None = "20260824_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    availability_ddl = postgresql.ENUM(
        "UNVERIFIED",
        "VERIFIED_AVAILABLE",
        "VERIFIED_UNAVAILABLE",
        name="property_availability_status",
    )
    rights_ddl = postgresql.ENUM("PENDING", "APPROVED", "REJECTED", name="media_rights_status")
    availability_ddl.create(op.get_bind(), checkfirst=True)
    rights_ddl.create(op.get_bind(), checkfirst=True)
    availability = postgresql.ENUM(name="property_availability_status", create_type=False)
    rights = postgresql.ENUM(name="media_rights_status", create_type=False)
    op.add_column("properties", sa.Column("source_verified_at", sa.Date()))
    op.add_column(
        "properties",
        sa.Column("availability_status", availability, nullable=False, server_default="UNVERIFIED"),
    )
    op.create_table(
        "property_cover_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("storage_key", sa.String(180), unique=True),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("mime_type", sa.String(64)),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("alt_en", sa.String(320)),
        sa.Column("alt_ar", sa.String(320)),
        sa.Column("provenance_url", sa.Text(), nullable=False),
        sa.Column("rights_status", rights, nullable=False, server_default="PENDING"),
        sa.Column("display_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    publication = postgresql.ENUM(
        "DRAFT", "PUBLISHED", "ARCHIVED", name="publication_status", create_type=False
    )
    op.create_table(
        "trust_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("google_business_url", sa.Text(), nullable=False),
        sa.Column("google_rating", sa.Numeric(2, 1), nullable=False),
        sa.Column("google_review_count", sa.Integer(), nullable=False),
        sa.Column("snapshot_verified_at", sa.Date(), nullable=False),
        sa.Column("office_address", sa.String(320), nullable=False),
        sa.Column("status", publication, nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("trust_profiles")
    op.drop_table("property_cover_media")
    op.drop_column("properties", "availability_status")
    op.drop_column("properties", "source_verified_at")
    postgresql.ENUM(name="media_rights_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="property_availability_status").drop(op.get_bind(), checkfirst=True)
