# ruff: noqa: I001
from __future__ import annotations

import io
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import pytest

from wyrdcraeft.models.morphology import (
    ParadigmPart,
    ParadigmVariant,
    VerbParadigm,
    Word,
    _StrongInfDerivationContext,
    _StrongPrincipalPartContext,
    _WeakInfDerivationContext,
    _WeakPainsg1DerivationContext,
    _WeakPrincipalPartContext,
    _WeakPsinsg2DerivationContext,
)
from wyrdcraeft.services.morphology.generation.participles import (
    add_participle_to_adjectives,
    build_participle_adjective,
)
from wyrdcraeft.services.morphology.generation.sound_changes import (
    derive_sound_changed_forms,
    emit_sound_changed_forms,
    emit_sound_changed_from_source,
)
from wyrdcraeft.services.morphology.generation import common as generation_common
from wyrdcraeft.services.morphology.generation.common import (
    StrongVerbGenerator,
    VerbFormGenerator,
    WeakVerbGenerator,
)
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


def _make_part(**overrides: object) -> ParadigmPart:
    payload: dict[str, object] = {
        "para_id": "if",
        "prefix": "0",
        "pre_vowel": "0",
        "vowel": "a",
        "post_vowel": "m",
        "boundary": "n",
        "dental": "0",
        "ending": "an",
    }
    payload.update(overrides)
    return ParadigmPart(**payload)


def _make_variant(
    *,
    variant_id: int = 0,
    parts: dict[str, ParadigmPart] | None = None,
) -> ParadigmVariant:
    return ParadigmVariant(
        variant_id=variant_id,
        parts=parts if parts is not None else {"if": _make_part()},
    )


def _make_verb_paradigm(**overrides: object) -> VerbParadigm:
    payload: dict[str, object] = {
        "ID": "90",
        "title": "test-paradigm",
        "type": "w",
        "class": "1",
        "subdivision": "0",
        "subclass": "0",
        "wright": "0",
        "variants": [_make_variant()],
    }
    payload.update(overrides)
    return VerbParadigm(**payload)


def test_derive_sound_changed_forms_psinsg2_ngst_chain() -> None:
    observed = derive_sound_changed_forms(function="PsInSg2", form="angst")
    assert observed == ["ancst", "anst"]


def test_process_paradigm_routes_variant_payload_from_flow() -> None:
    word = _make_word(prefix="ge")
    vp = _make_verb_paradigm(
        ID="87",
        type="w",
        variants=[
            _make_variant(
                variant_id=0,
                parts={
                    "if": _make_part(
                        para_id="if",
                        boundary="n",
                        vowel="a",
                        ending="an",
                    ),
                    "painsg1": _make_part(
                        para_id="painsg1",
                        boundary="t",
                        vowel="o",
                        ending="e",
                    ),
                },
            ),
            _make_variant(
                variant_id=2,
                parts={
                    "if": _make_part(
                        para_id="if",
                        boundary="n",
                        vowel="a",
                        ending="an",
                    ),
                },
            ),
        ],
    )
    observed: list[tuple[str, int, str, str, str, str]] = []

    def _on_variant(  # noqa: PLR0913
        captured_word: Word,
        captured_vp: VerbParadigm,
        variant: ParadigmVariant,
        formhash: dict[str, str],
        boundary_inf: str,
        vowel_inf: str,
        vowel_pa: str,
    ) -> None:
        observed.append(
            (
                captured_word.title,
                variant.variant_id,
                formhash["var"],
                captured_vp.ID,
                boundary_inf,
                f"{vowel_inf}/{vowel_pa}",
            )
        )

    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session.word_pool, session.run_state, output)
    generator._process_variant = _on_variant  # type: ignore[method-assign,assignment]

    generator._process_paradigm(word=word, vp=vp)

    assert observed == [
        ("test", 0, "0", "87", "n", "a/o"),
        ("test", 2, "2", "87", "n", "a/o"),
    ]


def test_process_part_routes_strong_generation_from_flow() -> None:
    word = _make_word(prefix="ge")
    vp = _make_verb_paradigm(ID="91", type="s")
    variant = _make_variant(variant_id=3)
    item = _make_part(para_id="papt", prefix="be")
    formhash = _base_formhash()
    strong_calls: list[tuple[object, ...]] = []
    weak_calls: list[tuple[object, ...]] = []

    def _derive_segments(
        captured_word: Word,
        captured_item: ParadigmPart,
        captured_boundary_inf: str,
    ) -> tuple[str, str, str, str]:
        assert captured_word is word
        assert captured_item is item
        assert captured_boundary_inf == "n"
        return "ge-be", "l", "a", "m"

    def _generate_strong(*args: object) -> None:
        strong_calls.append(args)

    def _generate_weak(*args: object) -> None:
        weak_calls.append(args)

    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session.word_pool, session.run_state, output)
    generator._derive_part_stem_segments = _derive_segments  # type: ignore[method-assign,assignment]
    generator._strong_generator.generate_verb_parts = _generate_strong  # type: ignore[method-assign,assignment]
    generator._weak_generator.generate_verb_parts = _generate_weak  # type: ignore[method-assign,assignment]

    generator._process_part(
        word=word,
        vp=vp,
        variant=variant,
        item=item,
        formhash_var=formhash,
        boundary_inf="n",
        vowel_inf="a",
        vowel_pa="o",
    )

    assert strong_calls == [
        (formhash, word, item, "ge-be", "l", "a", "m", 3),
    ]
    assert weak_calls == []


def test_process_part_routes_weak_generation_from_flow() -> None:
    word = _make_word(prefix="ge")
    vp = _make_verb_paradigm(ID="87", type="w")
    variant = _make_variant(variant_id=4)
    item = _make_part(para_id="if", prefix="0")
    formhash = _base_formhash()
    strong_calls: list[tuple[object, ...]] = []
    weak_calls: list[tuple[object, ...]] = []

    def _derive_segments(
        captured_word: Word,
        captured_item: ParadigmPart,
        captured_boundary_inf: str,
    ) -> tuple[str, str, str, str]:
        assert captured_word is word
        assert captured_item is item
        assert captured_boundary_inf == "n"
        return "ge", "l", "a", "m"

    def _generate_strong(*args: object) -> None:
        strong_calls.append(args)

    def _generate_weak(*args: object) -> None:
        weak_calls.append(args)

    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session.word_pool, session.run_state, output)
    generator._derive_part_stem_segments = _derive_segments  # type: ignore[method-assign,assignment]
    generator._strong_generator.generate_verb_parts = _generate_strong  # type: ignore[method-assign,assignment]
    generator._weak_generator.generate_verb_parts = _generate_weak  # type: ignore[method-assign,assignment]

    generator._process_part(
        word=word,
        vp=vp,
        variant=variant,
        item=item,
        formhash_var=formhash,
        boundary_inf="n",
        vowel_inf="a",
        vowel_pa="o",
    )

    assert strong_calls == []
    assert weak_calls == [
        (formhash, word, item, "ge", "l", "a", "m", 4, "87", "a", "o"),
    ]


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


def _strong_inf_context(**overrides: object) -> _StrongInfDerivationContext:
    payload: dict[str, object] = {
        "formhash": _base_formhash() | {"class1": "s"},
        "word": _make_word(),
        "prefix": "0",
        "pre_vowel": "0",
        "base_vowel": "a",
        "post_vowel": "m",
        "boundary": "n",
    }
    payload.update(overrides)
    return _StrongInfDerivationContext(**payload)  # type: ignore[arg-type]


def _strong_principal_context(**overrides: object) -> _StrongPrincipalPartContext:
    payload: dict[str, object] = {
        "formhash": _base_formhash() | {"class1": "s"},
        "word": _make_word(),
        "prefix": "0",
        "pre_vowel": "0",
        "post_vowel": "m",
        "boundary": "n",
        "ending": "an",
    }
    payload.update(overrides)
    return _StrongPrincipalPartContext(**payload)  # type: ignore[arg-type]


class _RecordingSink:
    """Capture emitted ``form_data`` payloads without TSV geminate expansion."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def emit_form_data(
        self, run_state: object, form_data: dict[str, str]
    ) -> list[object]:
        """Record one emitted row payload."""
        del run_state
        self.rows.append(
            (form_data["form"], form_data["function"], form_data["probability"])
        )
        return []


def _strong_generator(
    session: GeneratorSession, sink: _RecordingSink
) -> StrongVerbGenerator:
    return StrongVerbGenerator(
        session.word_pool,
        session.run_state,
        cast("io.StringIO", sink),
    )


def test_emit_strong_derived_from_inf_non_umlaut_an_branch_order() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    fp = strong._emit_derived_from_inf_non_umlaut(
        context=_strong_inf_context(),
        vowel="a",
        ending="an",
        probability=0,
        probability_plus_one=1,
    )

    assert fp == "0-0-a-m-n-ende"
    assert sink.rows == [
        ("amnanne", "IdIf", "0"),
        ("amnenne", "IdIf", "0"),
        ("amnende", "PsPt", "0"),
        ("amne", "PsInSg1", "0"),
        ("amnu", "PsInSg1", "1"),
        ("amno", "PsInSg1", "1"),
        ("amnæ", "PsInSg1", "1"),
        ("amnaþ", "PsInPl", "0"),
        ("amneþ", "PsInPl", "1"),
        ("amnes", "PsInPl", "1"),
        ("amnas", "PsInPl", "1"),
        ("amne", "PsSuSg", "0"),
        ("amnen", "PsSuPl", "0"),
        ("amnaþ", "ImPl", "0"),
    ]


def test_emit_strong_derived_from_inf_non_umlaut_n_branch_order() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    fp = strong._emit_derived_from_inf_non_umlaut(
        context=_strong_inf_context(),
        vowel="a",
        ending="n",
        probability=0,
        probability_plus_one=1,
    )

    assert fp == "0-0-a-m-n-nde"
    assert sink.rows == [
        ("amnnne", "IdIf", "0"),
        ("amnnde", "PsPt", "0"),
        ("amn", "PsInSg1", "0"),
        ("amnþ", "PsInPl", "0"),
        ("amn", "PsSuSg", "0"),
        ("amnn", "PsSuPl", "0"),
        ("amnþ", "ImPl", "0"),
    ]


def test_emit_strong_umlaut_for_vowel_sequence() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    strong._emit_umlaut_for_vowel(
        context=_strong_inf_context(),
        vowel="æ",
        probability=2,
    )

    rows = sink.rows
    assert [(row[1], row[2]) for row in rows if row[1] == "PsInSg2"][:5] == [
        ("PsInSg2", "3"),
        ("PsInSg2", "3"),
        ("PsInSg2", "3"),
        ("PsInSg2", "3"),
        ("PsInSg2", "2"),
    ]
    assert rows[0] == ("æmnstu", "PsInSg2", "3")
    assert rows[1] == ("æmnest", "PsInSg2", "3")
    assert rows[2] == ("æmnist", "PsInSg2", "3")
    assert rows[3] == ("æmns", "PsInSg2", "3")
    assert rows[4] == ("æmnst", "PsInSg2", "2")
    # The sound-change branch appends derived rows after its own source row.
    assert ("æmneþ", "PsInSg3", "3") in rows
    assert ("æmniþ", "PsInSg3", "3") in rows
    assert ("æmnþ", "PsInSg3", "2") in rows


def test_emit_strong_derived_from_inf_sequence_event_ordering() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    strong._emit_derived_from_inf_sequence(
        context=_strong_inf_context(),
        ending="an",
        vowel="a",
        probability=1,
        umlaut_vowels=["æ", "e"],
    )

    rows = sink.rows
    assert rows[0] == ("amnanne", "IdIf", "1")
    pspt_idx = rows.index(("amnende", "PsPt", "1"))
    imsg_idx = next(idx for idx, row in enumerate(rows) if row[1] == "ImSg")
    # ``ImSg`` is emitted immediately after the non-umlaut block completes.
    assert imsg_idx > pspt_idx
    assert rows[imsg_idx][2] == "1"
    # Umlaut branches follow, one per umlaut vowel, with incrementing probability.
    assert ("æmnst", "PsInSg2", "1") in rows
    assert ("emnþ", "PsInSg3", "2") in rows
    # The present participle is projected into the adjective pool.
    assert len(session.word_pool.adjectives) == 1


def test_dispatch_strong_derived_from_principal_part_routes_painpl() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)

    did_dispatch = strong._dispatch_derived_from_principal_part(
        context=_strong_principal_context(),
        para_id="PaInPl",
        form_parts="0-0-a-m-n-e",
        active_vowel="a",
        probability=1,
    )

    assert did_dispatch
    assert sink.rows == [
        ("amne", "PaInSg2", "1"),
        ("amne", "PaSuSg", "1"),
        ("amnen", "PaSuPl", "1"),
    ]
    assert not session.word_pool.adjectives


def test_dispatch_strong_derived_from_principal_part_papt_only() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)

    did_dispatch = strong._dispatch_derived_from_principal_part(
        context=_strong_principal_context(),
        para_id="PaPt",
        form_parts="0-0-a-m-n-en",
        active_vowel="a",
        probability=None,
    )

    assert did_dispatch
    # ``PaPt`` only projects a past participle; it emits no further form rows.
    assert sink.rows == []
    assert len(session.word_pool.adjectives) == 1
    assert session.word_pool.adjectives[0].papart == 1


def test_dispatch_strong_derived_from_principal_part_routes_painsg1() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    did_dispatch = strong._dispatch_derived_from_principal_part(
        context=_strong_principal_context(),
        para_id="PaInSg1",
        form_parts="fp-main",
        active_vowel="a",
        probability=2,
    )

    assert did_dispatch
    assert sink.rows == [("amn", "PaInSg3", "2")]


def test_dispatch_strong_derived_from_principal_part_unknown_para_id() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    did_dispatch = strong._dispatch_derived_from_principal_part(
        context=_strong_principal_context(),
        para_id="PsInSg1",
        form_parts="fp-main",
        active_vowel="a",
        probability=2,
    )

    assert not did_dispatch
    assert sink.rows == []


def test_emit_strong_painsg1_derived_sequence() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    strong._emit_painsg1_derived(
        context=_strong_principal_context(),
        active_vowel="a",
        probability=0,
    )

    assert sink.rows == [("amn", "PaInSg3", "0")]


def test_emit_strong_painpl_derived_sequence() -> None:
    session = GeneratorSession()
    sink = _RecordingSink()
    strong = _strong_generator(session, sink)
    strong._emit_painpl_derived(
        context=_strong_principal_context(),
        active_vowel="a",
        probability=1,
    )

    assert sink.rows == [
        ("amne", "PaInSg2", "1"),
        ("amne", "PaSuSg", "1"),
        ("amnen", "PaSuPl", "1"),
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
    generator = VerbFormGenerator(session.word_pool, session.run_state, output)
    word = _make_word(prefix="1")

    generator._add_participle_to_adjectives(
        word,
        "ge",
        "ge-l-a-m",
        is_past=False,
    )

    assert session.adjectives == []


def test_add_participle_to_adjectives_helper_appends_present_participle() -> None:
    session = GeneratorSession()
    word = _make_word(prefix="0", title="lemma", wright="W")

    add_participle_to_adjectives(
        session.word_pool,
        word=word,
        prefix="ge",
        form_parts="ge-l-a-m-0\n",
        is_past=False,
    )

    assert len(session.adjectives) == 1
    adjective = session.adjectives[0]
    assert adjective.title == "gelam"
    assert adjective.stem == "lam"
    assert adjective.pspart == 1
    assert adjective.papart == 0
    assert adjective.prefix == "ge"


def test_add_participle_to_adjectives_helper_appends_past_participle() -> None:
    session = GeneratorSession()
    word = _make_word(prefix="0", title="lemma", wright="W")

    add_participle_to_adjectives(
        session.word_pool,
        word=word,
        prefix="0",
        form_parts="0-l-a-m-0\n",
        is_past=True,
    )

    assert len(session.adjectives) == 1
    adjective = session.adjectives[0]
    assert adjective.title == "lam"
    assert adjective.stem == "lam"
    assert adjective.pspart == 0
    assert adjective.papart == 1


def test_add_participle_to_adjectives_helper_skips_mismatched_prefix() -> None:
    session = GeneratorSession()
    word = _make_word(prefix="1")

    add_participle_to_adjectives(
        session.word_pool,
        word=word,
        prefix="ge",
        form_parts="ge-l-a-m",
        is_past=False,
    )

    assert session.adjectives == []


def _weak_psinsg2_context(**overrides: object) -> _WeakPsinsg2DerivationContext:
    payload: dict[str, object] = {
        "formhash": _base_formhash(),
        "prefix": "ge",
        "pre_vowel": "l",
        "vowel": "a",
        "boundary": "t",
    }
    payload.update(overrides)
    return _WeakPsinsg2DerivationContext(**payload)  # type: ignore[arg-type]


def _weak_painsg1_context(**overrides: object) -> _WeakPainsg1DerivationContext:
    payload: dict[str, object] = {
        "formhash": _base_formhash(),
        "word": _make_word(prefix="ge", stem="lam"),
        "prefix": "ge",
        "pre_vowel": "l",
        "boundary": "t",
        "dental": "ed",
    }
    payload.update(overrides)
    return _WeakPainsg1DerivationContext(**payload)  # type: ignore[arg-type]


def _weak_inf_context(**overrides: object) -> _WeakInfDerivationContext:
    payload: dict[str, object] = {
        "formhash": _base_formhash(),
        "word": _make_word(prefix="ge", stem="lam"),
        "prefix": "ge",
        "pre_vowel": "l",
        "vowel": "a",
        "post_vowel": "m",
        "boundary": "t",
    }
    payload.update(overrides)
    return _WeakInfDerivationContext(**payload)  # type: ignore[arg-type]


def test_emit_weak_derived_from_psinsg2_sequence() -> None:
    forms: list[tuple[str, str, str | int | None]] = []
    sounds: list[tuple[str, str, str | int | None, int]] = []

    def _emit_form(
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        probability: str | int | None,
        post_vowel_simple: str,
    ) -> None:
        del context, post_vowel_simple
        forms.append((ending, function, probability))

    def _emit_sound(  # noqa: PLR0913
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        probability: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
    ) -> None:
        del context, post_vowel_simple
        sounds.append((ending, function, probability, consonant_change_prob))

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_psinsg2_form_with_post_derivation_context = _emit_form  # type: ignore[method-assign,assignment]
    weak._emit_weak_psinsg2_sound_with_post_derivation_context = _emit_sound  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_from_psinsg2(
        context=_weak_psinsg2_context(),
        probability=0,
        probability_plus_one=1,
        post_vowel_simple="m",
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

    def _emit_form(
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        probability: str | int | None,
        post_vowel_simple: str,
    ) -> None:
        del context
        forms.append((ending, function, probability, post_vowel_simple))

    def _emit_sound(  # noqa: PLR0913
        context: _WeakPsinsg2DerivationContext,
        ending: str,
        function: str,
        probability: str | int | None,
        consonant_change_prob: int,
        post_vowel_simple: str,
    ) -> None:
        del context
        sounds.append(
            (ending, function, probability, consonant_change_prob, post_vowel_simple)
        )

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_psinsg2_form_with_post_derivation_context = _emit_form  # type: ignore[method-assign,assignment]
    weak._emit_weak_psinsg2_sound_with_post_derivation_context = _emit_sound  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_from_psinsg2_context(
        context=_weak_psinsg2_context(),
        probability=None,
        post_vowel="mm",
    )

    assert ("est", "PsInSg2", 1, "m") in forms
    assert all(row[-1] == "m" for row in forms)
    assert ("st", "PsInSg2", "", 1, "m") in sounds
    assert ("þ", "PsInSg3", 1, 0, "m") in sounds


def test_emit_weak_derived_from_painsg1_variant_sequence() -> None:
    forms: list[tuple[str, str, str | int | None]] = []
    manuals: list[tuple[str, str, str, str | int | None]] = []

    def _emit_row(  # noqa: PLR0913
        context: _WeakPainsg1DerivationContext,
        current_vowel: str,
        ending: str,
        function: str,
        prob: str | int | None,
        post_vowel_simple: str,
    ) -> tuple[str, str]:
        del context, current_vowel, post_vowel_simple
        forms.append((ending, function, prob))
        return "form", "fp"

    def _emit_manual(
        context: _WeakPainsg1DerivationContext,
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        del context
        manuals.append((form, form_parts, function, prob))

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_painsg1_form_for_vowel_from_context = _emit_row  # type: ignore[method-assign,assignment]
    weak._emit_weak_painsg1_manual_context = _emit_manual  # type: ignore[method-assign,assignment]
    form_parts = weak._emit_weak_derived_from_painsg1_variant(
        context=_weak_painsg1_context(),
        vowel="o",
        post_vowel_simple="m",
        probability=2,
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

    def _emit_variant(
        *,
        context: _WeakPainsg1DerivationContext,
        vowel: str,
        post_vowel_simple: str,
        probability: int,
    ) -> str:
        del context, post_vowel_simple
        observed.append((vowel, probability))
        return f"fp-{vowel}-{probability}"

    def _on_participle(context: _WeakPainsg1DerivationContext, form_parts: str) -> None:
        del context
        participles.append(form_parts)

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_derived_from_painsg1_variant = _emit_variant  # type: ignore[method-assign,assignment]
    weak._emit_weak_painsg1_participle_context = _on_participle  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_from_painsg1_sequence(
        context=_weak_painsg1_context(),
        vowel="a",
        vowel_inf="a",
        vowel_pa="o",
        post_vowel_simple="m",
        probability=0,
    )

    assert observed == [("o", 0), ("a", 1)]
    assert participles == ["fp-o-0", "fp-a-1"]


def test_is_weak_item_shape_window_bounds() -> None:
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    assert weak._is_weak_item_shape_window("89")
    assert weak._is_weak_item_shape_window("92")
    assert not weak._is_weak_item_shape_window("88")
    assert not weak._is_weak_item_shape_window("93")
    assert not weak._is_weak_item_shape_window("abc")


def test_should_use_weak_item_shape_for_irregular_paradigm_types() -> None:
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    assert weak._should_use_weak_item_shape("127", paradigm_type="a")
    assert weak._should_use_weak_item_shape("114", paradigm_type="pp")
    assert not weak._should_use_weak_item_shape("127", paradigm_type="w")
    assert weak._should_use_weak_item_shape("90", paradigm_type="w")


def test_emit_weak_principal_form_probability_switch_for_painsg1() -> None:
    observed: list[tuple[object, ...]] = []
    formhash = _base_formhash()

    def _emit_form_context(*args: object) -> tuple[str, str]:
        observed.append(args)
        (
            _formhash,
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
            (f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}-{dental}-{ending}"),
        )

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_principal_form_context = _emit_form_context  # type: ignore[method-assign,assignment]
    form_parts = weak._emit_weak_principal_form(
        para_id="PaInSg1",
        formhash=formhash,
        prefix="ge",
        default_parts=("l", "a", "m", "t"),
        item_parts=("X", "Y", "Z", "B"),
        dental="ed",
        ending="e",
        variant_id=0,
        use_item_shape=False,
    )

    assert form_parts == "ge-l-a-m-t-ed-e"
    assert observed == [
        (formhash, "ge", "l", "a", "m", "t", "ed", "e", "PaInSg1", None),
    ]


def test_emit_weak_principal_form_context_forwards_dental_and_probability() -> None:
    observed: list[tuple[object, ...]] = []

    def _emit_form_for_context(  # noqa: PLR0913
        formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        *,
        dental: str | None = "",
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        observed.append(
            (
                formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                ending,
                function,
                dental,
                prob,
            )
        )
        return "form", "fp"

    formhash = _base_formhash()
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_form_for_context = _emit_form_for_context  # type: ignore[method-assign,assignment]
    result = weak._emit_weak_principal_form_context(
        formhash,
        "ge",
        "l",
        "a",
        "m",
        "t",
        "ed",
        "e",
        "PaInSg1",
        1,
    )

    assert result == ("form", "fp")
    assert observed == [
        (formhash, "ge", "l", "a", "m", "t", "e", "PaInSg1", "ed", 1),
    ]


def test_emit_weak_derived_from_inf_by_class2_general_branch() -> None:
    observed: list[tuple[str | None, str, str, str | int | None]] = []
    participles: list[str] = []

    def _emit_row(
        context: _WeakInfDerivationContext,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        del context
        observed.append((dental, ending, function, prob))
        return "form", f"fp-{ending}-{function}"

    def _on_participle(context: _WeakInfDerivationContext, form_parts: str) -> None:
        del context
        participles.append(form_parts)

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_derived_inf_form = _emit_row  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_inf_participle = _on_participle  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_from_inf_by_class2(
        context=_weak_inf_context(),
        class2="1",
        original_ending="ian",
        probability=0,
        probability_plus_one=1,
        perl_inf_vowel_end=False,
        regex_vowel_end=False,
    )

    assert observed[0] == (None, "ian", "if", 0)
    assert participles == ["fp-ende-PsPt"]


def test_emit_weak_derived_from_inf_by_class2_two_uses_general_path() -> None:
    observed: list[tuple[str | None, str, str, str | int | None]] = []
    participles: list[str] = []

    def _emit_row(
        context: _WeakInfDerivationContext,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        del context
        observed.append((dental, ending, function, prob))
        return "form", f"fp-{ending}-{function}"

    def _on_participle(context: _WeakInfDerivationContext, form_parts: str) -> None:
        del context
        participles.append(form_parts)

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_derived_inf_form = _emit_row  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_inf_participle = _on_participle  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_from_inf_by_class2(
        context=_weak_inf_context(),
        class2="2",
        original_ending="ian",
        probability=0,
        probability_plus_one=1,
        perl_inf_vowel_end=False,
        regex_vowel_end=False,
    )

    assert observed[0] == (None, "ian", "if", 0)
    assert all(
        not (ending == "an" and function == "if") for _, ending, function, _ in observed
    )
    assert participles == ["fp-ende-PsPt"]


def test_emit_weak_derived_from_inf_sequence_normalizes_none_probability() -> None:
    observed: list[tuple[str | None, str, str, str | int | None]] = []
    participles: list[str] = []

    def _emit_row(
        context: _WeakInfDerivationContext,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
    ) -> tuple[str, str]:
        del context
        observed.append((dental, ending, function, prob))
        return "form", f"fp-{ending}-{function}"

    def _on_participle(context: _WeakInfDerivationContext, form_parts: str) -> None:
        del context
        participles.append(form_parts)

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_weak_derived_inf_form = _emit_row  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_inf_participle = _on_participle  # type: ignore[method-assign,assignment]
    weak._emit_weak_derived_from_inf_sequence(
        context=_weak_inf_context(),
        class2="1",
        original_ending="ian",
        probability=None,
    )

    assert observed[0] == (None, "ian", "if", "")
    assert ("i", "u", "PsInSg1", 1) in observed
    assert participles == ["fp-ende-PsPt"]


def test_generate_weak_derived_from_inf_routes_direct_context_emitter() -> None:
    observed: list[tuple[object, ...]] = []
    participles: list[tuple[str, str, str, bool]] = []
    formhash = _base_formhash()
    word = _make_word(prefix="ge", stem="lam")

    def _emit_form_for_context(  # noqa: PLR0913
        captured_formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        *,
        dental: str | None = "",
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        observed.append(
            (
                captured_formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                ending,
                function,
                dental,
                prob,
            )
        )
        return "form", f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}-{ending}"

    def _add_participle_to_adjectives(
        captured_word: Word,
        prefix: str,
        form_parts: str,
        *,
        is_past: bool,
    ) -> None:
        participles.append((captured_word.stem, prefix, form_parts, is_past))

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_form_for_context = _emit_form_for_context  # type: ignore[method-assign,assignment]
    weak._add_participle_to_adjectives = _add_participle_to_adjectives  # type: ignore[method-assign,assignment]
    weak._generate_weak_derived_from_inf(
        formhash=formhash,
        word=word,
        prefix="ge",
        pre_vowel="l",
        vowel="a",
        post_vowel="m",
        boundary="t",
        original_ending="ian",
        probability=None,
    )

    assert observed[0] == (formhash, "ge", "l", "a", "m", "t", "ian", "if", None, "")
    assert (formhash, "ge", "l", "a", "m", "t", "u", "PsInSg1", "i", 1) in observed
    assert participles == [("lam", "ge", "ge-l-a-m-t-ende", False)]


def test_generate_verb_parts_routes_direct_derivation_stack() -> None:
    observed_forms: list[tuple[object, ...]] = []
    observed_sounds: list[tuple[object, ...]] = []
    observed_imsg: list[tuple[object, ...]] = []
    participles: list[tuple[str, str, str, bool]] = []
    word = _make_word(prefix="ge", stem="lam")
    item = ParadigmPart(
        para_id="if",
        prefix="0",
        pre_vowel="0",
        vowel="a",
        post_vowel="m",
        boundary="t",
        dental="0",
        ending="an",
    )

    def _emit_form_for_context(  # noqa: PLR0913
        captured_formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        *,
        dental: str | None = "",
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        observed_forms.append(
            (
                captured_formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                ending,
                function,
                dental,
                prob,
            )
        )
        return "form", f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}-{ending}"

    def _emit_sound_for_context(  # noqa: PLR0913
        captured_formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        prob: str | int | None,
        *,
        dental: str | None = "",
        sound_change_prob_delta: int = 1,
    ) -> None:
        observed_sounds.append(
            (
                captured_formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                ending,
                function,
                prob,
                dental,
                sound_change_prob_delta,
            )
        )

    def _emit_imsg_for_context(  # noqa: PLR0913
        captured_formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        prob: str | int | None,
    ) -> None:
        observed_imsg.append(
            (
                captured_formhash,
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                prob,
            )
        )

    def _add_participle_to_adjectives(
        captured_word: Word,
        prefix: str,
        form_parts: str,
        *,
        is_past: bool,
    ) -> None:
        participles.append((captured_word.stem, prefix, form_parts, is_past))

    formhash = _base_formhash()
    session = GeneratorSession()
    strong = StrongVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    strong._emit_form_for_context = _emit_form_for_context  # type: ignore[method-assign,assignment]
    strong._emit_sound_changed_form_for_context = _emit_sound_for_context  # type: ignore[method-assign,assignment]
    strong._emit_imsg_for_context = _emit_imsg_for_context  # type: ignore[method-assign,assignment]
    strong._add_participle_to_adjectives = _add_participle_to_adjectives  # type: ignore[method-assign,assignment]
    strong.generate_verb_parts(
        formhash,
        word,
        item,
        "ge",
        "l",
        "a",
        "m",
        0,
    )

    assert observed_forms[0] == (
        formhash,
        "ge",
        "l",
        "a",
        "m",
        "t",
        "an",
        "if",
        "",
        None,
    )
    assert (
        formhash,
        "ge",
        "l",
        "a",
        "m",
        "t",
        "anne",
        "IdIf",
        "",
        None,
    ) in observed_forms
    assert observed_imsg == [(formhash, "ge", "l", "a", "m", "t", None)]
    assert participles == [("lam", "ge", "ge-l-a-m-t-ende", False)]
    assert observed_sounds


def _weak_principal_context(**overrides: object) -> _WeakPrincipalPartContext:
    payload: dict[str, object] = {
        "formhash": _base_formhash(),
        "word": _make_word(prefix="ge", stem="lam"),
        "prefix": "ge",
        "pre_vowel": "l",
        "vowel": "a",
        "post_vowel": "m",
        "boundary": "t",
        "ending": "an",
        "dental": "ed",
        "probability": 0,
        "vowel_inf": "a",
        "vowel_pa": "o",
    }
    payload.update(overrides)
    return _WeakPrincipalPartContext(**payload)  # type: ignore[arg-type]


def _record_weak_branches(weak: WeakVerbGenerator, calls: list[str]) -> None:
    """Replace the three weak derived-branch entry points with recorders."""

    def _on_inf(context: _WeakPrincipalPartContext) -> None:
        del context
        calls.append("if")

    def _on_psinsg2(context: _WeakPrincipalPartContext) -> None:
        del context
        calls.append("psinsg2")

    def _on_painsg1(context: _WeakPrincipalPartContext) -> None:
        del context
        calls.append("painsg1")

    weak._emit_weak_principal_inf_derivation = _on_inf  # type: ignore[method-assign,assignment]
    weak._emit_weak_principal_psinsg2_derivation = _on_psinsg2  # type: ignore[method-assign,assignment]
    weak._emit_weak_principal_painsg1_derivation = _on_painsg1  # type: ignore[method-assign,assignment]


def test_dispatch_weak_derived_forms_selects_psinsg2_branch() -> None:
    calls: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, calls)

    did_dispatch = weak._dispatch_weak_derived_forms(
        context=_weak_principal_context(),
        para_id="PsInSg2",
        use_item_shape=False,
    )

    assert did_dispatch
    assert calls == ["psinsg2"]


def test_dispatch_weak_derived_forms_selects_inf_branch() -> None:
    calls: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, calls)

    did_dispatch = weak._dispatch_weak_derived_forms(
        context=_weak_principal_context(),
        para_id="if",
        use_item_shape=False,
    )

    assert did_dispatch
    assert calls == ["if"]


def test_dispatch_weak_derived_forms_selects_painsg1_branch() -> None:
    calls: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, calls)

    did_dispatch = weak._dispatch_weak_derived_forms(
        context=_weak_principal_context(),
        para_id="PaInSg1",
        use_item_shape=False,
    )

    assert did_dispatch
    assert calls == ["painsg1"]


def test_dispatch_weak_derived_forms_unknown_para_id() -> None:
    calls: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, calls)

    did_dispatch = weak._dispatch_weak_derived_forms(
        context=_weak_principal_context(),
        para_id="PsPt",
        use_item_shape=False,
    )

    assert not did_dispatch
    assert calls == []


def test_dispatch_weak_derived_forms_skips_item_shape_mode() -> None:
    calls: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, calls)

    did_dispatch = weak._dispatch_weak_derived_forms(
        context=_weak_principal_context(),
        para_id="if",
        use_item_shape=True,
    )

    assert not did_dispatch
    assert calls == []


def test_dispatch_weak_principal_part_derivations_emits_papt_only() -> None:
    observed: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, observed)

    def _on_pspt(context: _WeakPrincipalPartContext, form_parts: str) -> None:
        del context
        observed.append(f"pspt:{form_parts}")

    def _on_papt(context: _WeakPrincipalPartContext, form_parts: str) -> None:
        del context
        observed.append(f"papt:{form_parts}")

    weak._emit_weak_principal_pspt_participle = _on_pspt  # type: ignore[method-assign,assignment]
    weak._emit_weak_principal_papt_participle = _on_papt  # type: ignore[method-assign,assignment]

    did_dispatch = weak._dispatch_weak_principal_part_derivations(
        context=_weak_principal_context(),
        para_id="PaPt",
        use_item_shape=False,
        form_parts="fp-main",
    )

    assert not did_dispatch
    assert observed == ["papt:fp-main"]


def test_dispatch_weak_principal_part_derivations_emits_pspt_only() -> None:
    observed: list[str] = []
    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    _record_weak_branches(weak, observed)

    def _on_pspt(context: _WeakPrincipalPartContext, form_parts: str) -> None:
        del context
        observed.append(f"pspt:{form_parts}")

    def _on_papt(context: _WeakPrincipalPartContext, form_parts: str) -> None:
        del context
        observed.append(f"papt:{form_parts}")

    weak._emit_weak_principal_pspt_participle = _on_pspt  # type: ignore[method-assign,assignment]
    weak._emit_weak_principal_papt_participle = _on_papt  # type: ignore[method-assign,assignment]

    did_dispatch = weak._dispatch_weak_principal_part_derivations(
        context=_weak_principal_context(),
        para_id="PsPt",
        use_item_shape=False,
        form_parts="fp-main",
    )

    assert not did_dispatch
    assert observed == ["pspt:fp-main"]


def test_generate_weak_painsg1_uses_preterite_vowel_and_sound_changes() -> None:
    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session.word_pool, session.run_state, output)
    word = _make_word(prefix="ge", stem="lam")

    generator._weak_generator._generate_weak_derived_from_painsg1(
        formhash=_base_formhash(),
        word=word,
        prefix="ge",
        pre_vowel="l",
        vowel="a",
        post_vowel="mm",
        boundary="t",
        dental="ed",
        probability=0,
        vowel_inf="a",
        vowel_pa="o",
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


def test_generate_weak_derived_from_painsg1_routes_manuals_and_participles() -> None:
    forms: list[tuple[object, ...]] = []
    manuals: list[tuple[object, ...]] = []
    participles: list[tuple[str, str, str, bool]] = []
    word = _make_word(prefix="ge", stem="lam")

    def _emit_form(  # noqa: PLR0913
        _formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        forms.append(
            (
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                dental,
                ending,
                function,
                prob,
            )
        )
        return "form", f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}-{dental}"

    def _emit_manual(
        _context: _WeakPainsg1DerivationContext,
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        manuals.append((form, form_parts, function, prob))

    def _add_participle_to_adjectives(
        captured_word: Word,
        prefix: str,
        form_parts: str,
        *,
        is_past: bool,
    ) -> None:
        participles.append((captured_word.stem, prefix, form_parts, is_past))

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._generate_and_print_form = _emit_form  # type: ignore[method-assign,assignment]
    weak._emit_weak_painsg1_manual_context = _emit_manual  # type: ignore[method-assign,assignment]
    weak._add_participle_to_adjectives = _add_participle_to_adjectives  # type: ignore[method-assign,assignment]
    weak._generate_weak_derived_from_painsg1(
        formhash=_base_formhash(),
        word=word,
        prefix="ge",
        pre_vowel="l",
        vowel="a",
        post_vowel="mm",
        boundary="t",
        dental="ed",
        probability=0,
        vowel_inf="a",
        vowel_pa="o",
    )

    assert forms[0] == ("ge", "l", "o", "m", "t", "ed", "e", "PaInSg1", 0)
    assert manuals[0] == ("gelomted", "ge-l-o-m-t-ed", "PaPt", 0)
    assert participles == [
        ("lam", "ge", "ge-l-o-m-t-ed", True),
        ("lam", "ge", "ge-l-a-m-t-ed", True),
    ]


def test_generate_verb_parts_routes_direct_weak_painsg1_stack() -> None:
    forms: list[tuple[object, ...]] = []
    manuals: list[tuple[object, ...]] = []
    participles: list[tuple[str, str, str, bool]] = []
    word = _make_word(prefix="ge", stem="lam")
    item = ParadigmPart(
        para_id="PaInSg1",
        prefix="0",
        pre_vowel="0",
        vowel="a",
        post_vowel="mm",
        boundary="t",
        dental="ed",
        ending="e",
    )

    def _emit_form_for_context(  # noqa: PLR0913
        _captured_formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        ending: str,
        function: str,
        *,
        dental: str | None = "",
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        forms.append(
            (
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                dental,
                ending,
                function,
                prob,
            )
        )
        return "form", f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}-{dental}"

    def _emit_form(  # noqa: PLR0913
        _formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        forms.append(
            (
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                dental,
                ending,
                function,
                prob,
            )
        )
        return "form", f"{prefix}-{pre_vowel}-{vowel}-{post_vowel}-{boundary}-{dental}"

    def _emit_manual(
        _context: _WeakPainsg1DerivationContext,
        form: str,
        form_parts: str,
        function: str,
        prob: str | int | None,
    ) -> None:
        manuals.append((form, form_parts, function, prob))

    def _add_participle_to_adjectives(
        captured_word: Word,
        prefix: str,
        form_parts: str,
        *,
        is_past: bool,
    ) -> None:
        participles.append((captured_word.stem, prefix, form_parts, is_past))

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._emit_form_for_context = _emit_form_for_context  # type: ignore[method-assign,assignment]
    weak._generate_and_print_form = _emit_form  # type: ignore[method-assign,assignment]
    weak._emit_weak_painsg1_manual_context = _emit_manual  # type: ignore[method-assign,assignment]
    weak._add_participle_to_adjectives = _add_participle_to_adjectives  # type: ignore[method-assign,assignment]
    weak.generate_verb_parts(
        _base_formhash(),
        word,
        item,
        "ge",
        "l",
        "a",
        "mm",
        0,
        "87",
        "a",
        "o",
    )

    assert forms[0] == ("ge", "l", "a", "mm", "t", "ed", "e", "PaInSg1", None)
    assert ("ge", "l", "o", "m", "t", "ed", "e", "PaInSg1", 0) in forms
    assert manuals[0] == ("gelomted", "ge-l-o-m-t-ed", "PaPt", 0)
    assert participles == [
        ("lam", "ge", "ge-l-o-m-t-ed", True),
        ("lam", "ge", "ge-l-a-m-t-ed", True),
    ]


def test_generate_weak_verb_parts_uses_item_shape_for_id_window() -> None:
    session = GeneratorSession()
    output = io.StringIO()
    generator = VerbFormGenerator(session.word_pool, session.run_state, output)
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

    generator._weak_generator.generate_verb_parts(
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


def test_generate_weak_derived_from_psinsg2_routes_simplified_post_vowel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forms: list[tuple[object, ...]] = []
    sounds: list[tuple[object, ...]] = []

    def _emit_form(  # noqa: PLR0913
        _formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None = None,
    ) -> tuple[str, str]:
        forms.append(
            (
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                dental,
                ending,
                function,
                prob,
            )
        )
        return "form", "fp"

    def _emit_sound(  # noqa: PLR0913
        _run_state: object,
        _output_file: object,
        _formhash: dict[str, str],
        prefix: str,
        pre_vowel: str,
        vowel: str,
        post_vowel: str,
        boundary: str,
        dental: str | None,
        ending: str,
        function: str,
        prob: str | int | None,
        *,
        sound_change_prob_delta: int = 1,
    ) -> None:
        sounds.append(
            (
                prefix,
                pre_vowel,
                vowel,
                post_vowel,
                boundary,
                dental,
                ending,
                function,
                prob,
                sound_change_prob_delta,
            )
        )

    monkeypatch.setattr(
        generation_common,
        "_generate_and_print_form_with_sound_changes_row",
        _emit_sound,
    )

    session = GeneratorSession()
    weak = WeakVerbGenerator(session.word_pool, session.run_state, io.StringIO())
    weak._generate_and_print_form = _emit_form  # type: ignore[method-assign,assignment]
    weak._generate_weak_derived_from_psinsg2(
        formhash=_base_formhash(),
        prefix="ge",
        pre_vowel="l",
        vowel="a",
        post_vowel="mm",
        boundary="t",
        probability=None,
    )

    assert forms[0] == ("ge", "l", "a", "m", "t", None, "est", "PsInSg2", 1)
    assert sounds[0] == ("ge", "l", "a", "m", "t", None, "st", "PsInSg2", "", 1)
