"""
Create POS reference tables and replace dictionary/catalog text POS columns.

Revision ID: 20260706_01
Revises: 20260704_02
Create Date: 2026-07-06
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

#: Alembic revision identifier for POS reference-table normalization.
revision: str = "20260706_01"
#: Previous Alembic revision identifier.
down_revision: str | None = "20260704_02"
#: Alembic branch labels for this revision.
branch_labels: str | tuple[str, ...] | None = None
#: Alembic revision dependencies.
depends_on: str | tuple[str, ...] | None = None

#: BT dictionary POS labels mapped to canonical ``parts_of_speech.code`` values.
_BT_TO_CANONICAL_POS: dict[str, str] = {
    "noun": "noun",
    "verb": "verb",
    "adj": "adjective",
    "adv": "adverb",
    "pron": "pronoun",
    "numeral": "numeral",
    "prep": "preposition",
    "conj": "conjunction",
    "interj": "interjection",
    "indecl": "indeclinable",
    "unknown": "unknown",
}
def upgrade() -> None:
    """
    Seed POS lookup tables and convert product tables to POS foreign keys.

    Side Effects:
        Creates and seeds ``parts_of_speech`` / ``inflection_codes``, then
        replaces text POS columns on ``bt_entries``, ``morph_classes``, and
        ``lemma_morph_classes`` with ``pos_id`` foreign keys.

    """
    bind = op.get_bind()
    sqlite_connection = _require_sqlite_connection(bind)
    pos_map = ensure_parts_of_speech(sqlite_connection)
    ensure_inflection_codes(sqlite_connection, pos_map)
    _upgrade_bt_entries(bind, pos_map=pos_map)
    _upgrade_morph_classes(bind)
    _upgrade_lemma_morph_classes(bind)


def downgrade() -> None:
    """
    Restore legacy text POS columns and remove normalized POS lookup tables.

    Side Effects:
        Replaces ``pos_id`` foreign keys with legacy text POS columns on the
        affected product tables, restores legacy BT headword column names, and
        drops ``inflection_codes`` / ``parts_of_speech``.

    """
    bind = op.get_bind()
    _downgrade_lemma_morph_classes(bind)
    _downgrade_morph_classes(bind)
    _downgrade_bt_entries(bind)
    op.drop_index("idx_inflection_codes_pos_id", table_name="inflection_codes")
    op.drop_index("idx_inflection_codes_code", table_name="inflection_codes")
    op.drop_table("inflection_codes")
    op.drop_index("idx_parts_of_speech_code", table_name="parts_of_speech")
    op.drop_table("parts_of_speech")


def _require_sqlite_connection(bind: Connection) -> sqlite3.Connection:
    """
    Return the sqlite3 driver connection underneath one Alembic bind.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Returns:
        Underlying ``sqlite3.Connection`` used by the current SQLAlchemy bind.

    Raises:
        TypeError: The migration is not running against the sqlite3 driver.

    """
    proxied_connection = bind.connection
    driver_connection = getattr(proxied_connection, "driver_connection", None)
    if isinstance(driver_connection, sqlite3.Connection):
        return driver_connection
    legacy_connection = getattr(proxied_connection, "connection", None)
    if isinstance(legacy_connection, sqlite3.Connection):
        return legacy_connection
    msg = "Migration 20260706_01 requires a sqlite3 driver connection."
    raise TypeError(msg)


def _upgrade_bt_entries(bind: Connection, *, pos_map: dict[str, int]) -> None:
    """
    Replace legacy BT text POS and headword columns with normalized fields.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Keyword Args:
        pos_map: Seeded mapping from canonical POS code to surrogate identifier.

    Side Effects:
        Adds and backfills ``bt_entries.pos_id``, renames
        ``headword_macronized`` to ``headword``, drops ``headword_raw`` /
        ``pos``, and recreates the uniqueness constraint on ``(norm_key,
        pos_id)``.

    Raises:
        ValueError: Backfill produced one or more NULL ``pos_id`` values.

    """
    op.add_column("bt_entries", sa.Column("pos_id", sa.Integer(), nullable=True))
    bind.execute(
        sa.text(
            """
            UPDATE bt_entries
            SET pos_id = CASE pos
                WHEN 'noun' THEN :noun_id
                WHEN 'verb' THEN :verb_id
                WHEN 'adj' THEN :adjective_id
                WHEN 'adv' THEN :adverb_id
                WHEN 'pron' THEN :pronoun_id
                WHEN 'numeral' THEN :numeral_id
                WHEN 'prep' THEN :preposition_id
                WHEN 'conj' THEN :conjunction_id
                WHEN 'interj' THEN :interjection_id
                WHEN 'indecl' THEN :indeclinable_id
                ELSE :unknown_id
            END
            """
        ),
        {
            "noun_id": pos_map["noun"],
            "verb_id": pos_map["verb"],
            "adjective_id": pos_map["adjective"],
            "adverb_id": pos_map["adverb"],
            "pronoun_id": pos_map["pronoun"],
            "numeral_id": pos_map["numeral"],
            "preposition_id": pos_map["preposition"],
            "conjunction_id": pos_map["conjunction"],
            "interjection_id": pos_map["interjection"],
            "indeclinable_id": pos_map["indeclinable"],
            "unknown_id": pos_map["unknown"],
        },
    )
    _assert_no_null_pos_ids(bind, table_name="bt_entries")
    with op.batch_alter_table("bt_entries", recreate="always") as batch_op:
        batch_op.alter_column(
            "headword_macronized",
            existing_type=sa.Text(),
            new_column_name="headword",
        )
        batch_op.drop_column("headword_raw")
        batch_op.drop_column("pos")
        batch_op.alter_column("pos_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_bt_entries_pos_id_parts_of_speech",
            "parts_of_speech",
            ["pos_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_bt_entries_norm_key_pos_id",
            ["norm_key", "pos_id"],
        )


def _upgrade_morph_classes(bind: Connection) -> None:
    """
    Replace morphology catalog text POS values with POS foreign keys.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Side Effects:
        Adds and backfills ``morph_classes.pos_id``, drops legacy text ``pos``,
        and recreates the ``idx_morph_classes_pos`` index on ``pos_id``.

    Raises:
        ValueError: Backfill produced one or more NULL ``pos_id`` values.

    """
    op.add_column("morph_classes", sa.Column("pos_id", sa.Integer(), nullable=True))
    bind.execute(
        sa.text(
            """
            UPDATE morph_classes
            SET pos_id = (
                SELECT id
                FROM parts_of_speech
                WHERE code = morph_classes.pos
            )
            """
        )
    )
    _assert_no_null_pos_ids(bind, table_name="morph_classes")
    op.drop_index("idx_morph_classes_pos", table_name="morph_classes")
    with op.batch_alter_table("morph_classes", recreate="always") as batch_op:
        batch_op.drop_column("pos")
        batch_op.alter_column("pos_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_morph_classes_pos_id_parts_of_speech",
            "parts_of_speech",
            ["pos_id"],
            ["id"],
        )
        batch_op.create_index("idx_morph_classes_pos", ["pos_id"])


def _upgrade_lemma_morph_classes(bind: Connection) -> None:
    """
    Replace lemma-assignment text POS values with POS foreign keys.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Side Effects:
        Adds and backfills ``lemma_morph_classes.pos_id``, drops legacy text
        ``pos``, and recreates the uniqueness constraint on
        ``(normalized_title, pos_id)``.

    Raises:
        ValueError: Backfill produced one or more NULL ``pos_id`` values.

    """
    op.add_column(
        "lemma_morph_classes",
        sa.Column("pos_id", sa.Integer(), nullable=True),
    )
    bind.execute(
        sa.text(
            """
            UPDATE lemma_morph_classes
            SET pos_id = (
                SELECT id
                FROM parts_of_speech
                WHERE code = lemma_morph_classes.pos
            )
            """
        )
    )
    _assert_no_null_pos_ids(bind, table_name="lemma_morph_classes")
    with op.batch_alter_table("lemma_morph_classes", recreate="always") as batch_op:
        batch_op.drop_column("pos")
        batch_op.alter_column("pos_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_lemma_morph_classes_pos_id_parts_of_speech",
            "parts_of_speech",
            ["pos_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_lemma_morph_classes_normalized_title_pos_id",
            ["normalized_title", "pos_id"],
        )


def _downgrade_bt_entries(bind: Connection) -> None:
    """
    Restore legacy BT text POS and dual-headword columns.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Side Effects:
        Adds and backfills legacy ``pos`` / ``headword_raw`` /
        ``headword_macronized`` columns, then removes ``pos_id`` and
        ``headword``.

    Raises:
        ValueError: Backfill produced one or more NULL legacy ``pos`` values.

    """
    op.add_column("bt_entries", sa.Column("pos", sa.Text(), nullable=True))
    op.add_column("bt_entries", sa.Column("headword_raw", sa.Text(), nullable=True))
    bind.execute(sa.text("UPDATE bt_entries SET headword_raw = headword"))
    bind.execute(
        sa.text(
            """
            UPDATE bt_entries
            SET pos = CASE (
                SELECT code
                FROM parts_of_speech
                WHERE id = bt_entries.pos_id
            )
                WHEN 'noun' THEN 'noun'
                WHEN 'verb' THEN 'verb'
                WHEN 'adjective' THEN 'adj'
                WHEN 'adverb' THEN 'adv'
                WHEN 'pronoun' THEN 'pron'
                WHEN 'numeral' THEN 'numeral'
                WHEN 'preposition' THEN 'prep'
                WHEN 'conjunction' THEN 'conj'
                WHEN 'interjection' THEN 'interj'
                WHEN 'indeclinable' THEN 'indecl'
                ELSE 'unknown'
            END
            """
        )
    )
    _assert_no_null_text_pos(bind, table_name="bt_entries")
    with op.batch_alter_table("bt_entries", recreate="always") as batch_op:
        batch_op.alter_column(
            "headword",
            existing_type=sa.Text(),
            new_column_name="headword_macronized",
        )
        batch_op.alter_column("pos", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("headword_raw", existing_type=sa.Text(), nullable=False)
        batch_op.drop_column("pos_id")
        batch_op.create_unique_constraint(
            "uq_bt_entries_norm_key_pos",
            ["norm_key", "pos"],
        )


def _downgrade_morph_classes(bind: Connection) -> None:
    """
    Restore legacy morphology catalog text POS values.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Side Effects:
        Adds and backfills legacy text ``pos`` on ``morph_classes``, then
        removes ``pos_id`` and recreates ``idx_morph_classes_pos`` on the text
        column.

    Raises:
        ValueError: Backfill produced one or more NULL legacy ``pos`` values.

    """
    op.add_column("morph_classes", sa.Column("pos", sa.Text(), nullable=True))
    bind.execute(
        sa.text(
            """
            UPDATE morph_classes
            SET pos = (
                SELECT code
                FROM parts_of_speech
                WHERE id = morph_classes.pos_id
            )
            """
        )
    )
    _assert_no_null_text_pos(bind, table_name="morph_classes")
    op.drop_index("idx_morph_classes_pos", table_name="morph_classes")
    with op.batch_alter_table("morph_classes", recreate="always") as batch_op:
        batch_op.alter_column("pos", existing_type=sa.Text(), nullable=False)
        batch_op.drop_column("pos_id")
        batch_op.create_index("idx_morph_classes_pos", ["pos"])


def _downgrade_lemma_morph_classes(bind: Connection) -> None:
    """
    Restore legacy lemma-assignment text POS values.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Side Effects:
        Adds and backfills legacy text ``pos`` on ``lemma_morph_classes``, then
        removes ``pos_id`` and recreates the text uniqueness constraint.

    Raises:
        ValueError: Backfill produced one or more NULL legacy ``pos`` values.

    """
    op.add_column("lemma_morph_classes", sa.Column("pos", sa.Text(), nullable=True))
    bind.execute(
        sa.text(
            """
            UPDATE lemma_morph_classes
            SET pos = (
                SELECT code
                FROM parts_of_speech
                WHERE id = lemma_morph_classes.pos_id
            )
            """
        )
    )
    _assert_no_null_text_pos(bind, table_name="lemma_morph_classes")
    with op.batch_alter_table("lemma_morph_classes", recreate="always") as batch_op:
        batch_op.alter_column("pos", existing_type=sa.Text(), nullable=False)
        batch_op.drop_column("pos_id")
        batch_op.create_unique_constraint(
            "uq_lemma_morph_classes_normalized_title_pos",
            ["normalized_title", "pos"],
        )


def _assert_no_null_pos_ids(bind: Connection, *, table_name: str) -> None:
    """
    Verify one upgraded table has no NULL ``pos_id`` rows.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Keyword Args:
        table_name: Table name whose ``pos_id`` column should be fully backfilled.

    Raises:
        ValueError: One or more rows still have ``pos_id`` set to NULL.

    """
    null_count = bind.execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE pos_id IS NULL")  # noqa: S608
    ).scalar_one()
    if int(null_count) != 0:
        msg = f"{table_name} still contains NULL pos_id values after backfill"
        raise ValueError(msg)


def _assert_no_null_text_pos(bind: Connection, *, table_name: str) -> None:
    """
    Verify one downgraded table has no NULL text ``pos`` rows.

    Args:
        bind: Alembic SQLAlchemy connection for the running migration.

    Keyword Args:
        table_name: Table name whose legacy text ``pos`` should be fully backfilled.

    Raises:
        ValueError: One or more rows still have legacy ``pos`` set to NULL.

    """
    null_count = bind.execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE pos IS NULL")  # noqa: S608
    ).scalar_one()
    if int(null_count) != 0:
        msg = f"{table_name} still contains NULL pos values after backfill"
        raise ValueError(msg)
