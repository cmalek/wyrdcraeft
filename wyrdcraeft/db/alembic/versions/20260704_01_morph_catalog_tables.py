"""
Add morphology Wright catalog reference tables.

Revision ID: 20260704_01
Revises: 20260703_01
Create Date: 2026-07-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for morphology catalog tables.
revision: str = "20260704_01"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260703_01"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Create morphology catalog reference and junction tables.

    Side Effects:
        Adds morph catalog tables and lookup indexes to the target DB.

    """
    op.create_table(
        "morph_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_key", sa.Text(), nullable=False, unique=True),
        sa.Column("citation_apa", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("retrieved_date", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "morph_classes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("class_key", sa.Text(), nullable=False, unique=True),
        sa.Column("pos", sa.Text(), nullable=False),
        sa.Column("canonical_name", sa.Text(), nullable=False),
        sa.Column("modern_class", sa.Text(), nullable=False),
        sa.Column("traditional_class", sa.Text(), nullable=False),
        sa.Column("wright_label", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "mapping_rationale", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_assignable", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "paradigmatic_words_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "aliases_json", sa.Text(), nullable=False, server_default="[]"
        ),
        sa.Column(
            "features_json", sa.Text(), nullable=False, server_default="{}"
        ),
    )
    op.create_index("idx_morph_classes_pos", "morph_classes", ["pos"])
    op.create_index(
        "idx_morph_classes_class_key", "morph_classes", ["class_key"]
    )

    op.create_table(
        "wright_sections",
        sa.Column("section_no", sa.Integer(), primary_key=True),
        sa.Column("section_text", sa.Text(), nullable=True),
        sa.Column(
            "work",
            sa.Text(),
            nullable=False,
            server_default="Wright & Wright, Old English Grammar",
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "morph_class_wright_sections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "morph_class_id",
            sa.Integer(),
            sa.ForeignKey("morph_classes.id"),
            nullable=False,
        ),
        sa.Column(
            "section_no",
            sa.Integer(),
            sa.ForeignKey("wright_sections.section_no"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("morph_class_id", "section_no"),
    )
    op.create_index(
        "idx_morph_class_wright_sections_section_no",
        "morph_class_wright_sections",
        ["section_no"],
    )

    op.create_table(
        "morph_class_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "morph_class_id",
            sa.Integer(),
            sa.ForeignKey("morph_classes.id"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("morph_sources.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("morph_class_id", "source_id"),
    )


def downgrade() -> None:
    """
    Drop morphology catalog reference and junction tables.

    Side Effects:
        Removes morph catalog tables and their dependent indexes.

    """
    op.drop_table("morph_class_sources")
    op.drop_index(
        "idx_morph_class_wright_sections_section_no",
        table_name="morph_class_wright_sections",
    )
    op.drop_table("morph_class_wright_sections")
    op.drop_table("wright_sections")
    op.drop_index("idx_morph_classes_class_key", table_name="morph_classes")
    op.drop_index("idx_morph_classes_pos", table_name="morph_classes")
    op.drop_table("morph_classes")
    op.drop_table("morph_sources")
