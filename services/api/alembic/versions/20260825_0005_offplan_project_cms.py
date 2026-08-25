"""Add the empty Off-Plan Project CMS and import-review foundation.

Revision ID: 20260825_0005
Revises: 20260825_0004
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0005"
down_revision: str | None = "20260825_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SUPER_ADMIN_ROLE_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
PERMISSIONS = {
    "project.read": uuid.UUID("20000000-0000-4000-8000-000000000020"),
    "project.create": uuid.UUID("20000000-0000-4000-8000-000000000021"),
    "project.update": uuid.UUID("20000000-0000-4000-8000-000000000022"),
    "project.publish": uuid.UUID("20000000-0000-4000-8000-000000000023"),
    "project-import.manage": uuid.UUID("20000000-0000-4000-8000-000000000024"),
}


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
    availability = postgresql.ENUM(
        "AVAILABLE",
        "LIMITED_AVAILABILITY",
        "SOLD_OUT",
        "COMING_SOON",
        name="project_availability_status",
    )
    construction = postgresql.ENUM(
        "PRE_LAUNCH",
        "LAUNCHED",
        "UNDER_CONSTRUCTION",
        "NEAR_COMPLETION",
        "COMPLETED",
        "ON_HOLD",
        "NOT_CONFIRMED",
        name="project_construction_status",
    )
    priority = postgresql.ENUM("A", "B", "C", name="project_priority")
    property_type = postgresql.ENUM(
        "APARTMENT",
        "VILLA",
        "TOWNHOUSE",
        "PENTHOUSE",
        "DUPLEX",
        "MANSION",
        "RESIDENTIAL_PLOT",
        "OTHER",
        name="project_property_type",
    )
    bedroom = postgresql.ENUM(
        "STUDIO",
        "ONE",
        "TWO",
        "THREE",
        "FOUR",
        "FIVE",
        "SIX_PLUS",
        name="project_bedroom_option",
    )
    payment_stage = postgresql.ENUM(
        "BOOKING",
        "DURING_CONSTRUCTION",
        "HANDOVER",
        "POST_HANDOVER",
        "OTHER",
        name="project_payment_stage",
    )
    source_type = postgresql.ENUM(
        "OWNER_MANIFEST",
        "DLD_PROJECT_STATUS",
        "OFFICIAL_DEVELOPER_PAGE",
        "OFFICIAL_DEVELOPER_BROCHURE",
        "OFFICIAL_MASTER_COMMUNITY_PAGE",
        "OWNER_SUPPLIED_DOCUMENT",
        "OWNER_APPROVED_PARTNER_FEED",
        "APPROVED_SECONDARY_SOURCE",
        name="project_source_type",
    )
    media_category = postgresql.ENUM(
        "COVER",
        "GALLERY",
        "EXTERIOR",
        "INTERIOR",
        "AMENITIES",
        "FLOOR_PLAN",
        "MASTER_PLAN",
        "LOCATION_MAP",
        "CONSTRUCTION",
        "VIDEO_REFERENCE",
        name="project_media_category",
    )
    review_status = postgresql.ENUM(
        "DISCOVERED",
        "EXTRACTED",
        "NEEDS_REVIEW",
        "READY_FOR_APPROVAL",
        "APPROVED",
        "REJECTED",
        "FAILED",
        "MERGED",
        name="project_import_review_status",
    )
    for enum in (
        availability,
        construction,
        priority,
        property_type,
        bedroom,
        payment_stage,
        source_type,
        media_category,
        review_status,
    ):
        enum.create(op.get_bind(), checkfirst=True)

    availability = postgresql.ENUM(name="project_availability_status", create_type=False)
    construction = postgresql.ENUM(name="project_construction_status", create_type=False)
    priority = postgresql.ENUM(name="project_priority", create_type=False)
    property_type = postgresql.ENUM(name="project_property_type", create_type=False)
    bedroom = postgresql.ENUM(name="project_bedroom_option", create_type=False)
    payment_stage = postgresql.ENUM(name="project_payment_stage", create_type=False)
    source_type = postgresql.ENUM(name="project_source_type", create_type=False)
    media_category = postgresql.ENUM(name="project_media_category", create_type=False)
    review_status = postgresql.ENUM(name="project_import_review_status", create_type=False)

    publication = postgresql.ENUM(
        "DRAFT", "PUBLISHED", "ARCHIVED", name="publication_status", create_type=False
    )
    rights = postgresql.ENUM(name="media_rights_status", create_type=False)

    op.create_table(
        "area_communities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("name_en", sa.String(240), nullable=False),
        sa.Column("name_ar", sa.String(240), nullable=False),
        sa.Column("emirate", sa.String(120), nullable=False),
        sa.Column("status", publication, nullable=False, server_default="DRAFT"),
        *timestamps(),
    )
    op.create_index("ix_area_communities_status", "area_communities", ["status"])
    op.create_index(
        "ix_area_communities_search", "area_communities", ["slug", "name_en", "emirate"]
    )
    op.create_table(
        "area_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "area_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("area_communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(2)),
        sa.Column("alias", sa.String(240), nullable=False),
        sa.Column("normalized_alias", sa.String(240), nullable=False, unique=True),
        sa.CheckConstraint("locale IS NULL OR locale IN ('en', 'ar')", name="ck_area_alias_locale"),
    )
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column(
            "developer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("developers.id"),
            nullable=False,
        ),
        sa.Column(
            "area_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("area_communities.id"),
            nullable=False,
        ),
        sa.Column("status", publication, nullable=False, server_default="DRAFT"),
        sa.Column("availability_status", availability, nullable=False),
        sa.Column(
            "construction_status", construction, nullable=False, server_default="NOT_CONFIRMED"
        ),
        sa.Column("handover_quarter", sa.String(2)),
        sa.Column("handover_year", sa.Integer()),
        sa.Column("original_handover_value", sa.String(240)),
        sa.Column("last_verified_at", sa.DateTime(timezone=True)),
        sa.Column("priority", priority, nullable=False, server_default="B"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("internal_notes", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        *timestamps(),
        sa.CheckConstraint(
            "handover_quarter IS NULL OR handover_quarter IN ('Q1','Q2','Q3','Q4')",
            name="ck_project_handover_quarter",
        ),
        sa.CheckConstraint(
            "handover_year IS NULL OR handover_year BETWEEN 2000 AND 2200",
            name="ck_project_handover_year",
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_project_display_order"),
    )
    op.create_index("ix_projects_developer_id", "projects", ["developer_id"])
    op.create_index("ix_projects_area_id", "projects", ["area_id"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index(
        "ix_projects_search",
        "projects",
        ["slug", "status", "availability_status", "construction_status"],
    )
    op.create_table(
        "project_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("official_name", sa.String(240), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column("seo_title", sa.String(240), nullable=False),
        sa.Column("seo_description", sa.String(320), nullable=False),
        sa.UniqueConstraint("project_id", "locale"),
        sa.CheckConstraint("locale IN ('en', 'ar')", name="ck_project_translation_locale"),
    )
    op.create_table(
        "project_property_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("property_type", property_type, nullable=False),
        sa.UniqueConstraint("project_id", "property_type"),
    )
    op.create_table(
        "project_bedroom_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bedroom_option", bedroom, nullable=False),
        sa.UniqueConstraint("project_id", "bedroom_option"),
    )
    op.create_table(
        "project_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("source_title", sa.String(320)),
        sa.Column("source_developer_domain", sa.String(320)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index(
        "ix_project_sources_project_type", "project_sources", ["project_id", "source_type"]
    )
    op.create_table(
        "project_payment_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("raw_source_text", sa.Text(), nullable=False),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_sources.id"),
            nullable=False,
        ),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )
    op.create_table(
        "project_payment_milestones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payment_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_payment_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stage", payment_stage, nullable=False),
        sa.Column("label_en", sa.String(240), nullable=False),
        sa.Column("label_ar", sa.String(240)),
        sa.Column("percentage", sa.Numeric(5, 2)),
        sa.Column("due_trigger", sa.String(320)),
        sa.Column("source_value", sa.Text(), nullable=False),
        sa.UniqueConstraint("payment_plan_id", "sequence"),
        sa.CheckConstraint("sequence >= 0", name="ck_payment_milestone_sequence"),
        sa.CheckConstraint(
            "percentage IS NULL OR percentage BETWEEN 0 AND 100",
            name="ck_payment_milestone_percentage",
        ),
    )
    op.create_table(
        "project_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", media_category, nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("rights_status", rights, nullable=False, server_default="PENDING"),
        sa.Column("alt_en", sa.String(320)),
        sa.Column("alt_ar", sa.String(320)),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_key", sa.String(180), unique=True),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("mime_type", sa.String(64)),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        *timestamps(),
        sa.CheckConstraint("display_order >= 0", name="ck_project_media_display_order"),
    )
    op.create_index(
        "ix_project_media_project_category", "project_media", ["project_id", "category"]
    )
    op.create_table(
        "project_import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clean_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("needs_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
    )
    op.create_table(
        "project_import_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_source_payload", postgresql.JSONB(), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB()),
        sa.Column("owner_manifest_values", postgresql.JSONB(), nullable=False),
        sa.Column("normalized_project_name", sa.String(240)),
        sa.Column(
            "proposed_developer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("developers.id"),
        ),
        sa.Column(
            "proposed_area_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("area_communities.id"),
        ),
        sa.Column("official_source_url", sa.Text()),
        sa.Column("source_urls", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("extracted_at", sa.DateTime(timezone=True)),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("match_result", postgresql.JSONB()),
        sa.Column("validation_errors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("conflict_reasons", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("review_status", review_status, nullable=False, server_default="DISCOVERED"),
        sa.Column("linked_project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        *timestamps(),
    )
    op.create_index(
        "ix_project_import_candidates_review_status", "project_import_candidates", ["review_status"]
    )
    op.create_index(
        "ix_project_import_candidates_dedupe",
        "project_import_candidates",
        ["normalized_project_name", "proposed_developer_id", "proposed_area_id"],
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    for code, permission_id in PERMISSIONS.items():
        op.execute(
            postgresql.insert(permissions)
            .values(id=permission_id, code=code)
            .on_conflict_do_nothing(index_elements=["code"])
        )
        op.execute(
            postgresql.insert(role_permissions)
            .values(role_id=SUPER_ADMIN_ROLE_ID, permission_id=permission_id)
            .on_conflict_do_nothing(index_elements=["role_id", "permission_id"])
        )


def downgrade() -> None:
    for permission_id in PERMISSIONS.values():
        op.execute(
            sa.text("DELETE FROM role_permissions WHERE permission_id = :permission_id").bindparams(
                permission_id=permission_id
            )
        )
        op.execute(
            sa.text("DELETE FROM permissions WHERE id = :permission_id").bindparams(
                permission_id=permission_id
            )
        )
    for table in (
        "project_import_candidates",
        "project_import_batches",
        "project_media",
        "project_payment_milestones",
        "project_payment_plans",
        "project_sources",
        "project_bedroom_options",
        "project_property_types",
        "project_translations",
        "projects",
        "area_aliases",
        "area_communities",
    ):
        op.drop_table(table)
    for enum_name in (
        "project_import_review_status",
        "project_media_category",
        "project_source_type",
        "project_payment_stage",
        "project_bedroom_option",
        "project_property_type",
        "project_priority",
        "project_construction_status",
        "project_availability_status",
    ):
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
