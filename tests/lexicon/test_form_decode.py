"""Tests for morphology function-code decoding."""

from __future__ import annotations

from wyrdcraeft.services.dictionary.form_decode import (
    MorphologyRowPayload,
    build_morphology_table,
    build_paradigm_sidebar,
    decode_function_dimensions,
    filter_display_variants,
    format_verb_class,
    infer_bt_pos_from_wordclasses,
    lexical_distance,
    morphology_row_matches_pos,
    normalized_query_at_affix,
)


def test_decode_verb_pa_in_sg2() -> None:
    decoded = decode_function_dimensions(function="PaInSg2", wordclass="verb")
    assert decoded["tense"] == "past"
    assert decoded["mood"] == "indicative"
    assert decoded["number"] == "singular"
    assert decoded["person"] == "2nd"


def test_decode_verb_imperative_plural() -> None:
    decoded = decode_function_dimensions(function="ImPl", wordclass="verb")
    assert decoded["mood"] == "imperative"
    assert decoded["number"] == "plural"


def test_decode_verb_inflected_infinitive() -> None:
    decoded = decode_function_dimensions(function="IdIf", wordclass="verb")
    assert decoded["form"] == "inflected infinitive"


def test_decode_noun_plural_neuter_accusative() -> None:
    decoded = decode_function_dimensions(function="PlNeAc", wordclass="noun")
    assert decoded["number"] == "plural"
    assert decoded["gender"] == "neuter"
    assert decoded["case"] == "accusative"


def test_morphology_row_matches_entry_pos_filters_participle_for_noun() -> None:
    assert morphology_row_matches_pos(wordclass="noun", entry_pos="noun")
    assert not morphology_row_matches_pos(wordclass="verb", entry_pos="noun")


def test_infer_bt_pos_from_wordclasses_requires_single_mapping() -> None:
    assert infer_bt_pos_from_wordclasses({"noun"}) == "noun"
    assert infer_bt_pos_from_wordclasses({"noun", "verb"}) is None


def test_build_morphology_table_includes_surface_form_column() -> None:
    table = build_morphology_table(
        [("abbades", "SgMaGe", "", "", "", "abades")],
        wordclass="noun",
    )
    assert table.columns[0] == "form"
    assert table.rows[0][0] == "abbades"
    assert table.rows[0][1] == "genitive"


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


def test_format_verb_class_maps_strong_and_weak_labels() -> None:
    assert format_verb_class("s", "5", "f") == "Strong 5"
    assert format_verb_class("w", "2", "a") == "Weak II"
    assert format_verb_class("pp", "1", "0") == "Preterite-Present"
    assert format_verb_class("a", "0", "0") == "Anomalous"


def test_filter_display_variants_drops_genitive_endings() -> None:
    assert filter_display_variants(["abbod", "es", "abbud"]) == ["abbod", "abbud"]


def test_normalized_query_at_affix_requires_start_or_end() -> None:
    assert normalized_query_at_affix("mōd", "mōd")
    assert normalized_query_at_affix("acol-mōd", "mōd")
    assert normalized_query_at_affix("mōd-cræft", "mōd")
    assert not normalized_query_at_affix("iraland", "mod")


def test_lexical_distance_prefers_exact_matches() -> None:
    assert lexical_distance("mōd", "mōd") == 0
    assert lexical_distance("abbad", "abbod") == 1
    assert lexical_distance("acol-mōd", "mōd") > lexical_distance("mōd", "mōd")
