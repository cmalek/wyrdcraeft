from __future__ import annotations

import io

from wyrdcraeft.models.morphology import ParadigmPart, Word
from wyrdcraeft.services.morphology.generation.sound_changes import (
    derive_sound_changed_forms,
)
from wyrdcraeft.services.morphology.generation.strong_inflections import (
    emit_strong_derived_from_inf_non_umlaut,
    emit_strong_umlaut_for_vowel,
)
from wyrdcraeft.services.morphology.generation.weak_inflections import (
    emit_weak_derived_from_painsg1_variant,
    emit_weak_derived_from_psinsg2,
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


def test_emit_strong_derived_from_inf_non_umlaut_an_branch_order() -> None:
    observed: list[tuple[str, str, str | int | None]] = []

    def _emit_form(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append((ending, function, probability))
        return "form", f"fp-{ending}-{function}"

    fp = emit_strong_derived_from_inf_non_umlaut(
        ending="an",
        probability=0,
        probability_plus_one=1,
        emit_form=_emit_form,
    )

    assert fp == "fp-ende-PsPt"
    assert observed == [
        ("anne", "IdIf", 0),
        ("enne", "IdIf", 0),
        ("ende", "PsPt", 0),
        ("e", "PsInSg1", 0),
        ("u", "PsInSg1", 1),
        ("o", "PsInSg1", 1),
        ("æ", "PsInSg1", 1),
        ("aþ", "PsInPl", 0),
        ("eþ", "PsInPl", 1),
        ("es", "PsInPl", 1),
        ("as", "PsInPl", 1),
        ("e", "PsSuSg", 0),
        ("en", "PsSuPl", 0),
        ("aþ", "ImPl", 0),
    ]


def test_emit_strong_umlaut_for_vowel_sequence() -> None:
    forms: list[tuple[str, str, str | int | None]] = []
    sounds: list[tuple[str, str, str | int | None]] = []

    def _emit_form(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        forms.append((ending, function, probability))
        return "form", "parts"

    def _emit_sound(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        sounds.append((ending, function, probability))

    emit_strong_umlaut_for_vowel(
        probability=2,
        emit_form=_emit_form,
        emit_sound=_emit_sound,
    )

    assert forms == [
        ("stu", "PsInSg2", 3),
        ("est", "PsInSg2", 3),
        ("ist", "PsInSg2", 3),
        ("s", "PsInSg2", 3),
        ("eþ", "PsInSg3", 3),
        ("iþ", "PsInSg3", 3),
    ]
    assert sounds == [
        ("st", "PsInSg2", 2),
        ("þ", "PsInSg3", 2),
    ]


def test_emit_weak_derived_from_psinsg2_sequence() -> None:
    forms: list[tuple[str, str, str | int | None]] = []
    sounds: list[tuple[str, str, str | int | None, int]] = []

    def _emit_form(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        forms.append((ending, function, probability))

    def _emit_sound(
        ending: str,
        function: str,
        probability: str | int | None,
        consonant_change_prob: int,
    ) -> None:
        sounds.append((ending, function, probability, consonant_change_prob))

    emit_weak_derived_from_psinsg2(
        probability=0,
        probability_plus_one=1,
        emit_form=_emit_form,
        emit_sound=_emit_sound,
    )

    assert forms == [
        ("est", "PsInSg2", 1),
        ("es", "PsInSg2", 1),
        ("ist", "PsInSg2", 1),
        ("s", "PsInSg2", 1),
        ("eþ", "PsInSg3", 1),
        ("ieþ", "PsInSg3", 1),
        ("iþ", "PsInSg3", 1),
        ("e", "ImSg", 0),
        ("ie", "ImSg", 0),
        ("0", "ImSg", 0),
    ]
    assert sounds == [
        ("st", "PsInSg2", 0, 1),
        ("þ", "PsInSg3", 1, 0),
    ]


def test_emit_weak_derived_from_painsg1_variant_sequence() -> None:
    forms: list[tuple[str, str, str | int | None]] = []
    manuals: list[tuple[str, str, str, str | int | None]] = []

    def _emit_form(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        forms.append((ending, function, probability))

    def _emit_manual(
        form: str,
        form_parts: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        manuals.append((form, form_parts, function, probability))

    form_parts = emit_weak_derived_from_painsg1_variant(
        prefix="ge",
        pre_vowel="l",
        vowel="o",
        post_vowel_simple="m",
        boundary="t",
        dental="ed",
        probability=2,
        emit_form=_emit_form,
        emit_manual=_emit_manual,
    )

    assert form_parts == "ge-l-o-m-t-ed"
    assert forms == [
        ("e", "PaInSg1", 2),
        ("est", "PaInSg2", 2),
        ("es", "PaInSg2", 3),
        ("e", "PaInSg3", 2),
        ("on", "PaInPl", 2),
        ("e", "PaSuSg", 2),
        ("en", "PaSuPl", 2),
    ]
    assert manuals == [
        ("gelomted", "ge-l-o-m-t-ed", "PaPt", 2),
        ("gelomtt", "ge-l-o-m-t-ed", "PaPt", 3),
        ("gelomt", "ge-l-o-m-t-ed", "PaPt", 3),
    ]


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
