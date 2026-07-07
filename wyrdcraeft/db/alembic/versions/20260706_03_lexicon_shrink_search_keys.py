"""
Shrink lexicon read model to search index tables only.

Revision ID: 20260706_03
Revises: 20260706_02
Create Date: 2026-07-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for lexicon search-index shrink.
revision: str = "20260706_03"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260706_02"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Rename search tables and drop lexicon projection tables.

    Side Effects:
        Renames ``lexicon_search_keys`` / ``lexicon_build_meta``, retargets
        ``search_keys`` foreign keys to ``bt_entries`` and ``forms``, and drops
        ``lexicon_entries`` / ``lexicon_forms``.

    """
    op.drop_index("idx_lexicon_search_keys_dedupe", table_name="lexicon_search_keys")
    op.drop_index("idx_lexicon_search_keys_form_id", table_name="lexicon_search_keys")
    op.drop_index("idx_lexicon_search_keys_entry_id", table_name="lexicon_search_keys")
    op.drop_index("idx_lexicon_search_keys_key_text", table_name="lexicon_search_keys")

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
    op.execute(
        """
        INSERT INTO search_keys (
            id,
            key_text,
            key_kind,
            rank_tier,
            entry_id,
            form_id,
            display_text
        )
        SELECT
            id,
            key_text,
            key_kind,
            rank_tier,
            entry_id,
            form_id,
            display_text
        FROM lexicon_search_keys
        """
    )
    op.drop_table("lexicon_search_keys")
    op.drop_table("lexicon_forms")
    op.drop_table("lexicon_entries")

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

    op.rename_table("lexicon_build_meta", "search_build_meta")


def downgrade() -> None:
    """
    Restore lexicon projection tables and legacy search table names.

    Side Effects:
        Recreates empty ``lexicon_entries`` / ``lexicon_forms`` projection tables,
        retargets search-key foreign keys back to them, and renames search tables
        to their legacy ``lexicon_*`` names.

    """
    op.rename_table("search_build_meta", "lexicon_build_meta")

    op.drop_index("idx_search_keys_dedupe", table_name="search_keys")
    op.drop_index("idx_search_keys_form_id", table_name="search_keys")
    op.drop_index("idx_search_keys_entry_id", table_name="search_keys")
    op.drop_index("idx_search_keys_key_text", table_name="search_keys")

    op.create_table(
        "lexicon_entries",
        sa.Column("entry_id", sa.Integer(), primary_key=True),
        sa.Column("norm_key", sa.Text(), nullable=False),
        sa.Column("pos", sa.Text(), nullable=False),
        sa.Column("headword", sa.Text(), nullable=False),
        sa.Column("summary_sense", sa.Text(), nullable=False),
        sa.Column("etymology", sa.Text(), nullable=False),
        sa.Column("variants_json", sa.Text(), nullable=False),
        sa.Column("genders_json", sa.Text(), nullable=False),
        sa.Column("senses_json", sa.Text(), nullable=False),
    )
    op.create_index(
        "idx_lexicon_entries_norm_pos",
        "lexicon_entries",
        ["norm_key", "pos"],
    )

    op.create_table(
        "lexicon_forms",
        sa.Column("form_id", sa.Integer(), primary_key=True),
        sa.Column(
            "entry_id",
            sa.Integer(),
            sa.ForeignKey("lexicon_entries.entry_id"),
        ),
        sa.Column("bt", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("form", sa.Text(), nullable=False),
        sa.Column("formi", sa.Text(), nullable=False),
        sa.Column("wordclass", sa.Text(), nullable=False),
        sa.Column("function", sa.Text(), nullable=False),
        sa.Column("probability", sa.Text(), nullable=False),
        sa.Column("class1", sa.Text(), nullable=False),
        sa.Column("class2", sa.Text(), nullable=False),
        sa.Column("class3", sa.Text(), nullable=False),
        sa.Column("paradigm", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("idx_lexicon_forms_entry_id", "lexicon_forms", ["entry_id"])

    op.create_table(
        "lexicon_search_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_text", sa.Text(), nullable=False),
        sa.Column("key_kind", sa.Text(), nullable=False),
        sa.Column("rank_tier", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=True),
        sa.Column("form_id", sa.Integer(), nullable=True),
        sa.Column("display_text", sa.Text(), nullable=False),
    )
    op.execute(
        """
        INSERT INTO lexicon_search_keys (
            id,
            key_text,
            key_kind,
            rank_tier,
            entry_id,
            form_id,
            display_text
        )
        SELECT
            id,
            key_text,
            key_kind,
            rank_tier,
            entry_id,
            form_id,
            display_text
        FROM search_keys
        """
    )
    op.drop_table("search_keys")

    with op.batch_alter_table("lexicon_search_keys", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_lexicon_search_keys_entry_id_lexicon_entries",
            "lexicon_entries",
            ["entry_id"],
            ["entry_id"],
        )
        batch_op.create_foreign_key(
            "fk_lexicon_search_keys_form_id_lexicon_forms",
            "lexicon_forms",
            ["form_id"],
            ["form_id"],
        )

    op.create_index(
        "idx_lexicon_search_keys_key_text",
        "lexicon_search_keys",
        ["key_text"],
    )
    op.create_index(
        "idx_lexicon_search_keys_entry_id",
        "lexicon_search_keys",
        ["entry_id"],
    )
    op.create_index(
        "idx_lexicon_search_keys_form_id",
        "lexicon_search_keys",
        ["form_id"],
    )
    op.execute(
        """
        CREATE UNIQUE INDEX idx_lexicon_search_keys_dedupe
        ON lexicon_search_keys(
            TRIM(key_text),
            key_kind,
            rank_tier,
            COALESCE(entry_id, -1),
            COALESCE(form_id, -1),
            TRIM(display_text)
        )
        """
    )
