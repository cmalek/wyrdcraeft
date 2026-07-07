"""
Drop legacy lexicon search-index tables.

Revision ID: 20260707_01
Revises: 20260706_04
Create Date: 2026-07-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for dropping legacy search-index tables.
revision: str = "20260707_01"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260706_04"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Drop legacy lexicon search-index tables from the canonical schema.

    Side Effects:
        Removes ``search_keys`` and ``search_build_meta`` from upgraded
        databases.

    """
    op.drop_table("search_keys")
    op.drop_table("search_build_meta")


def downgrade() -> None:
    """
    Recreate empty legacy lexicon search-index tables.

    Side Effects:
        Restores empty ``search_keys`` and ``search_build_meta`` tables, along
        with the legacy foreign keys and indexes required by older lexicon code.

    """
    op.create_table(
        "search_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_text", sa.Text(), nullable=False),
        sa.Column("key_kind", sa.Text(), nullable=False),
        sa.Column("rank_tier", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=True),
        sa.Column("form_id", sa.Integer(), nullable=True),
        sa.Column("display_text", sa.Text(), nullable=False),
    )
    with op.batch_alter_table("search_keys", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_search_keys_entry_id_bt_entries",
            "bt_entries",
            ["entry_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_search_keys_form_id_forms",
            "forms",
            ["form_id"],
            ["id"],
        )

    op.create_index("idx_search_keys_key_text", "search_keys", ["key_text"])
    op.create_index("idx_search_keys_entry_id", "search_keys", ["entry_id"])
    op.create_index("idx_search_keys_form_id", "search_keys", ["form_id"])
    op.execute(
        """
        CREATE UNIQUE INDEX idx_search_keys_dedupe
        ON search_keys(
            TRIM(key_text),
            key_kind,
            rank_tier,
            COALESCE(entry_id, -1),
            COALESCE(form_id, -1),
            TRIM(display_text)
        )
        """
    )

    op.create_table(
        "search_build_meta",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )
