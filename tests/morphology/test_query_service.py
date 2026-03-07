from __future__ import annotations

import io

import pytest

from wyrdcraeft.services.morphology.generation.common import print_one_form
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.generation.query import MorphologyQueryService
from wyrdcraeft.services.morphology.generation.sinks import (
    CompositeSink,
    SqliteIndexSink,
    TsvParitySink,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

from .snapshot_io import parse_form_output

pytestmark = pytest.mark.morphology


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
