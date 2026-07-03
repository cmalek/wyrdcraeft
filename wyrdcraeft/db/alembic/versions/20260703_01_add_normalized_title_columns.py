"""
Add macron-preserving normalized_title columns for morphology joins.

Revision ID: 20260703_01
Revises: 20260630_01
Create Date: 2026-07-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for normalized_title columns.
revision: str = "20260703_01"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260630_01"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Add normalized_title columns to morphology and dictionary source tables.

    Side Effects:
        Adds nullable columns and indexes; rebuild commands populate values.

    """
    op.add_column("forms", sa.Column("normalized_title", sa.Text(), nullable=True))
    op.add_column(
        "bt_entries", sa.Column("normalized_title", sa.Text(), nullable=True)
    )
    op.add_column(
        "bt_variants", sa.Column("normalized_title", sa.Text(), nullable=True)
    )
    op.create_index(
        "idx_forms_normalized_title",
        "forms",
        ["normalized_title"],
    )
    op.create_index(
        "idx_bt_entries_normalized_title",
        "bt_entries",
        ["normalized_title"],
    )
    op.create_index(
        "idx_bt_variants_normalized_title",
        "bt_variants",
        ["normalized_title"],
    )


def downgrade() -> None:
    """
    Remove normalized_title columns and lookup indexes.

    Side Effects:
        Drops normalized_title columns from source tables.

    """
    op.drop_index("idx_bt_variants_normalized_title", table_name="bt_variants")
    op.drop_index("idx_bt_entries_normalized_title", table_name="bt_entries")
    op.drop_index("idx_forms_normalized_title", table_name="forms")
    op.drop_column("bt_variants", "normalized_title")
    op.drop_column("bt_entries", "normalized_title")
    op.drop_column("forms", "normalized_title")
