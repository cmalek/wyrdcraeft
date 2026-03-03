from __future__ import annotations

import io

from wyrdcraeft.models.morphology import ParadigmPart, Word
from wyrdcraeft.services.morphology.generation.sound_changes import (
    derive_sound_changed_forms,
)
from wyrdcraeft.services.morphology.generators.common import VerbFormGenerator
from wyrdcraeft.services.morphology.session import GeneratorSession

from .snapshot_io import parse_form_output


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
        "vb_weak": 1,
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


def _base_formhash() -> dict[str, str]:
    return {
        "title": "test",
        "stem": "test",
        "BT": "000001",
        "wordclass": "verb",
        "class1": "w",
        "class2": "1",
        "class3": "0",
        "paradigm": "test-paradigm",
        "paraID": "90",
        "wright": "0",
        "comment": "",
        "var": "0",
    }


def test_derive_sound_changed_forms_psinsg2_ngst_chain() -> None:
    observed = derive_sound_changed_forms(function="PsInSg2", form="angst")
    assert observed == ["ancst", "anst"]


def test_derive_sound_changed_forms_psinsg2_gst_chain() -> None:
    observed = derive_sound_changed_forms(function="PsInSg2", form="agst")
    assert observed == ["ahst", "axst"]


def test_derive_sound_changed_forms_psinsg3_td_th_chain() -> None:
    observed = derive_sound_changed_forms(function="PsInSg3", form="bedþ")
    assert observed == ["bett", "bet"]


def test_generate_weak_painsg1_uses_preterite_vowel_and_sound_changes() -> None:
    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session, output)
    word = _make_word(prefix="ge", stem="lam")

    generator._generate_weak_derived_from_painsg1(
        _base_formhash(),
        word,
        "ge",
        "l",
        "a",
        "mm",
        "t",
        "ed",
        0,
        "a",
        "o",
    )
    rows = parse_form_output(output.getvalue())
    papt_rows = [row for row in rows if row["function"] == "PaPt"]

    assert papt_rows
    assert papt_rows[0]["form"] == "gelomted"
    emitted_forms = {row["form"] for row in papt_rows}
    assert {
        "gelomted",
        "gelamted",
        "gelomtt",
        "gelamt",
        "gelamtt",
        "gelomt",
    }.issubset(emitted_forms)


def test_generate_weak_verb_parts_uses_item_shape_for_id_window() -> None:
    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session, output)
    word = _make_word(prefix="0")
    item = ParadigmPart(
        para_id="PsPt",
        prefix="0",
        pre_vowel="X",
        vowel="Y",
        post_vowel="Z",
        boundary="B",
        dental="d",
        ending="e",
    )

    generator._generate_weak_verb_parts(
        _base_formhash(),
        word,
        item,
        "0",
        "ignored",
        "ignored",
        "ignored",
        0,
        "90",
        "",
        "",
    )

    rows = parse_form_output(output.getvalue())
    assert rows
    assert rows[0]["function"] == "PsPt"
    assert rows[0]["formParts"] == "0-X-Y-Z-B-d-e"
    assert len(session.adjectives) == 1
    assert session.adjectives[0].pspart == 1
