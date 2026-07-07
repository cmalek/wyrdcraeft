"""
Drop legacy denormalized string columns from morphology forms.

Revision ID: 20260706_04
Revises: 20260706_03
Create Date: 2026-07-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for legacy forms string-column drop.
revision: str = "20260706_04"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260706_03"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Drop legacy denormalized string columns from ``forms``.

    Side Effects:
        Removes ``wright``, ``paradigm``, ``paraID``, ``wordclass``, ``function``,
        and ``class1``-``class3``. Foreign-key columns and normalized ``*_key``
        lookup columns remain unchanged.

    """
    with op.batch_alter_table("forms", recreate="always") as batch_op:
        batch_op.drop_column("class3")
        batch_op.drop_column("class2")
        batch_op.drop_column("class1")
        batch_op.drop_column("wordclass")
        batch_op.drop_column("function")
        batch_op.drop_column("paraID")
        batch_op.drop_column("paradigm")
        batch_op.drop_column("wright")


def downgrade() -> None:
    """
    Restore legacy denormalized string columns on ``forms``.

    Side Effects:
        Re-adds empty-string defaults for dropped legacy columns. Downgrade does
        not repopulate historical string values.

    """
    with op.batch_alter_table("forms", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("wright", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("paradigm", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("paraID", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("wordclass", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("function", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("class1", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("class2", sa.Text(), nullable=False, server_default=""),
        )
        batch_op.add_column(
            sa.Column("class3", sa.Text(), nullable=False, server_default=""),
        )
