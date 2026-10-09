from __future__ import annotations

import pytest

from wyrdcraeft.models.morphology import VerbParadigm, Word
from wyrdcraeft.services.morphology.assigners.adj import set_adj_paradigm
from wyrdcraeft.services.morphology.assigners.noun import set_noun_paradigm
from wyrdcraeft.services.morphology.assigners.verb import (
    _assign_verb_heuristics,
    set_verb_paradigm,
)
from wyrdcraeft.services.morphology.session import GeneratorSession, WordPool


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

    set_adj_paradigm(session.word_pool)

    assert word.adj_paradigm == ["glæd"]


def test_set_adj_paradigm_stem_propagation() -> None:
    session = GeneratorSession()
    source = _make_word(adjective=1, wright="426", stem="same")
    derived = _make_word(adjective=1, wright="0", stem="same")
    session.words = [source, derived]

    set_adj_paradigm(session.word_pool)

    assert source.adj_paradigm == ["blind"]
    assert derived.adj_paradigm == ["blind"]


def test_set_noun_paradigm_r_stem_opt_in() -> None:
    session = GeneratorSession()
    session.enable_r_stem_nouns = True
    word = _make_word(noun=1, n_masc=1, stem="fæder")
    session.nouns = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["fæder"]


def test_set_noun_paradigm_simple_stem_propagation() -> None:
    session = GeneratorSession()
    source = _make_word(noun=1, stem="same", wright="356")
    derived = _make_word(noun=1, stem="same", wright="0")
    session.nouns = [source, derived]
    session.words = [source, derived]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert source.noun_paradigm == ["cynn"]
    assert derived.noun_paradigm == ["cynn"]


def test_set_noun_paradigm_advanced_stem_propagation() -> None:
    session = GeneratorSession()
    source = _make_word(noun=1, stem="his", wright="356")
    derived = _make_word(noun=1, stem="hys", wright="0")
    session.nouns = [source, derived]
    session.words = [source, derived]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert source.noun_paradigm == ["cynn"]
    assert derived.noun_paradigm == ["cynn"]


def test_set_noun_paradigm_heuristic_incel_suffix() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, stem="princel", wright="0")
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["hof"]


def test_set_noun_paradigm_heuristic_terminal_e_gender_order() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, stem="lande", wright="0", n_fem=1, n_masc=1, n_neut=1)
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["tunge", "stán", "hof"]


def test_set_noun_paradigm_heuristic_short_syllable_front_vowel() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, stem="fæ", wright="0", n_masc=1, n_neut=1, syllables=1)
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["dæg", "fæt"]


def test_set_noun_paradigm_heuristic_nd_stem_masculine() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, stem="friend", wright="0", n_masc=1)
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["wígend"]


def test_set_noun_paradigm_final_fallback_neuter_long_stem() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, n_neut=1, stem="sten", wright="0")
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["word"]


def test_set_noun_paradigm_final_fallback_neuter_short_stem() -> None:
    session = GeneratorSession()
    word = _make_word(noun=1, n_neut=1, stem="bi", wright="0")
    session.nouns = [word]
    session.words = [word]

    set_noun_paradigm(
        session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
    )

    assert word.noun_paradigm == ["hof"]


def test_set_verb_paradigm_strong_heuristic_assignment() -> None:
    session = GeneratorSession()
    word = _make_word(verb=1, vb_strong=1, stem="faran")
    session.words = [word]
    session.verbs = [word]
    session.verb_paradigms = {
        "31": _make_verb_paradigm(paradigm_id="31", title="other", verb_type="s"),
    }

    set_verb_paradigm(session.word_pool)

    assert [vp.ID for vp in word.vb_paradigm] == ["31"]


def test_set_verb_paradigm_fallback_for_weak_verbs() -> None:
    session = GeneratorSession()
    word = _make_word(verb=1, vb_weak=1, stem="zzzz")
    session.words = [word]
    session.verbs = [word]
    session.verb_paradigms = {
        "76": _make_verb_paradigm(paradigm_id="76", title="other", verb_type="w"),
    }

    set_verb_paradigm(session.word_pool)

    assert [vp.ID for vp in word.vb_paradigm] == ["76"]


# Strong-verb Mitchell arms compare the macron spellings OENormalizer.VOWEL
# captures (ī ȳ ēo ū ā ō). Acute literals never occur in those stems.
_HEURISTIC_IDS = (
    "1",
    "2",
    "3",
    "5",
    "6",
    "9",
    "10",
    "13",
    "14",
    "16",
    "19",
    "22",
    "31",
    "40",
    "48",
    "63",
    "73",
    "74",
    "76",
    "87",
)


def _heuristic_ids(stem: str, *, strong: int, weak: int) -> list[str]:
    word = _make_word(verb=1, vb_strong=strong, vb_weak=weak, stem=stem)
    pool = WordPool()
    for paradigm_id in _HEURISTIC_IDS:
        pool.verb_paradigms[paradigm_id] = _make_verb_paradigm(
            paradigm_id=paradigm_id,
            title="other",
            verb_type="s",
        )
    _assign_verb_heuristics([word], pool)
    return [paradigm.ID for paradigm in word.vb_paradigm]


@pytest.mark.parametrize(
    ("stem", "strong", "weak", "expected"),
    [
        ("helpan", 1, 0, "13"),
        ("restan", 1, 0, "16"),
        ("beran", 1, 0, "19"),
        ("belan", 1, 0, "19"),
        ("metan", 1, 0, "22"),
        ("weþan", 1, 0, "22"),
        ("faran", 1, 0, "31"),
        ("weorpan", 1, 0, "14"),
        ("feohtan", 1, 0, "14"),
        ("gieldan", 1, 0, "63"),
        ("bindan", 1, 0, "10"),
        ("byndan", 1, 0, "10"),
        ("niendan", 1, 0, "10"),
        ("nerian", 0, 1, "73"),
        ("ferigan", 0, 1, "73"),
        ("byrgan", 0, 1, "73"),
        ("swarian", 0, 1, "87"),
        ("gadrian", 0, 1, "87"),
        ("timbrian", 0, 1, "87"),
        ("lufian", 0, 1, "87"),
        ("hebban", 0, 1, "74"),
        ("cyssan", 0, 1, "74"),
        ("fyllan", 0, 1, "76"),
        ("fillan", 0, 1, "76"),
        ("zzzz", 1, 0, None),
        ("zzzz", 0, 1, None),
        ("bocan", 1, 0, None),
        ("bocan", 0, 1, None),
        ("faran", 0, 0, None),
        ("glīdan", 1, 0, "1"),
        ("līþan", 1, 0, "2"),
        ("grīsan", 1, 0, "3"),
        ("mȳdan", 1, 0, "1"),
        ("rēofan", 1, 0, "5"),
        ("rēosan", 1, 0, "6"),
        ("brūcan", 1, 0, "9"),
        ("hātan", 1, 0, "40"),
        ("blōtan", 1, 0, "48"),
    ],
)
def test_assign_verb_heuristics_arms(
    stem: str,
    strong: int,
    weak: int,
    expected: str | None,
) -> None:
    ids = _heuristic_ids(stem, strong=strong, weak=weak)
    assert ids == ([] if expected is None else [expected])


def test_set_verb_paradigm_macron_heuristic_keeps_earlier_assignment() -> None:
    session = GeneratorSession()
    example = _make_word(verb=1, vb_strong=1, stem="snīdan", title="snīdan")
    leftover = _make_word(verb=1, vb_strong=1, stem="glīdan", title="glīdan")
    session.words = [example, leftover]
    session.verbs = [example, leftover]
    session.verb_paradigms = {
        "77": _make_verb_paradigm(paradigm_id="77", title="snīdan", verb_type="s"),
        "1": _make_verb_paradigm(paradigm_id="1", title="bīdan", verb_type="s"),
        "13": _make_verb_paradigm(paradigm_id="13", title="helpan", verb_type="s"),
    }

    set_verb_paradigm(session.word_pool)

    assert [vp.ID for vp in example.vb_paradigm] == ["77"]
    assert [vp.ID for vp in leftover.vb_paradigm] == ["1"]


def test_assign_verb_heuristics_skips_missing_or_existing_paradigm() -> None:
    word = _make_word(verb=1, vb_strong=1, stem="helpan")
    assert _assign_verb_heuristics([word], WordPool()) == []
    assert word.vb_paradigm == []

    existing = _make_verb_paradigm(paradigm_id="9", title="kept", verb_type="s")
    word.vb_paradigm = [existing]
    pool = WordPool()
    pool.verb_paradigms["13"] = _make_verb_paradigm(
        paradigm_id="13",
        title="other",
        verb_type="s",
    )
    assert _assign_verb_heuristics([word], pool) == []
    assert word.vb_paradigm == [existing]
