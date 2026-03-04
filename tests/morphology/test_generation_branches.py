from __future__ import annotations

import io

from wyrdcraeft.models.morphology import ParadigmPart, Word
from wyrdcraeft.services.morphology.generation.participles import (
    build_participle_adjective,
)
from wyrdcraeft.services.morphology.generation.sound_changes import (
    derive_sound_changed_forms,
    emit_sound_changed_forms,
    emit_sound_changed_from_source,
)
from wyrdcraeft.services.morphology.generation.strong_inflections import (
    dispatch_strong_derived_from_principal_part,
    dispatch_strong_verb_part_branches,
    emit_strong_derived_from_inf_non_umlaut,
    emit_strong_derived_from_inf_sequence,
    emit_strong_painpl_derived,
    emit_strong_painsg1_derived,
    emit_strong_umlaut_for_vowel,
)
from wyrdcraeft.services.morphology.generation.weak_inflections import (
    dispatch_weak_derived_forms,
    dispatch_weak_principal_part_derivations,
    emit_weak_derived_from_inf_by_class2,
    emit_weak_derived_from_inf_sequence,
    emit_weak_derived_from_painsg1_sequence,
    emit_weak_derived_from_painsg1_variant,
    emit_weak_derived_from_psinsg2,
    emit_weak_derived_from_psinsg2_context,
    emit_weak_principal_form,
    is_weak_item_shape_window,
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


def test_emit_sound_changed_forms_psinsg2_probability_delta() -> None:
    observed: list[tuple[str, str, str, str | int | None]] = []

    def _emit_manual(
        form: str,
        form_parts: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        observed.append((form, form_parts, function, probability))

    emit_sound_changed_forms(
        function="PsInSg2",
        form="agst",
        form_parts="fp",
        probability=2,
        sound_change_prob_delta=1,
        emit_manual=_emit_manual,
    )

    assert observed == [
        ("ahst", "fp", "PsInSg2", 3),
        ("axst", "fp", "PsInSg2", 3),
    ]


def test_emit_sound_changed_forms_psinsg3_zero_delta() -> None:
    observed: list[tuple[str, str, str, str | int | None]] = []

    def _emit_manual(
        form: str,
        form_parts: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        observed.append((form, form_parts, function, probability))

    emit_sound_changed_forms(
        function="PsInSg3",
        form="bedþ",
        form_parts="fp",
        probability=1,
        sound_change_prob_delta=0,
        emit_manual=_emit_manual,
    )

    assert observed == [
        ("bett", "fp", "PsInSg3", 1),
        ("bet", "fp", "PsInSg3", 1),
    ]


def test_emit_sound_changed_from_source_keeps_source_ordering() -> None:
    observed: list[tuple[str, str, str, str | int | None]] = []
    calls: list[str] = []

    def _emit_source_form() -> tuple[str, str]:
        calls.append("source")
        return "agst", "fp"

    def _emit_manual(
        form: str,
        form_parts: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        calls.append("manual")
        observed.append((form, form_parts, function, probability))

    emit_sound_changed_from_source(
        function="PsInSg2",
        probability=2,
        sound_change_prob_delta=1,
        emit_source_form=_emit_source_form,
        emit_manual=_emit_manual,
    )

    assert calls[0] == "source"
    assert observed == [
        ("ahst", "fp", "PsInSg2", 3),
        ("axst", "fp", "PsInSg2", 3),
    ]


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


def test_emit_strong_derived_from_inf_sequence_event_ordering() -> None:
    events: list[tuple[object, ...]] = []

    def _emit_form_for_vowel(
        active_vowel: str,
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        events.append(("form", active_vowel, ending, function, probability))
        return "form", f"fp-{active_vowel}-{ending}-{function}"

    def _emit_sound_for_vowel(
        active_vowel: str,
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> None:
        events.append(("sound", active_vowel, ending, function, probability))

    def _on_participle(form_parts: str) -> None:
        events.append(("part", form_parts))

    def _emit_imsg(probability: str | int | None) -> None:
        events.append(("imsg", probability))

    emit_strong_derived_from_inf_sequence(
        ending="an",
        vowel="a",
        probability=1,
        umlaut_vowels=["æ", "e"],
        emit_form_for_vowel=_emit_form_for_vowel,
        emit_sound_for_vowel=_emit_sound_for_vowel,
        on_participle=_on_participle,
        emit_imsg=_emit_imsg,
    )

    part_idx = events.index(("part", "fp-a-ende-PsPt"))
    assert part_idx > 0
    assert events[0] == ("form", "a", "anne", "IdIf", 1)
    assert events[part_idx + 1] == ("imsg", 1)
    assert ("sound", "æ", "st", "PsInSg2", 1) in events
    assert ("sound", "e", "þ", "PsInSg3", 2) in events


def test_dispatch_strong_verb_part_branches_painpl() -> None:
    calls: list[str] = []

    did_dispatch = dispatch_strong_verb_part_branches(
        para_id="PaInPl",
        on_papt=lambda: calls.append("papt"),
        on_inf=lambda: calls.append("if"),
        on_painsg1=lambda: calls.append("painsg1"),
        on_painpl=lambda: calls.append("painpl"),
    )

    assert did_dispatch
    assert calls == ["painpl"]


def test_dispatch_strong_verb_part_branches_papt_only() -> None:
    calls: list[str] = []

    did_dispatch = dispatch_strong_verb_part_branches(
        para_id="PaPt",
        on_papt=lambda: calls.append("papt"),
        on_inf=lambda: calls.append("if"),
        on_painsg1=lambda: calls.append("painsg1"),
        on_painpl=lambda: calls.append("painpl"),
    )

    assert did_dispatch
    assert calls == ["papt"]


def test_dispatch_strong_derived_from_principal_part_routes_painsg1() -> None:
    observed: list[tuple[object, ...]] = []

    def _on_papt_form_parts(form_parts: str) -> None:
        observed.append(("papt", form_parts))

    def _on_inf(active_vowel: str, probability: str | int | None) -> None:
        observed.append(("if", active_vowel, probability))

    def _emit_form_for_vowel(
        active_vowel: str,
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append(("form", active_vowel, ending, function, probability))
        return "form", "parts"

    did_dispatch = dispatch_strong_derived_from_principal_part(
        para_id="PaInSg1",
        form_parts="fp-main",
        active_vowel="a",
        probability=2,
        on_papt_form_parts=_on_papt_form_parts,
        on_inf=_on_inf,
        emit_form_for_vowel=_emit_form_for_vowel,
    )

    assert did_dispatch
    assert observed == [("form", "a", "0", "PaInSg3", 2)]


def test_emit_strong_painsg1_derived_sequence() -> None:
    observed: list[tuple[str, str, str | int | None]] = []

    def _emit_form(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append((ending, function, probability))
        return "form", "parts"

    emit_strong_painsg1_derived(
        probability=0,
        emit_form=_emit_form,
    )

    assert observed == [("0", "PaInSg3", 0)]


def test_emit_strong_painpl_derived_sequence() -> None:
    observed: list[tuple[str, str, str | int | None]] = []

    def _emit_form(
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append((ending, function, probability))
        return "form", "parts"

    emit_strong_painpl_derived(
        probability=1,
        emit_form=_emit_form,
    )

    assert observed == [
        ("e", "PaInSg2", 1),
        ("e", "PaSuSg", 1),
        ("en", "PaSuPl", 1),
    ]


def test_build_participle_adjective_sanitizes_fields() -> None:
    word = _make_word(prefix="ge", title="lemma")
    adjective = build_participle_adjective(
        word=word,
        prefix="ge",
        form_parts="ge-l-a-m-0\n",
        is_past=False,
    )

    assert adjective.title == "gelam"
    assert adjective.stem == "lam"
    assert adjective.pspart == 1
    assert adjective.papart == 0


def test_add_participle_to_adjectives_respects_prefix_numeric_match() -> None:
    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session, output)
    word = _make_word(prefix="1")

    generator._add_participle_to_adjectives(
        word,
        "ge",
        "ge-l-a-m",
        is_past=False,
    )

    assert session.adjectives == []


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


def test_emit_weak_derived_from_psinsg2_context_simplifies_post_vowel() -> None:
    forms: list[tuple[str, str, str | int | None, str]] = []
    sounds: list[tuple[str, str, str | int | None, int, str]] = []

    def _emit_form_with_post(
        ending: str,
        function: str,
        probability: str | int | None,
        post_vowel_simple: str,
    ) -> None:
        forms.append((ending, function, probability, post_vowel_simple))

    def _emit_sound_with_post(
        ending: str,
        function: str,
        probability: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
    ) -> None:
        sounds.append(
            (ending, function, probability, consonant_change_prob, post_vowel_simple)
        )

    emit_weak_derived_from_psinsg2_context(
        probability=None,
        post_vowel="mm",
        emit_form_with_post=_emit_form_with_post,
        emit_sound_with_post=_emit_sound_with_post,
    )

    assert ("est", "PsInSg2", 1, "m") in forms
    assert all(row[-1] == "m" for row in forms)
    assert ("st", "PsInSg2", "", 1, "m") in sounds
    assert ("þ", "PsInSg3", 1, 0, "m") in sounds


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


def test_emit_weak_derived_from_painsg1_sequence_uses_preterite_order() -> None:
    observed: list[tuple[str, int]] = []
    participles: list[str] = []

    def _emit_variant(vowel: str, probability: int) -> str:
        observed.append((vowel, probability))
        return f"fp-{vowel}-{probability}"

    emit_weak_derived_from_painsg1_sequence(
        vowel="a",
        vowel_inf="a",
        vowel_pa="o",
        probability=0,
        emit_variant=_emit_variant,
        on_participle=participles.append,
    )

    assert observed == [("o", 0), ("a", 1)]
    assert participles == ["fp-o-0", "fp-a-1"]


def test_is_weak_item_shape_window_bounds() -> None:
    assert is_weak_item_shape_window("89")
    assert is_weak_item_shape_window("92")
    assert not is_weak_item_shape_window("88")
    assert not is_weak_item_shape_window("93")
    assert not is_weak_item_shape_window("abc")


def test_emit_weak_principal_form_probability_switch_for_painsg1() -> None:
    observed: list[tuple[object, ...]] = []

    def _emit_form(*args: object) -> tuple[str, str]:
        observed.append(args)
        (
            prefix,
            pre_vowel,
            vowel,
            post_vowel,
            boundary,
            dental,
            ending,
            _function,
            _probability,
        ) = args
        return (
            "form",
            (
                f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-"
                f"{boundary}-{dental}-{ending}"
            ),
        )

    form_parts = emit_weak_principal_form(
        para_id="PaInSg1",
        prefix="ge",
        default_parts=("l", "a", "m", "t"),
        item_parts=("X", "Y", "Z", "B"),
        dental="ed",
        ending="e",
        variant_id=0,
        use_item_shape=False,
        emit_form=_emit_form,
    )

    assert form_parts == "ge-l-a-m-t-ed-e"
    assert observed == [
        ("ge", "l", "a", "m", "t", "ed", "e", "PaInSg1", None),
    ]


def test_emit_weak_derived_from_inf_by_class2_general_branch() -> None:
    observed: list[tuple[str | None, str, str, str | int | None]] = []
    participles: list[str] = []

    def _emit_form(
        dental: str | None,
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append((dental, ending, function, probability))
        return "form", f"fp-{ending}-{function}"

    emit_weak_derived_from_inf_by_class2(
        class2="1",
        original_ending="ian",
        probability=0,
        probability_plus_one=1,
        perl_inf_vowel_end=False,
        regex_vowel_end=False,
        emit_form=_emit_form,
        on_participle=participles.append,
    )

    assert observed[0] == (None, "ian", "if", 0)
    assert participles == ["fp-ende-PsPt"]


def test_emit_weak_derived_from_inf_by_class2_two_uses_general_path() -> None:
    observed: list[tuple[str | None, str, str, str | int | None]] = []
    participles: list[str] = []

    def _emit_form(
        dental: str | None,
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append((dental, ending, function, probability))
        return "form", f"fp-{ending}-{function}"

    emit_weak_derived_from_inf_by_class2(
        class2="2",
        original_ending="ian",
        probability=0,
        probability_plus_one=1,
        perl_inf_vowel_end=False,
        regex_vowel_end=False,
        emit_form=_emit_form,
        on_participle=participles.append,
    )

    assert observed[0] == (None, "ian", "if", 0)
    assert all(
        not (ending == "an" and function == "if")
        for _, ending, function, _ in observed
    )
    assert participles == ["fp-ende-PsPt"]


def test_emit_weak_derived_from_inf_sequence_normalizes_none_probability() -> None:
    observed: list[tuple[str | None, str, str, str | int | None]] = []
    participles: list[str] = []

    def _emit_form(
        dental: str | None,
        ending: str,
        function: str,
        probability: str | int | None,
    ) -> tuple[str, str]:
        observed.append((dental, ending, function, probability))
        return "form", f"fp-{ending}-{function}"

    emit_weak_derived_from_inf_sequence(
        class2="1",
        prefix="ge",
        pre_vowel="l",
        vowel="a",
        post_vowel="m",
        boundary="t",
        original_ending="ian",
        probability=None,
        emit_form=_emit_form,
        on_participle=participles.append,
    )

    assert observed[0] == (None, "ian", "if", "")
    assert ("i", "u", "PsInSg1", 1) in observed
    assert participles == ["fp-ende-PsPt"]


def test_dispatch_weak_derived_forms_selects_psinsg2_branch() -> None:
    calls: list[str] = []

    did_dispatch = dispatch_weak_derived_forms(
        para_id="PsInSg2",
        use_item_shape=False,
        on_inf=lambda: calls.append("if"),
        on_psinsg2=lambda: calls.append("psinsg2"),
        on_painsg1=lambda: calls.append("painsg1"),
    )

    assert did_dispatch
    assert calls == ["psinsg2"]


def test_dispatch_weak_derived_forms_skips_item_shape_mode() -> None:
    calls: list[str] = []

    did_dispatch = dispatch_weak_derived_forms(
        para_id="if",
        use_item_shape=True,
        on_inf=lambda: calls.append("if"),
        on_psinsg2=lambda: calls.append("psinsg2"),
        on_painsg1=lambda: calls.append("painsg1"),
    )

    assert not did_dispatch
    assert calls == []


def test_dispatch_weak_principal_part_derivations_emits_papt_only() -> None:
    observed: list[str] = []

    did_dispatch = dispatch_weak_principal_part_derivations(
        para_id="PaPt",
        use_item_shape=False,
        form_parts="fp-main",
        on_pspt_participle=lambda form_parts: observed.append(f"pspt:{form_parts}"),
        on_papt_participle=lambda form_parts: observed.append(f"papt:{form_parts}"),
        on_inf=lambda: observed.append("if"),
        on_psinsg2=lambda: observed.append("psinsg2"),
        on_painsg1=lambda: observed.append("painsg1"),
    )

    assert not did_dispatch
    assert observed == ["papt:fp-main"]


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
