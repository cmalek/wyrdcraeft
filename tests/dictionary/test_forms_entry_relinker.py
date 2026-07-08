"""Tests for dictionary-driven ``forms.entry_id`` relinking."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.services.dictionary.forms_entry_relinker import FormsEntryRelinker
from wyrdcraeft.services.morphology.catalog.pos_seed import ensure_parts_of_speech

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def relinker_db(tmp_path: Path) -> Iterator[tuple[Path, sqlite3.Connection]]:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    connection = sqlite3.connect(db_path)
    ensure_parts_of_speech(connection)
    connection.commit()
    yield db_path, connection
    connection.close()


def _pos_id(connection: sqlite3.Connection, code: str) -> int:
    return int(
        connection.execute(
            "SELECT id FROM parts_of_speech WHERE code = ?",
            (code,),
        ).fetchone()[0]
    )


def _insert_bt_entry(
    connection: sqlite3.Connection,
    *,
    entry_id: int,
    normalized_title: str,
    pos_code: str,
    norm_key: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO bt_entries (
            id,
            norm_key,
            headword,
            normalized_title,
            pos_id,
            genders_json,
            etymology,
            see_also_json,
            source_line_nos_json,
            entry_order
        ) VALUES (?, ?, ?, ?, ?, '[]', '', '[]', '[]', ?)
        """,
        (
            entry_id,
            norm_key or normalized_title,
            normalized_title,
            normalized_title,
            _pos_id(connection, pos_code),
            entry_id,
        ),
    )


def _insert_bt_variant(
    connection: sqlite3.Connection,
    *,
    entry_id: int,
    normalized_title: str,
    spelling: str,
) -> None:
    connection.execute(
        """
        INSERT INTO bt_variants (
            entry_id,
            spelling_raw,
            spelling_macronized,
            normalized_title
        ) VALUES (?, ?, ?, ?)
        """,
        (entry_id, spelling, spelling, normalized_title),
    )


def _insert_form(
    connection: sqlite3.Connection,
    *,
    form_id: int,
    normalized_title: str,
    wordclass_code: str,
    entry_id: int | None = None,
) -> None:
    token = normalized_title or f"form-{form_id}"
    connection.execute(
        """
        INSERT INTO forms (
            id,
            counter,
            formi,
            BT,
            title,
            normalized_title,
            stem,
            form,
            formParts,
            var,
            probability,
            comment,
            bt_key,
            title_key,
            stem_key,
            form_key,
            formi_key,
            wordclass_id,
            entry_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            form_id,
            form_id,
            token,
            token,
            token,
            normalized_title,
            token,
            token,
            "",
            "0",
            "0",
            "",
            token,
            token,
            token,
            token,
            token,
            _pos_id(connection, wordclass_code),
            entry_id,
        ),
    )


def _fetch_form_entry_id(connection: sqlite3.Connection, form_id: int) -> int | None:
    row = connection.execute(
        "SELECT entry_id FROM forms WHERE id = ?",
        (form_id,),
    ).fetchone()
    assert row is not None
    value = row[0]
    return None if value is None else int(value)


def test_relink_all_noops_for_empty_forms(
    relinker_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, _connection = relinker_db
    engine = create_engine(db_path)
    try:
        with engine.begin() as connection:
            relinker = FormsEntryRelinker(connection)
            assert relinker.relink_all() == 0
    finally:
        engine.dispose()


def test_relink_all_sets_entry_id_for_single_match(
    relinker_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = relinker_db
    _insert_bt_entry(
        connection,
        entry_id=42,
        normalized_title="stān",
        pos_code="noun",
    )
    _insert_form(
        connection,
        form_id=1,
        normalized_title="stān",
        wordclass_code="noun",
    )
    connection.commit()

    engine = create_engine(db_path)
    try:
        relinker = FormsEntryRelinker(engine)
        assert relinker.relink_all() == 1
    finally:
        engine.dispose()

    assert _fetch_form_entry_id(connection, 1) == 42


def test_relink_all_leaves_entry_id_null_for_ambiguous_join(
    relinker_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = relinker_db
    _insert_bt_entry(
        connection,
        entry_id=1,
        normalized_title="alpha",
        pos_code="noun",
    )
    _insert_bt_entry(
        connection,
        entry_id=2,
        normalized_title="beta",
        pos_code="noun",
        norm_key="beta-alt",
    )
    _insert_bt_variant(
        connection,
        entry_id=1,
        normalized_title="alias",
        spelling="alias",
    )
    _insert_bt_variant(
        connection,
        entry_id=2,
        normalized_title="alias",
        spelling="alias",
    )
    _insert_form(
        connection,
        form_id=1,
        normalized_title="alias",
        wordclass_code="noun",
    )
    connection.commit()

    engine = create_engine(db_path)
    try:
        relinker = FormsEntryRelinker(engine)
        assert relinker.relink_all() == 1
    finally:
        engine.dispose()

    assert _fetch_form_entry_id(connection, 1) is None


def test_relink_leaves_entry_id_null_for_same_title_same_pos_homographs(
    relinker_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = relinker_db
    _insert_bt_entry(
        connection,
        entry_id=10,
        normalized_title="dup",
        pos_code="noun",
    )
    _insert_bt_entry(
        connection,
        entry_id=20,
        normalized_title="dup",
        pos_code="noun",
        norm_key="dup-alt",
    )
    _insert_form(
        connection,
        form_id=1,
        normalized_title="dup",
        wordclass_code="noun",
    )
    connection.commit()

    engine = create_engine(db_path)
    try:
        relinker = FormsEntryRelinker(engine)
        assert relinker.relink_all() == 1
    finally:
        engine.dispose()

    assert _fetch_form_entry_id(connection, 1) is None


def test_relink_all_replaces_stale_entry_id_after_dictionary_rebuild(
    relinker_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = relinker_db
    _insert_bt_entry(
        connection,
        entry_id=1,
        normalized_title="stān",
        pos_code="noun",
    )
    _insert_form(
        connection,
        form_id=1,
        normalized_title="stān",
        wordclass_code="noun",
        entry_id=1,
    )
    connection.commit()

    engine = create_engine(db_path)
    try:
        relinker = FormsEntryRelinker(engine)
        assert relinker.clear_all_entry_ids() == 1
    finally:
        engine.dispose()

    assert _fetch_form_entry_id(connection, 1) is None

    connection.execute("DELETE FROM bt_entries WHERE id = 1")
    _insert_bt_entry(
        connection,
        entry_id=5,
        normalized_title="stān",
        pos_code="noun",
        norm_key="stan-rebuilt",
    )
    connection.commit()

    engine = create_engine(db_path)
    try:
        relinker = FormsEntryRelinker(engine)
        assert relinker.relink_all() == 1
    finally:
        engine.dispose()

    assert _fetch_form_entry_id(connection, 1) == 5
