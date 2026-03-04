from __future__ import annotations

from wyrdcraeft.models.morphology import VerbParadigm, Word
from wyrdcraeft.services.morphology.assigners.adj import set_adj_paradigm
from wyrdcraeft.services.morphology.assigners.noun import set_noun_paradigm
from wyrdcraeft.services.morphology.assigners.verb import set_verb_paradigm
from wyrdcraeft.services.morphology.session import GeneratorSession


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


def _make_verb_paradigm(
    *, paradigm_id: str, title: str, verb_type: str
) -> VerbParadigm:
    return VerbParadigm(
        ID=paradigm_id,
        title=title,
        type=verb_type,
        **{"class": "0"},
        subdivision="0",
        subclass="0",
        wright="0",
        variants=[],
    )


def test_set_adj_paradigm_wright_rule_425() -> None:
    session = GeneratorSession()
    word = _make_word(adjective=1, wright="425", stem="glæd")
    session.words = [word]

    set_adj_paradigm(session)

    assert word.adj_paradigm == ["glæd"]


def test_set_noun_paradigm_r_stem_opt_in() -> None:
    session = GeneratorSession()
    session.enable_r_stem_nouns = True
    word = _make_word(noun=1, n_masc=1, stem="fæder")
    session.nouns = [word]

    set_noun_paradigm(session)

    assert word.noun_paradigm == ["fæder"]


def test_set_noun_paradigm_simple_stem_propagation() -> None:
    session = GeneratorSession()
    source = _make_word(noun=1, stem="same", wright="356")
    derived = _make_word(noun=1, stem="same", wright="0")
    session.nouns = [source, derived]
    session.words = [source, derived]

    set_noun_paradigm(session)

    assert source.noun_paradigm == ["cynn"]
    assert derived.noun_paradigm == ["cynn"]


def test_set_noun_paradigm_advanced_stem_propagation() -> None:
    session = GeneratorSession()
    source = _make_word(noun=1, stem="his", wright="356")
    derived = _make_word(noun=1, stem="hys", wright="0")
    session.nouns = [source, derived]
    session.words = [source, derived]

    set_noun_paradigm(session)

    assert source.noun_paradigm == ["cynn"]
    assert derived.noun_paradigm == ["cynn"]


def test_set_noun_paradigm_heuristic_incel_suffix() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, stem="princel", wright="0")
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(session)

    assert word.noun_paradigm == ["hof"]


def test_set_noun_paradigm_final_fallback_neuter_long_stem() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, n_neut=1, stem="sten", wright="0")
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(session)

    assert word.noun_paradigm == ["word"]


def test_set_verb_paradigm_strong_heuristic_assignment() -> None:
    session = GeneratorSession()
    word = _make_word(verb=1, vb_strong=1, stem="faran")
    session.words = [word]
    session.verbs = [word]
    session.verb_paradigms = {
        "31": _make_verb_paradigm(paradigm_id="31", title="other", verb_type="s"),
    }

    set_verb_paradigm(session)

    assert [vp.ID for vp in word.vb_paradigm] == ["31"]


def test_set_verb_paradigm_fallback_for_weak_verbs() -> None:
    session = GeneratorSession()
    word = _make_word(verb=1, vb_weak=1, stem="zzzz")
    session.words = [word]
    session.verbs = [word]
    session.verb_paradigms = {
        "76": _make_verb_paradigm(paradigm_id="76", title="other", verb_type="w"),
    }

    set_verb_paradigm(session)

    assert [vp.ID for vp in word.vb_paradigm] == ["76"]
