"""
Regression tests for the GeneratorSession -> WordPool/GenerationRunState split.

GeneratorSession's 11 public attributes must keep working exactly as before
(read and write) via forwarding properties onto the new word_pool/run_state
collaborators, so every existing caller keeps working unchanged during the
incremental migration in the rest of this plan.
"""

from wyrdcraeft.services.morphology.session import (
    GenerationRunState,
    GeneratorSession,
    WordPool,
)


def test_session_composes_word_pool_and_run_state():
    session = GeneratorSession()
    assert isinstance(session.word_pool, WordPool)
    assert isinstance(session.run_state, GenerationRunState)


def test_word_pool_attrs_forward_through_session():
    session = GeneratorSession()
    session.words = ["w1", "w2"]
    assert session.word_pool.words == ["w1", "w2"]
    session.word_pool.words.append("w3")
    assert session.words == ["w1", "w2", "w3"]


def test_run_state_attrs_forward_through_session():
    session = GeneratorSession()
    session.output_counter = 5
    assert session.run_state.output_counter == 5
    session.run_state.output_counter += 1
    assert session.output_counter == 6

    session.enable_r_stem_nouns = True
    assert session.run_state.enable_r_stem_nouns is True


def _make_word(**overrides):
    from wyrdcraeft.models.morphology import Word

    defaults = {
        "nid": 1,
        "title": "a",
        "wright": "",
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
        "stem": "a",
    }
    defaults.update(overrides)
    return Word(**defaults)


def test_word_pool_categorize_matches_load_all_categorization():
    pool = WordPool()
    pool.words = [
        _make_word(nid=1, title="a", stem="a", verb=1),
        _make_word(nid=2, title="b", stem="b", adjective=1),
        _make_word(nid=3, title="c", stem="c", noun=1),
    ]
    pool.categorize()
    assert [w.title for w in pool.verbs] == ["a"]
    assert [w.title for w in pool.adjectives] == ["b"]
    assert [w.title for w in pool.nouns] == ["c"]


def test_word_pool_append_participle():
    pool = WordPool()
    pool.adjectives = []
    participle = _make_word(nid=9, title="p", stem="p", pspart=1)
    pool.append_participle(participle)
    assert pool.adjectives == [participle]
