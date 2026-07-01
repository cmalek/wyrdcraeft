"""
Create the initial canonical database schema.

Revision ID: 20260630_01
Revises:
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
#: Alembic revision identifier for the initial canonical schema.
revision: str = "20260630_01"
#: Previous Alembic revision identifier.
down_revision: str | None = None
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Create the canonical morphology, dictionary, and lexicon tables.

    Side Effects:
        Adds all initial product tables and lookup indexes to the target DB.

    """
    op.create_table(
        "forms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("counter", sa.Integer(), nullable=False),
        sa.Column("formi", sa.Text(), nullable=False),
        sa.Column("BT", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("form", sa.Text(), nullable=False),
        sa.Column("formParts", sa.Text(), nullable=False),
        sa.Column("var", sa.Text(), nullable=False),
        sa.Column("probability", sa.Text(), nullable=False),
        sa.Column("function", sa.Text(), nullable=False),
        sa.Column("wright", sa.Text(), nullable=False),
        sa.Column("paradigm", sa.Text(), nullable=False),
        sa.Column("paraID", sa.Text(), nullable=False),
        sa.Column("wordclass", sa.Text(), nullable=False),
        sa.Column("class1", sa.Text(), nullable=False),
        sa.Column("class2", sa.Text(), nullable=False),
        sa.Column("class3", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("bt_key", sa.Text(), nullable=False),
        sa.Column("title_key", sa.Text(), nullable=False),
        sa.Column("stem_key", sa.Text(), nullable=False),
        sa.Column("form_key", sa.Text(), nullable=False),
        sa.Column("formi_key", sa.Text(), nullable=False),
    )
    op.create_index("idx_forms_bt_key", "forms", ["bt_key"])
    op.create_index("idx_forms_title_key", "forms", ["title_key"])
    op.create_index("idx_forms_stem_key", "forms", ["stem_key"])
    op.create_index("idx_forms_form_key", "forms", ["form_key"])
    op.create_index("idx_forms_formi_key", "forms", ["formi_key"])

    op.create_table(
        "bt_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("norm_key", sa.Text(), nullable=False),
        sa.Column("headword_raw", sa.Text(), nullable=False),
        sa.Column("headword_macronized", sa.Text(), nullable=False),
        sa.Column("pos", sa.Text(), nullable=False),
        sa.Column("genders_json", sa.Text(), nullable=False),
        sa.Column("etymology", sa.Text(), nullable=False),
        sa.Column("see_also_json", sa.Text(), nullable=False),
        sa.Column("source_line_nos_json", sa.Text(), nullable=False),
        sa.UniqueConstraint("norm_key", "pos"),
    )
    op.create_index("idx_bt_entries_norm_key", "bt_entries", ["norm_key"])

    op.create_table(
        "bt_senses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "entry_id",
            sa.Integer(),
            sa.ForeignKey("bt_entries.id"),
            nullable=False,
        ),
        sa.Column("sense_label", sa.Text(), nullable=False),
        sa.Column("gloss_en", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
    )

    op.create_table(
        "bt_variants",
        sa.Column(
            "entry_id",
            sa.Integer(),
            sa.ForeignKey("bt_entries.id"),
            nullable=False,
        ),
        sa.Column("spelling_raw", sa.Text(), nullable=False),
        sa.Column("spelling_macronized", sa.Text(), nullable=False),
    )
    op.create_index("idx_bt_variants_spelling", "bt_variants", ["spelling_macronized"])

    op.create_table(
        "bt_edit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("op", sa.Text(), nullable=False),
        sa.Column("source_line_no", sa.Integer(), nullable=False),
        sa.Column("target_norm_key", sa.Text(), nullable=False),
        sa.Column("target_pos", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("applied", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
    )

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
        sa.Column(
            "entry_id",
            sa.Integer(),
            sa.ForeignKey("lexicon_entries.entry_id"),
        ),
        sa.Column(
            "form_id",
            sa.Integer(),
            sa.ForeignKey("lexicon_forms.form_id"),
        ),
        sa.Column("display_text", sa.Text(), nullable=False),
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

    op.create_table(
        "lexicon_build_meta",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    """
    Drop the initial canonical schema.

    Side Effects:
        Removes the initial product tables and their dependent indexes.

    """
    op.drop_table("lexicon_build_meta")
    op.drop_index("idx_lexicon_search_keys_dedupe", table_name="lexicon_search_keys")
    op.drop_index("idx_lexicon_search_keys_form_id", table_name="lexicon_search_keys")
    op.drop_index("idx_lexicon_search_keys_entry_id", table_name="lexicon_search_keys")
    op.drop_index("idx_lexicon_search_keys_key_text", table_name="lexicon_search_keys")
    op.drop_table("lexicon_search_keys")
    op.drop_index("idx_lexicon_forms_entry_id", table_name="lexicon_forms")
    op.drop_table("lexicon_forms")
    op.drop_index("idx_lexicon_entries_norm_pos", table_name="lexicon_entries")
    op.drop_table("lexicon_entries")
    op.drop_table("bt_edit_log")
    op.drop_index("idx_bt_variants_spelling", table_name="bt_variants")
    op.drop_table("bt_variants")
    op.drop_table("bt_senses")
    op.drop_index("idx_bt_entries_norm_key", table_name="bt_entries")
    op.drop_table("bt_entries")
    op.drop_index("idx_forms_formi_key", table_name="forms")
    op.drop_index("idx_forms_form_key", table_name="forms")
    op.drop_index("idx_forms_stem_key", table_name="forms")
    op.drop_index("idx_forms_title_key", table_name="forms")
    op.drop_index("idx_forms_bt_key", table_name="forms")
    op.drop_table("forms")
