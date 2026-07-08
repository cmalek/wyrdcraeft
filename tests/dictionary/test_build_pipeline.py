"""Tests for the unified dictionary build orchestrator."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTPos, legacy_bt_sense
from wyrdcraeft.services.dictionary.pipeline import IndexReport

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _pos_id(connection: sqlite3.Connection, code: str) -> int:
    row = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = ?",
        (code,),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _fetch_form_entry_id(connection: sqlite3.Connection, *, normalized_title: str) -> int | None:
    row = connection.execute(
        "SELECT entry_id FROM forms WHERE normalized_title = ?",
        (normalized_title,),
    ).fetchone()
    assert row is not None
    return None if row[0] is None else int(row[0])


def _fetch_entry_id(connection: sqlite3.Connection, *, normalized_title: str) -> int:
    row = connection.execute(
        "SELECT id FROM bt_entries WHERE normalized_title = ?",
        (normalized_title,),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _fetch_entry_pos(connection: sqlite3.Connection, *, normalized_title: str) -> str:
    row = connection.execute(
        """
        SELECT parts_of_speech.code
        FROM bt_entries
        JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
        WHERE bt_entries.normalized_title = ?
        """,
        (normalized_title,),
    ).fetchone()
    assert row is not None
    return str(row[0])


def _insert_form(
    connection: sqlite3.Connection,
    *,
    normalized_title: str,
    wordclass_code: str,
    entry_id: int | None = None,
) -> None:
    token = normalized_title
    connection.execute(
        """
        INSERT INTO forms (
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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
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


@pytest.fixture
def build_pipeline_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    return db_path


def test_dictionary_build_pipeline_ensures_schema_and_rebuilds_dictionary_on_empty_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wyrdcraeft.services.dictionary import build_pipeline as build_module

    db_path = tmp_path / "fresh.sqlite3"
    morph_calls: list[Path] = []

    def fake_run_morphology_generation(*, db_path: Path, options: object) -> int:
        _ = options
        morph_calls.append(db_path)
        return 0

    monkeypatch.setattr(
        build_module,
        "run_morphology_generation",
        fake_run_morphology_generation,
    )

    report = build_module.DictionaryBuildPipeline(db_path).run(
        source=_SAMPLE_LINES,
        with_morphology=False,
        morph_options=build_module.MorphBuildOptions(limit=1),
    )

    assert db_path.is_file()
    assert report.bt_entries_written > 0
    assert report.forms_regenerated is True
    assert morph_calls == [db_path.resolve()]

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"forms", "bt_entries", "bt_senses", "bt_variants"} <= tables


def test_dictionary_build_pipeline_relinks_forms_after_rebuild(
    build_pipeline_db: Path,
) -> None:
    from wyrdcraeft.services.dictionary.build_pipeline import (
        DictionaryBuildPipeline,
        MorphBuildOptions,
    )

    with sqlite3.connect(build_pipeline_db) as connection:
        _insert_form(
            connection,
            normalized_title="abbad",
            wordclass_code="noun",
            entry_id=999,
        )
        connection.commit()

    report = DictionaryBuildPipeline(build_pipeline_db).run(
        source=_SAMPLE_LINES,
        with_morphology=False,
        morph_options=MorphBuildOptions(limit=1),
    )

    with sqlite3.connect(build_pipeline_db) as connection:
        linked_entry_id = _fetch_form_entry_id(connection, normalized_title="abbad")
        current_entry_id = _fetch_entry_id(connection, normalized_title="abbad")

    assert report.entry_ids_cleared == 1
    assert report.entry_ids_linked >= 1
    assert report.forms_regenerated is False
    assert linked_entry_id == current_entry_id
    assert linked_entry_id != 999


def test_dictionary_build_pipeline_skips_morphology_when_forms_exist(
    build_pipeline_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wyrdcraeft.services.dictionary import build_pipeline as build_module

    with sqlite3.connect(build_pipeline_db) as connection:
        _insert_form(
            connection,
            normalized_title="abbad",
            wordclass_code="noun",
        )
        connection.commit()

    morph_called = False

    def fake_run_morphology_generation(*, db_path: Path, options: object) -> int:
        nonlocal morph_called
        _ = (db_path, options)
        morph_called = True
        return 0

    monkeypatch.setattr(
        build_module,
        "run_morphology_generation",
        fake_run_morphology_generation,
    )

    report = build_module.DictionaryBuildPipeline(build_pipeline_db).run(
        source=_SAMPLE_LINES,
        with_morphology=False,
        morph_options=build_module.MorphBuildOptions(limit=1),
    )

    assert report.forms_source_count == 1
    assert report.forms_regenerated is False
    assert morph_called is False


def test_dictionary_build_pipeline_runs_morphology_when_forms_empty(
    build_pipeline_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wyrdcraeft.services.dictionary import build_pipeline as build_module

    def fake_run_morphology_generation(*, db_path: Path, options: object) -> int:
        _ = options
        with sqlite3.connect(db_path) as connection:
            _insert_form(
                connection,
                normalized_title="abbad",
                wordclass_code="noun",
            )
            connection.commit()
        return 1

    monkeypatch.setattr(
        build_module,
        "run_morphology_generation",
        fake_run_morphology_generation,
    )

    report = build_module.DictionaryBuildPipeline(build_pipeline_db).run(
        source=_SAMPLE_LINES,
        with_morphology=False,
        morph_options=build_module.MorphBuildOptions(limit=1),
    )

    with sqlite3.connect(build_pipeline_db) as connection:
        forms_count = int(connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0])

    assert report.forms_source_count == 0
    assert report.forms_regenerated is True
    assert forms_count == 1


def test_dictionary_build_pipeline_infers_pos_when_forms_exist(
    build_pipeline_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wyrdcraeft.services.dictionary import build_pipeline as build_module

    with sqlite3.connect(build_pipeline_db) as connection:
        _insert_form(
            connection,
            normalized_title="lemma",
            wordclass_code="noun",
        )
        connection.commit()

    def fake_run(
        self: object,
        source: Path,
        sink: object,
        *,
        warnings_path: Path | None = None,
        llm_fix_pass: object | None = None,
    ) -> IndexReport:
        _ = (self, warnings_path, llm_fix_pass)
        entry = BTConsolidatedEntry(
            norm_key="lemma",
            headword_raw="lemma",
            headword_macronized="lemma",
            normalized_title="lemma",
            pos=BTPos.UNKNOWN,
            senses=[legacy_bt_sense("I", "lemma gloss")],
        )
        sink.write_entries([entry], [])
        return IndexReport(
            source=source.resolve(),
            index_db=sink.db_path,
            merged=1,
        )

    monkeypatch.setattr(build_module.BTIndexPipeline, "run", fake_run)

    report = build_module.DictionaryBuildPipeline(build_pipeline_db).run(
        source=_SAMPLE_LINES,
        with_morphology=False,
        morph_options=build_module.MorphBuildOptions(limit=1),
    )

    with sqlite3.connect(build_pipeline_db) as connection:
        pos_code = _fetch_entry_pos(connection, normalized_title="lemma")

    assert report.pos_inferred == 1
    assert pos_code == "noun"


def test_dictionary_build_pipeline_writes_parse_warnings(
    build_pipeline_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wyrdcraeft.services.dictionary import build_pipeline as build_module

    def fake_run_morphology_generation(*, db_path: object, options: object) -> int:
        _ = (db_path, options)
        return 0

    monkeypatch.setattr(
        build_module,
        "run_morphology_generation",
        fake_run_morphology_generation,
    )

    source = _write_warning_fixture(
        tmp_path,
        [
            "modtest@<B>modtest;</B> n. <B>I.</B> <I>intrans.</I>@modtest",
        ],
    )
    warnings_path = tmp_path / "parse_warnings.jsonl"

    report = build_module.DictionaryBuildPipeline(build_pipeline_db).run(
        source=source,
        with_morphology=False,
        morph_options=build_module.MorphBuildOptions(limit=1),
        warnings_path=warnings_path,
    )

    warnings = [
        json.loads(line)
        for line in warnings_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert report.bt_entries_written > 0
    assert any(row["failure_reason"] == "modifier_only_fragment" for row in warnings)


def _write_warning_fixture(tmp_path: Path, lines: list[str]) -> Path:
    source = tmp_path / "warning_fixture.txt"
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return source
