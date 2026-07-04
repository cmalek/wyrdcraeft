import json
from importlib.resources import files
from pathlib import Path

import pytest
from sqlalchemy import func, select

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import (  # noqa: F401
    MorphClass,
    MorphClassSource,
    MorphClassWrightSection,
    MorphSource,
    WrightSection,
)
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))


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
