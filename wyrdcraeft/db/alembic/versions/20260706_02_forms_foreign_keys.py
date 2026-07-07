"""
Add nullable foreign-key columns to morphology forms.

Revision ID: 20260706_02
Revises: 20260706_01
Create Date: 2026-07-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for forms foreign-key columns.
revision: str = "20260706_02"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260706_01"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Add nullable foreign-key columns to ``forms``.

    Side Effects:
        Adds ``wordclass_id``, ``inflection_code_id``, ``morph_class_id``, and
        ``entry_id`` with lookup indexes. Existing rows remain NULL until the
        morphology sink populates them on rebuild.

    """
    with op.batch_alter_table("forms", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("wordclass_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("inflection_code_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("morph_class_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("entry_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_forms_wordclass_id_parts_of_speech",
            "parts_of_speech",
            ["wordclass_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_forms_inflection_code_id_inflection_codes",
            "inflection_codes",
            ["inflection_code_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_forms_morph_class_id_morph_classes",
            "morph_classes",
            ["morph_class_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_forms_entry_id_bt_entries",
            "bt_entries",
            ["entry_id"],
            ["id"],
        )
        batch_op.create_index("idx_forms_wordclass_id", ["wordclass_id"])
        batch_op.create_index("idx_forms_inflection_code_id", ["inflection_code_id"])
        batch_op.create_index("idx_forms_morph_class_id", ["morph_class_id"])
        batch_op.create_index("idx_forms_entry_id", ["entry_id"])


def downgrade() -> None:
    """
    Remove nullable foreign-key columns from ``forms``.

    Side Effects:
        Drops ``forms`` foreign-key columns and their lookup indexes.

    """
    with op.batch_alter_table("forms", recreate="always") as batch_op:
        batch_op.drop_index("idx_forms_entry_id")
        batch_op.drop_index("idx_forms_morph_class_id")
        batch_op.drop_index("idx_forms_inflection_code_id")
        batch_op.drop_index("idx_forms_wordclass_id")
        batch_op.drop_column("entry_id")
        batch_op.drop_column("morph_class_id")
        batch_op.drop_column("inflection_code_id")
        batch_op.drop_column("wordclass_id")
