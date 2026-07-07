import json
import sqlite3
from importlib.resources import files
from pathlib import Path

import pytest
from sqlalchemy import func, select

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import (  # noqa: F401
    LemmaMorphClass,
    MorphClass,
    MorphClassSource,
    MorphClassWrightSection,
    MorphSource,
    WrightSection,
)
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.models.sqlalchemy import Form
from wyrdcraeft.paths import CANONICAL_DB_FILENAME
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))
MORPHOLOGY_DATA_DIR = (
    Path(__file__).resolve().parents[2] / "wyrdcraeft" / "etc" / "morphology"
)
SUBSET_DICTIONARY = (
    Path(__file__).resolve().parents[1] / "fixtures" / "morphology" / "test_dict.txt"
)

pytestmark = pytest.mark.morphology


@pytest.fixture
def catalog_db(tmp_path: Path):
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    yield engine
    engine.dispose()


def test_morph_catalog_models_importable() -> None:
    assert MorphClass.__tablename__ == "morph_classes"
    assert WrightSection.__tablename__ == "wright_sections"
    assert LemmaMorphClass.__tablename__ == "lemma_morph_classes"


def test_lemma_morph_class_migration_applies_on_empty_db(tmp_path: Path) -> None:
    db_path = tmp_path / "empty-catalog.sqlite3"
    upgrade_canonical_db(db_path)

    with sqlite3.connect(db_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'",
            )
        }
        morph_class_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(morph_classes)")
        }

    assert "lemma_morph_classes" in table_names
    assert "recognition_hints_json" in morph_class_columns


def test_catalog_loader_populates_recognition_hints_json(catalog_db) -> None:
    MorphologyCatalogLoader(catalog_db).load_fixture(FIXTURE)

    with catalog_db.connect() as conn:
        hints_json = conn.execute(
            select(MorphClass.recognition_hints_json).where(
                MorphClass.class_key == "noun.masculine.a_stem",
            ),
        ).scalar_one()

    assert json.loads(hints_json) == {"requires_lexeme_lookup": True}


def test_catalog_loader_seeds_fixture(catalog_db) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected_classes = len(fixture["morph_classes"])
    expected_sources = len(fixture["sources"])

    MorphologyCatalogLoader(catalog_db).load_fixture(FIXTURE)

    with catalog_db.connect() as conn:
        assert (
            conn.execute(select(func.count()).select_from(MorphSource)).scalar_one()
            == expected_sources
        )
        assert (
            conn.execute(select(func.count()).select_from(MorphClass)).scalar_one()
            == expected_classes
        )
        assert (
            conn.execute(select(func.count()).select_from(WrightSection)).scalar_one()
            >= 1
        )


def test_catalog_loader_is_idempotent(catalog_db) -> None:
    loader = MorphologyCatalogLoader(catalog_db)
    loader.load_fixture(FIXTURE)
    with catalog_db.connect() as conn:
        count1 = conn.execute(select(func.count()).select_from(MorphClass)).scalar_one()
    loader.load_fixture(FIXTURE)
    with catalog_db.connect() as conn:
        count2 = conn.execute(select(func.count()).select_from(MorphClass)).scalar_one()
    assert count1 == count2


def test_catalog_loader_ensure_seeded_skips_when_populated(catalog_db) -> None:
    loader = MorphologyCatalogLoader(catalog_db)
    assert loader.ensure_seeded(FIXTURE) is True
    assert loader.ensure_seeded(FIXTURE) is False


def test_catalog_loader_ensure_seeded_refresh(catalog_db) -> None:
    loader = MorphologyCatalogLoader(catalog_db)
    assert loader.ensure_seeded(FIXTURE) is True
    assert loader.ensure_seeded(FIXTURE, refresh=True) is True


def test_wright_paradigms_fixture_matches_expected_counts() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert len(data["sources"]) >= 1
    assert len(data["morph_classes"]) == 113
    ids = {c["id"] for c in data["morph_classes"]}
    assert len(ids) == 113
    for c in data["morph_classes"]:
        assert c["pos"] in {"noun", "verb", "adjective", "adverb", "pronoun"}


def test_wright_paradigms_fixture_is_packaged() -> None:
    assert FIXTURE.exists()


def test_catalog_loader_rejects_unknown_source_keys(catalog_db, tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["morph_classes"][0]["source_keys"] = ["nonexistent_source"]
    bad_fixture = tmp_path / "bad_fixture.json"
    bad_fixture.write_text(json.dumps(payload), encoding="utf-8")

    loader = MorphologyCatalogLoader(catalog_db)
    with pytest.raises(ValueError, match="Unknown source_keys"):
        loader.load_fixture(bad_fixture)


def test_catalog_loader_rejects_missing_morph_class_fields(
    catalog_db,
    tmp_path: Path,
) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    del payload["morph_classes"][0]["pos"]
    bad_fixture = tmp_path / "bad_fixture.json"
    bad_fixture.write_text(json.dumps(payload), encoding="utf-8")

    loader = MorphologyCatalogLoader(catalog_db)
    with pytest.raises(ValueError, match="missing required keys"):
        loader.load_fixture(bad_fixture)


def test_morphology_build_populates_form_foreign_keys_for_known_lemma(
    runner,
    isolated_morphology_app_data: Path,
) -> None:
    """Build a small morphology slice and verify normalized FK columns on forms."""
    result = runner.invoke(
        cli,
        [
            "morphology",
            "build",
            "--limit",
            "50",
            "--data-dir",
            str(MORPHOLOGY_DATA_DIR),
            "--dictionary",
            str(SUBSET_DICTIONARY),
        ],
    )
    assert result.exit_code == 0

    db_path = isolated_morphology_app_data / CANONICAL_DB_FILENAME
    assert db_path.exists()

    engine = create_engine(db_path)
    try:
        with engine.connect() as connection:
            verb_pos_id = connection.execute(
                select(PartOfSpeech.id).where(PartOfSpeech.code == "verb"),
            ).scalar_one()
            form_row = connection.execute(
                select(Form)
                .where(Form.normalized_title == "āǣþan")
                .limit(1),
            ).one()
    finally:
        engine.dispose()

    assert form_row.wordclass_id == verb_pos_id
    assert form_row.inflection_code_id is not None
    assert form_row.morph_class_id is not None


def test_catalog_loader_refresh_replaces_stale_rows(
    catalog_db,
    tmp_path: Path,
) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    reduced = {**payload, "morph_classes": payload["morph_classes"][:1]}
    reduced_fixture = tmp_path / "reduced_fixture.json"
    reduced_fixture.write_text(json.dumps(reduced), encoding="utf-8")

    loader = MorphologyCatalogLoader(catalog_db)
    loader.load_fixture(reduced_fixture)
    with catalog_db.connect() as conn:
        reduced_count = conn.execute(
            select(func.count()).select_from(MorphClass)
        ).scalar_one()
    assert reduced_count == 1

    loader.load_fixture(FIXTURE, refresh=True)
    with catalog_db.connect() as conn:
        full_count = conn.execute(
            select(func.count()).select_from(MorphClass)
        ).scalar_one()
    assert full_count == 113
