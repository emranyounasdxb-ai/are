"""Create authenticated Admin CMS foundation.

Revision ID: 20260824_0001
Revises: None
Create Date: 2026-08-24
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260824_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROLE_IDS = {
    "super-admin": uuid.UUID("10000000-0000-4000-8000-000000000001"),
    "property-manager": uuid.UUID("10000000-0000-4000-8000-000000000002"),
    "content-manager": uuid.UUID("10000000-0000-4000-8000-000000000003"),
    "hr": uuid.UUID("10000000-0000-4000-8000-000000000004"),
    "enquiry-manager": uuid.UUID("10000000-0000-4000-8000-000000000005"),
}

PERMISSIONS = [
    "property.read",
    "property.create",
    "property.update",
    "property.publish",
    "content.read",
    "content.create",
    "content.update",
    "content.publish",
    "careers.read",
    "careers.create",
    "careers.update",
    "careers.publish",
    "enquiries.read",
    "enquiries.update",
    "applications.read",
    "applications.update",
    "users.manage",
    "audit.read",
]
PERMISSION_IDS = {
    code: uuid.UUID(f"20000000-0000-4000-8000-{index:012d}")
    for index, code in enumerate(PERMISSIONS, start=1)
}

ROLE_GRANTS = {
    "property-manager": [code for code in PERMISSIONS if code.startswith("property.")],
    "content-manager": [code for code in PERMISSIONS if code.startswith("content.")],
    "hr": [code for code in PERMISSIONS if code.startswith(("careers.", "applications."))],
    "enquiry-manager": [code for code in PERMISSIONS if code.startswith("enquiries.")],
}


def upgrade() -> None:
    publication_status = postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "ARCHIVED",
        name="publication_status",
        create_type=False,
    )
    property_purpose = postgresql.ENUM(
        "BUY", "RENT", "OFF_PLAN", name="property_purpose", create_type=False
    )
    job_status = postgresql.ENUM(
        "DRAFT", "OPEN", "CLOSED", "ARCHIVED", name="job_status", create_type=False
    )
    publication_status.create(op.get_bind(), checkfirst=True)
    property_purpose.create(op.get_bind(), checkfirst=True)
    job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
    )
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(120), nullable=False, unique=True),
    )
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent_hash", sa.String(64)),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])

    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("purpose", property_purpose, nullable=False),
        sa.Column("property_type", sa.String(120), nullable=False),
        sa.Column("emirate", sa.String(120), nullable=False),
        sa.Column("community", sa.String(180), nullable=False),
        sa.Column("developer", sa.String(180)),
        sa.Column("bedrooms", sa.Integer()),
        sa.Column("bathrooms", sa.Integer()),
        sa.Column("area", sa.Numeric(12, 2)),
        sa.Column("area_unit", sa.String(24)),
        sa.Column("price", sa.Numeric(16, 2)),
        sa.Column("price_on_request", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("currency", sa.String(3), nullable=False, server_default="AED"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("provenance_note", sa.Text(), nullable=False),
        sa.Column("external_reference_url", sa.Text()),
        sa.Column("status", publication_status, nullable=False, server_default="DRAFT"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_properties_status", "properties", ["status"])
    op.create_index("ix_properties_search", "properties", ["slug", "property_type", "emirate"])
    op.create_table(
        "property_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.UniqueConstraint("property_id", "locale"),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_property_translation_locale"),
    )

    op.create_table(
        "insight_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("category", sa.String(120), nullable=False),
        sa.Column("author_display_name", sa.String(160), nullable=False),
        sa.Column("source_links", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", publication_status, nullable=False, server_default="DRAFT"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_insight_posts_status", "insight_posts", ["status"])
    op.create_index("ix_insight_posts_search", "insight_posts", ["slug", "category"])
    op.create_table(
        "insight_post_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "insight_post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("insight_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("body", postgresql.JSONB(), nullable=False),
        sa.Column("seo_title", sa.String(240), nullable=False),
        sa.Column("seo_description", sa.String(320), nullable=False),
        sa.UniqueConstraint("insight_post_id", "locale"),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_insight_translation_locale"),
    )

    op.create_table(
        "job_openings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("department", sa.String(160), nullable=False),
        sa.Column("location", sa.String(160), nullable=False),
        sa.Column("employment_type", sa.String(100), nullable=False),
        sa.Column("closing_date", sa.Date()),
        sa.Column("status", job_status, nullable=False, server_default="DRAFT"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_job_openings_status", "job_openings", ["status"])
    op.create_index("ix_job_openings_search", "job_openings", ["slug", "department"])
    op.create_table(
        "job_opening_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_opening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("responsibilities", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("requirements", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("benefits", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.UniqueConstraint("job_opening_id", "locale"),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_job_translation_locale"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column("entity_type", sa.String(120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("outcome", sa.String(40), nullable=False, server_default="success"),
        sa.Column("before_summary", postgresql.JSONB()),
        sa.Column("after_summary", postgresql.JSONB()),
        sa.Column("request_correlation_id", sa.String(80), nullable=False),
        sa.Column("metadata_summary", postgresql.JSONB()),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])
    op.create_index(
        "ix_audit_logs_request_correlation_id", "audit_logs", ["request_correlation_id"]
    )

    roles_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug"),
        sa.column("name"),
    )
    permissions_table = sa.table(
        "permissions", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("code")
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    role_names = {
        "super-admin": "Super Admin",
        "property-manager": "Property Manager",
        "content-manager": "Content Manager",
        "hr": "HR",
        "enquiry-manager": "Enquiry Manager",
    }
    op.bulk_insert(
        roles_table,
        [{"id": ROLE_IDS[slug], "slug": slug, "name": name} for slug, name in role_names.items()],
    )
    op.bulk_insert(
        permissions_table,
        [{"id": PERMISSION_IDS[code], "code": code} for code in PERMISSIONS],
    )
    grants = [(ROLE_IDS["super-admin"], PERMISSION_IDS[code]) for code in PERMISSIONS]
    for role_slug, permission_codes in ROLE_GRANTS.items():
        grants.extend((ROLE_IDS[role_slug], PERMISSION_IDS[code]) for code in permission_codes)
    op.bulk_insert(
        role_permissions_table,
        [{"role_id": role_id, "permission_id": permission_id} for role_id, permission_id in grants],
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("job_opening_translations")
    op.drop_table("job_openings")
    op.drop_table("insight_post_translations")
    op.drop_table("insight_posts")
    op.drop_table("property_translations")
    op.drop_table("properties")
    op.drop_table("sessions")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
    postgresql.ENUM(name="job_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="property_purpose").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="publication_status").drop(op.get_bind(), checkfirst=True)
