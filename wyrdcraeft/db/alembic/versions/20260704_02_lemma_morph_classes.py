"""
Add lemma morph-class assignment table and recognition hints column.

Revision ID: 20260704_02
Revises: 20260704_01
Create Date: 2026-07-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for lemma morph-class assignment schema.
revision: str = "20260704_02"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260704_01"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Add recognition hints to morph classes and create lemma assignment table.

    Side Effects:
        Adds ``recognition_hints_json`` to ``morph_classes`` and creates
        ``lemma_morph_classes`` with lookup indexes.

    """
    op.add_column(
        "morph_classes",
        sa.Column(
            "recognition_hints_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
    )

    op.create_table(
        "lemma_morph_classes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("pos", sa.Text(), nullable=False),
        sa.Column(
            "morph_class_id",
            sa.Integer(),
            sa.ForeignKey("morph_classes.id"),
            nullable=False,
        ),
        sa.Column(
            "assignment_source",
            sa.Text(),
            nullable=False,
            server_default="rule",
        ),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="100"),
        sa.Column(
            "features_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("normalized_title", "pos"),
    )
    op.create_index(
        "idx_lemma_morph_classes_morph_class_id",
        "lemma_morph_classes",
        ["morph_class_id"],
    )
    op.create_index(
        "idx_lemma_morph_classes_normalized_title",
        "lemma_morph_classes",
        ["normalized_title"],
    )


def downgrade() -> None:
    """
    Drop lemma assignment table and recognition hints column.

    Side Effects:
        Removes ``lemma_morph_classes`` and ``recognition_hints_json``.

    """
    op.drop_index(
        "idx_lemma_morph_classes_normalized_title",
        table_name="lemma_morph_classes",
    )
    op.drop_index(
        "idx_lemma_morph_classes_morph_class_id",
        table_name="lemma_morph_classes",
    )
    op.drop_table("lemma_morph_classes")
    op.drop_column("morph_classes", "recognition_hints_json")
