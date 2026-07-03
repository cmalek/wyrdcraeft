"""Integration tests for the Bosworth-Toller dictionary index pipeline."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from wyrdcraeft.models.dictionary import BTPos
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink

_CORPUS_SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "corpus_sample.txt"
)
_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _seed_forms_table(db_path: Path, row_count: int) -> int:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE forms (
                id INTEGER PRIMARY KEY,
                lemma TEXT NOT NULL
            );
            """
        )
        for index in range(row_count):
            conn.execute(
                "INSERT INTO forms (lemma) VALUES (?)",
                (f"lemma-{index}",),
            )
        conn.commit()
    return row_count


def _index_fixture(source: Path, temp_dir: Path) -> tuple[Path, dict[str, object]]:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    if not index_db.exists():
        _seed_forms_table(index_db, row_count=1)
    sink = BTSqliteSink(index_db)
    try:
        report = BTIndexPipeline().run(source, sink)
    finally:
        sink.close()
    return index_db, report.to_dict()


def _fetch_entry(
    conn: sqlite3.Connection,
    *,
    norm_key: str,
    pos: str,
) -> sqlite3.Row | None:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT id, norm_key, headword_raw, pos
        FROM bt_entries
        WHERE norm_key = ? AND pos = ?
        """,
        (norm_key, pos),
    ).fetchone()


def test_index_pipeline_corpus_sample(temp_dir: Path) -> None:
    index_db, report = _index_fixture(_CORPUS_SAMPLE, temp_dir)

    assert index_db.is_file()
    assert report["parsed"] > 0
    assert report["merged"] > 0
    assert report["senses_written"] > 0
    assert "noun" in report["pos_counts"]
    assert report["skipped"] >= 0


def test_index_pipeline_report_json_fields(temp_dir: Path) -> None:
    _, report = _index_fixture(_SAMPLE_LINES, temp_dir)

    assert set(report) >= {
        "source",
        "index_db",
        "lines_read",
        "parsed",
        "skipped",
        "merged",
        "pos_counts",
        "warning_counts",
        "skipped_by_reason",
    }
    assert isinstance(report["pos_counts"], dict)
    assert isinstance(report["warning_counts"], dict)


def test_abbad_noun_merged_without_separate_add_rows(temp_dir: Path) -> None:
    index_db, _report = _index_fixture(_SAMPLE_LINES, temp_dir)

    with sqlite3.connect(index_db) as conn:
        conn.row_factory = sqlite3.Row
        abbad = _fetch_entry(conn, norm_key="abbad", pos=BTPos.NOUN.value)
        assert abbad is not None

        add_like_rows = conn.execute(
            """
            SELECT norm_key, pos, headword_raw
            FROM bt_entries
            WHERE headword_raw LIKE '%Add%'
               OR norm_key IN ('abbod', 'abbodhad', 'abbodisse')
            """
        ).fetchall()

        assert add_like_rows == []

        sense_rows = conn.execute(
            """
            SELECT sense_label, gloss_en, order_index
            FROM bt_senses
            WHERE entry_id = ?
            ORDER BY order_index
            """,
            (abbad["id"],),
        ).fetchall()
        assert len(sense_rows) >= 2
        labels = {row["sense_label"] for row in sense_rows}
        assert "I" in labels
        assert "II" in labels

        variant_rows = conn.execute(
            """
            SELECT spelling_raw
            FROM bt_variants
            WHERE entry_id = ?
            """,
            (abbad["id"],),
        ).fetchall()
        variant_spellings = {row["spelling_raw"] for row in variant_rows}
        assert "abbod" in variant_spellings


def test_index_pipeline_schema_indexes(temp_dir: Path) -> None:
    index_db, _report = _index_fixture(_SAMPLE_LINES, temp_dir)

    with sqlite3.connect(index_db) as conn:
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
        assert "idx_bt_entries_norm_key" in indexes
        assert "idx_bt_variants_spelling" in indexes

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"bt_entries", "bt_senses", "bt_variants", "bt_edit_log"} <= tables


def test_index_pipeline_preserves_existing_forms_in_canonical_db(
    temp_dir: Path,
) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    initial_forms = _seed_forms_table(index_db, row_count=4)

    sink = BTSqliteSink(index_db)
    try:
        report = BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()

    with sqlite3.connect(index_db) as conn:
        forms_count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        bt_count = conn.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]

    assert forms_count == initial_forms
    assert bt_count == report.merged
    assert bt_count > 0


@pytest.mark.slow
def test_full_oe_bt_index_completes(temp_dir: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "data" / "oe_bt.txt"
    if not source.is_file():
        pytest.skip("data/oe_bt.txt not available")

    report_path = temp_dir / "full_report.json"
    index_db, report = _index_fixture(source, temp_dir)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert report["merged"] > 10_000
    assert report["parsed"] > report["merged"]
    assert sum(report["pos_counts"].values()) == report["merged"]
    assert index_db.stat().st_size > 0
