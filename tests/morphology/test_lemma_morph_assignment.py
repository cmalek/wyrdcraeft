"""Tests for lemma-to-morph-class assignment during morphology build."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import LemmaMorphClass, MorphClass
from wyrdcraeft.models.morphology import VerbParadigm, Word
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.services.morphology.catalog.assigner import LemmaMorphClassAssigner
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.paradigm_map import ParadigmClassMapper

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
def assigner(catalog_db) -> LemmaMorphClassAssigner:
    return LemmaMorphClassAssigner(catalog_db, ParadigmClassMapper())


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


def _make_verb_paradigm(*, paradigm_id: str, title: str) -> VerbParadigm:
    return VerbParadigm(
        ID=paradigm_id,
        title=title,
        type="0",
        **{"class": "0"},
        subdivision="0",
        subclass="0",
        wright="0",
    )


def _assignment(
    catalog_db,
    *,
    normalized_title: str,
    pos: str,
) -> LemmaMorphClass | None:
    with Session(catalog_db) as session:
        return session.scalar(
            select(LemmaMorphClass)
            .join(
                PartOfSpeech,
                PartOfSpeech.id == LemmaMorphClass.pos_id,
            )
            .where(
                LemmaMorphClass.normalized_title == normalized_title,
                PartOfSpeech.code == pos,
            ),
        )


def _class_key(catalog_db, morph_class_id: int) -> str:
    with catalog_db.connect() as conn:
        return conn.execute(
            select(MorphClass.class_key).where(MorphClass.id == morph_class_id),
        ).scalar_one()


def test_noun_stan_assigns_masculine_a_stem(assigner, catalog_db) -> None:
    word = _make_word(
        title="st\u0101n",
        noun=1,
        n_masc=1,
        noun_paradigm=["st\u00e1n"],
    )
    result = assigner.assign_all([word])

    assert result.assigned == 1
    row = _assignment(catalog_db, normalized_title="st\u0101n", pos="noun")
    assert row is not None
    assert _class_key(catalog_db, row.morph_class_id) == "noun.masculine.a_stem"
    assert row.assignment_source == "paradigm"
    assert row.confidence == 100


def test_verb_paradigm_id_assigns_strong_3_liquid_cluster(assigner, catalog_db) -> None:
    word = _make_word(
        title="helpan",
        verb=1,
        vb_strong=1,
        vb_paradigm=[_make_verb_paradigm(paradigm_id="13", title="helpan")],
    )
    result = assigner.assign_all([word])

    assert result.assigned == 1
    row = _assignment(catalog_db, normalized_title="helpan", pos="verb")
    assert row is not None
    assert _class_key(catalog_db, row.morph_class_id) == "verb.strong_3.liquid_cluster"


def test_present_participle_berende_assigns_present_participle_class(
    assigner,
    catalog_db,
) -> None:
    word = _make_word(
        title="berende",
        pspart=1,
        adjective=0,
        verb=0,
    )
    result = assigner.assign_all([word])

    assert result.assigned == 1
    row = _assignment(catalog_db, normalized_title="berende", pos="adjective")
    assert row is not None
    assert _class_key(catalog_db, row.morph_class_id) == "adj.present_participle"


def test_skip_when_no_match_writes_no_row(assigner, catalog_db) -> None:
    """
    Unmatched inflectable lemmas produce no ``lemma_morph_classes`` row.

    When no pipeline step resolves a morph class, the assigner skips the lemma
    rather than inserting a placeholder row with ``confidence=0``.
    """
    word = _make_word(
        title="unmappednoun",
        noun=1,
        n_masc=1,
        noun_paradigm=["totally_unknown_paradigm"],
        wright="0",
    )
    result = assigner.assign_all([word])

    assert result.skipped == 1
    assert result.assigned == 0
    assert _assignment(catalog_db, normalized_title="unmappednoun", pos="noun") is None


def test_non_inflectable_pos_is_ignored(assigner) -> None:
    word = _make_word(title="under", preposition=1)
    result = assigner.assign_all([word])

    assert result.assigned == 0
    assert result.skipped == 0


def test_wright_section_intersection_assigns_when_paradigm_missing(
    assigner,
    catalog_db,
) -> None:
    word = _make_word(
        title="customnoun",
        noun=1,
        n_masc=1,
        wright="334",
    )
    result = assigner.assign_all([word])

    assert result.assigned == 1
    row = _assignment(catalog_db, normalized_title="customnoun", pos="noun")
    assert row is not None
    assert _class_key(catalog_db, row.morph_class_id) == "noun.masculine.a_stem"
    assert row.assignment_source == "wright_section"
