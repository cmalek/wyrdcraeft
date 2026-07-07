"""Tests for morphology form foreign-key verification helper."""

from __future__ import annotations

import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morphology import FormRow
from wyrdcraeft.models.sqlalchemy import Form
from wyrdcraeft.paths import CANONICAL_DB_FILENAME
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)
from wyrdcraeft.services.morphology.generation.form_fk_verification import (
    FormFkVerificationService,
    format_form_fk_verification_report,
)
from wyrdcraeft.services.morphology.generation.sinks import SqliteIndexSink

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.morphology

CATALOG_FIXTURE = Path(
    str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")),
)
MORPHOLOGY_DATA_DIR = (
    Path(__file__).resolve().parents[2] / "wyrdcraeft" / "etc" / "morphology"
)
SUBSET_DICTIONARY = (
    Path(__file__).resolve().parents[1] / "fixtures" / "morphology" / "test_dict.txt"
)

#: Documented verification baseline for subset build ``--limit 50`` lemmas.
SUBSET_BUILD_LIMIT = 50
SUBSET_BUILD_BASELINE = {
    "total_forms": 41485,
    "null_fk_counts": {
        "wordclass_id": 0,
        "inflection_code_id": 0,
        "morph_class_id": 38597,
        # Subset build does not attach Bosworth-Toller entries for generated forms.
        "entry_id": 41485,
    },
}


def _form_row(
    *,
    counter: str,
    formi: str,
    bt: str,
    function: str = "PsInSg3",
    wordclass: str = "verb",
) -> FormRow:
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
        probability="1",
        function=function,
        wright="",
        paradigm="",
        paraID="",
        wordclass=wordclass,
        class1="",
        class2="",
        class3="",
        comment="",
    )


@pytest.fixture
def verification_db(tmp_path: Path) -> Iterator[tuple[Path, sqlite3.Connection]]:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    with sqlite3.connect(db_path) as seed_connection:
        pos_map = ensure_parts_of_speech(seed_connection)
        ensure_inflection_codes(seed_connection, pos_map)
        seed_connection.commit()
    MorphologyCatalogLoader(engine).load_fixture(CATALOG_FIXTURE)
    engine.dispose()
    connection = sqlite3.connect(db_path)
    yield db_path, connection
    connection.close()


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
            source_line_nos_json
        ) VALUES (?, ?, ?, ?, ?, '[]', '', '[]', '[]')
        """,
        (entry_id, normalized_title, normalized_title, normalized_title, pos_id),
    )


def _insert_lemma_assignment(
    connection: sqlite3.Connection,
    *,
    normalized_title: str,
    pos_code: str,
    morph_class_key: str,
) -> int:
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


def test_form_fk_verification_matches_resolver_for_sink_rows(
    verification_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = verification_db
    _insert_bt_entry(
        connection,
        entry_id=42,
        normalized_title="helpan",
        pos_code="verb",
    )
    morph_class_id = _insert_lemma_assignment(
        connection,
        normalized_title="helpan",
        pos_code="verb",
        morph_class_key="verb.strong_3.liquid_cluster",
    )
    connection.commit()

    sink = SqliteIndexSink(db_path)
    sink.emit_rows([_form_row(counter="1", formi="helpaþ", bt="helpan")])
    sink.close()

    service = FormFkVerificationService(connection, sample_size=10, rng_seed=0)
    report = service.verify()

    assert report.ok
    assert report.sampled_forms == 1
    assert report.null_fk_counts.total_forms == 1
    assert report.null_fk_counts.wordclass_id == 0
    assert report.null_fk_counts.inflection_code_id == 0
    assert report.null_fk_counts.morph_class_id == 0
    assert report.null_fk_counts.entry_id == 0
    assert morph_class_id > 0


def test_form_fk_verification_reports_null_entry_id_baseline(
    verification_db: tuple[Path, sqlite3.Connection],
) -> None:
    db_path, connection = verification_db
    sink = SqliteIndexSink(db_path)
    sink.emit_rows([_form_row(counter="1", formi="helpaþ", bt="helpan")])
    sink.close()

    report = FormFkVerificationService(connection, sample_size=5).verify()

    assert report.ok
    assert report.null_fk_counts.entry_id == 1
    rendered = format_form_fk_verification_report(report)
    assert "entry_id=1" in rendered


def test_form_fk_verification_after_subset_morphology_build(
    runner,
    isolated_morphology_app_data: Path,
) -> None:
    result = runner.invoke(
        cli,
        [
            "morphology",
            "build",
            "--limit",
            str(SUBSET_BUILD_LIMIT),
            "--data-dir",
            str(MORPHOLOGY_DATA_DIR),
            "--dictionary",
            str(SUBSET_DICTIONARY),
        ],
    )
    assert result.exit_code == 0

    db_path = isolated_morphology_app_data / CANONICAL_DB_FILENAME
    service = FormFkVerificationService.from_db_path(
        db_path,
        sample_size=SUBSET_BUILD_LIMIT,
        rng_seed=0,
    )
    try:
        report = service.verify()
    finally:
        service.close()

    assert report.ok
    assert report.sampled_forms == SUBSET_BUILD_LIMIT
    assert report.null_fk_counts.total_forms == SUBSET_BUILD_BASELINE["total_forms"]
    for column, expected_nulls in SUBSET_BUILD_BASELINE["null_fk_counts"].items():
        assert getattr(report.null_fk_counts, column) == expected_nulls

    engine = create_engine(db_path)
    try:
        with engine.connect() as connection:
            populated = connection.execute(
                select(Form.morph_class_id).where(Form.morph_class_id.is_not(None)),
            ).all()
    finally:
        engine.dispose()
    assert populated
