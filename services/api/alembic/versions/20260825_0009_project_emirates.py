"""Add controlled UAE Emirates to Areas and Projects.

Revision ID: 20260825_0009
Revises: 20260825_0008
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260825_0009"
down_revision: str | None = "20260825_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMIRATES = (
    "DUBAI",
    "ABU_DHABI",
    "SHARJAH",
    "AJMAN",
    "UMM_AL_QUWAIN",
    "RAS_AL_KHAIMAH",
    "FUJAIRAH",
)


def upgrade() -> None:
    emirate = postgresql.ENUM(*EMIRATES, name="uae_emirate")
    emirate.create(op.get_bind(), checkfirst=True)
    op.drop_index("ix_area_communities_search", table_name="area_communities")
    op.execute(
        """
        ALTER TABLE area_communities
        ALTER COLUMN emirate TYPE uae_emirate
        USING CASE emirate
          WHEN 'Dubai' THEN 'DUBAI'::uae_emirate
          WHEN 'Abu Dhabi' THEN 'ABU_DHABI'::uae_emirate
          WHEN 'Sharjah' THEN 'SHARJAH'::uae_emirate
          WHEN 'Ajman' THEN 'AJMAN'::uae_emirate
          WHEN 'Umm Al Quwain' THEN 'UMM_AL_QUWAIN'::uae_emirate
          WHEN 'Ras Al Khaimah' THEN 'RAS_AL_KHAIMAH'::uae_emirate
          WHEN 'Fujairah' THEN 'FUJAIRAH'::uae_emirate
        END
        """
    )
    op.create_index("ix_area_communities_emirate", "area_communities", ["emirate"])
    op.create_index(
        "ix_area_communities_search", "area_communities", ["slug", "name_en", "emirate"]
    )
    op.add_column("projects", sa.Column("emirate", emirate, nullable=True))
    op.execute(
        """
        UPDATE projects AS project
        SET emirate = area.emirate
        FROM area_communities AS area
        WHERE project.area_id = area.id
        """
    )
    op.alter_column("projects", "emirate", nullable=False)
    op.create_index("ix_projects_emirate", "projects", ["emirate"])


def downgrade() -> None:
    op.drop_index("ix_projects_emirate", table_name="projects")
    op.drop_column("projects", "emirate")
    op.drop_index("ix_area_communities_search", table_name="area_communities")
    op.drop_index("ix_area_communities_emirate", table_name="area_communities")
    op.execute(
        """
        ALTER TABLE area_communities
        ALTER COLUMN emirate TYPE VARCHAR(120)
        USING CASE emirate
          WHEN 'DUBAI' THEN 'Dubai'
          WHEN 'ABU_DHABI' THEN 'Abu Dhabi'
          WHEN 'SHARJAH' THEN 'Sharjah'
          WHEN 'AJMAN' THEN 'Ajman'
          WHEN 'UMM_AL_QUWAIN' THEN 'Umm Al Quwain'
          WHEN 'RAS_AL_KHAIMAH' THEN 'Ras Al Khaimah'
          WHEN 'FUJAIRAH' THEN 'Fujairah'
        END
        """
    )
    op.create_index(
        "ix_area_communities_search", "area_communities", ["slug", "name_en", "emirate"]
    )
    postgresql.ENUM(name="uae_emirate").drop(op.get_bind(), checkfirst=True)
