from __future__ import annotations

import io
import sqlite3
from importlib.resources import files
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

from wyrdcraeft.cli import (
    cli as _cli,  # noqa: F401 — load CLI before generation modules
)
from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morphology import FormRow, QueryFormRow
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.models.sqlalchemy import Form
from wyrdcraeft.paths import CANONICAL_DB_FILENAME, DICTIONARY_INDEX_FILENAME
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)
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
_CATALOG_FIXTURE = Path(
    str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")),
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


def _seed_catalog_morph_class_assignment(
    db_path: Path,
    *,
    normalized_title: str,
    pos_code: str,
    morph_class_key: str,
) -> int:
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(_CATALOG_FIXTURE)
    engine.dispose()

    with sqlite3.connect(db_path) as connection:
        pos_id = connection.execute(
            "SELECT id FROM parts_of_speech WHERE code = ?",
            (pos_code,),
        ).fetchone()[0]
        morph_class_id = connection.execute(
            "SELECT id FROM morph_classes WHERE class_key = ?",
            (morph_class_key,),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO lemma_morph_classes (
                normalized_title,
                pos_id,
                morph_class_id
            ) VALUES (?, ?, ?)
            """,
            (normalized_title, pos_id, morph_class_id),
        )
        connection.commit()
    return int(morph_class_id)


def _seed_abbod_noun_form_with_catalog(tmp_path: Path) -> Path:
    db_path = tmp_path / "catalog-morph-query.sqlite3"
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        pos_map = ensure_parts_of_speech(connection)
        ensure_inflection_codes(connection, pos_map)
        connection.commit()

    _seed_catalog_morph_class_assignment(
        db_path,
        normalized_title="abbod",
        pos_code="noun",
        morph_class_key="noun.masculine.a_stem",
    )

    session = GeneratorSession()
    output = io.StringIO()
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


def test_query_service_exposes_morph_class_metadata_when_fk_set(
    tmp_path: Path,
) -> None:
    db_path = _seed_abbod_noun_form_with_catalog(tmp_path)

    query_service = MorphologyQueryService(db_path)
    try:
        lemma_rows = query_service.lookup_by_lemma("abbod", limit=10)
        form_rows = query_service.lookup_by_form("abbod", limit=10)
    finally:
        query_service.close()

    assert lemma_rows
    assert form_rows
    row = lemma_rows[0]
    assert row.morph_class_id is not None
    assert row.morph_class is not None
    assert row.morph_class.class_key == "noun.masculine.a_stem"
    assert row.morph_class.pos == "noun"
    assert row.morph_class.canonical_name == "masculine a-stem declension"
    assert row.morph_class.modern_class == "a-stem"
    assert row.morph_class.wright_label == "masculine a-stems"
    assert row.morph_class.display_label == "noun, a-stem"
    assert row.morph_class.wright_sections == (
        334,
        335,
        336,
        337,
        338,
        339,
        340,
        341,
    )
    assert row.wright == ""
    assert row.paradigm == ""
    assert form_rows[0].morph_class_id == row.morph_class_id
    assert form_rows[0].morph_class == row.morph_class


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
        normalized_title=bt,
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


_EXPECTED_FORMS_LOOKUP_INDEXES = {
    "idx_forms_bt_key",
    "idx_forms_title_key",
    "idx_forms_stem_key",
    "idx_forms_form_key",
    "idx_forms_formi_key",
    "idx_forms_normalized_title",
    "idx_forms_wordclass_id",
    "idx_forms_inflection_code_id",
    "idx_forms_morph_class_id",
    "idx_forms_entry_id",
}


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


def _insert_bt_entry(
    connection: sqlite3.Connection,
    *,
    entry_id: int,
    normalized_title: str,
    pos_code: str,
) -> None:
    pos_id = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = ?",
        (pos_code,),
    ).fetchone()[0]
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
        (entry_id, normalized_title, normalized_title, normalized_title, pos_id, entry_id),
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


def test_sqlite_index_sink_leaves_entry_id_null_for_ambiguous_homograph(
    isolated_morphology_app_data: Path,
) -> None:
    """Ambiguous dictionary joins must persist NULL ``entry_id`` on inserted forms."""
    db_path = isolated_morphology_app_data / CANONICAL_DB_FILENAME
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        pos_map = ensure_parts_of_speech(connection)
        ensure_inflection_codes(connection, pos_map)
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
        connection.commit()

    sink = SqliteIndexSink(db_path)
    sink.emit_rows([_form_row(counter="1", formi="alias", bt="alias")])
    sink.close()

    engine = create_engine(db_path)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                select(
                    Form.entry_id,
                    Form.wordclass_id,
                    Form.inflection_code_id,
                ).where(Form.normalized_title == "alias"),
            ).one()
            noun_pos_id = connection.execute(
                select(PartOfSpeech.id).where(PartOfSpeech.code == "noun"),
            ).scalar_one()
    finally:
        engine.dispose()

    assert row.entry_id is None
    assert row.wordclass_id == noun_pos_id


def test_sqlite_index_sink_keeps_lookup_indexes_after_close(tmp_path: Path) -> None:
    db_path = tmp_path / "deferred-index.sqlite3"
    sink = SqliteIndexSink(db_path)
    sink.emit_rows([_form_row(counter="1", formi="abbod")])
    sink.close()

    engine = create_engine(db_path)
    try:
        with engine.connect() as connection:
            index_rows = connection.execute(text("PRAGMA index_list('forms')")).fetchall()
    finally:
        engine.dispose()

    index_names = {str(row[1]) for row in index_rows if str(row[1]).startswith("idx_forms_")}
    assert index_names == _EXPECTED_FORMS_LOOKUP_INDEXES


def test_sqlite_index_sink_flushes_in_batches_before_close(tmp_path: Path) -> None:
    db_path = tmp_path / "batched-index.sqlite3"
    sink = SqliteIndexSink(db_path, batch_size=2)
    sink.emit_rows(
        [
            _form_row(counter="1", formi="bat-a"),
            _form_row(counter="2", formi="bat-b"),
            _form_row(counter="3", formi="bat-c"),
        ]
    )
    sink.close()

    engine = create_engine(db_path)
    try:
        with sessionmaker(bind=engine, future=True)() as session:
            count = session.query(Form).count()
    finally:
        engine.dispose()

    assert count == 3


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
    morphology_db = tmp_path / "wyrdcraeft.sqlite3"
    morphology_db.write_text("", encoding="utf-8")
    dictionary_db = tmp_path / "custom-dictionary.sqlite3"
    dictionary_db.write_text("", encoding="utf-8")

    resolved = resolve_dictionary_db_path(morphology_db, dictionary_db)

    assert resolved == dictionary_db.resolve()


def test_resolve_dictionary_db_path_uses_sibling_dictionary(tmp_path) -> None:
    morphology_db = tmp_path / "wyrdcraeft.sqlite3"
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
                "normalized_title": "abbod",
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
        "normalized_title": "a",
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
