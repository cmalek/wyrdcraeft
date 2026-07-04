"""Tests for read-only Wright catalog lemma class lookup."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morphology import Word
from wyrdcraeft.services.morphology.catalog.assigner import LemmaMorphClassAssigner
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.paradigm_map import ParadigmClassMapper
from wyrdcraeft.services.morphology.catalog.query import (
    MorphClassView,
    MorphologyCatalogQueryService,
)

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))


@pytest.fixture
def catalog_db(tmp_path: Path):
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
    yield engine
    engine.dispose()


@pytest.fixture
def query_service(catalog_db) -> MorphologyCatalogQueryService:
    return MorphologyCatalogQueryService(catalog_db)


def _make_word(**overrides: object) -> Word:
    payload: dict[str, object] = {
        "nid": 1,
        "title": "test",
        "wright": "0",
        "noun": 0,
        "pronoun": 0,
        "adjective": 0,
        "verb": 0,
        "participle": 0,
        "pspart": 0,
        "papart": 0,
        "adverb": 0,
        "preposition": 0,
        "conjunction": 0,
        "interjection": 0,
        "numeral": 0,
        "vb_weak": 0,
        "vb_strong": 0,
        "vb_contracted": 0,
        "vb_pretpres": 0,
        "vb_anomalous": 0,
        "vb_uncertain": 0,
        "n_masc": 0,
        "n_fem": 0,
        "n_neut": 0,
        "n_uncert": 0,
        "stem": "test",
        "prefix": "0",
        "syllables": 1,
    }
    payload.update(overrides)
    return Word(**payload)


def test_lookup_stan_noun_returns_masculine_a_stem(
    catalog_db,
    query_service: MorphologyCatalogQueryService,
) -> None:
    word = _make_word(
        title="st\u0101n",
        noun=1,
        n_masc=1,
        noun_paradigm=["st\u00e1n"],
    )
    LemmaMorphClassAssigner(catalog_db, ParadigmClassMapper()).assign_all([word])

    view = query_service.lookup_lemma_class("st\u0101n", "noun")

    assert view is not None
    assert isinstance(view, MorphClassView)
    assert view.class_key == "noun.masculine.a_stem"
    assert view.pos == "noun"
    assert view.canonical_name == "masculine a-stem declension"
    assert view.modern_class == "a-stem"
    assert view.wright_label == "masculine a-stems"
    assert view.wright_sections == (334, 335, 336, 337, 338, 339, 340, 341)
    assert len(view.sources) == 2
    source_keys = {source.source_key for source in view.sources}
    assert source_keys == {"wright_1914", "oldenglish_info"}
    wright = next(source for source in view.sources if source.source_key == "wright_1914")
    assert "Wright" in wright.citation_apa
    assert wright.url.startswith("https://")


def test_lookup_missing_lemma_returns_none(
    query_service: MorphologyCatalogQueryService,
) -> None:
    assert query_service.lookup_lemma_class("nonexistentlemma", "noun") is None


def test_lookup_normalizes_title_before_query(
    catalog_db,
    query_service: MorphologyCatalogQueryService,
) -> None:
    word = _make_word(
        title="st\u0101n",
        noun=1,
        n_masc=1,
        noun_paradigm=["st\u00e1n"],
    )
    LemmaMorphClassAssigner(catalog_db, ParadigmClassMapper()).assign_all([word])

    assert query_service.lookup_lemma_class("ST\u0100N", "noun") is not None
    assert query_service.lookup_lemma_class("  st\u0101n  ", "noun") is not None


def test_from_db_path_uses_isolated_database(tmp_path: Path) -> None:
    db_path = tmp_path / "isolated.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    MorphologyCatalogLoader(engine).load_fixture(FIXTURE)
    engine.dispose()

    service = MorphologyCatalogQueryService.from_db_path(db_path)

    assert service.lookup_lemma_class("st\u0101n", "noun") is None
