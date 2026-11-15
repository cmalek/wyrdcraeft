"""Tests for browse paradigm sidebar grids."""

from __future__ import annotations

from wyrdcraeft.services.dictionary.paradigm_sidebar import (
    MorphologyRowPayload,
    build_paradigm_sidebar,
)


def test_build_noun_paradigm_grid_uses_fk_joined_codes_without_legacy_classes() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="abbodes",
                formi="abades",
                function="SgMaGe",
                wordclass="noun",
                class1="",
                class2="",
                class3="",
            ),
            MorphologyRowPayload(
                form="abbodas",
                formi="abbodas",
                function="PlMaNo",
                wordclass="noun",
                class1="",
                class2="",
                class3="",
            ),
        ],
        wordclass="noun",
        entry_genders=("m",),
    )
    assert sidebar.sections[0].title == "Noun"
    assert sidebar.sections[0].columns == ("", "Singular", "Plural")
    assert sidebar.sections[0].rows[2] == ("Gen", "abbodes", "-")


def test_build_noun_paradigm_grid_groups_case_and_number() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="abbodes",
                formi="abades",
                function="SgMaGe",
                wordclass="noun",
                class1="weak",
                class2="",
                class3="",
            ),
            MorphologyRowPayload(
                form="abbodas",
                formi="abbodas",
                function="PlMaNo",
                wordclass="noun",
                class1="weak",
                class2="",
                class3="",
            ),
        ],
        wordclass="noun",
        entry_genders=("m",),
    )
    assert sidebar.sections[0].title == "Noun"
    assert sidebar.sections[0].columns == ("", "Singular", "Plural")
    assert sidebar.sections[0].rows[2] == ("Gen", "abbodes", "-")


def test_build_noun_paradigm_grid_includes_instrumental_case() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="by",
                formi="by",
                function="SgNeIs",
                wordclass="noun",
                class1="strong",
                class2="",
                class3="",
            ),
        ],
        wordclass="noun",
        entry_genders=("n",),
    )
    assert ("Inst", "by", "-") in sidebar.sections[0].rows


def test_build_noun_paradigm_grid_falls_back_when_entry_gender_mismatches_forms() -> (
    None
):
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="ge-līcan",
                formi="gelican",
                function="SgMaNo",
                wordclass="noun",
                class1="",
                class2="",
                class3="",
            ),
            MorphologyRowPayload(
                form="ge-līcan",
                formi="gelican",
                function="SgMaGe",
                wordclass="noun",
                class1="",
                class2="",
                class3="",
            ),
        ],
        wordclass="noun",
        entry_genders=("f",),
    )
    assert sidebar.sections[0].title == "Noun"
    assert sidebar.sections[0].rows[0] == ("Nom", "ge-līcan", "-")
    assert sidebar.sections[0].rows[2] == ("Gen", "ge-līcan", "-")


def test_build_adjective_sidebar_uses_payload_inflection() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="wīd",
                formi="wid",
                function="PoSgMaNo",
                wordclass="adjective",
                class1="",
                class2="",
                class3="",
                inflection="strong",
            ),
            MorphologyRowPayload(
                form="wīdan",
                formi="widan",
                function="PoSgMaAc",
                wordclass="adjective",
                class1="",
                class2="",
                class3="",
                inflection="weak",
            ),
        ],
        wordclass="adjective",
    )
    titles = [section.title for section in sidebar.sections]
    assert "Strong · Positive" in titles
    assert "Weak · Positive" in titles


def test_build_verb_sidebar_accepts_lowercase_function_codes() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="eom",
                formi="eom",
                function="psinsg1",
                wordclass="verb",
                class1="",
                class2="",
                class3="",
            ),
            MorphologyRowPayload(
                form="wæs",
                formi="wæs",
                function="painsg1",
                wordclass="verb",
                class1="",
                class2="",
                class3="",
            ),
            MorphologyRowPayload(
                form="wesan",
                formi="wesan",
                function="if",
                wordclass="verb",
                class1="",
                class2="",
                class3="",
            ),
        ],
        wordclass="verb",
    )
    present, past = sidebar.sections
    assert (present.title, past.title) == ("Present", "Past")
    assert ("Indicative Sing", "1", "eom") in present.rows
    assert ("Infinitive", "", "wesan") in present.rows
    assert ("Indicative Sing", "1", "wæs") in past.rows
    assert all("wæs" not in cell for row in present.rows for cell in row)
    assert all("eom" not in cell for row in past.rows for cell in row)


def test_build_verb_sidebar_places_ps_su_sg_on_subjunctive_sing_row() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="singe",
                formi="singe",
                function="PsSuSg",
                wordclass="verb",
                class1="",
                class2="",
                class3="",
            ),
            MorphologyRowPayload(
                form="sunge",
                formi="sunge",
                function="PaSuSg",
                wordclass="verb",
                class1="",
                class2="",
                class3="",
            ),
        ],
        wordclass="verb",
    )
    present, past = sidebar.sections
    assert present.rows == (("Subjunctive Sing", "1,2,3", "singe"),)
    assert past.rows == (("Subjunctive Sing", "1,2,3", "sunge"),)
    # Subjunctive Pl has no form in either tense, so it is dropped.
    assert all(row[0] != "Subjunctive Pl" for row in (*present.rows, *past.rows))


def _row(form: str, function: str, wordclass: str) -> MorphologyRowPayload:
    return MorphologyRowPayload(
        form=form,
        formi=form,
        function=function,
        wordclass=wordclass,
        class1="",
        class2="",
        class3="",
    )


def test_verb_splits_into_present_and_past_sections() -> None:
    sidebar = build_paradigm_sidebar(
        [
            _row("singan", "If", "verb"),
            _row("singe", "PsInSg1", "verb"),
            _row("sang", "PaInSg1", "verb"),
            _row("singende", "PsPt", "verb"),
            _row("sungen", "PaPt", "verb"),
            _row("sing", "ImSg", "verb"),
        ],
        wordclass="verb",
    )
    sections = sidebar.sections
    assert [(s.title, s.primary, s.secondary) for s in sections] == [
        ("Present", "Present", ""),
        ("Past", "Past", ""),
    ]
    for section in sections:
        assert section.columns == ("", "Person", "Forms")
        assert not section.flat
        assert all(row[:3] != ("", "Present", "Past") for row in section.rows)
    present, past = sections
    assert present.rows[0] == ("Infinitive", "", "singan")
    assert ("Participles", "", "singende") in present.rows
    assert ("Imperative Sing", "", "sing") in present.rows
    assert all(row[0] != "Infinitive" for row in past.rows)
    assert all(not row[0].startswith("Imperative") for row in past.rows)
    assert ("Participles", "", "sungen") in past.rows


def test_unparsed_verb_code_has_no_verb_grid() -> None:
    # Neither tense has a form, so both sections are omitted and the sidebar
    # falls back to the decoded morphology table, as other parts of speech do.
    sidebar = build_paradigm_sidebar(
        [_row("wesan", "???", "verb")],
        wordclass="verb",
    )
    (section,) = sidebar.sections
    assert section.title == "Forms"
    assert section.rows[0][0] == "wesan"


def _featured_pronoun_rows() -> list[MorphologyRowPayload]:
    return [
        _row("ic", "SgMaNo", "pronoun"),
        _row("mec", "SgFeAc", "pronoun"),
        _row("hit", "SgNeGe", "pronoun"),
        _row("we", "PlMaNo", "pronoun"),
        _row("þy", "SgNeIs", "pronoun"),
        _row("", "SgMaDa", "pronoun"),
    ]


def test_pronoun_with_features_splits_singular_and_plural() -> None:
    sidebar = build_paradigm_sidebar(
        _featured_pronoun_rows(),
        wordclass="pronoun",
    )
    singular, plural = sidebar.sections
    assert (singular.title, plural.title) == ("Singular", "Plural")
    assert (singular.primary, plural.primary) == ("Singular", "Plural")
    assert singular.secondary == plural.secondary == ""
    assert not singular.flat
    assert not plural.flat
    assert singular.columns == ("", "Masc.", "Fem.", "Neut.")
    assert plural.columns == ("", "Plural")
    assert singular.rows == (
        ("Nom", "ic", "", ""),
        ("Acc", "", "mec", ""),
        ("Gen", "", "", "hit"),
        ("Inst", "", "", "þy"),
    )
    assert plural.rows == (("Nom", "we"),)


def test_pronoun_unplaceable_form_beside_featured_rows_makes_entry_flat() -> None:
    sidebar = build_paradigm_sidebar(
        [*_featured_pronoun_rows(), _row("junk", "nope", "pronoun")],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.flat is True
    assert section.rows == (("ic, mec, hit, we, þy, junk",),)


def test_pronoun_dual_and_partial_forms_make_entry_flat() -> None:
    sidebar = build_paradigm_sidebar(
        [
            _row("ic", "SgMaNo", "pronoun"),
            _row("wit", "DuMaNo", "pronoun"),
            _row("hwæs", "MaGe", "pronoun"),
        ],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.flat is True
    assert section.rows == (("ic, wit, hwæs",),)


def test_pronoun_featureless_forms_around_one_featured_form_make_entry_flat() -> None:
    sidebar = build_paradigm_sidebar(
        [
            _row("a", "", "pronoun"),
            _row("b", "SgNeDa", "pronoun"),
            _row("c", "", "pronoun"),
        ],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.flat is True
    assert section.rows == (("a, b, c",),)


def test_pronoun_dual_only_entry_is_flat_with_every_form() -> None:
    sidebar = build_paradigm_sidebar(
        [
            _row("wit", "DuMaNo", "pronoun"),
            _row("unc", "DuMaAc", "pronoun"),
            _row("uncer", "DuMaGe", "pronoun"),
            _row("wit", "DuFeNo", "pronoun"),
        ],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.flat is True
    assert section.rows == (("wit, unc, uncer",),)


def test_pronoun_without_instrumental_has_no_inst_row() -> None:
    rows = [row for row in _featured_pronoun_rows() if row.form != "þy"]
    sidebar = build_paradigm_sidebar(rows, wordclass="pronoun")
    assert all(row[0] != "Inst" for section in sidebar.sections for row in section.rows)


def test_pronoun_without_features_is_one_flat_section() -> None:
    sidebar = build_paradigm_sidebar(
        [
            _row("hwā", "", "pronoun"),
            _row("hwæt", "nope", "pronoun"),
            _row("hwā", "", "pronoun"),
            _row("hwone", "", "pronoun"),
        ],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.flat is True
    assert section.primary == section.secondary == ""
    assert len(section.columns) == 1
    assert section.columns[0] not in {"case", "gender", "number", "person"}
    assert section.rows == (("hwā, hwæt, hwone",),)


def test_pronoun_with_partial_features_falls_back_to_flat() -> None:
    sidebar = build_paradigm_sidebar(
        [_row("hwæs", "MaGe", "pronoun")],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.flat is True
    assert section.rows == (("hwæs",),)


def test_blank_pronoun_surface_keeps_flat_pronoun_table() -> None:
    # A featured row with no surface spelling yields neither a paradigm nor a
    # flat list, so the sidebar keeps the decoded flat morphology table.
    sidebar = build_paradigm_sidebar(
        [_row("", "SgMaNo", "pronoun")],
        wordclass="pronoun",
    )
    (section,) = sidebar.sections
    assert section.title == "Forms"
    assert section.columns[0] == "form"
    assert "nominative" in section.rows[0]


def test_adjective_sections_carry_both_axes() -> None:
    rows = [
        MorphologyRowPayload(
            form=f"{infl}-{degree}-{number}{gender}",
            formi="",
            function=f"{degree}{number}{gender}No",
            wordclass="adjective",
            class1="",
            class2="",
            class3="",
            inflection=infl,
        )
        for infl in ("strong", "weak")
        for degree in ("Po", "Co", "Sp")
        for number, gender in (("Sg", "Ma"), ("Sg", "Fe"), ("Sg", "Ne"), ("Pl", "Ma"))
    ]
    sidebar = build_paradigm_sidebar(rows, wordclass="adjective")
    assert [(s.primary, s.secondary) for s in sidebar.sections] == [
        (primary, secondary)
        for primary in ("Strong", "Weak")
        for secondary in ("Positive", "Comparative", "Superlative")
    ]
    for section in sidebar.sections:
        assert section.title == f"{section.primary} · {section.secondary}"
        assert section.columns == ("", "Masc. sg.", "Fem. sg.", "Neut. sg.", "Plural")
        assert not section.flat
    assert sidebar.sections[0].rows == (
        (
            "Nom",
            "strong-Po-SgMa",
            "strong-Po-SgFe",
            "strong-Po-SgNe",
            "strong-Po-PlMa",
        ),
    )


def test_empty_section_is_omitted() -> None:
    present_only = build_paradigm_sidebar(
        [_row("singe", "PsInSg1", "verb")],
        wordclass="verb",
    )
    assert [section.title for section in present_only.sections] == ["Present"]
    singular_only = build_paradigm_sidebar(
        [_row("ic", "SgMaNo", "pronoun"), _row("", "PlMaNo", "pronoun")],
        wordclass="pronoun",
    )
    (singular,) = singular_only.sections
    assert singular.title == "Singular"
    # Fem. and Neut. have no value in any row, so those columns are dropped.
    assert singular.columns == ("", "Masc.")
    assert singular.rows == (("Nom", "ic"),)


def test_noun_and_adverb_have_no_switch_axes() -> None:
    noun = build_paradigm_sidebar(
        [_row("stān", "SgMaNo", "noun")],
        wordclass="noun",
        entry_genders=("m",),
    )
    adverb = build_paradigm_sidebar(
        [_row("wīdest", "Su", "adverb")],
        wordclass="adverb",
    )
    assert noun.sections
    assert adverb.sections
    for section in (*noun.sections, *adverb.sections):
        assert section.primary == ""
        assert section.secondary == ""
        assert section.flat is False


def test_adverb_without_degree_falls_back_to_forms() -> None:
    sidebar = build_paradigm_sidebar(
        [_row("wel", "???", "adverb")],
        wordclass="adverb",
    )
    section = sidebar.sections[0]
    assert section.title == "Forms"
    assert section.rows[0][0] == "wel"


def test_build_adverb_sidebar_decodes_superlative_su_code() -> None:
    sidebar = build_paradigm_sidebar(
        [
            MorphologyRowPayload(
                form="wīdest",
                formi="widest",
                function="Su",
                wordclass="adverb",
                class1="",
                class2="",
                class3="",
            ),
        ],
        wordclass="adverb",
    )
    section = sidebar.sections[0]
    assert section.title == "Adverb"
    superlative_row = next(row for row in section.rows if row[0] == "Superlative")
    assert "wīdest" in superlative_row[1]
