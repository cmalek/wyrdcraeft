"""Pure layout and selection rules for the browse Forms section (ADR 0027)."""

from __future__ import annotations

import pytest

from wyrdcraeft.services.dictionary.browse_forms import (
    PRIMARY,
    SECONDARY,
    FormsSelection,
    axis_values,
    fit_columns,
    merge_feature_columns,
)
from wyrdcraeft.services.dictionary.paradigm_sidebar import ParadigmTableSection

#: A verb Present section shaped like ``_build_verb_sidebar`` output.
_VERB = ParadigmTableSection(
    title="Present",
    columns=("", "Person", "Forms"),
    rows=(
        ("Infinitive", "", "healdan"),
        ("Indicative Sing", "1", "healde, healdo, healdu, healdæ"),
        ("Subjunctive Pl", "1,2,3", "healden, healdon"),
    ),
    primary="Present",
)


def _adjective(primary: str, secondary: str) -> ParadigmTableSection:
    """Build one adjective section on both axes."""
    return ParadigmTableSection(
        title=f"{primary} · {secondary}",
        columns=("", "Masc. sg."),
        rows=(("Nom", f"{primary}{secondary}"),),
        primary=primary,
        secondary=secondary,
    )


@pytest.mark.parametrize("available", range(16, 121))
def test_fitted_table_never_exceeds_the_pane(available: int) -> None:
    # 16 = the longest label word ("Subjunctive", 11) + a one-cell forms
    # column + padding; below that the labels alone are wider than the pane.
    columns, rows, widths = fit_columns(_VERB, available, 1)
    assert sum(width + 2 for width in widths) <= available
    assert len(columns) == len(widths)
    assert all(len(row) == len(columns) for row in rows)


def test_wide_pane_keeps_every_column_at_natural_width() -> None:
    columns, _rows, widths = fit_columns(_VERB, 120, 1)
    assert columns == ("", "Person", "Forms")
    assert widths == (15, 6, len("healde, healdo, healdu, healdæ"))


def test_narrow_pane_merges_label_and_person() -> None:
    columns, rows, widths = fit_columns(_VERB, 26, 1)
    assert columns == ("", "Forms")
    assert rows[1] == ("Indicative Sing 1", "healde, healdo, healdu, healdæ")
    assert rows[0] == ("Infinitive", "healdan")
    assert widths[0] == len("Subjunctive")


def test_narrow_form_column_leaves_its_room_to_the_wide_one() -> None:
    noun = ParadigmTableSection(
        title="Noun",
        columns=("", "Singular", "Plural"),
        rows=(("Nom", "scild", "scilda, scildena, scildna"),),
    )
    _columns, _rows, widths = fit_columns(noun, 53, 1)
    assert widths == (3, len("Singular"), len("scilda, scildena, scildna"))
    _columns, _rows, widths = fit_columns(noun, 30, 1)
    assert widths == (3, len("Singular"), 30 - 5 - 10 - 2)


def test_merge_keeps_tables_with_one_feature_column() -> None:
    columns = ("", "Singular", "Plural")
    rows = (("Nom", "scild", "scildas"),)
    assert merge_feature_columns(columns, rows) == (columns, rows)


def test_secondary_axis_keeps_degree_order_when_strong_lacks_comparative() -> None:
    sections = [
        _adjective("Strong", "Positive"),
        _adjective("Strong", "Superlative"),
        _adjective("Weak", "Positive"),
        _adjective("Weak", "Comparative"),
        _adjective("Weak", "Superlative"),
    ]
    assert axis_values(sections, SECONDARY) == (
        "Positive",
        "Comparative",
        "Superlative",
    )
    assert axis_values(sections, PRIMARY) == ("Strong", "Weak")


def test_selection_stops_at_the_ends_and_reports_missing_combination() -> None:
    selection = FormsSelection(
        [_adjective("Strong", "Positive"), _adjective("Weak", "Comparative")]
    )
    assert not selection.step(PRIMARY, -1)
    assert selection.step(SECONDARY, 1)
    assert selection.visible_section() is None
    assert selection.label() == "Strong · Comparative"
    assert selection.step(PRIMARY, 1)
    section = selection.visible_section()
    assert section is not None
    assert section.title == "Weak · Comparative"
    assert not selection.step(PRIMARY, 1)
