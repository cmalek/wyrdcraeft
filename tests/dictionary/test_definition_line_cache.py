"""Tests for the cached ``bt_entries.definition_line_cache`` column."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy import event

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.services.dictionary import definition_cache as definition_cache_module
from wyrdcraeft.services.dictionary.browse_query import DictionaryBrowseQueryService
from wyrdcraeft.services.dictionary.definition_cache import DefinitionLineCache
from wyrdcraeft.services.dictionary.definition_line import definition_line
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from sqlalchemy.engine import Connection

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


@pytest.fixture
def lexicon_source_db(tmp_path: Path) -> Path:
    """Dictionary-backed canonical DB fixture for definition-line cache tests."""
    db_path = tmp_path / "definition-cache.sqlite3"
    upgrade_canonical_db(db_path)
    sink = BTSqliteSink(db_path, attach_mode=True)
    try:
        BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()
    return db_path


@pytest.fixture
def connection(lexicon_source_db: Path) -> Iterator[Connection]:
    """Long-lived writable connection, as the browse service holds."""
    engine = create_engine(lexicon_source_db)
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()
        engine.dispose()


def _entry_with_senses(db_path: Path) -> int:
    """Return the first entry id that has at least one non-empty gloss."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT entry_id FROM bt_senses
            WHERE TRIM(gloss_en) != ''
            ORDER BY entry_id ASC LIMIT 1
            """
        ).fetchone()
    assert row is not None
    return int(row[0])


def _entries_with_senses(db_path: Path) -> list[int]:
    """Return two distinct entry ids that both have senses."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT entry_id FROM bt_senses ORDER BY entry_id ASC LIMIT 2"
        ).fetchall()
    assert len(rows) == 2
    return [int(row[0]) for row in rows]


def _expected_line(db_path: Path, entry_id: int) -> str:
    """Compute the expected definition line straight from the stored senses."""
    with sqlite3.connect(db_path) as conn:
        pos_row = conn.execute(
            """
            SELECT p.code FROM bt_entries e
            JOIN parts_of_speech p ON p.id = e.pos_id
            WHERE e.id = ?
            """,
            (entry_id,),
        ).fetchone()
        glosses = conn.execute(
            """
            SELECT gloss_en FROM bt_senses WHERE entry_id = ?
            ORDER BY order_index ASC, id ASC
            """,
            (entry_id,),
        ).fetchall()
    assert pos_row is not None
    return definition_line(str(pos_row[0]), [str(row[0]).strip() for row in glosses])


def _raw_cache(db_path: Path, entry_id: int) -> str | None:
    """Read the cache column with an independent connection."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT definition_line_cache FROM bt_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
    assert row is not None
    return row[0]


def _execute(db_path: Path, sql: str, params: Sequence[object] = ()) -> None:
    """Run one write statement on an independent connection and commit."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(sql, tuple(params))
        conn.commit()


def _insert_sense(db_path: Path, entry_id: int, gloss: str) -> None:
    """Insert one minimal sense row for *entry_id*."""
    _execute(
        db_path,
        """
        INSERT INTO bt_senses (
            entry_id, sense_label, gloss_en, order_index, sense_path,
            parent_path, source_label_raw, source_fragment_raw,
            prefix_fragment_raw, modifiers_json, grammatical_context_json,
            usage_note
        ) VALUES (?, '', ?, 99, '99', NULL, '', ?, '', '[]', '[]', '')
        """,
        (entry_id, gloss, gloss),
    )


def _new_entry_without_senses(db_path: Path) -> int:
    """Insert one entry with no senses and return its id."""
    with sqlite3.connect(db_path) as conn:
        pos_id = conn.execute(
            "SELECT id FROM parts_of_speech WHERE code = 'noun'"
        ).fetchone()[0]
        cursor = conn.execute(
            """
            INSERT INTO bt_entries (
                norm_key, headword, normalized_title, pos_id, genders_json,
                etymology, see_also_json, source_line_nos_json, entry_order
            ) VALUES ('zzz', 'zzz', 'zzz', ?, '[]', '', '[]', '[]', 9999)
            """,
            (pos_id,),
        )
        conn.commit()
        assert cursor.lastrowid is not None
        return int(cursor.lastrowid)


def _prime(db_path: Path, connection: Connection, entry_id: int) -> None:
    """Fill the cache for *entry_id* and assert it was stored."""
    DefinitionLineCache(connection).get(entry_id)
    assert _raw_cache(db_path, entry_id) is not None


def test_first_get_computes_and_stores(
    lexicon_source_db: Path, connection: Connection
) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)
    cache = DefinitionLineCache(connection)
    assert cache.peek(entry_id) is None

    line = cache.get(entry_id)

    expected = _expected_line(lexicon_source_db, entry_id)
    assert line == expected
    assert line
    assert _raw_cache(lexicon_source_db, entry_id) == expected
    assert cache.peek(entry_id) == expected


def test_second_get_does_not_recompute(
    lexicon_source_db: Path,
    connection: Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def counting_line(pos: str, glosses: Sequence[str]) -> str:
        calls.append(pos)
        return definition_line(pos, glosses)

    monkeypatch.setattr(definition_cache_module, "definition_line", counting_line)
    entry_id = _entry_with_senses(lexicon_source_db)
    cache = DefinitionLineCache(connection)

    first = cache.get(entry_id)
    second = cache.get(entry_id)

    assert first == second
    assert len(calls) == 1


def test_entry_without_senses_caches_empty_string_once(
    lexicon_source_db: Path,
    connection: Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def counting_line(pos: str, glosses: Sequence[str]) -> str:
        calls.append(pos)
        return definition_line(pos, glosses)

    monkeypatch.setattr(definition_cache_module, "definition_line", counting_line)
    entry_id = _new_entry_without_senses(lexicon_source_db)
    cache = DefinitionLineCache(connection)

    assert cache.get(entry_id) == ""
    assert cache.get(entry_id) == ""
    assert _raw_cache(lexicon_source_db, entry_id) == ""
    assert cache.peek(entry_id) == ""
    assert len(calls) == 1


def test_sense_insert_update_delete_clear_cache(
    lexicon_source_db: Path, connection: Connection
) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)

    _prime(lexicon_source_db, connection, entry_id)
    _insert_sense(lexicon_source_db, entry_id, "an added sense")
    assert _raw_cache(lexicon_source_db, entry_id) is None
    assert "an added sense" in DefinitionLineCache(connection).get(entry_id)

    _prime(lexicon_source_db, connection, entry_id)
    _execute(
        lexicon_source_db,
        "UPDATE bt_senses SET gloss_en = 'a changed sense' "
        "WHERE entry_id = ? AND order_index = 99",
        (entry_id,),
    )
    assert _raw_cache(lexicon_source_db, entry_id) is None
    assert "a changed sense" in DefinitionLineCache(connection).get(entry_id)

    _prime(lexicon_source_db, connection, entry_id)
    _execute(
        lexicon_source_db,
        "DELETE FROM bt_senses WHERE entry_id = ? AND order_index = 99",
        (entry_id,),
    )
    assert _raw_cache(lexicon_source_db, entry_id) is None
    assert "a changed sense" not in DefinitionLineCache(connection).get(entry_id)


def test_variant_change_clears_cache(
    lexicon_source_db: Path, connection: Connection
) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)

    _prime(lexicon_source_db, connection, entry_id)
    _execute(
        lexicon_source_db,
        """
        INSERT INTO bt_variants (
            entry_id, spelling_raw, spelling_macronized, normalized_title
        ) VALUES (?, 'qqq', 'qqq', 'qqq')
        """,
        (entry_id,),
    )
    assert _raw_cache(lexicon_source_db, entry_id) is None

    _prime(lexicon_source_db, connection, entry_id)
    _execute(
        lexicon_source_db,
        "UPDATE bt_variants SET spelling_raw = 'qqr' WHERE spelling_raw = 'qqq'",
    )
    assert _raw_cache(lexicon_source_db, entry_id) is None

    _prime(lexicon_source_db, connection, entry_id)
    _execute(lexicon_source_db, "DELETE FROM bt_variants WHERE spelling_raw = 'qqr'")
    assert _raw_cache(lexicon_source_db, entry_id) is None


def test_pos_change_clears_cache(
    lexicon_source_db: Path, connection: Connection
) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)
    _prime(lexicon_source_db, connection, entry_id)

    _execute(
        lexicon_source_db,
        """
        UPDATE bt_entries
        SET pos_id = (
            SELECT id FROM parts_of_speech
            WHERE id != bt_entries.pos_id ORDER BY id LIMIT 1
        )
        WHERE id = ?
        """,
        (entry_id,),
    )

    assert _raw_cache(lexicon_source_db, entry_id) is None


def test_writing_the_cache_does_not_clear_it(
    lexicon_source_db: Path, connection: Connection
) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)

    _execute(
        lexicon_source_db,
        "UPDATE bt_entries SET definition_line_cache = 'stored' WHERE id = ?",
        (entry_id,),
    )
    _execute(
        lexicon_source_db,
        "UPDATE bt_entries SET headword = headword WHERE id = ?",
        (entry_id,),
    )

    assert _raw_cache(lexicon_source_db, entry_id) == "stored"
    assert DefinitionLineCache(connection).get(entry_id) == "stored"


def test_moving_a_sense_to_another_entry_clears_both(
    lexicon_source_db: Path, connection: Connection
) -> None:
    source_id, target_id = _entries_with_senses(lexicon_source_db)
    _prime(lexicon_source_db, connection, source_id)
    _prime(lexicon_source_db, connection, target_id)

    _execute(
        lexicon_source_db,
        """
        UPDATE bt_senses SET entry_id = ?
        WHERE id = (SELECT MIN(id) FROM bt_senses WHERE entry_id = ?)
        """,
        (target_id, source_id),
    )

    assert _raw_cache(lexicon_source_db, source_id) is None
    assert _raw_cache(lexicon_source_db, target_id) is None


def test_failed_cache_write_returns_computed_line(lexicon_source_db: Path) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)
    expected = _expected_line(lexicon_source_db, entry_id)
    engine = sqlalchemy_create_engine(
        f"sqlite:///{lexicon_source_db}",
        connect_args={"timeout": 0.05},
    )
    locker = sqlite3.connect(lexicon_source_db, isolation_level=None)
    conn = engine.connect()
    try:
        locker.execute("BEGIN IMMEDIATE")
        cache = DefinitionLineCache(conn)

        assert cache.get(entry_id) == expected
        assert cache.peek(entry_id) is None

        locker.execute("ROLLBACK")
        assert cache.get(entry_id) == expected
        assert cache.peek(entry_id) is None
        assert DefinitionLineCache(conn).get(entry_id) == expected
        assert cache.peek(entry_id) == expected
    finally:
        conn.close()
        engine.dispose()
        locker.close()


def test_failed_write_is_not_retried_while_locked(lexicon_source_db: Path) -> None:
    first_id, second_id = _entries_with_senses(lexicon_source_db)
    engine = sqlalchemy_create_engine(
        f"sqlite:///{lexicon_source_db}",
        connect_args={"timeout": 0.5},
    )
    updates: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _count_updates(*args: object) -> None:
        statement = str(args[2])
        if statement.lstrip().upper().startswith("UPDATE BT_ENTRIES"):
            updates.append(statement)

    locker = sqlite3.connect(lexicon_source_db, isolation_level=None)
    conn = engine.connect()
    try:
        locker.execute("BEGIN IMMEDIATE")
        cache = DefinitionLineCache(conn)
        assert cache.get(first_id) == _expected_line(lexicon_source_db, first_id)

        started = time.monotonic()
        line = cache.get(second_id)
        elapsed = time.monotonic() - started

        assert line == _expected_line(lexicon_source_db, second_id)
        assert elapsed < 0.25
        assert len(updates) == 1
        assert cache.peek(second_id) is None
    finally:
        conn.close()
        engine.dispose()
        locker.close()


def test_glosses_follow_details_sense_path_order(
    lexicon_source_db: Path, connection: Connection
) -> None:
    entry_id = _new_entry_without_senses(lexicon_source_db)
    for gloss, order_index, path in (
        ("first", 0, "1"),
        ("second", 1, "2"),
        ("first sub", 2, "1.1"),
    ):
        _execute(
            lexicon_source_db,
            """
            INSERT INTO bt_senses (
                entry_id, sense_label, gloss_en, order_index, sense_path,
                parent_path, source_label_raw, source_fragment_raw,
                prefix_fragment_raw, modifiers_json, grammatical_context_json,
                usage_note
            ) VALUES (?, '', ?, ?, ?, NULL, '', ?, '', '[]', '[]', '')
            """,
            (entry_id, gloss, order_index, path, gloss),
        )
    service = DictionaryBrowseQueryService(lexicon_source_db)
    try:
        details = service.get_details(entry_id)
    finally:
        service.close()
    assert details is not None
    details_order = [sense.gloss_en for sense in details.senses]
    assert details_order == ["first", "first sub", "second"]

    assert DefinitionLineCache(connection).get(entry_id) == definition_line(
        details.pos, details_order
    )


def test_read_only_cache_never_writes(lexicon_source_db: Path) -> None:
    entry_id = _entry_with_senses(lexicon_source_db)
    empty_id = _new_entry_without_senses(lexicon_source_db)
    engine = sqlalchemy_create_engine(f"sqlite:///{lexicon_source_db}")
    updates: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _count_updates(*args: object) -> None:
        statement = str(args[2])
        if statement.lstrip().upper().startswith("UPDATE"):
            updates.append(statement)

    conn = engine.connect()
    try:
        cache = DefinitionLineCache(conn, write=False)
        assert cache.get(entry_id) == _expected_line(lexicon_source_db, entry_id)
        assert cache.get(empty_id) == ""
        assert cache.get(entry_id) == _expected_line(lexicon_source_db, entry_id)
        assert updates == []
        assert _raw_cache(lexicon_source_db, entry_id) is None
        assert _raw_cache(lexicon_source_db, empty_id) is None
    finally:
        conn.close()
        engine.dispose()
