"""Focused tests for the normalized Bosworth-Toller SQLite sink."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _seed_forms_table(db_path: Path, row_count: int) -> int:
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, function, wright, paradigm, paraID,
                wordclass, class1, class2, class3, comment, bt_key, title_key,
                stem_key, form_key, formi_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    "",
                    "0",
                    "0",
                    "No",
                    "0",
                    "demo",
                    "0",
                    "noun",
                    "",
                    "",
                    "",
                    "",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                    f"lemma-{index}",
                )
                for index in range(row_count)
            ],
        )
        conn.commit()
    return row_count


def _run_index(db_path: Path, *, attach_mode: bool = False) -> None:
    sink = BTSqliteSink(db_path, attach_mode=attach_mode)
    try:
        BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()


def test_sink_persists_headword_with_normalized_pos_fk(temp_dir: Path) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    _seed_forms_table(index_db, row_count=1)

    _run_index(index_db)

    with sqlite3.connect(index_db) as conn:
        conn.row_factory = sqlite3.Row
        entry = conn.execute(
            """
            SELECT e.norm_key, e.headword, p.code AS pos_code
            FROM bt_entries e
            JOIN parts_of_speech p ON p.id = e.pos_id
            WHERE e.norm_key = ? AND p.code = ?
            """,
            ("abbad", "noun"),
        ).fetchone()
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(bt_entries)").fetchall()
        }

    assert entry is not None
    assert entry["headword"] == "abbad"
    assert entry["pos_code"] == "noun"
    assert {"headword", "pos_id"} <= columns
    assert "headword_raw" not in columns
    assert "headword_macronized" not in columns
    assert "pos" not in columns


def test_sink_rerun_reuses_seeded_parts_of_speech_rows(temp_dir: Path) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    _seed_forms_table(index_db, row_count=1)

    _run_index(index_db, attach_mode=True)
    with sqlite3.connect(index_db) as conn:
        first_pos_count = conn.execute("SELECT COUNT(*) FROM parts_of_speech").fetchone()[0]

    _run_index(index_db, attach_mode=True)
    with sqlite3.connect(index_db) as conn:
        second_pos_count = conn.execute(
            "SELECT COUNT(*) FROM parts_of_speech"
        ).fetchone()[0]

    assert first_pos_count > 0
    assert second_pos_count == first_pos_count
