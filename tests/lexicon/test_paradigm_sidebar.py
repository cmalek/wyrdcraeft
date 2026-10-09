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
    section = sidebar.sections[0]
    assert section.title == "Verb"
    assert any("eom" in cell for row in section.rows for cell in row)
    assert any("wæs" in cell for row in section.rows for cell in row)
    assert any("wesan" in cell for row in section.rows for cell in row)


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
    section = sidebar.sections[0]
    subjunctive_sing_row = next(
        row
        for row in section.rows
        if row[0] == "Subjunctive Sing" and row[1] == "1,2,3"
    )
    assert "singe" in subjunctive_sing_row[2]
    assert "sunge" in subjunctive_sing_row[3]
    subjunctive_pl_row = next(
        row for row in section.rows if row[0] == "Subjunctive Pl" and row[1] == "1,2,3"
    )
    assert subjunctive_pl_row[2] == "-"
    assert subjunctive_pl_row[3] == "-"


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
