"""
Add the cached browse definition line and the triggers that clear it.

Revision ID: 20261115_01
Revises: 20260707_03
Create Date: 2026-11-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

#: Alembic revision identifier for the cached definition line.
revision: str = "20261115_01"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260707_03"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None

#: SQL that nulls one entry's cached line; ``{ref}`` is ``NEW`` or ``OLD``.
_CLEAR_SQL = (
    "UPDATE bt_entries SET definition_line_cache = NULL "
    "WHERE id = {ref}.entry_id;"
)

#: Trigger name to ``CREATE TRIGGER`` body, in creation order.
_TRIGGERS: dict[str, str] = {
    "trg_bt_senses_insert_clear_definition_line": (
        "AFTER INSERT ON bt_senses BEGIN " + _CLEAR_SQL.format(ref="NEW") + " END"
    ),
    "trg_bt_senses_update_clear_definition_line": (
        "AFTER UPDATE ON bt_senses BEGIN "
        + _CLEAR_SQL.format(ref="OLD")
        + " "
        + _CLEAR_SQL.format(ref="NEW")
        + " END"
    ),
    "trg_bt_senses_delete_clear_definition_line": (
        "AFTER DELETE ON bt_senses BEGIN " + _CLEAR_SQL.format(ref="OLD") + " END"
    ),
    "trg_bt_variants_insert_clear_definition_line": (
        "AFTER INSERT ON bt_variants BEGIN " + _CLEAR_SQL.format(ref="NEW") + " END"
    ),
    "trg_bt_variants_update_clear_definition_line": (
        "AFTER UPDATE ON bt_variants BEGIN "
        + _CLEAR_SQL.format(ref="OLD")
        + " "
        + _CLEAR_SQL.format(ref="NEW")
        + " END"
    ),
    "trg_bt_variants_delete_clear_definition_line": (
        "AFTER DELETE ON bt_variants BEGIN " + _CLEAR_SQL.format(ref="OLD") + " END"
    ),
    "trg_bt_entries_pos_clear_definition_line": (
        "AFTER UPDATE OF pos_id ON bt_entries "
        "WHEN OLD.pos_id IS NOT NEW.pos_id BEGIN "
        "UPDATE bt_entries SET definition_line_cache = NULL WHERE id = NEW.id; "
        "END"
    ),
}


def upgrade() -> None:
    """
    Add ``bt_entries.definition_line_cache`` and its clearing triggers.

    Side Effects:
        Adds a nullable text column to ``bt_entries`` and creates SQLite
        triggers that null it when the entry's senses, variants or part of
        speech change.

    """
    op.add_column(
        "bt_entries",
        sa.Column("definition_line_cache", sa.Text(), nullable=True),
    )
    for name, body in _TRIGGERS.items():
        op.execute(f"CREATE TRIGGER {name} {body}")


def downgrade() -> None:
    """
    Drop the clearing triggers and the cached definition line column.

    Side Effects:
        Drops the triggers created by :func:`upgrade` and removes
        ``bt_entries.definition_line_cache``.

    """
    for name in reversed(_TRIGGERS):
        op.execute(f"DROP TRIGGER IF EXISTS {name}")
    with op.batch_alter_table("bt_entries") as batch_op:
        batch_op.drop_column("definition_line_cache")
