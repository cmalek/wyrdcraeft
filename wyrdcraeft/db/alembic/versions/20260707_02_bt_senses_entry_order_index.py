"""
Add ordered lookup index for dictionary sense reads.

Revision ID: 20260707_02
Revises: 20260707_01
Create Date: 2026-07-07
"""

from __future__ import annotations

from alembic import op

#: Alembic revision identifier for ordered dictionary-sense lookups.
revision: str = "20260707_02"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260707_01"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Add index supporting ordered sense lookup by dictionary entry.

    Side Effects:
        Creates a composite index on ``bt_senses`` covering entry ownership and
        stable ordering columns.

    """
    op.create_index(
        "idx_bt_senses_entry_order",
        "bt_senses",
        ["entry_id", "order_index", "id"],
    )


def downgrade() -> None:
    """
    Remove ordered lookup index for dictionary sense reads.

    Side Effects:
        Drops the composite ``bt_senses`` lookup index.

    """
    op.drop_index("idx_bt_senses_entry_order", table_name="bt_senses")
