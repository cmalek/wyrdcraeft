"""Tests for Wright catalog paradigm exemplar mapping."""

from __future__ import annotations

import pytest

from wyrdcraeft.services.morphology.catalog.paradigm_map import ParadigmClassMapper


@pytest.fixture
def mapper() -> ParadigmClassMapper:
    return ParadigmClassMapper()


def test_noun_paradigm_stan_maps_to_masculine_a_stem(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_noun_paradigm("st\u00e1n") == "noun.masculine.a_stem"
    assert mapper.class_key_from_noun_paradigm("st\u0101n") == "noun.masculine.a_stem"


def test_noun_paradigm_guma_maps_to_weak_n_stem(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_noun_paradigm("guma") == "noun.masculine.weak_n_stem"


def test_verb_exemplar_helpan_maps_to_liquid_cluster(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_verb_exemplar("helpan") == "verb.strong_3.liquid_cluster"


def test_verb_paradigm_id_maps_via_para_vb(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_verb_paradigm_id("13") == "verb.strong_3.liquid_cluster"
    assert mapper.class_key_from_verb_paradigm_id("1") == "verb.strong_1.regular"


def test_verb_paradigm_id_unknown_returns_none(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_verb_paradigm_id("99999") is None


def test_adj_paradigm_blind_maps_to_strong_a_o_stem(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_adj_paradigm("blind") == "adj.strong.a_o_stem"


def test_present_participle_title_maps_to_present_participle_class(
    mapper: ParadigmClassMapper,
) -> None:
    assert mapper.class_key_from_participle_title("berende", is_present=True) == (
        "adj.present_participle"
    )


def test_past_participle_title_maps_to_past_participle_class(
    mapper: ParadigmClassMapper,
) -> None:
    assert mapper.class_key_from_participle_title("boren", is_present=False) == (
        "adj.past_participle"
    )


def test_unknown_paradigm_returns_none(mapper: ParadigmClassMapper) -> None:
    assert mapper.class_key_from_noun_paradigm("totally_unknown_paradigm") is None
    assert mapper.class_key_from_adj_paradigm("not_in_fixture") is None
    assert mapper.class_key_from_verb_exemplar("not_in_fixture") is None
