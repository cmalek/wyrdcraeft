from __future__ import annotations

import io
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from wyrdcraeft.cli import (
    cli as _cli,  # noqa: F401 — load CLI before generation modules
)
from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.models.morphology import FormRow, QueryFormRow
from wyrdcraeft.models.sqlalchemy import Form
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.morphology.generation.common import print_one_form
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.generation.query import (
    MorphologyQueryService,
    _infer_bt_pos_filter,
    resolve_dictionary_db_path,
)
from wyrdcraeft.services.morphology.generation.sinks import (
    CompositeSink,
    SqliteIndexSink,
    TsvParitySink,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from .snapshot_io import parse_form_output

pytestmark = pytest.mark.morphology

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _write_morphology_index(subset_session, tmp_path: Path) -> Path:
    output = io.StringIO()
    db_path = tmp_path / "morphology-index.sqlite3"
    sqlite_sink = SqliteIndexSink(db_path)
    sink = CompositeSink(TsvParitySink(output), sqlite_sink)

    output_manual_forms(subset_session, sink)
    generate_vbforms(subset_session, sink)
    generate_adjforms(subset_session, sink)
    generate_advforms(subset_session, sink)
    generate_numforms(subset_session, sink)
    generate_nounforms(subset_session, sink)
    sqlite_sink.close()
    return db_path


def _index_dictionary(source: Path, db_path: Path, *, attach_mode: bool = False) -> None:
    sink = BTSqliteSink(db_path, attach_mode=attach_mode)
    try:
        BTIndexPipeline().run(source, sink)
    finally:
        sink.close()


def _seed_abbod_noun_form(tmp_path: Path) -> Path:
    session = GeneratorSession()
    output = io.StringIO()
    db_path = tmp_path / "morphology-index.sqlite3"
    sqlite_sink = SqliteIndexSink(db_path)
    sink = CompositeSink(TsvParitySink(output), sqlite_sink)

    print_one_form(
        session,
        {
            "BT": "000028",
            "title": "abbod",
            "stem": "abbod",
            "form": "abbod",
            "formParts": "0-abbod-0",
            "var": "0",
            "probability": "0",
            "function": "No",
            "wright": "0",
            "paradigm": "demo",
            "paraID": "0",
            "wordclass": "noun",
            "class1": "",
            "class2": "",
            "class3": "",
            "comment": "",
        },
        sink,
    )
    sqlite_sink.close()
    return db_path


def test_query_service_lemma_and_form_lookup(subset_session, tmp_path) -> None:
    output = io.StringIO()
    db_path = tmp_path / "morphology-index.sqlite3"
    sqlite_sink = SqliteIndexSink(db_path)
    sink = CompositeSink(TsvParitySink(output), sqlite_sink)

    output_manual_forms(subset_session, sink)
    generate_vbforms(subset_session, sink)
    generate_adjforms(subset_session, sink)
    generate_advforms(subset_session, sink)
    generate_numforms(subset_session, sink)
    generate_nounforms(subset_session, sink)
    sqlite_sink.close()

    rows = parse_form_output(output.getvalue())
    assert rows

    sample = rows[0]
    query_service = MorphologyQueryService(db_path)
    try:
        lemma_rows = query_service.lookup_by_lemma(sample["BT"], limit=10)
        form_rows = query_service.lookup_by_form(sample["form"], limit=10)
        limited = query_service.lookup_by_lemma(sample["BT"], limit=1)
    finally:
        query_service.close()

    assert lemma_rows
    assert form_rows
    assert any(sample["BT"] == row.BT for row in lemma_rows)
    assert any(sample["form"] == row.form for row in form_rows)
    assert len(limited) == 1
    assert limited[0].counter == lemma_rows[0].counter


def test_query_service_indexes_reduced_secondary_rows(tmp_path) -> None:
    session = GeneratorSession()
    output = io.StringIO()
    db_path = tmp_path / "secondary-index.sqlite3"
    sqlite_sink = SqliteIndexSink(db_path)
    sink = CompositeSink(TsvParitySink(output), sqlite_sink)

    form_data = {
        "BT": "000001",
        "title": "godd",
        "stem": "godd",
        "form": "godd",
        "formParts": "0-godd-0",
        "var": "0",
        "probability": "0",
        "function": "Po",
        "wright": "0",
        "paradigm": "demo",
        "paraID": "0",
        "wordclass": "noun",
        "class1": "",
        "class2": "",
        "class3": "",
        "comment": "",
    }

    print_one_form(session, form_data, sink)
    sqlite_sink.close()

    query_service = MorphologyQueryService(db_path)
    try:
        primary_rows = query_service.lookup_by_form("godd", limit=10)
        reduced_rows = query_service.lookup_by_form("god", limit=10)
    finally:
        query_service.close()

    assert primary_rows
    assert reduced_rows
    assert any(row.formi == "godd" for row in primary_rows)
    assert any(row.formi == "god" for row in reduced_rows)


def _form_row(*, counter: str, formi: str, bt: str = "ord") -> FormRow:
    return FormRow(
        counter=counter,
        formi=formi,
        BT=bt,
        title=bt,
        stem=bt,
        form=formi,
        formParts="",
        var="0",
        probability="0",
        function="No",
        wright="0",
        paradigm="demo",
        paraID="0",
        wordclass="noun",
        class1="",
        class2="",
        class3="",
        comment="",
    )


def test_sqlite_index_sink_bulk_inserts_via_sqlalchemy_form_model(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "sqlalchemy-index.sqlite3"
    sink = SqliteIndexSink(db_path)
    sink.emit_rows([_form_row(counter="1", formi="abbod")])
    sink.close()

    engine = create_engine(db_path)
    try:
        with sessionmaker(bind=engine, future=True)() as session:
            forms = session.query(Form).all()
    finally:
        engine.dispose()

    assert len(forms) == 1
    assert forms[0].form == "abbod"


def test_sqlite_index_sink_preserves_counter_then_id_order(tmp_path: Path) -> None:
    db_path = tmp_path / "order-index.sqlite3"
    sink = SqliteIndexSink(db_path)
    sink.emit_rows(
        [_form_row(counter="3", formi="ord-c"), _form_row(counter="1", formi="ord-a")]
    )
    sink.emit_rows([_form_row(counter="2", formi="ord-b")])
    sink.close()

    query_service = MorphologyQueryService(db_path)
    try:
        rows = query_service.lookup_by_lemma("ord", limit=10)
    finally:
        query_service.close()

    assert [row.counter for row in rows] == ["1", "2", "3"]
    assert [row.formi for row in rows] == ["ord-a", "ord-b", "ord-c"]


def test_resolve_dictionary_db_path_prefers_explicit_override(tmp_path) -> None:
    morphology_db = tmp_path / "morphology.sqlite3"
    morphology_db.write_text("", encoding="utf-8")
    dictionary_db = tmp_path / "custom-dictionary.sqlite3"
    dictionary_db.write_text("", encoding="utf-8")

    resolved = resolve_dictionary_db_path(morphology_db, dictionary_db)

    assert resolved == dictionary_db.resolve()


def test_resolve_dictionary_db_path_uses_sibling_dictionary(tmp_path) -> None:
    morphology_db = tmp_path / "morphology.sqlite3"
    morphology_db.write_text("", encoding="utf-8")
    sibling = tmp_path / DICTIONARY_INDEX_FILENAME
    sibling.write_text("", encoding="utf-8")

    resolved = resolve_dictionary_db_path(morphology_db)

    assert resolved == sibling.resolve()


def test_resolve_dictionary_db_path_uses_attach_mode_tables(
    subset_session,
    tmp_path,
) -> None:
    morphology_db = _write_morphology_index(subset_session, tmp_path)
    _index_dictionary(_SAMPLE_LINES, morphology_db, attach_mode=True)

    resolved = resolve_dictionary_db_path(morphology_db)

    assert resolved == morphology_db.resolve()


def test_infer_bt_pos_filter_maps_unambiguous_noun() -> None:
    rows = [
        QueryFormRow.model_validate(
            {
                "counter": "1",
                "formi": "abbod",
                "BT": "abbod",
                "title": "abbod",
                "stem": "abbod",
                "form": "abbod",
                "formParts": "",
                "var": "0",
                "probability": "0",
                "function": "No",
                "wright": "0",
                "paradigm": "demo",
                "paraID": "0",
                "wordclass": "noun",
                "class1": "",
                "class2": "",
                "class3": "",
                "comment": "",
                "lemma_key": "abbod|||abbod",
                "form_key": "abbod",
            }
        )
    ]

    assert _infer_bt_pos_filter(rows) == "noun"


def test_infer_bt_pos_filter_returns_none_for_mixed_wordclasses() -> None:
    base = {
        "counter": "1",
        "formi": "a",
        "BT": "a",
        "title": "a",
        "stem": "a",
        "form": "a",
        "formParts": "",
        "var": "0",
        "probability": "0",
        "function": "No",
        "wright": "0",
        "paradigm": "demo",
        "paraID": "0",
        "class1": "",
        "class2": "",
        "class3": "",
        "comment": "",
        "lemma_key": "a|||a",
        "form_key": "a",
    }
    rows = [
        QueryFormRow.model_validate({**base, "wordclass": "noun"}),
        QueryFormRow.model_validate({**base, "counter": "2", "wordclass": "verb"}),
    ]

    assert _infer_bt_pos_filter(rows) is None


def test_dictionary_join_with_sibling_db(tmp_path) -> None:
    morphology_db = _seed_abbod_noun_form(tmp_path)
    dictionary_db = tmp_path / DICTIONARY_INDEX_FILENAME
    _index_dictionary(_SAMPLE_LINES, dictionary_db)

    query_service = MorphologyQueryService(morphology_db)
    try:
        form_rows = query_service.lookup_by_lemma("abbod", limit=20)
        dictionary_entries = query_service.lookup_dictionary_entries(
            "abbod",
            form_rows,
        )
    finally:
        query_service.close()

    assert form_rows
    assert all(row.wordclass == "noun" for row in form_rows)
    assert len(dictionary_entries) == 1
    entry = dictionary_entries[0]
    assert entry["headword"] == "abbad"
    assert entry["pos"] == "noun"
    assert entry["genders"] == ["m"]
    assert entry["senses"]
    assert any("abbot" in str(sense["gloss_en"]).lower() for sense in entry["senses"])


def test_dictionary_join_attach_mode_single_db(tmp_path) -> None:
    morphology_db = _seed_abbod_noun_form(tmp_path)
    _index_dictionary(_SAMPLE_LINES, morphology_db, attach_mode=True)

    query_service = MorphologyQueryService(morphology_db)
    try:
        form_rows = query_service.lookup_by_lemma("abbod", limit=20)
        dictionary_entries = query_service.lookup_dictionary_entries(
            "abbod",
            form_rows,
        )
    finally:
        query_service.close()

    assert form_rows
    assert len(dictionary_entries) == 1
    assert dictionary_entries[0]["pos"] == "noun"


def test_dictionary_join_without_dictionary_db_returns_empty(tmp_path) -> None:
    morphology_db = _seed_abbod_noun_form(tmp_path)

    query_service = MorphologyQueryService(morphology_db)
    try:
        form_rows = query_service.lookup_by_lemma("abbod", limit=5)
        dictionary_entries = query_service.lookup_dictionary_entries(
            "abbod",
            form_rows,
        )
    finally:
        query_service.close()

    assert form_rows
    assert dictionary_entries == []
