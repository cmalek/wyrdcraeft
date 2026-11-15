"""Assemble Wright-style paradigm grids for the dictionary browse sidebar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from wyrdcraeft.services.dictionary.entry_view import drop_empty_columns
from wyrdcraeft.services.dictionary.form_decode import (
    _ADJ_PATTERN,
    _GENDER_LABELS,
    _IMP_PATTERN,
    _MOOD_LABELS,
    _NOUN_LIKE_PATTERN,
    _NUMBER_LABELS,
    _TENSE_LABELS,
    _VERB_FINITE_PATTERN,
    _VERB_FINITE_SG_PATTERN,
    _VERB_FUNCTION_LABELS,
    _decode_noun_like,
    _label,
    _pick_inflection,
    build_morphology_table,
    decode_function_dimensions,
    format_bt_gender_label,
)
from wyrdcraeft.services.morphology.text_utils import canonicalize_inflection_code

#: Short case labels used in POS paradigm sidebar grids.
_PARADIGM_CASE_CODE_TO_LABEL: Final[dict[str, str]] = {
    "No": "Nom",
    "Ac": "Acc",
    "Ge": "Gen",
    "Da": "Dat",
    "Is": "Inst",
}
#: Case row order for case-by-column paradigm grids.
_CASE_ORDER: Final[tuple[str, ...]] = ("Nom", "Acc", "Gen", "Dat", "Inst")
#: Adjective grid column per singular gender code.
_ADJ_SG_COLUMNS: Final[dict[str, str]] = {
    "Ma": "Masc. sg.",
    "Fe": "Fem. sg.",
    "Ne": "Neut. sg.",
}
#: Adjective grid columns in display order.
_ADJ_COLUMNS: Final[tuple[str, ...]] = ("Masc. sg.", "Fem. sg.", "Neut. sg.", "Plural")
#: Pronoun singular grid column per gender code.
_PRONOUN_SG_COLUMNS: Final[dict[str, str]] = {
    "Ma": "Masc.",
    "Fe": "Fem.",
    "Ne": "Neut.",
}
#: Verb row labels and persons in display order (Infinitive is prepended).
_VERB_ROW_ORDER: Final[tuple[tuple[str, str], ...]] = (
    ("Indicative Sing", "1"),
    ("Indicative Sing", "2"),
    ("Indicative Sing", "3"),
    ("Indicative Pl", "1,2,3"),
    ("Subjunctive Sing", "1,2,3"),
    ("Subjunctive Pl", "1,2,3"),
    ("Participles", ""),
    ("Imperative Sing", ""),
    ("Imperative Pl", ""),
    ("Inflected Infin", ""),
)


@dataclass(frozen=True)
class ParadigmTableSection:
    """
    One titled paradigm grid section for the browse sidebar.

    The visible table of a switch group is the section whose ``primary`` and
    ``secondary`` equal the current selections; a section with both empty is
    in no switch and is always shown.

    Attributes:
        title: Section heading shown above the grid.
        columns: Ordered column headers.
        rows: Cell values aligned to ``columns``.
        primary: Primary switch value (for example ``Present`` or ``Strong``).
        secondary: Secondary switch value (for example ``Comparative``).
        flat: Whether the section is one row of deduplicated forms with no
            feature columns.

    """

    #: Section heading shown above the grid.
    title: str
    #: Ordered column headers.
    columns: tuple[str, ...]
    #: Cell values aligned to ``columns``.
    rows: tuple[tuple[str, ...], ...]
    #: Primary switch value, or empty when the section is in no primary switch.
    primary: str = ""
    #: Secondary switch value, or empty when in no secondary switch.
    secondary: str = ""
    #: Whether the section holds one row of deduplicated forms only.
    flat: bool = False


@dataclass(frozen=True)
class ParadigmSidebarSpec:
    """
    Ordered paradigm table sections for one POS-filtered morphology sidebar.

    Attributes:
        sections: Sidebar sections in display order.

    """

    #: Sidebar sections in display order.
    sections: tuple[ParadigmTableSection, ...]


@dataclass(frozen=True)
class MorphologyRowPayload:
    """
    Minimal morphology payload consumed by paradigm grid builders.

    Attributes:
        form: Surface spelling.
        formi: Alternate surface spelling.
        function: Morphology function code.
        wordclass: Morphology wordclass label.
        class1: First morphology class column.
        class2: Second morphology class column.
        class3: Third morphology class column.
        inflection: FK-backed strong/weak label when legacy classes are empty.

    """

    #: Surface spelling.
    form: str
    #: Alternate surface spelling.
    formi: str
    #: Morphology function code.
    function: str
    #: Morphology wordclass label.
    wordclass: str
    #: First morphology class column.
    class1: str
    #: Second morphology class column.
    class2: str
    #: Third morphology class column.
    class3: str
    #: FK-backed strong/weak label when legacy classes are empty.
    inflection: str = ""


def _surface_form(form: str, formi: str) -> str:
    """
    Pick the preferred surface spelling for one morphology row.

    Args:
        form: Primary surface spelling.
        formi: Alternate surface spelling.

    Returns:
        Non-empty surface spelling.

    """
    return form.strip() or formi.strip()


def _paradigm_grid_case_label(code: str) -> str | None:
    """
    Map one morphology case code to a short paradigm grid row label.

    Args:
        code: Morphology case code such as ``No`` or ``Is``.

    Returns:
        Grid row label, or ``None`` when the code is unsupported.

    """
    return _PARADIGM_CASE_CODE_TO_LABEL.get(code.strip())


def _join_surfaces(values: set[str]) -> str:
    """
    Join distinct surface spellings for one paradigm cell.

    Args:
        values: Distinct non-empty surface spellings.

    Returns:
        Comma-separated spellings, or ``-`` when empty.

    """
    ordered = sorted(value for value in values if value.strip())
    if not ordered:
        return "-"
    return ", ".join(ordered)


def _join_cell(values: set[str] | None) -> str:
    """
    Join distinct surface spellings for one switchable paradigm cell.

    Args:
        values: Distinct surface spellings, or ``None`` for a missing cell.

    Returns:
        Comma-separated sorted spellings, or an empty string when none.

    """
    return ", ".join(sorted(value for value in values or () if value.strip()))


def _finish_section(  # noqa: PLR0913
    title: str,
    columns: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    form_start: int,
    primary: str = "",
    secondary: str = "",
) -> ParadigmTableSection | None:
    """
    Drop formless rows and empty columns, then build one grid section.

    Args:
        title: Section heading.
        columns: Ordered column headers.
        rows: Candidate cell rows aligned to ``columns``.

    Keyword Args:
        form_start: Index of the first form (non-feature) cell in each row.
        primary: Primary switch value.
        secondary: Secondary switch value.

    Returns:
        The section, or ``None`` when no row has a form.

    """
    kept = [row for row in rows if any(cell.strip() for cell in row[form_start:])]
    if not kept:
        return None
    kept_columns, kept_rows = drop_empty_columns(columns, kept)
    return ParadigmTableSection(
        title=title,
        columns=kept_columns,
        rows=kept_rows,
        primary=primary,
        secondary=secondary,
    )


def _case_grid_rows(
    cells: dict[tuple[str, ...], set[str]],
    columns: tuple[str, ...],
) -> list[tuple[str, ...]]:
    """
    Lay out case rows (Nom to Inst) over the given form columns.

    Args:
        cells: Surface spellings keyed by ``(case, column)``.
        columns: Form column labels in display order.

    Returns:
        One row per case: the case label then one joined cell per column.

    """
    return [
        (case, *(_join_cell(cells.get((case, column))) for column in columns))
        for case in _CASE_ORDER
    ]


def _gender_code_from_label(label: str) -> str:
    """
    Map one decoded gender label back to a morphology gender code.

    Args:
        label: Decoded gender label.

    Returns:
        ``Ma``, ``Fe``, or ``Ne`` when recognized.

    """
    normalized = label.strip().casefold()
    for code, mapped in _GENDER_LABELS.items():
        if mapped == normalized:
            return code
    return ""


def _append_surface(
    target: dict[tuple[str, ...], set[str]],
    key: tuple[str, ...],
    surface: str,
) -> None:
    """
    Append one surface spelling to a paradigm cell bucket.

    Args:
        target: Paradigm cell map.
        key: Cell coordinate tuple.
        surface: Surface spelling to append.

    Side Effects:
        Mutates ``target`` when ``surface`` is non-empty.

    """
    if not surface.strip():
        return
    target.setdefault(key, set()).add(surface.strip())


def _sidebar_has_content(sidebar: ParadigmSidebarSpec) -> bool:
    """
    Return whether a paradigm sidebar contains any non-empty cell values.

    Args:
        sidebar: Candidate sidebar specification.

    Returns:
        ``True`` when at least one cell has a real form value.

    """
    for section in sidebar.sections:
        for row in section.rows:
            data_cells = row[1:] if len(row) > 1 else row
            for cell in data_cells:
                if cell.strip() not in {"", "-"}:
                    return True
    return False


def build_paradigm_sidebar(
    rows: list[MorphologyRowPayload],
    *,
    wordclass: str,
    entry_genders: tuple[str, ...] = (),
) -> ParadigmSidebarSpec:
    """
    Build POS-aware paradigm grids for the browse morphology sidebar.

    Args:
        rows: Morphology rows sharing one dictionary entry POS filter.

    Keyword Args:
        wordclass: Dominant morphology wordclass for the sidebar.
        entry_genders: Gender markers stored on the dictionary entry.

    Returns:
        Ordered paradigm table sections for sidebar rendering.

    """
    pos = wordclass.strip().casefold()
    if pos in {"verb", "participle"}:
        sidebar = _build_verb_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "noun":
        sidebar = _build_noun_sidebar(rows, entry_genders=entry_genders)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "adjective":
        sidebar = _build_adjective_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "pronoun":
        sidebar = _build_pronoun_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    elif pos == "adverb":
        sidebar = _build_adverb_sidebar(rows)
        if _sidebar_has_content(sidebar):
            return sidebar
    table = build_morphology_table(
        [
            (
                row.form,
                row.function,
                row.class1,
                row.class2,
                row.class3,
                row.formi,
                row.inflection,
            )
            for row in rows
        ],
        wordclass=wordclass,
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Forms",
                columns=table.columns,
                rows=table.rows,
            ),
        )
    )


def _build_verb_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build the Wright-style verb conjugation grids, one per tense.

    Args:
        rows: Verb morphology rows.

    Returns:
        Verb sidebar specification with ``Present`` and ``Past`` sections,
        each omitted when it has no form.

    """
    cells, infinitive = _collect_verb_cells(rows)
    sections: list[ParadigmTableSection] = []
    for title, tense in (("Present", "present"), ("Past", "past")):
        table_rows: list[tuple[str, ...]] = []
        if infinitive and tense == "present":
            table_rows.append(("Infinitive", "", infinitive))
        for label, person in _VERB_ROW_ORDER:
            key = (label, person, tense) if person else (label, tense)
            table_rows.append((label, person, _join_cell(cells.get(key))))
        section = _finish_section(
            title,
            ("", "Person", "Forms"),
            table_rows,
            form_start=2,
            primary=title,
        )
        if section is not None:
            sections.append(section)
    return ParadigmSidebarSpec(sections=tuple(sections))


def _collect_verb_cells(
    rows: list[MorphologyRowPayload],
) -> tuple[dict[tuple[str, ...], set[str]], str]:
    """
    Collect verb conjugation cells keyed by row label, person and tense.

    Args:
        rows: Verb morphology rows.

    Returns:
        The cell map (keys ``(label, person, tense)`` for finite forms and
        ``(label, tense)`` otherwise) and the infinitive surface, if any.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    infinitive = ""
    for row in rows:
        surface = _surface_form(row.form, row.formi)
        code = canonicalize_inflection_code(row.function)
        exact = _VERB_FUNCTION_LABELS.get(code)
        if exact is not None and exact.get("form") == "infinitive":
            infinitive = surface or infinitive
            continue
        if code in {"If", "Inf"}:
            infinitive = surface or infinitive
            continue
        if code == "IdIf":
            _append_surface(cells, ("Inflected Infin", "present"), surface)
            continue
        if code in {"PsPa", "PsPt", "Pp"}:
            _append_surface(cells, ("Participles", "present"), surface)
            continue
        if code == "PaPt":
            _append_surface(cells, ("Participles", "past"), surface)
            continue
        imperative = _IMP_PATTERN.fullmatch(code)
        if imperative is not None:
            number = _label(_NUMBER_LABELS, imperative.group("number"))
            label = "Imperative Pl" if number == "plural" else "Imperative Sing"
            _append_surface(cells, (label, "present"), surface)
            continue
        finite_key = _verb_finite_key(code)
        if finite_key is not None:
            _append_surface(cells, finite_key, surface)
    return cells, infinitive


def _verb_finite_key(code: str) -> tuple[str, str, str] | None:
    """
    Map one finite verb function code to its ``(label, person, tense)`` cell.

    Args:
        code: Canonical verb function code such as ``PsInSg1`` or ``PaSuPl``.

    Returns:
        The cell key, or ``None`` when ``code`` is not a finite form.

    """
    finite_sg = _VERB_FINITE_SG_PATTERN.fullmatch(code)
    if finite_sg is not None:
        tense = _label(_TENSE_LABELS, finite_sg.group("tense"))
        mood = _label(_MOOD_LABELS, finite_sg.group("mood"))
        if mood == "indicative":
            row_label = "Indicative Sing"
        elif mood == "subjunctive":
            row_label = "Subjunctive Sing"
        else:
            row_label = mood.title()
        return (row_label, finite_sg.group("person"), tense)
    finite = _VERB_FINITE_PATTERN.fullmatch(code)
    if finite is None:
        return None
    tense = _label(_TENSE_LABELS, finite.group("tense"))
    mood = _label(_MOOD_LABELS, finite.group("mood"))
    number = _label(_NUMBER_LABELS, finite.group("number"))
    if mood == "indicative":
        row_label = "Indicative Pl"
    elif mood == "subjunctive":
        row_label = "Subjunctive Sing" if number == "singular" else "Subjunctive Pl"
    else:
        row_label = mood.title()
    return (row_label, "1,2,3", tense)


def _collect_noun_sidebar_cells(
    rows: list[MorphologyRowPayload],
    *,
    allowed_genders: frozenset[str] | None = None,
) -> dict[tuple[str, ...], set[str]]:
    """
    Collect noun declension cells keyed by case and number labels.

    Args:
        rows: Noun morphology rows.

    Keyword Args:
        allowed_genders: Morphology gender codes to keep; ``None`` keeps all.

    Returns:
        Case/number cell map for noun sidebar rendering.

    Note:
        Per ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``,
        noun paradigms are keyed by case and number; optional gender filtering
        follows dictionary-entry gender tags when they agree with form codes.
        PoS scope: ``noun``.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        decoded = _decode_noun_like(row.function.strip())
        if "case" not in decoded:
            continue
        match = _NOUN_LIKE_PATTERN.fullmatch(row.function.strip())
        if match is None:
            continue
        gender_code = match.group("gender")
        if allowed_genders and gender_code not in allowed_genders:
            continue
        case_label = _paradigm_grid_case_label(match.group("case"))
        if case_label is None:
            continue
        number_label = "Singular" if match.group("number") == "Sg" else "Plural"
        _append_surface(
            cells,
            (case_label, number_label),
            _surface_form(row.form, row.formi),
        )
    return cells


def _build_noun_sidebar(
    rows: list[MorphologyRowPayload],
    *,
    entry_genders: tuple[str, ...],
) -> ParadigmSidebarSpec:
    """
    Build the case-by-number noun declension grid.

    Args:
        rows: Noun morphology rows.

    Keyword Args:
        entry_genders: Gender markers stored on the dictionary entry.

    Returns:
        Noun sidebar specification.

    Note:
        Per ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``,
        noun paradigms group surface forms by case and number. When entry gender
        tags disagree with generated masculine/feminine/neuter form codes, the
        grid falls back to unfiltered cells so mis-tagged lemmas still display.
        PoS scope: ``noun``.

    """
    allowed_genders = frozenset(
        {
            _gender_code_from_label(format_bt_gender_label(gender))
            for gender in entry_genders
            if gender.strip()
        }
    )
    cells = _collect_noun_sidebar_cells(
        rows,
        allowed_genders=allowed_genders or None,
    )
    if not cells and rows and allowed_genders:
        cells = _collect_noun_sidebar_cells(rows)
    case_order: tuple[str, ...] = ("Nom", "Acc", "Gen", "Dat")
    if any(cells.get(("Inst", number)) for number in ("Singular", "Plural")):
        case_order = (*case_order, "Inst")
    table_rows = tuple(
        (
            case,
            _join_surfaces(cells.get((case, "Singular"), set())),
            _join_surfaces(cells.get((case, "Plural"), set())),
        )
        for case in case_order
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Noun",
                columns=("", "Singular", "Plural"),
                rows=table_rows,
            ),
        )
    )


def _build_adjective_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build Wright-style adjective grids grouped by inflection and degree.

    Args:
        rows: Adjective morphology rows.

    Returns:
        Adjective sidebar specification.

    """
    sections: list[ParadigmTableSection] = []
    for inflection in ("strong", "weak"):
        for degree_label, degree_code in (
            ("Positive", "Po"),
            ("Comparative", "Co"),
            ("Superlative", "Sp"),
        ):
            section = _build_adjective_degree_section(
                rows,
                inflection=inflection,
                degree_code=degree_code,
                degree_label=degree_label,
            )
            if section is not None:
                sections.append(section)
    return ParadigmSidebarSpec(sections=tuple(sections))


def _build_adjective_degree_section(
    rows: list[MorphologyRowPayload],
    *,
    inflection: str,
    degree_code: str,
    degree_label: str,
) -> ParadigmTableSection | None:
    """
    Build one adjective degree grid for a single inflection type.

    Args:
        rows: Adjective morphology rows.

    Keyword Args:
        inflection: ``strong`` or ``weak`` inflection label.
        degree_code: Degree code prefix such as ``Po`` or ``Co``.
        degree_label: Degree name such as ``Positive``; the secondary switch.

    Returns:
        Grid section titled ``<Inflection> · <Degree>`` when any form is
        populated, otherwise ``None``.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        inflection_label = _pick_inflection(
            row.class1,
            row.class2,
            row.class3,
            morph_class_inflection=row.inflection,
        ).casefold()
        if inflection_label != inflection:
            continue
        match = _ADJ_PATTERN.fullmatch(row.function.strip())
        if match is None or match.group("degree") != degree_code:
            continue
        case_label = _paradigm_grid_case_label(match.group("case"))
        if case_label is None:
            continue
        if match.group("number") == "Pl":
            column = "Plural"
        else:
            column = _ADJ_SG_COLUMNS.get(match.group("gender"), "")
        if not column:
            continue
        _append_surface(cells, (case_label, column), _surface_form(row.form, row.formi))
    primary = inflection.title()
    return _finish_section(
        f"{primary} · {degree_label}",
        ("", *_ADJ_COLUMNS),
        _case_grid_rows(cells, _ADJ_COLUMNS),
        form_start=1,
        primary=primary,
        secondary=degree_label,
    )


def _build_pronoun_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build pronoun case grids split into ``Singular`` and ``Plural`` sections.

    Args:
        rows: Pronoun morphology rows.

    Returns:
        Pronoun sidebar specification. Unless every form places in a
        singular or plural grid cell, one flat section lists all forms.

    Note:
        Per ADR 0027, singular forms vary by gender (Masc., Fem., Neut.
        columns) and plural forms do not (one Plural column). Every form is
        shown, so one unplaceable form (dual, partial or missing features)
        turns the whole entry into the flat list.

    """
    cells = _collect_pronoun_cells(rows)
    if not cells:
        flat = _flat_forms_section("Pronoun", rows)
        return ParadigmSidebarSpec(sections=() if flat is None else (flat,))
    sections: list[ParadigmTableSection] = []
    for title, columns in (
        ("Singular", tuple(_PRONOUN_SG_COLUMNS.values())),
        ("Plural", ("Plural",)),
    ):
        section = _finish_section(
            title,
            ("", *columns),
            _case_grid_rows(cells, columns),
            form_start=1,
            primary=title,
        )
        if section is not None:
            sections.append(section)
    return ParadigmSidebarSpec(sections=tuple(sections))


def _collect_pronoun_cells(
    rows: list[MorphologyRowPayload],
) -> dict[tuple[str, ...], set[str]]:
    """
    Collect pronoun surfaces keyed by case label and grid column.

    Args:
        rows: Pronoun morphology rows.

    Returns:
        Cell map keyed by ``(case, column)``. Rows with no surface spelling
        contribute nothing. When any row with a surface cannot be placed
        (dual number, partial or missing case/gender/number), the map is
        empty so the caller shows every form in the flat fallback instead.

    """
    cells: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        surface = _surface_form(row.form, row.formi)
        if not surface:
            continue
        key = _pronoun_cell_key(row.function)
        if key is None:
            return {}
        _append_surface(cells, key, surface)
    return cells


def _pronoun_cell_key(function: str) -> tuple[str, str] | None:
    """
    Map one pronoun function code to its ``(case, column)`` grid cell.

    Args:
        function: Morphology function code such as ``SgMaNo``.

    Returns:
        The cell key, or ``None`` when the code is not a singular or plural
        form with case and gender.

    """
    match = _NOUN_LIKE_PATTERN.fullmatch(function.strip())
    if match is None:
        return None
    case_label = _paradigm_grid_case_label(match.group("case"))
    number = match.group("number")
    if number == "Pl":
        column = "Plural"
    elif number == "Sg":
        column = _PRONOUN_SG_COLUMNS.get(match.group("gender"), "")
    else:
        column = ""
    if case_label is None or not column:
        return None
    return (case_label, column)


def _flat_forms_section(
    title: str,
    rows: list[MorphologyRowPayload],
) -> ParadigmTableSection | None:
    """
    Build a flat section listing deduplicated forms in first-seen order.

    Args:
        title: Section heading.
        rows: Morphology rows whose surfaces are listed.

    Returns:
        A ``flat`` section with one ``Forms`` column and one row, or ``None``
        when no row has a surface spelling.

    """
    forms = dict.fromkeys(
        surface for row in rows if (surface := _surface_form(row.form, row.formi))
    )
    if not forms:
        return None
    return ParadigmTableSection(
        title=title,
        columns=("Forms",),
        rows=((", ".join(forms),),),
        flat=True,
    )


def _build_adverb_sidebar(rows: list[MorphologyRowPayload]) -> ParadigmSidebarSpec:
    """
    Build a simple adverb degree list.

    Args:
        rows: Adverb morphology rows.

    Returns:
        Adverb sidebar specification.

    """
    cells: dict[str, set[str]] = {}
    for row in rows:
        decoded = decode_function_dimensions(
            function=row.function,
            wordclass="adverb",
            class1=row.class1,
            class2=row.class2,
            class3=row.class3,
        )
        degree = decoded.get("degree", "")
        if not degree:
            continue
        cells.setdefault(degree.title(), set()).add(_surface_form(row.form, row.formi))
    if not cells:
        table = build_morphology_table(
            [
                (
                    row.form,
                    row.function,
                    row.class1,
                    row.class2,
                    row.class3,
                    row.formi,
                )
                for row in rows
            ],
            wordclass="adverb",
        )
        return ParadigmSidebarSpec(
            sections=(
                ParadigmTableSection(
                    title="Adverb",
                    columns=table.columns,
                    rows=table.rows,
                ),
            )
        )
    table_rows = tuple(
        (degree, _join_surfaces(cells[degree]))
        for degree in ("Positive", "Comparative", "Superlative")
        if degree in cells
    )
    return ParadigmSidebarSpec(
        sections=(
            ParadigmTableSection(
                title="Adverb",
                columns=("Degree", "Form"),
                rows=table_rows,
            ),
        )
    )
