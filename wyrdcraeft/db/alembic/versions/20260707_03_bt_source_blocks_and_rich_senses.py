"""
Add source-block entry ordering and rich Bosworth-Toller sense columns.

Revision ID: 20260707_03
Revises: 20260707_02
Create Date: 2026-07-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for source-block entry identity and rich senses.
revision: str = "20260707_03"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260707_02"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Drop homograph uniqueness and add source-block sense metadata columns.

    Side Effects:
        Rebuilds ``bt_entries`` without the ``(norm_key, pos_id)`` uniqueness
        constraint, adds ``entry_order``, and backfills rich sense columns on
        ``bt_senses``.

    """
    op.add_column("bt_entries", sa.Column("entry_order", sa.Integer(), nullable=True))
    op.execute("UPDATE bt_entries SET entry_order = id")
    with op.batch_alter_table("bt_entries", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_bt_entries_norm_key_pos_id", type_="unique")
        batch_op.alter_column(
            "entry_order",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_index("idx_bt_entries_entry_order", ["entry_order"])

    op.add_column("bt_senses", sa.Column("sense_path", sa.Text(), nullable=True))
    op.add_column("bt_senses", sa.Column("parent_path", sa.Text(), nullable=True))
    op.add_column("bt_senses", sa.Column("source_label_raw", sa.Text(), nullable=True))
    op.add_column(
        "bt_senses",
        sa.Column("source_fragment_raw", sa.Text(), nullable=True),
    )
    op.add_column(
        "bt_senses",
        sa.Column("prefix_fragment_raw", sa.Text(), nullable=True),
    )
    op.add_column("bt_senses", sa.Column("modifiers_json", sa.Text(), nullable=True))
    op.add_column(
        "bt_senses",
        sa.Column("grammatical_context_json", sa.Text(), nullable=True),
    )
    op.add_column("bt_senses", sa.Column("usage_note", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE bt_senses
        SET
            sense_path = CAST(order_index + 1 AS TEXT),
            parent_path = NULL,
            source_label_raw = sense_label,
            source_fragment_raw = gloss_en,
            prefix_fragment_raw = '',
            modifiers_json = '[]',
            grammatical_context_json = '[]',
            usage_note = ''
        """
    )
    with op.batch_alter_table("bt_senses", recreate="always") as batch_op:
        batch_op.alter_column("sense_path", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column(
            "source_label_raw",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch_op.alter_column(
            "source_fragment_raw",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch_op.alter_column(
            "prefix_fragment_raw",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch_op.alter_column(
            "modifiers_json",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch_op.alter_column(
            "grammatical_context_json",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch_op.alter_column("usage_note", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    """
    Restore homograph uniqueness and remove rich sense metadata columns.

    Side Effects:
        Drops source-block ordering and rich sense columns, then recreates the
        legacy ``(norm_key, pos_id)`` uniqueness constraint on ``bt_entries``.

    """
    with op.batch_alter_table("bt_senses", recreate="always") as batch_op:
        batch_op.drop_column("usage_note")
        batch_op.drop_column("grammatical_context_json")
        batch_op.drop_column("modifiers_json")
        batch_op.drop_column("prefix_fragment_raw")
        batch_op.drop_column("source_fragment_raw")
        batch_op.drop_column("source_label_raw")
        batch_op.drop_column("parent_path")
        batch_op.drop_column("sense_path")

    with op.batch_alter_table("bt_entries", recreate="always") as batch_op:
        batch_op.drop_index("idx_bt_entries_entry_order")
        batch_op.drop_column("entry_order")
        batch_op.create_unique_constraint(
            "uq_bt_entries_norm_key_pos_id",
            ["norm_key", "pos_id"],
        )
