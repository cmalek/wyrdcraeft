"""Integration tests for the Bosworth-Toller dictionary index pipeline."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.models.dictionary import BTPos
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.resources import default_bt_source_path
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
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment, bt_key, title_key,
                stem_key, form_key, formi_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        SELECT e.id, e.norm_key, e.headword, p.code AS pos
        FROM bt_entries e
        JOIN parts_of_speech p ON p.id = e.pos_id
        WHERE e.norm_key = ? AND p.code = ?
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
            SELECT e.norm_key, p.code AS pos, e.headword
            FROM bt_entries e
            JOIN parts_of_speech p ON p.id = e.pos_id
            WHERE e.headword LIKE '%Add%'
               OR e.norm_key IN ('abbod', 'abbodhad', 'abbodisse')
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
    source = default_bt_source_path()
    if not source.is_file():
        pytest.skip("packaged oe_bt.txt not available")

    report_path = temp_dir / "full_report.json"
    index_db, report = _index_fixture(source, temp_dir)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert report["merged"] > 10_000
    assert report["parsed"] > report["merged"]
    assert sum(report["pos_counts"].values()) == report["merged"]
    assert index_db.stat().st_size > 0


def _write_source(temp_dir: Path, name: str, lines: list[str]) -> Path:
    source = temp_dir / name
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return source


def _load_warnings(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_index_with_warnings(source: Path, temp_dir: Path) -> tuple[dict[str, object], list[dict[str, object]], Path]:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    if not index_db.exists():
        _seed_forms_table(index_db, row_count=1)
    warnings_path = temp_dir / "parse_warnings.jsonl"
    sink = BTSqliteSink(index_db)
    try:
        report = BTIndexPipeline().run(source, sink, warnings_path=warnings_path)
    finally:
        sink.close()
    return report.to_dict(), _load_warnings(warnings_path), index_db


def _warning_reasons(warnings: list[dict[str, object]]) -> set[str]:
    return {str(row["failure_reason"]) for row in warnings}


def test_index_pipeline_stores_adloma_dependency_tail_gloss(temp_dir: Path) -> None:
    """
    Regression lock for adloma attestation tail bleed-through (oe_bt.txt line 491).

    The italic ``poor wretches, i.e.`` gloss after ``:--`` currently remains in
    ``gloss_en`` until attestation stripping improves for that pattern.
    """
    source = _write_source(
        temp_dir,
        "adloma_tail.txt",
        [
            (
                "adloma@<B>ād-loma,</B> -lama? an; <I>m. One crippled by the flame?</I>"
                " cui flamma claudicationem attulit? -- Earme ādloman"
                " <I>poor wretches, i.e.</I> diaboli, Exon. 46a; Th. 156, 33; Gū. 884.@ad-loma"
            ),
        ],
    )
    _report, _warnings, index_db = _run_index_with_warnings(source, temp_dir)

    with sqlite3.connect(index_db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT gloss_en
            FROM bt_senses s
            JOIN bt_entries e ON e.id = s.entry_id
            WHERE e.norm_key = 'adloma'
            """
        ).fetchone()

    assert row is not None
    assert row["gloss_en"] == "One crippled by the flame?; poor wretches, i.e"


def test_index_pipeline_skips_gesteald_place_before_and_add_fragment(
    temp_dir: Path,
) -> None:
    """
    ``Place before … and add:`` editorial cross-ref debris must not be indexed.

    Corpus: oe_bt.txt ge-steald (line 28091).
    """
    source = _write_source(
        temp_dir,
        "gesteald_editorial.txt",
        [
            (
                "gesteald@<B>ge-steald.</B>. <I>Place before</I> ge-stealla,"
                " <I>and add:</I> v. ǣht-, feoh-, flet-, in-, māðurn-, þrȳþ-,"
                " wil-, wuldor-gesteald.@ge-steald"
            ),
        ],
    )
    report, _warnings, index_db = _run_index_with_warnings(source, temp_dir)

    with sqlite3.connect(index_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]

    assert count == 0
    assert report["merged"] == 0


def test_index_pipeline_emits_modifier_only_fragment_warning(temp_dir: Path) -> None:
    source = _write_source(
        temp_dir,
        "modifier_only.txt",
        [
            "modtest@<B>modtest;</B> n. <B>I.</B> <I>intrans.</I>@modtest",
        ],
    )
    report, warnings, _index_db = _run_index_with_warnings(source, temp_dir)

    assert "parse:modifier_only_fragment" in report["warning_counts"]
    assert "modifier_only_fragment" in _warning_reasons(warnings)


def test_index_pipeline_emits_orphan_source_label_depth_fallback_warning(
    temp_dir: Path,
) -> None:
    source = _write_source(
        temp_dir,
        "orphan_label.txt",
        [
            (
                "orptest@<B>orptest;</B> n. <B>I.</B> <I>first gloss</I> :-- x "
                "<B>II a.</B> <I>second gloss</I> :-- y@orptest"
            ),
        ],
    )
    report, warnings, _index_db = _run_index_with_warnings(source, temp_dir)

    assert "parse:orphan_source_label_depth_fallback" in report["warning_counts"]
    assert "orphan_source_label_depth_fallback" in _warning_reasons(warnings)


def test_index_pipeline_emits_editorial_fragment_without_gloss_warning(
    temp_dir: Path,
) -> None:
    source = _write_source(
        temp_dir,
        "editorial_debris.txt",
        [
            "edtest@<B>edtest;</B> n. <B>I.</B> <I>seed gloss</I> :-- x@edtest",
            "edtest@<B>edtest.</B> <I>Substitute the following:</I> <I>wk.</I>@edtest",
        ],
    )
    report, warnings, _index_db = _run_index_with_warnings(source, temp_dir)

    assert "parse:editorial_fragment_without_gloss" in report["warning_counts"]
    assert "editorial_fragment_without_gloss" in _warning_reasons(warnings)


def test_index_pipeline_persists_target_missing_edit_log_row(temp_dir: Path) -> None:
    source = _write_source(
        temp_dir,
        "target_missing.txt",
        [
            "tmtest@<B>tmtest;</B> n. <B>I.</B> <I>seed gloss</I> :-- x@tmtest",
            "tmtest@<B>tmtest.</B> <I>Dele</I> passage <B>III.</B>@tmtest",
        ],
    )
    _report, warnings, index_db = _run_index_with_warnings(source, temp_dir)

    with sqlite3.connect(index_db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT note, applied
            FROM bt_edit_log
            WHERE source_line_no = 2
            """
        ).fetchone()

    assert row is not None
    assert int(row["applied"]) == 0
    assert str(row["note"]).startswith("target_missing:")
    assert "target_missing" in _warning_reasons(warnings)


def test_index_pipeline_persists_target_ambiguous_edit_log_row(temp_dir: Path) -> None:
    source = _write_source(
        temp_dir,
        "target_ambiguous.txt",
        [
            "ambig@<B>ambig,</B> ic -x; <I>v. first verb</I> :-- x@ambig",
            "ambig@<B>ambig,</B> ic -y; <I>v. second verb</I> :-- y@ambig",
            (
                "ambig@<B>ambig.</B> <I>Substitute the following for</I> ambig "
                "<I>in Dict</I>. <B>I.</B> <I>replacement gloss</I> :-- z@ambig"
            ),
        ],
    )
    _report, warnings, index_db = _run_index_with_warnings(source, temp_dir)

    with sqlite3.connect(index_db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT note, applied
            FROM bt_edit_log
            WHERE source_line_no = 3
            """
        ).fetchone()

    assert row is not None
    assert int(row["applied"]) == 0
    assert str(row["note"]).startswith("target_ambiguous:")
    assert "target_ambiguous" in _warning_reasons(warnings)
